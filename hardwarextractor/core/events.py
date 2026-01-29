"""Event types and Event class for detailed pipeline logging."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    """Detailed event types for pipeline progress tracking."""

    # Normalization phase
    NORMALIZING = "normalizing"
    NORMALIZED = "normalized"

    # Classification phase
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"

    # Resolution phase
    RESOLVING = "resolving"
    CANDIDATES_FOUND = "candidates_found"
    CANDIDATE_SELECTED = "candidate_selected"
    EXACT_MATCH = "exact_match"
    NEEDS_SELECTION = "needs_selection"

    # SourceChain phase
    SOURCE_CHAIN_START = "source_chain_start"
    SOURCE_TRYING = "source_trying"
    SOURCE_SKIPPED = "source_skipped"
    SOURCE_SUCCESS = "source_success"
    SOURCE_EMPTY = "source_empty"
    SOURCE_FAILED = "source_failed"
    SOURCE_ANTIBOT = "source_antibot"
    SOURCE_TIMEOUT = "source_timeout"
    SOURCE_UPGRADING = "source_upgrading"
    CHAIN_EXHAUSTED = "chain_exhausted"

    # Extraction phase
    EXTRACTING = "extracting"
    EXTRACTED = "extracted"
    EXTRACTION_FAILED = "extraction_failed"

    # Validation phase
    VALIDATING = "validating"
    VALIDATED = "validated"
    VALIDATION_WARNING = "validation_warning"

    # Mapping phase
    MAPPING = "mapping"
    MAPPED = "mapped"

    # Calculation phase
    CALCULATING = "calculating"
    CALCULATED = "calculated"

    # Final states
    COMPLETE = "complete"
    COMPLETE_PARTIAL = "complete_partial"
    FAILED = "failed"

    # Error states
    ERROR_RECOVERABLE = "error_recoverable"
    ERROR_FATAL = "error_fatal"

    # Ficha operations
    FICHA_COMPONENT_ADDED = "ficha_component_added"
    FICHA_EXPORTED = "ficha_exported"
    FICHA_RESET = "ficha_reset"


# Progress percentages for each phase
PHASE_PROGRESS = {
    EventType.NORMALIZING: 5,
    EventType.NORMALIZED: 10,
    EventType.CLASSIFYING: 15,
    EventType.CLASSIFIED: 20,
    EventType.RESOLVING: 25,
    EventType.CANDIDATES_FOUND: 30,
    EventType.EXACT_MATCH: 35,
    EventType.NEEDS_SELECTION: 35,
    EventType.SOURCE_CHAIN_START: 40,
    EventType.SOURCE_TRYING: 45,
    EventType.SOURCE_SUCCESS: 60,
    EventType.EXTRACTING: 65,
    EventType.EXTRACTED: 70,
    EventType.VALIDATING: 75,
    EventType.VALIDATED: 80,
    EventType.MAPPING: 85,
    EventType.MAPPED: 90,
    EventType.CALCULATING: 92,
    EventType.CALCULATED: 95,
    EventType.COMPLETE: 100,
    EventType.COMPLETE_PARTIAL: 100,
    EventType.FAILED: 100,
}


@dataclass
class Event:
    """Detailed event emitted during pipeline execution.

    Attributes:
        type: The type of event (from EventType enum)
        message: Human-readable log message
        progress: Progress percentage (0-100)
        data: Optional additional data (varies by event type)
        source_index: For SOURCE_* events, the index in the chain (1-based)
        source_total: For SOURCE_* events, total sources in chain
        source_name: For SOURCE_* events, the provider name
        error: For error events, the error message
        recoverable: For error events, whether the error is recoverable
    """

    type: EventType
    message: str
    progress: int = 0
    data: Optional[dict[str, Any]] = None
    source_index: Optional[int] = None
    source_total: Optional[int] = None
    source_name: Optional[str] = None
    error: Optional[str] = None
    recoverable: bool = True

    def __post_init__(self):
        # Auto-calculate progress if not provided
        if self.progress == 0 and self.type in PHASE_PROGRESS:
            self.progress = PHASE_PROGRESS[self.type]

    def to_ipc(self) -> dict[str, Any]:
        """Convert to IPC JSON format for CLI communication."""
        result: dict[str, Any] = {
            "type": self._ipc_type(),
            "value": self.message,
        }

        if self.progress > 0:
            result["progress"] = self.progress

        if self.data:
            result["data"] = self.data

        if self.error:
            result["error"] = self.error
            result["recoverable"] = self.recoverable

        return result

    def _ipc_type(self) -> str:
        """Map EventType to IPC message type."""
        if self.type in (EventType.FAILED, EventType.ERROR_RECOVERABLE, EventType.ERROR_FATAL):
            return "error"
        if self.type == EventType.CANDIDATES_FOUND:
            return "candidates"
        if self.type == EventType.COMPLETE:
            return "result"
        if self.type == EventType.COMPLETE_PARTIAL:
            return "result_partial"
        if self.type.value.startswith("ficha_"):
            return "ficha_update"
        if self.type in (EventType.NORMALIZING, EventType.CLASSIFYING, EventType.RESOLVING,
                         EventType.EXTRACTING, EventType.VALIDATING, EventType.MAPPING):
            return "status"
        return "log"

    @classmethod
    def normalizing(cls, input_raw: str) -> Event:
        return cls(EventType.NORMALIZING, f"Normalizando: {input_raw[:50]}...")

    @classmethod
    def normalized(cls, normalized: str) -> Event:
        return cls(EventType.NORMALIZED, f"Normalizado: {normalized}")

    @classmethod
    def classifying(cls) -> Event:
        return cls(EventType.CLASSIFYING, "Clasificando componente...")

    @classmethod
    def classified(cls, component_type: str, confidence: float, reason: str = "") -> Event:
        pct = int(confidence * 100)
        msg = f"Detectado: {component_type} ({pct}%)"
        if reason:
            msg += f" - {reason}"
        return cls(
            EventType.CLASSIFIED,
            msg,
            data={"type": component_type, "confidence": confidence, "reason": reason}
        )

    @classmethod
    def resolving(cls) -> Event:
        return cls(EventType.RESOLVING, "Resolviendo fuentes...")

    @classmethod
    def candidates_found(cls, count: int, candidates: list) -> Event:
        return cls(
            EventType.CANDIDATES_FOUND,
            f"Encontrados {count} candidatos",
            data={"candidates": candidates}
        )

    @classmethod
    def exact_match(cls, candidate: dict) -> Event:
        return cls(
            EventType.EXACT_MATCH,
            f"Match exacto: {candidate.get('brand', '')} {candidate.get('model', '')}",
            data={"candidate": candidate}
        )

    @classmethod
    def needs_selection(cls, candidates: list) -> Event:
        return cls(
            EventType.NEEDS_SELECTION,
            f"Selecciona entre {len(candidates)} candidatos",
            data={"candidates": candidates}
        )

    @classmethod
    def source_chain_start(cls, total_sources: int) -> Event:
        return cls(
            EventType.SOURCE_CHAIN_START,
            f"Iniciando cadena de {total_sources} fuentes",
            source_total=total_sources
        )

    @classmethod
    def source_trying(
        cls,
        provider: str,
        url: str = "",
        index: int = 0,
        total: int = 0
    ) -> Event:
        if index and total:
            msg = f"Fuente {index}/{total}: {provider}..."
        else:
            msg = f"Intentando: {provider}..."
        return cls(
            EventType.SOURCE_TRYING,
            msg,
            source_index=index if index else None,
            source_total=total if total else None,
            source_name=provider,
            data={"url": url} if url else None
        )

    @classmethod
    def source_success(cls, provider: str, specs_count: int) -> Event:
        return cls(
            EventType.SOURCE_SUCCESS,
            f"{provider}: OK ({specs_count} specs)",
            source_name=provider,
            data={"specs_count": specs_count}
        )

    @classmethod
    def source_failed(cls, provider: str, reason: str) -> Event:
        return cls(
            EventType.SOURCE_FAILED,
            f"{provider}: {reason}",
            source_name=provider,
            error=reason
        )

    @classmethod
    def source_antibot(cls, provider: str, reason: str = "") -> Event:
        msg = f"{provider}: bloqueado"
        if reason:
            msg += f" ({reason})"
        return cls(
            EventType.SOURCE_ANTIBOT,
            msg,
            source_name=provider,
            error=f"anti-bot: {reason}" if reason else "anti-bot"
        )

    @classmethod
    def source_timeout(cls, provider: str) -> Event:
        return cls(
            EventType.SOURCE_TIMEOUT,
            f"{provider}: timeout",
            source_name=provider,
            error="timeout"
        )

    @classmethod
    def source_upgrading(cls, provider: str) -> Event:
        return cls(
            EventType.SOURCE_UPGRADING,
            f"{provider}: cambiando a Playwright...",
            source_name=provider
        )

    @classmethod
    def source_skipped(cls, provider: str, reason: str) -> Event:
        return cls(
            EventType.SOURCE_SKIPPED,
            f"{provider}: omitido ({reason})",
            source_name=provider
        )

    @classmethod
    def source_empty(cls, provider: str) -> Event:
        return cls(
            EventType.SOURCE_EMPTY,
            f"{provider}: sin datos",
            source_name=provider
        )

    @classmethod
    def chain_exhausted(cls, total_tried: int) -> Event:
        return cls(
            EventType.CHAIN_EXHAUSTED,
            f"Agotadas {total_tried} fuentes sin éxito",
            error="chain_exhausted",
            recoverable=False
        )

    @classmethod
    def extracting(cls, url: str) -> Event:
        domain = url.split("/")[2] if "/" in url else url
        return cls(EventType.EXTRACTING, f"Extrayendo de {domain}...")

    @classmethod
    def extracted(cls, count: int) -> Event:
        return cls(EventType.EXTRACTED, f"Extraídos {count} campos")

    @classmethod
    def validating(cls) -> Event:
        return cls(EventType.VALIDATING, "Validando specs...")

    @classmethod
    def validated(cls, valid_count: int, total_count: int) -> Event:
        return cls(
            EventType.VALIDATED,
            f"Validados {valid_count}/{total_count} campos",
            data={"valid": valid_count, "total": total_count}
        )

    @classmethod
    def mapping(cls) -> Event:
        return cls(EventType.MAPPING, "Mapeando a template...")

    @classmethod
    def mapped(cls, fields_mapped: int) -> Event:
        return cls(EventType.MAPPED, f"Mapeados {fields_mapped} campos")

    @classmethod
    def calculating(cls) -> Event:
        return cls(EventType.CALCULATING, "Calculando valores derivados...")

    @classmethod
    def calculated(cls, count: int) -> Event:
        return cls(EventType.CALCULATED, f"Calculados {count} valores")

    @classmethod
    def complete(cls, component_type: str, brand: str, model: str) -> Event:
        return cls(
            EventType.COMPLETE,
            f"Completado: {component_type} - {brand} {model}",
            data={"type": component_type, "brand": brand, "model": model}
        )

    @classmethod
    def complete_partial(cls, reason: str) -> Event:
        return cls(
            EventType.COMPLETE_PARTIAL,
            f"Completado parcialmente: {reason}",
            data={"reason": reason}
        )

    @classmethod
    def failed(cls, reason: str) -> Event:
        return cls(
            EventType.FAILED,
            f"Fallido: {reason}",
            error=reason,
            recoverable=False
        )

    @classmethod
    def error_recoverable(cls, message: str) -> Event:
        return cls(
            EventType.ERROR_RECOVERABLE,
            message,
            error=message,
            recoverable=True
        )

    @classmethod
    def candidate_selected(cls, index: int, url: str) -> Event:
        return cls(
            EventType.CANDIDATE_SELECTED,
            f"Candidato #{index + 1} seleccionado",
            data={"index": index, "url": url}
        )

    @classmethod
    def ready_to_add(cls, component_data: dict) -> Event:
        comp_type = component_data.get("type", "")
        brand = component_data.get("brand", "")
        model = component_data.get("model", "")
        return cls(
            EventType.COMPLETE,
            f"Listo para agregar: {comp_type} - {brand} {model}",
            data=component_data
        )

    @classmethod
    def ficha_component_added(cls, component_type: str, component_id: str) -> Event:
        return cls(
            EventType.FICHA_COMPONENT_ADDED,
            f"Componente agregado: {component_type}",
            data={"type": component_type, "id": component_id}
        )

    @classmethod
    def ficha_exported(cls, format: str, path: str, rows: int) -> Event:
        return cls(
            EventType.FICHA_EXPORTED,
            f"Ficha exportada: {path} ({rows} filas)",
            data={"format": format, "path": path, "rows": rows}
        )

    @classmethod
    def ficha_reset(cls) -> Event:
        return cls(EventType.FICHA_RESET, "Ficha reiniciada")
