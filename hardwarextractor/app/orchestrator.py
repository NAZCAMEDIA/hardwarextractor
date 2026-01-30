from __future__ import annotations

import re
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
    SpecField,
    SpecStatus,
)
from hardwarextractor.normalize.input import fingerprint, normalize_input
from hardwarextractor.resolver.resolver import resolve_component
from hardwarextractor.app.config import AppConfig, DEFAULT_CONFIG
from hardwarextractor.scrape.service import scrape_specs, set_log_callback
from hardwarextractor.scrape.engines.detector import AntiBotDetector
from hardwarextractor.validate.validator import validate_specs
from hardwarextractor.data.reference_urls import get_reference_url
from hardwarextractor.data.spec_templates import apply_template_to_specs
from hardwarextractor.core.cross_validator import CrossValidator, CrossValidationResult
from hardwarextractor.data.catalog_writer import add_validated_component


# Type for event callback
EventCallback = Callable[[Event], None]

# JEDEC Standards para RAM (voltaje y pines estandar por tipo DDR)
# Fuente: JEDEC JESD79 series specifications
# https://www.jedec.org/standards-documents/docs/jesd-79-5b (DDR5)
# https://www.jedec.org/standards-documents/docs/jesd-79-4c (DDR4)
JEDEC_STANDARDS = {
    "DDR5": {"voltage": 1.1, "pins": 288},   # JESD79-5: 1.1V, 288-pin DIMM
    "DDR4": {"voltage": 1.2, "pins": 288},   # JESD79-4: 1.2V, 288-pin DIMM
    "DDR3": {"voltage": 1.5, "pins": 240},   # JESD79-3: 1.5V, 240-pin DIMM
    "DDR2": {"voltage": 1.8, "pins": 240},   # JESD79-2: 1.8V, 240-pin DIMM
}


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
        self._cross_validator = CrossValidator(
            scrape_fn=self.scrape_fn,
            event_callback=self._emit,
            min_sources_for_validation=2,
            min_confidence_for_persist=0.6,
        )

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
            # No candidates in catalog - try web search
            self._emit(Event.log("info", "No catalog match, trying web search..."))
            events.append(OrchestratorEvent(status="WEB_SEARCH", progress=30, log="Searching web sources..."))

            web_candidate = self._search_web_sources(input_raw, component_type)
            if web_candidate:
                resolve_result.candidates = [web_candidate]
                self._emit(Event.log("info", f"Found via web search: {web_candidate.source_name}"))
            else:
                self._emit(Event.error_recoverable("No candidates found in catalog or web"))
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

        # Check if candidate already has specs from web search
        if candidate.web_search_specs:
            specs = candidate.web_search_specs
            self._emit(Event.source_success(source_name, len(specs)))
            events.append(OrchestratorEvent(status="WEB_SEARCH_COMPLETE", progress=60, log=f"Web search specs ({len(specs)} fields)"))
        else:
            # Normal scraping flow
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

            # NOTA: El fallback chain genérico (URLs de búsqueda) está deshabilitado
            # porque produce datos basura al parsear páginas de resultados de búsqueda
            # como si fueran páginas de producto.
            # Solo usamos URLs de referencia directas (TechPowerUp) + catálogo interno.

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

        # NOTE: Templates are applied at export time, not during processing
        # This allows internal calculations to work without "unknown" string values

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

    def _search_web_sources(
        self,
        input_raw: str,
        component_type: ComponentType,
    ) -> Optional[ResolveCandidate]:
        """Search web sources when no catalog candidates found.

        Uses cross-validation: queries 2+ sources and only validates
        data that matches between sources. Validated data is automatically
        added to the catalog.

        Args:
            input_raw: The raw user input
            component_type: The classified component type

        Returns:
            ResolveCandidate if found, None otherwise
        """
        from urllib.parse import quote_plus

        # Get reference sources for this component type
        reference_sources = self._source_chain_manager.get_reference_sources(component_type)

        if not reference_sources:
            return None

        # Collect sources for cross-validation
        sources_to_validate: List[tuple] = []  # [(source_name, spider_name, url), ...]

        for source in sorted(reference_sources, key=lambda s: s.priority)[:4]:  # Max 4 sources
            if not source.url_template or not source.spider_name:
                continue

            search_query = quote_plus(input_raw)
            search_url = source.url_template.format(query=search_query)
            sources_to_validate.append((source.name, source.spider_name, search_url))

        # If we have 2+ sources, use cross-validation
        if len(sources_to_validate) >= 2:
            self._emit(Event.log("info", f"Cross-validating {input_raw} from {len(sources_to_validate)} sources"))

            cv_result = self._cross_validator.validate_from_sources(
                component_input=input_raw,
                component_type=component_type,
                sources=sources_to_validate,
                cache=self.cache,
            )

            # If we have validated specs from cross-validation
            if cv_result.validated_specs:
                specs = cv_result.to_spec_fields()

                # Extract brand/model
                brand = self._infer_brand_from_part_number(input_raw)
                model = input_raw

                # Try to get brand/model from successful sources
                for sr in cv_result.all_source_results:
                    if sr.success:
                        for spec in sr.specs:
                            if spec.key == "brand" and spec.value:
                                brand = spec.value
                            elif spec.key == "model" and spec.value:
                                model = spec.value
                        if brand and model != input_raw:
                            break

                # If should_persist, add to catalog
                if cv_result.should_persist:
                    added = add_validated_component(cv_result, brand, model, input_raw)
                    if added:
                        self._emit(Event.log("info", f"Added {brand} {model} to validated catalog"))

                # Get the best source URL
                best_source = next(
                    (sr for sr in cv_result.all_source_results if sr.success),
                    None
                )
                source_url = best_source.source_url if best_source else ""
                source_name = best_source.source_name if best_source else "Cross-validated"

                return ResolveCandidate(
                    canonical={
                        "brand": brand,
                        "model": model,
                        "part_number": input_raw,
                    },
                    source_url=source_url,
                    source_name=source_name,
                    source_tier=SourceTier.REFERENCE,
                    spider_name="cross_validated",
                    score=sum(vs.confidence for vs in cv_result.validated_specs) / len(cv_result.validated_specs),
                    web_search_specs=specs,
                )

        # Fallback to single-source search if cross-validation didn't work
        for source in sorted(reference_sources, key=lambda s: s.priority):
            if not source.url_template or not source.spider_name:
                continue

            search_query = quote_plus(input_raw)
            search_url = source.url_template.format(query=search_query)

            self._emit(Event.source_trying(source.name, search_url))

            try:
                use_playwright = source.engine.value == "playwright"

                specs = self.scrape_fn(
                    source.spider_name,
                    search_url,
                    cache=self.cache,
                    enable_tier2=True,
                    user_agent=self.config.user_agent,
                    retries=2,
                    throttle_seconds_by_domain=self.config.throttle_seconds_by_domain,
                    use_playwright_fallback=use_playwright,
                )

                if specs and len(specs) >= 3:
                    self._emit(Event.source_success(source.name, len(specs)))

                    brand = ""
                    model = ""
                    for spec in specs:
                        if spec.key == "brand":
                            brand = spec.value
                        elif spec.key == "model":
                            model = spec.value

                    if not brand:
                        brand = self._infer_brand_from_part_number(input_raw)
                    if not model:
                        model = input_raw

                    return ResolveCandidate(
                        canonical={
                            "brand": brand,
                            "model": model,
                            "part_number": input_raw,
                        },
                        source_url=search_url,
                        source_name=source.name,
                        source_tier=source.tier,
                        spider_name=source.spider_name,
                        score=0.7,
                        web_search_specs=specs,
                    )

            except Exception as e:
                error_msg = str(e)
                self._emit(Event.source_failed(source.name, error_msg))

                if self._antibot_detector.is_antibot_error(error_msg):
                    self._emit(Event.source_antibot(source.name, "Anti-bot detected"))
                    self.mark_domain_blocked(search_url)

                continue

        return None

    def _infer_brand_from_part_number(self, part_number: str) -> str:
        """Infer brand from part number prefix patterns.

        Args:
            part_number: The raw part number input

        Returns:
            Brand name if recognized, empty string otherwise
        """
        pn_upper = part_number.upper()

        # RAM brand prefixes
        ram_prefixes = {
            "CT": "Crucial",
            "CMK": "Corsair",
            "CMW": "Corsair",
            "CMH": "Corsair",
            "F5-": "G.Skill",
            "F4-": "G.Skill",
            "KF": "Kingston",
            "KVR": "Kingston",
            "AD5": "ADATA",
            "AD4": "ADATA",
            "PV": "Patriot",
            "TL": "TeamGroup",
            "TF": "TeamGroup",
            "BL": "Crucial Ballistix",
        }

        # GPU brand patterns
        if "GEFORCE" in pn_upper or "RTX" in pn_upper or "GTX" in pn_upper:
            return "NVIDIA"
        if "RADEON" in pn_upper or "RX " in pn_upper:
            return "AMD"
        if "ARC " in pn_upper:
            return "Intel"

        # CPU brand patterns
        if "CORE" in pn_upper or "I5-" in pn_upper or "I7-" in pn_upper or "I9-" in pn_upper:
            return "Intel"
        if "RYZEN" in pn_upper:
            return "AMD"

        # Mainboard brand patterns
        if "ROG " in pn_upper or "TUF " in pn_upper:
            return "ASUS"
        if "MEG " in pn_upper or "MAG " in pn_upper or "PRO " in pn_upper and "MSI" in pn_upper:
            return "MSI"
        if "AORUS" in pn_upper:
            return "Gigabyte"
        if "TAICHI" in pn_upper:
            return "ASRock"

        # Storage brand patterns
        if "WD " in pn_upper or "WDS" in pn_upper:
            return "Western Digital"
        if "FIRECUDA" in pn_upper:
            return "Seagate"
        if "990 " in pn_upper or "980 " in pn_upper or "970 " in pn_upper:
            return "Samsung"

        # Check RAM prefixes
        for prefix, brand in ram_prefixes.items():
            if pn_upper.startswith(prefix):
                return brand

        return ""

    def _build_specs_from_catalog(
        self,
        candidate: ResolveCandidate,
        component_type: ComponentType,
    ) -> List[SpecField]:
        """Build basic specs from catalog data when scraping fails.

        Args:
            candidate: The resolved candidate with catalog data
            component_type: The component type

        Returns:
            List of SpecField objects extracted from catalog canonical data
        """
        specs: List[SpecField] = []
        canonical = candidate.canonical
        source_url = candidate.source_url

        def make_spec(key: str, label: str, value, unit: str = None) -> SpecField:
            return SpecField(
                key=key,
                label=label,
                value=value,
                unit=unit,
                status=SpecStatus.EXTRACTED_OFFICIAL,
                source_tier=SourceTier.CATALOG,
                source_name="Catalogo interno",
                source_url=source_url,
                confidence=0.6,
            )

        def has_spec(key: str) -> bool:
            return any(s.key == key for s in specs)

        def get_spec_value(key: str):
            for s in specs:
                if s.key == key:
                    return s.value
            return None

        # Extraer specs basicas del canonical
        brand = canonical.get("brand", "")
        model = canonical.get("model", "")
        part_number = canonical.get("part_number", "")

        if brand:
            specs.append(make_spec("brand", "Fabricante", brand))
        if model:
            specs.append(make_spec("model", "Modelo", model))
        if part_number:
            specs.append(make_spec("part_number", "Numero de parte", part_number))

        # Para CPUs, GPUs y otros, extraer info adicional del modelo
        if component_type == ComponentType.CPU:
            if model:
                # Extraer generación Intel (14900K -> Gen 14)
                if match := re.search(r'i[3579]-?(\d{2})\d{3}', model, re.IGNORECASE):
                    gen = match.group(1)
                    specs.append(make_spec("cpu.generation", "Generación", f"Gen {gen}"))
                # Extraer sufijo (K, KF, X, etc.)
                if match := re.search(r'(\d{4,5})([KFXU]+)', model, re.IGNORECASE):
                    suffix = match.group(2).upper()
                    if 'K' in suffix:
                        specs.append(make_spec("cpu.unlocked", "Desbloqueado", "Sí"))
                    if 'F' in suffix:
                        specs.append(make_spec("cpu.integrated_graphics", "Gráficos integrados", "No"))
                # Detectar familia (i9, i7, Ryzen 9, etc.)
                if match := re.search(r'(i[3579]|Ryzen\s*[3579])', model, re.IGNORECASE):
                    specs.append(make_spec("cpu.family", "Familia", match.group(1)))

        elif component_type == ComponentType.GPU:
            if model:
                # Extraer serie (RTX 4090, RX 7900, Arc A770)
                if match := re.search(r'(RTX|GTX|RX|Arc)\s*([A-Z]?\d{3,4})', model, re.IGNORECASE):
                    series = match.group(1).upper()
                    number = match.group(2)
                    specs.append(make_spec("gpu.series", "Serie", f"{series} {number}"))
                # Detectar variante (Ti, XT, Super)
                if match := re.search(r'(Ti|XT|Super|SUPER)', model, re.IGNORECASE):
                    specs.append(make_spec("gpu.variant", "Variante", match.group(1)))

        # === Parsear informacion adicional para DISK ===
        if component_type == ComponentType.DISK:
            # Parsear del modelo: "990 PRO 2TB"
            if model:
                if match := re.search(r'(\d+)\s*TB', model, re.IGNORECASE):
                    specs.append(make_spec("disk.capacity_tb", "Capacidad", int(match.group(1)), "TB"))
                elif match := re.search(r'(\d+)\s*GB', model, re.IGNORECASE):
                    specs.append(make_spec("disk.capacity_gb", "Capacidad", int(match.group(1)), "GB"))
                # Detectar tipo de disco
                if 'PRO' in model.upper():
                    specs.append(make_spec("disk.line", "Linea", "PRO"))
                elif 'EVO' in model.upper():
                    specs.append(make_spec("disk.line", "Linea", "EVO"))

            # Parsear del part_number para Samsung: MZ-V9P2T0BW
            if part_number:
                pn_upper = part_number.upper()

                # Samsung NVMe: MZ-V = NVMe, MZ-7 = SATA
                if pn_upper.startswith('MZ-V'):
                    specs.append(make_spec("disk.interface", "Interfaz", "NVMe PCIe"))
                    specs.append(make_spec("disk.form_factor", "Factor de forma", "M.2 2280"))
                    # V9P = 990 PRO, V8P = 980 PRO, V7S = 970 EVO
                    if 'V9P' in pn_upper:
                        specs.append(make_spec("disk.series", "Serie", "990 PRO"))
                        specs.append(make_spec("disk.pcie_gen", "Generacion PCIe", "4.0"))
                    elif 'V8P' in pn_upper:
                        specs.append(make_spec("disk.series", "Serie", "980 PRO"))
                        specs.append(make_spec("disk.pcie_gen", "Generacion PCIe", "4.0"))
                    elif 'V7S' in pn_upper:
                        specs.append(make_spec("disk.series", "Serie", "970 EVO Plus"))
                        specs.append(make_spec("disk.pcie_gen", "Generacion PCIe", "3.0"))

                elif pn_upper.startswith('MZ-7'):
                    specs.append(make_spec("disk.interface", "Interfaz", "SATA III"))
                    specs.append(make_spec("disk.form_factor", "Factor de forma", "2.5\""))

                # Capacidad: 2T0 = 2TB, 1T0 = 1TB, 500 = 500GB
                if match := re.search(r'(\d)T0', pn_upper):
                    specs.append(make_spec("disk.capacity_tb", "Capacidad", int(match.group(1)), "TB"))
                elif match := re.search(r'(\d{3})G', pn_upper):
                    specs.append(make_spec("disk.capacity_gb", "Capacidad", int(match.group(1)), "GB"))

                # WD Black SN850X: WDS200T2X0E
                if pn_upper.startswith('WDS'):
                    if match := re.search(r'WDS(\d)00T', pn_upper):
                        specs.append(make_spec("disk.capacity_tb", "Capacidad", int(match.group(1)), "TB"))
                    if '2X0E' in pn_upper:
                        specs.append(make_spec("disk.series", "Serie", "Black SN850X"))
                        specs.append(make_spec("disk.interface", "Interfaz", "NVMe PCIe 4.0"))

            return specs if len(specs) >= 3 else []

        # Retornar para otros tipos si tenemos al menos brand, model y part_number
        if component_type != ComponentType.RAM:
            return specs if len(specs) >= 3 else []

        # Parsear informacion adicional del modelo para RAM
        if model:
            if match := re.search(r'(\d+)\s*GB', model, re.IGNORECASE):
                specs.append(make_spec("ram.capacity_gb", "Capacidad", match.group(1), "GB"))

            if match := re.search(r'(\d{4,5})\s*MHz', model, re.IGNORECASE):
                specs.append(make_spec("ram.speed_effective_mt_s", "Velocidad efectiva", int(match.group(1)), "MT/s"))

            if match := re.search(r'(DDR[45])', model, re.IGNORECASE):
                specs.append(make_spec("ram.type", "Tipo", match.group(1).upper()))

        # Parsear informacion adicional del part_number para RAM
        if part_number:
            pn_upper = part_number.upper()

            # === Corsair patterns (CMK32GX5M2B6000C36) ===
            if (match := re.search(r'CMK(\d+)G', pn_upper)) and not has_spec("ram.capacity_gb"):
                specs.append(make_spec("ram.capacity_gb", "Capacidad", match.group(1), "GB"))

            if not has_spec("ram.type"):
                if 'X5' in pn_upper:
                    specs.append(make_spec("ram.type", "Tipo", "DDR5"))
                elif 'X4' in pn_upper:
                    specs.append(make_spec("ram.type", "Tipo", "DDR4"))

            if match := re.search(r'M(\d)', pn_upper):
                specs.append(make_spec("ram.modules", "Modulos", match.group(1)))

            if (match := re.search(r'[AB](\d{4,5})', pn_upper)) and not has_spec("ram.speed_effective_mt_s"):
                specs.append(make_spec("ram.speed_effective_mt_s", "Velocidad efectiva", int(match.group(1)), "MT/s"))

            if match := re.search(r'C(\d{2})', pn_upper):
                specs.append(make_spec("ram.latency_cl", "Latencia", int(match.group(1))))

            # === G.Skill patterns (F5-6000J3038F16GX2-RS5K) ===
            # F5 = DDR5, F4 = DDR4
            if not has_spec("ram.type"):
                if pn_upper.startswith('F5'):
                    specs.append(make_spec("ram.type", "Tipo", "DDR5"))
                elif pn_upper.startswith('F4'):
                    specs.append(make_spec("ram.type", "Tipo", "DDR4"))

            # F5-6000 = 6000 MHz
            if (match := re.search(r'F[45]-(\d{4})', pn_upper)) and not has_spec("ram.speed_effective_mt_s"):
                specs.append(make_spec("ram.speed_effective_mt_s", "Velocidad efectiva", int(match.group(1)), "MT/s"))

            # J3038 = CL30-38-38
            if match := re.search(r'J(\d{2})(\d{2})', pn_upper):
                if not has_spec("ram.latency_cl"):
                    specs.append(make_spec("ram.latency_cl", "Latencia CL", int(match.group(1))))
                if not has_spec("ram.latency_trcd"):
                    specs.append(make_spec("ram.latency_trcd", "Latencia tRCD", int(match.group(2))))

            # F16GX2 = 16GB x 2 modules
            if match := re.search(r'F(\d+)GX(\d)', pn_upper):
                if not has_spec("ram.capacity_gb"):
                    total_gb = int(match.group(1)) * int(match.group(2))
                    specs.append(make_spec("ram.capacity_gb", "Capacidad", total_gb, "GB"))
                if not has_spec("ram.modules"):
                    specs.append(make_spec("ram.modules", "Modulos", match.group(2)))
                if not has_spec("ram.capacity_per_module"):
                    specs.append(make_spec("ram.capacity_per_module", "Capacidad por modulo", match.group(1), "GB"))

            # === Kingston Fury patterns (KF556C40BBK2-32) ===
            if (match := re.search(r'KF[45](\d{2})C(\d{2})', pn_upper)):
                if not has_spec("ram.speed_effective_mt_s"):
                    speed = int(match.group(1)) * 100  # 56 -> 5600
                    specs.append(make_spec("ram.speed_effective_mt_s", "Velocidad efectiva", speed, "MT/s"))
                if not has_spec("ram.latency_cl"):
                    specs.append(make_spec("ram.latency_cl", "Latencia CL", int(match.group(2))))
                if not has_spec("ram.type"):
                    if 'KF5' in pn_upper:
                        specs.append(make_spec("ram.type", "Tipo", "DDR5"))
                    elif 'KF4' in pn_upper:
                        specs.append(make_spec("ram.type", "Tipo", "DDR4"))

            # Kingston capacity: -32 = 32GB, K2 = 2 modules
            if (match := re.search(r'-(\d{2,3})$', pn_upper)) and not has_spec("ram.capacity_gb"):
                specs.append(make_spec("ram.capacity_gb", "Capacidad", int(match.group(1)), "GB"))
            if (match := re.search(r'K(\d)', pn_upper)) and not has_spec("ram.modules"):
                specs.append(make_spec("ram.modules", "Modulos", match.group(1)))

        # Aplicar estandares JEDEC segun tipo DDR detectado
        ddr_type = get_spec_value("ram.type")
        if ddr_type and ddr_type in JEDEC_STANDARDS:
            jedec = JEDEC_STANDARDS[ddr_type]

            if not has_spec("ram.voltage_v"):
                specs.append(make_spec("ram.voltage_v", "Voltaje", jedec["voltage"], "V"))

            if not has_spec("ram.pins"):
                specs.append(make_spec("ram.pins", "Numero de pines", jedec["pins"]))

        return specs if len(specs) > 3 else []
