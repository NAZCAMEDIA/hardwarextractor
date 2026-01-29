from __future__ import annotations

from typing import Callable, List, Optional

from hardwarextractor.aggregate.aggregator import aggregate_components
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.classifier.heuristic import classify_component
from hardwarextractor.core.events import Event, EventType
from hardwarextractor.core.source_chain import (
    FetchEngine,
    Source,
    SourceChainManager,
)
from datetime import date

from hardwarextractor.models.schemas import (
    CATALOG_LAST_UPDATED,
    ComponentRecord,
    ComponentType,
    OrchestratorEvent,
    ResolveCandidate,
    SourceTier,
    SOURCE_TIER_CONFIDENCE,
)
from hardwarextractor.normalize.input import fingerprint, normalize_input
from hardwarextractor.resolver.resolver import resolve_component
from hardwarextractor.app.config import AppConfig, DEFAULT_CONFIG
from hardwarextractor.scrape.service import scrape_specs, set_log_callback
from hardwarextractor.scrape.engines.detector import AntiBotDetector
from hardwarextractor.validate.validator import validate_specs
from hardwarextractor.data.reference_urls import get_reference_url


# Type for event callback
EventCallback = Callable[[Event], None]


class Orchestrator:
    """Orchestrates the component analysis pipeline.

    Supports both legacy OrchestratorEvent (for backwards compatibility)
    and new Event system with callbacks for detailed logging.
    """

    def __init__(
        self,
        cache: Optional[SQLiteCache] = None,
        scrape_fn=None,
        config: AppConfig = DEFAULT_CONFIG,
        event_callback: Optional[EventCallback] = None,
    ) -> None:
        self.cache = cache
        self.scrape_fn = scrape_fn or scrape_specs
        self.config = config
        self.components: List[ComponentRecord] = []
        self.last_candidates: List[ResolveCandidate] = []
        self.last_input_raw: Optional[str] = None
        self.last_input_normalized: Optional[str] = None
        self.last_component_type = None
        self.last_confidence: float = 0.0
        self._event_callback = event_callback
        self._source_chain_manager = SourceChainManager()
        self._antibot_detector = AntiBotDetector()

        # Configurar callback para logs del servicio de scrape
        set_log_callback(self._on_scrape_log)

    def _on_scrape_log(self, level: str, message: str) -> None:
        """Handle log messages from scrape service."""
        if self._event_callback:
            # Convertir logs de scrape en eventos
            self._emit(Event.log(level, message))

    def set_event_callback(self, callback: EventCallback) -> None:
        """Set the callback for detailed events."""
        self._event_callback = callback

    def _emit(self, event: Event) -> None:
        """Emit an event to the callback if set."""
        if self._event_callback:
            self._event_callback(event)

    def process_input(self, input_raw: str) -> List[OrchestratorEvent]:
        """Process a raw input string through the analysis pipeline.

        Args:
            input_raw: The raw user input (e.g., "Corsair CMK32GX4M2B3200C16")

        Returns:
            List of OrchestratorEvent for legacy compatibility
        """
        events: List[OrchestratorEvent] = []
        self.last_input_raw = input_raw

        # Emit detailed event
        self._emit(Event.normalizing(input_raw))

        normalized = normalize_input(input_raw)
        self.last_input_normalized = normalized

        events.append(OrchestratorEvent(status="NORMALIZE_INPUT", progress=10, log="Input normalized"))

        # Classify component type
        component_type, confidence = classify_component(normalized)
        self.last_component_type = component_type
        self.last_confidence = confidence

        self._emit(Event.classified(component_type.value, confidence))
        events.append(OrchestratorEvent(
            status="CLASSIFY_COMPONENT",
            progress=20,
            log=f"Classified as {component_type.value} (confidence: {confidence:.0%})"
        ))

        # Resolve to candidates
        resolve_result = resolve_component(input_raw, component_type)
        if not resolve_result.candidates:
            self._emit(Event.error_recoverable("No candidates found for input"))
            events.append(OrchestratorEvent(status="ERROR_RECOVERABLE", progress=100, log="No candidates found"))
            return events

        self.last_candidates = resolve_result.candidates

        if not resolve_result.exact:
            self._emit(Event.needs_selection([
                {"brand": c.canonical.get("brand", ""), "model": c.canonical.get("model", ""), "url": c.source_url}
                for c in self.last_candidates
            ]))
            events.append(OrchestratorEvent(
                status="NEEDS_USER_SELECTION",
                progress=40,
                log="Selection required",
                candidates=self.last_candidates
            ))
            return events

        return events + self._process_candidate(self.last_candidates[0], component_type, confidence)

    def select_candidate(self, index: int, component_type=None, confidence: Optional[float] = None) -> List[OrchestratorEvent]:
        """Select a candidate by index for processing.

        Args:
            index: Index of the candidate to select (must be >= 0)
            component_type: Override component type (optional)
            confidence: Override confidence (optional)

        Returns:
            List of OrchestratorEvent for legacy compatibility
        """
        if index < 0 or index >= len(self.last_candidates):
            self._emit(Event.error_recoverable("Candidate index out of range"))
            return [OrchestratorEvent(status="ERROR_RECOVERABLE", progress=100, log="Candidate index out of range")]

        candidate = self.last_candidates[index]
        selected_type = component_type or self.last_component_type
        selected_confidence = confidence if confidence is not None else self.last_confidence

        self._emit(Event.candidate_selected(index, candidate.source_url))
        return self._process_candidate(candidate, selected_type, selected_confidence)

    def _process_candidate(
        self,
        candidate: ResolveCandidate,
        component_type: ComponentType,
        confidence: float,
    ) -> List[OrchestratorEvent]:
        """Process a selected candidate through scraping and aggregation.

        Args:
            candidate: The resolved candidate to process
            component_type: The classified component type
            confidence: Classification confidence

        Returns:
            List of OrchestratorEvent for legacy compatibility
        """
        events: List[OrchestratorEvent] = []
        events.append(OrchestratorEvent(status="RESOLVE_ENTITY", progress=35, log="Candidate selected"))

        # Emit source trying event
        source_name = candidate.spider_name
        self._emit(Event.source_trying(source_name, candidate.source_url))

        # Determine if Playwright should be used
        use_playwright = self.should_use_playwright(candidate)

        specs = []
        actual_source_tier = candidate.source_tier
        actual_source_url = candidate.source_url
        actual_source_name = candidate.source_name

        try:
            specs = self.scrape_fn(
                candidate.spider_name,
                candidate.source_url,
                cache=self.cache,
                enable_tier2=self.config.enable_tier2,
                user_agent=self.config.user_agent,
                retries=self.config.retries,
                throttle_seconds_by_domain=self.config.throttle_seconds_by_domain,
                use_playwright_fallback=use_playwright,
            )
            validate_specs(specs)

            # Emit success event
            self._emit(Event.source_success(source_name, len(specs)))

        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)

            # Check if it's an anti-bot error
            if self._antibot_detector.is_antibot_error(error_msg):
                self._emit(Event.source_antibot(source_name, "Detected anti-bot protection"))
                self.mark_domain_blocked(candidate.source_url)
            else:
                self._emit(Event.source_failed(source_name, error_msg))

        # Si no se obtuvieron specs, intentar fallback a sitios de referencia
        if not specs:
            self._emit(Event.error_recoverable(f"No specs from {source_name}, trying fallback sources..."))
            events.append(OrchestratorEvent(status="FALLBACK", progress=50, log="Trying reference sources..."))

            model_name = candidate.canonical.get("model", "")
            component_type_str = component_type.value if hasattr(component_type, 'value') else str(component_type)

            # PASO 1: Intentar URL de referencia directa conocida (TechPowerUp)
            reference_url = get_reference_url(component_type_str, model_name)
            if reference_url:
                self._emit(Event.source_trying("techpowerup_direct", reference_url))
                try:
                    # Determinar el spider correcto
                    spider_name = "techpowerup_gpu_spider" if component_type_str == "GPU" else "techpowerup_cpu_spider"

                    specs = self.scrape_fn(
                        spider_name,
                        reference_url,
                        cache=self.cache,
                        enable_tier2=True,
                        user_agent=self.config.user_agent,
                        retries=2,
                        throttle_seconds_by_domain=self.config.throttle_seconds_by_domain,
                        use_playwright_fallback=True,
                    )

                    if specs:
                        self._emit(Event.source_success("TechPowerUp", len(specs)))
                        actual_source_tier = SourceTier.REFERENCE
                        actual_source_url = reference_url
                        actual_source_name = "TechPowerUp"

                except Exception as e:  # noqa: BLE001
                    self._emit(Event.source_failed("TechPowerUp", str(e)))

            # PASO 2: Si aún no hay specs, intentar el chain de fallback normal
            if not specs:
                fallback_chain = self._source_chain_manager.get_chain(component_type)

                for fallback_source in fallback_chain:
                    # Saltar si es el mismo source o si es CATALOG
                    if fallback_source.spider_name == candidate.spider_name:
                        continue
                    if fallback_source.source_type.value == "CATALOG":
                        continue

                    self._emit(Event.source_trying(fallback_source.name, f"Fallback: {fallback_source.spider_name}"))

                    try:
                        # Construir URL de búsqueda para el fallback
                        brand = candidate.canonical.get("brand", "")
                        search_term = f"{brand} {model_name}".strip()

                        # Usar URL template si existe, sino skip
                        fallback_url = fallback_source.url_template.format(query=search_term) if fallback_source.url_template else None

                        if not fallback_url:
                            continue

                        specs = self.scrape_fn(
                            fallback_source.spider_name,
                            fallback_url,
                            cache=self.cache,
                            enable_tier2=True,
                            user_agent=self.config.user_agent,
                            retries=1,
                            throttle_seconds_by_domain=self.config.throttle_seconds_by_domain,
                            use_playwright_fallback=True,
                        )

                        if specs:
                            self._emit(Event.source_success(fallback_source.name, len(specs)))
                            actual_source_tier = SourceTier.REFERENCE
                            actual_source_url = fallback_url
                            actual_source_name = fallback_source.name
                            break

                    except Exception:  # noqa: BLE001
                        self._emit(Event.source_failed(fallback_source.name, "Fallback failed"))
                        continue

        if not specs:
            # PASO FINAL: Usar datos del catálogo como último recurso
            self._emit(Event.source_trying("catalog_fallback", "Using catalog data as fallback"))
            catalog_specs = self._build_specs_from_catalog(candidate, component_type)
            if catalog_specs:
                specs = catalog_specs
                actual_source_tier = SourceTier.CATALOG
                actual_source_url = candidate.source_url
                actual_source_name = "Catálogo interno"
                self._emit(Event.source_success("catalog_fallback", len(specs)))
            else:
                self._emit(Event.error_recoverable("No specs found from any source"))
                events.append(OrchestratorEvent(status="ERROR_RECOVERABLE", progress=100, log="No specs found"))
                return events

        events.append(OrchestratorEvent(status="SCRAPE", progress=60, log=f"Scrape complete ({len(specs)} specs)"))

        # Create component record
        # Confianza basada en el tier de la fuente real (puede ser fallback)
        source_confidence = SOURCE_TIER_CONFIDENCE.get(actual_source_tier, 0.0)

        # Fecha de los datos: catálogo usa fecha fija, scraping usa fecha actual
        if actual_source_tier == SourceTier.CATALOG:
            data_date = CATALOG_LAST_UPDATED
        else:
            data_date = date.today().isoformat()

        component = ComponentRecord(
            component_id=fingerprint(actual_source_url),
            input_raw=self.last_input_raw or "",
            input_normalized=self.last_input_normalized or "",
            component_type=component_type,
            canonical=candidate.canonical,
            exact_match=True,  # Si llegamos aquí, encontramos el componente
            source_tier=actual_source_tier,
            source_confidence=source_confidence,
            data_date=data_date,
            specs=specs,
            source_url=actual_source_url,
            source_name=actual_source_name,
        )

        # Handle stacking vs replacement
        is_multi = getattr(component_type, "value", component_type) in ["RAM", "DISK"]
        if not is_multi:
            self.components = [c for c in self.components if c.component_type != component_type]
        self.components.append(component)

        # Aggregate and emit ready event
        ficha = aggregate_components(self.components)
        self._emit(Event.ready_to_add({
            "component_id": component.component_id,
            "type": component_type.value,
            "brand": component.canonical.get("brand", ""),
            "model": component.canonical.get("model", ""),
            "specs_count": len(specs),
        }))

        events.append(OrchestratorEvent(
            status="READY_TO_ADD",
            progress=90,
            log="Ready to add",
            component_result=component,
            ficha_update=ficha
        ))
        return events

    def get_source_chain(self, component_type: ComponentType) -> List[Source]:
        """Get the source chain for a component type.

        Args:
            component_type: The component type

        Returns:
            Ordered list of sources to try
        """
        return self._source_chain_manager.get_chain(component_type)

    def reset_blocked_domains(self) -> None:
        """Reset the blocked domains list."""
        self._source_chain_manager._blocked_domains.clear()

    def should_use_playwright(self, candidate: ResolveCandidate) -> bool:
        """Check if Playwright should be used for this candidate.

        Args:
            candidate: The candidate to check

        Returns:
            True if Playwright should be used
        """
        source = self._source_chain_manager.get_source_for_candidate(
            self.last_component_type, candidate
        )
        if source:
            return self._source_chain_manager.should_use_playwright(
                source, candidate.source_url
            )
        return self._source_chain_manager.is_domain_blocked(candidate.source_url)

    def mark_domain_blocked(self, url: str) -> None:
        """Mark a domain as blocked due to anti-bot detection.

        Args:
            url: The URL whose domain should be blocked
        """
        self._source_chain_manager.mark_domain_blocked(url)

    def _build_specs_from_catalog(
        self,
        candidate: ResolveCandidate,
        component_type: ComponentType,
    ) -> List:
        """Build basic specs from catalog data when scraping fails.

        Args:
            candidate: The resolved candidate with catalog data
            component_type: The component type

        Returns:
            List of SpecField objects extracted from catalog canonical data
        """
        from hardwarextractor.models.schemas import SpecField, SpecStatus, SourceTier
        import re

        specs = []
        canonical = candidate.canonical
        source_url = candidate.source_url

        def make_spec(key: str, label: str, value: str, unit: str = None) -> SpecField:
            return SpecField(
                key=key,
                label=label,
                value=value,
                unit=unit,
                status=SpecStatus.EXTRACTED_OFFICIAL,
                source_tier=SourceTier.CATALOG,
                source_name="Catálogo interno",
                source_url=source_url,
                confidence=0.6,
            )

        # Extraer specs básicas del canonical
        brand = canonical.get("brand", "")
        model = canonical.get("model", "")
        part_number = canonical.get("part_number", "")

        if brand:
            specs.append(make_spec("brand", "Fabricante", brand))
        if model:
            specs.append(make_spec("model", "Modelo", model))
        if part_number:
            specs.append(make_spec("part_number", "Número de parte", part_number))

        # Parsear información adicional del modelo para RAM
        if component_type == ComponentType.RAM and model:
            # Extraer capacidad (ej: "32GB", "16GB")
            capacity_match = re.search(r'(\d+)\s*GB', model, re.IGNORECASE)
            if capacity_match:
                specs.append(make_spec("ram.capacity_gb", "Capacidad", capacity_match.group(1), "GB"))

            # Extraer velocidad (ej: "6000MHz", "3200MHz") - mapper espera valor numérico en MT/s
            speed_match = re.search(r'(\d{4,5})\s*MHz', model, re.IGNORECASE)
            if speed_match:
                specs.append(make_spec("ram.speed_effective_mt_s", "Velocidad efectiva", int(speed_match.group(1)), "MT/s"))

            # Extraer tipo DDR (ej: "DDR5", "DDR4")
            ddr_match = re.search(r'(DDR[45])', model, re.IGNORECASE)
            if ddr_match:
                specs.append(make_spec("ram.type", "Tipo", ddr_match.group(1).upper()))

        # Parsear información adicional del part_number para RAM Corsair
        if component_type == ComponentType.RAM and part_number:
            pn_upper = part_number.upper()

            # Capacidad del part number (CMK32G... = 32GB)
            cap_match = re.search(r'CMK(\d+)G', pn_upper)
            if cap_match and not any(s.key == "ram.capacity_gb" for s in specs):
                specs.append(make_spec("ram.capacity_gb", "Capacidad", cap_match.group(1), "GB"))

            # DDR version (X4 = DDR4, X5 = DDR5)
            if 'X5' in pn_upper and not any(s.key == "ram.type" for s in specs):
                specs.append(make_spec("ram.type", "Tipo", "DDR5"))
            elif 'X4' in pn_upper and not any(s.key == "ram.type" for s in specs):
                specs.append(make_spec("ram.type", "Tipo", "DDR4"))

            # Módulos (M2 = 2 módulos)
            mod_match = re.search(r'M(\d)', pn_upper)
            if mod_match:
                specs.append(make_spec("ram.modules", "Módulos", mod_match.group(1)))

            # Velocidad del part number (B6000 = 6000MT/s) - valor numérico
            speed_pn_match = re.search(r'[AB](\d{4,5})', pn_upper)
            if speed_pn_match and not any(s.key == "ram.speed_effective_mt_s" for s in specs):
                specs.append(make_spec("ram.speed_effective_mt_s", "Velocidad efectiva", int(speed_pn_match.group(1)), "MT/s"))

            # CAS Latency (C36 = 36) - mapper espera valor numérico
            cl_match = re.search(r'C(\d{2})', pn_upper)
            if cl_match:
                specs.append(make_spec("ram.latency_cl", "Latencia", int(cl_match.group(1))))

        # JEDEC Standards para RAM (voltaje y pines estándar por tipo DDR)
        # Fuente: JEDEC JESD79 series specifications
        # https://www.jedec.org/standards-documents/docs/jesd-79-5b (DDR5)
        # https://www.jedec.org/standards-documents/docs/jesd-79-4c (DDR4)
        if component_type == ComponentType.RAM:
            JEDEC_STANDARDS = {
                "DDR5": {"voltage": 1.1, "pins": 288},   # JESD79-5: 1.1V, 288-pin DIMM
                "DDR4": {"voltage": 1.2, "pins": 288},   # JESD79-4: 1.2V, 288-pin DIMM
                "DDR3": {"voltage": 1.5, "pins": 240},   # JESD79-3: 1.5V, 240-pin DIMM
                "DDR2": {"voltage": 1.8, "pins": 240},   # JESD79-2: 1.8V, 240-pin DIMM
            }

            # Buscar el tipo DDR detectado
            ddr_type = None
            for s in specs:
                if s.key == "ram.type" and s.value in JEDEC_STANDARDS:
                    ddr_type = s.value
                    break

            if ddr_type:
                jedec = JEDEC_STANDARDS[ddr_type]

                # Agregar voltaje estándar si no existe
                if not any(s.key == "ram.voltage_v" for s in specs):
                    specs.append(make_spec("ram.voltage_v", "Voltaje", jedec["voltage"], "V"))

                # Agregar número de pines estándar si no existe
                if not any(s.key == "ram.pins" for s in specs):
                    specs.append(make_spec("ram.pins", "Número de pines", jedec["pins"]))

        return specs if len(specs) > 3 else []  # Solo retornar si tenemos datos útiles
