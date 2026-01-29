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
from hardwarextractor.scrape.service import scrape_specs
from hardwarextractor.scrape.engines.detector import AntiBotDetector
from hardwarextractor.validate.validator import validate_specs


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
            events.append(OrchestratorEvent(status="SCRAPE", progress=60, log="Scrape complete"))

        except Exception as exc:  # noqa: BLE001
            error_msg = str(exc)

            # Check if it's an anti-bot error
            if self._antibot_detector.is_antibot_error(error_msg):
                self._emit(Event.source_antibot(source_name, "Detected anti-bot protection"))
                # Mark domain as blocked for future requests
                self.mark_domain_blocked(candidate.source_url)
            else:
                self._emit(Event.source_failed(source_name, error_msg))

            self._emit(Event.error_recoverable(error_msg))
            events.append(OrchestratorEvent(status="ERROR_RECOVERABLE", progress=100, log=error_msg))
            return events

        # Create component record
        # Confianza basada en el tier de la fuente, no en la clasificación
        source_confidence = SOURCE_TIER_CONFIDENCE.get(candidate.source_tier, 0.0)

        # Fecha de los datos: catálogo usa fecha fija, scraping usa fecha actual
        if candidate.source_tier == SourceTier.CATALOG:
            data_date = CATALOG_LAST_UPDATED
        else:
            data_date = date.today().isoformat()

        component = ComponentRecord(
            component_id=fingerprint(candidate.source_url),
            input_raw=self.last_input_raw or "",
            input_normalized=self.last_input_normalized or "",
            component_type=component_type,
            canonical=candidate.canonical,
            exact_match=True,  # Si llegamos aquí, encontramos el componente
            source_tier=candidate.source_tier,
            source_confidence=source_confidence,
            data_date=data_date,
            specs=specs,
            source_url=candidate.source_url,
            source_name=candidate.source_name,
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
