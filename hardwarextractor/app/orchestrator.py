from __future__ import annotations

from typing import List, Optional

from hardwarextractor.aggregate.aggregator import aggregate_components
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.classifier.heuristic import classify_component
from hardwarextractor.models.schemas import ComponentRecord, OrchestratorEvent, ResolveCandidate
from hardwarextractor.normalize.input import fingerprint, normalize_input
from hardwarextractor.resolver.resolver import resolve_component
from hardwarextractor.app.config import AppConfig, DEFAULT_CONFIG
from hardwarextractor.scrape.service import scrape_specs
from hardwarextractor.validate.validator import validate_specs


class Orchestrator:
    def __init__(self, cache: Optional[SQLiteCache] = None, scrape_fn=None, config: AppConfig = DEFAULT_CONFIG) -> None:
        self.cache = cache
        self.scrape_fn = scrape_fn or scrape_specs
        self.config = config
        self.components: List[ComponentRecord] = []
        self.last_candidates: List[ResolveCandidate] = []
        self.last_input_raw: Optional[str] = None
        self.last_input_normalized: Optional[str] = None
        self.last_component_type = None
        self.last_confidence: float = 0.0

    def process_input(self, input_raw: str) -> List[OrchestratorEvent]:
        events: List[OrchestratorEvent] = []
        self.last_input_raw = input_raw
        normalized = normalize_input(input_raw)
        self.last_input_normalized = normalized

        events.append(OrchestratorEvent(status="NORMALIZE_INPUT", progress=10, log="Input normalized"))

        component_type, confidence = classify_component(normalized)
        self.last_component_type = component_type
        self.last_confidence = confidence
        events.append(OrchestratorEvent(status="CLASSIFY_COMPONENT", progress=20, log=f"Classified as {component_type.value}"))

        resolve_result = resolve_component(input_raw, component_type)
        if not resolve_result.candidates:
            events.append(OrchestratorEvent(status="ERROR_RECOVERABLE", progress=100, log="No candidates found"))
            return events

        self.last_candidates = resolve_result.candidates
        if not resolve_result.exact:
            events.append(OrchestratorEvent(status="NEEDS_USER_SELECTION", progress=40, log="Selection required", candidates=self.last_candidates))
            return events

        return events + self._process_candidate(self.last_candidates[0], component_type, confidence)

    def select_candidate(self, index: int, component_type=None, confidence: Optional[float] = None) -> List[OrchestratorEvent]:
        if index >= len(self.last_candidates):
            return [OrchestratorEvent(status="ERROR_RECOVERABLE", progress=100, log="Candidate index out of range")]
        candidate = self.last_candidates[index]
        selected_type = component_type or self.last_component_type
        selected_confidence = confidence if confidence is not None else self.last_confidence
        return self._process_candidate(candidate, selected_type, selected_confidence)

    def _process_candidate(self, candidate: ResolveCandidate, component_type, confidence: float) -> List[OrchestratorEvent]:
        events: List[OrchestratorEvent] = []
        events.append(OrchestratorEvent(status="RESOLVE_ENTITY", progress=35, log="Candidate selected"))

        try:
            specs = self.scrape_fn(
                candidate.spider_name,
                candidate.source_url,
                cache=self.cache,
                enable_tier2=self.config.enable_tier2,
                user_agent=self.config.user_agent,
                retries=self.config.retries,
                throttle_seconds_by_domain=self.config.throttle_seconds_by_domain,
            )
            validate_specs(specs)
            events.append(OrchestratorEvent(status="SCRAPE", progress=60, log="Scrape complete"))
        except Exception as exc:  # noqa: BLE001
            events.append(OrchestratorEvent(status="ERROR_RECOVERABLE", progress=100, log=str(exc)))
            return events

        component = ComponentRecord(
            component_id=fingerprint(candidate.source_url),
            input_raw=self.last_input_raw or "",
            input_normalized=self.last_input_normalized or "",
            component_type=component_type,
            classification_confidence=confidence,
            canonical=candidate.canonical,
            specs=specs,
        )
        is_multi = getattr(component_type, "value", component_type) in ["RAM", "DISK"]
        if not is_multi:
            self.components = [c for c in self.components if c.component_type != component_type]
        if is_multi:
            self.components.append(component)
        else:
            self.components.append(component)

        ficha = aggregate_components(self.components)
        events.append(OrchestratorEvent(status="READY_TO_ADD", progress=90, log="Ready to add", component_result=component, ficha_update=ficha))
        return events
