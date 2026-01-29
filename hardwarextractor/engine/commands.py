"""Command handlers for CLI engine."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Callable, Generator, Optional

from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.core.events import Event, EventType
from hardwarextractor.engine.ficha_manager import FichaManager
from hardwarextractor.engine.ipc import IPCProtocol, IPCMessage
from hardwarextractor.models.schemas import OrchestratorEvent, ResolveCandidate


class CommandHandler:
    """Handles CLI commands and orchestrates the engine.

    This class bridges the CLI commands with the underlying
    Orchestrator and FichaManager.
    """

    def __init__(
        self,
        orchestrator: Optional[Orchestrator] = None,
        ficha_manager: Optional[FichaManager] = None,
        ipc: Optional[IPCProtocol] = None,
    ):
        """Initialize the command handler.

        Args:
            orchestrator: The orchestrator instance (created if None)
            ficha_manager: The ficha manager (created if None)
            ipc: The IPC protocol for communication (optional)
        """
        self._orchestrator = orchestrator or Orchestrator()
        self._ficha_manager = ficha_manager or FichaManager()
        self._ipc = ipc
        self._last_component = None

    @property
    def ficha_manager(self) -> FichaManager:
        return self._ficha_manager

    @property
    def orchestrator(self) -> Orchestrator:
        return self._orchestrator

    def _emit(self, event: Event) -> None:
        """Emit an event via IPC if available."""
        if self._ipc:
            self._ipc.send(IPCMessage(
                type=event.to_ipc()["type"],
                value=event.message,
                progress=event.progress,
                data=event.data,
                error=event.error,
                recoverable=event.recoverable,
            ))

    def _emit_log(self, message: str) -> None:
        """Emit a log message."""
        if self._ipc:
            self._ipc.send_log(message)

    def analyze_component(self, input_text: str) -> Generator[Event, None, dict]:
        """Analyze a component from input text.

        Args:
            input_text: The component identifier (model, PN, etc.)

        Yields:
            Event objects for progress tracking

        Returns:
            Result dictionary with component data or error
        """
        yield Event.normalizing(input_text)

        # Process through orchestrator
        events = self._orchestrator.process_input(input_text)

        for orch_event in events:
            # Convert OrchestratorEvent to our Event format
            event = self._convert_orchestrator_event(orch_event)
            yield event

            # Check for terminal states
            if orch_event.status == "NEEDS_USER_SELECTION":
                return {
                    "status": "needs_selection",
                    "candidates": [
                        self._candidate_to_dict(c)
                        for c in orch_event.candidates or []
                    ]
                }

            if orch_event.status == "ERROR_RECOVERABLE":
                return {
                    "status": "error",
                    "message": orch_event.log,
                    "recoverable": True,
                }

            if orch_event.status == "READY_TO_ADD":
                self._last_component = orch_event.component_result
                return {
                    "status": "success",
                    "component": self._component_to_dict(orch_event.component_result),
                    "ficha": self._ficha_manager.to_dict(),
                }

        return {"status": "unknown"}

    def select_candidate(self, index: int) -> Generator[Event, None, dict]:
        """Select a candidate from the last candidate list.

        Args:
            index: 0-based index of the candidate to select

        Yields:
            Event objects for progress tracking

        Returns:
            Result dictionary
        """
        yield Event(EventType.CANDIDATE_SELECTED, f"Seleccionando candidato {index + 1}")

        events = self._orchestrator.select_candidate(index)

        for orch_event in events:
            event = self._convert_orchestrator_event(orch_event)
            yield event

            if orch_event.status == "ERROR_RECOVERABLE":
                return {
                    "status": "error",
                    "message": orch_event.log,
                    "recoverable": True,
                }

            if orch_event.status == "READY_TO_ADD":
                self._last_component = orch_event.component_result
                return {
                    "status": "success",
                    "component": self._component_to_dict(orch_event.component_result),
                }

        return {"status": "unknown"}

    def add_to_ficha(self) -> dict:
        """Add the last analyzed component to the ficha.

        Returns:
            Result dictionary with updated ficha
        """
        if self._last_component is None:
            return {
                "status": "error",
                "message": "No component to add",
            }

        self._ficha_manager.add_component(self._last_component)
        self._last_component = None

        return {
            "status": "success",
            "message": "Component added to ficha",
            "ficha": self._ficha_manager.to_dict(),
        }

    def show_ficha(self) -> dict:
        """Get the current ficha state.

        Returns:
            Ficha dictionary
        """
        return {
            "status": "success",
            "ficha": self._ficha_manager.to_dict(),
        }

    def export_ficha(self, format: str, path: Optional[str] = None) -> dict:
        """Export the ficha to a file.

        Args:
            format: Export format (csv, xlsx, md)
            path: Output path (auto-generated if None)

        Returns:
            Result with export path
        """
        if self._ficha_manager.component_count == 0:
            return {
                "status": "error",
                "message": "No components in ficha to export",
            }

        try:
            export_path = self._ficha_manager.export(format, path)
            return {
                "status": "success",
                "message": f"Exported to {export_path}",
                "path": export_path,
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Export failed: {str(e)}",
            }

    def reset_ficha(self) -> dict:
        """Reset the ficha to empty state.

        Returns:
            Confirmation dictionary
        """
        self._ficha_manager.reset()
        self._last_component = None

        return {
            "status": "success",
            "message": "Ficha reset",
        }

    def _convert_orchestrator_event(self, orch_event: OrchestratorEvent) -> Event:
        """Convert an OrchestratorEvent to our Event format."""
        status_map = {
            "NORMALIZE_INPUT": EventType.NORMALIZED,
            "CLASSIFY_COMPONENT": EventType.CLASSIFIED,
            "RESOLVE_ENTITY": EventType.EXACT_MATCH,
            "SCRAPE": EventType.EXTRACTED,
            "NEEDS_USER_SELECTION": EventType.NEEDS_SELECTION,
            "ERROR_RECOVERABLE": EventType.ERROR_RECOVERABLE,
            "READY_TO_ADD": EventType.COMPLETE,
        }

        event_type = status_map.get(orch_event.status, EventType.NORMALIZING)

        return Event(
            type=event_type,
            message=orch_event.log,
            progress=orch_event.progress,
            data={"candidates": orch_event.candidates} if orch_event.candidates else None,
        )

    def _candidate_to_dict(self, candidate: ResolveCandidate) -> dict:
        """Convert a ResolveCandidate to dictionary."""
        return {
            "brand": candidate.canonical.get("brand", ""),
            "model": candidate.canonical.get("model", ""),
            "part_number": candidate.canonical.get("part_number", ""),
            "source_name": candidate.source_name,
            "source_url": candidate.source_url,
            "score": candidate.score,
        }

    def _component_to_dict(self, component) -> dict:
        """Convert a ComponentRecord to dictionary."""
        if component is None:
            return {}

        return {
            "component_id": component.component_id,
            "type": component.component_type.value,
            "brand": component.canonical.get("brand", ""),
            "model": component.canonical.get("model", ""),
            "part_number": component.canonical.get("part_number", ""),
            "classification_confidence": component.classification_confidence,
            "specs": [
                {
                    "key": s.key,
                    "label": s.label,
                    "value": s.value,
                    "unit": s.unit,
                    "status": s.status.value,
                    "tier": s.source_tier.value,
                    "source_name": s.source_name,
                    "source_url": s.source_url,
                }
                for s in component.specs
            ],
        }
