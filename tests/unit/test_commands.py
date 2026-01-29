"""Tests for engine/commands.py - Command handlers."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from hardwarextractor.engine.commands import CommandHandler
from hardwarextractor.engine.ficha_manager import FichaManager
from hardwarextractor.engine.ipc import IPCProtocol, IPCMessage
from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.core.events import Event, EventType
from hardwarextractor.models.schemas import (
    ComponentRecord,
    ComponentType,
    OrchestratorEvent,
    ResolveCandidate,
    SpecField,
    SpecStatus,
    SourceTier,
)


class TestCommandHandlerCreation:
    """Test CommandHandler initialization."""

    def test_create_handler(self):
        """Test creating a command handler."""
        handler = CommandHandler()
        assert handler is not None
        assert handler.ficha_manager is not None
        assert handler.orchestrator is not None

    def test_create_with_custom_components(self):
        """Test creating handler with custom components."""
        orch = MagicMock(spec=Orchestrator)
        fm = MagicMock(spec=FichaManager)
        ipc = MagicMock(spec=IPCProtocol)

        handler = CommandHandler(
            orchestrator=orch,
            ficha_manager=fm,
            ipc=ipc,
        )

        assert handler._orchestrator is orch
        assert handler._ficha_manager is fm
        assert handler._ipc is ipc


class TestEmitMethods:
    """Test event emission methods."""

    def test_emit_with_ipc(self):
        """Test emitting events when IPC is available."""
        ipc = MagicMock(spec=IPCProtocol)
        handler = CommandHandler(ipc=ipc)

        event = Event(EventType.NORMALIZING, "Test message")
        handler._emit(event)

        ipc.send.assert_called_once()

    def test_emit_without_ipc(self):
        """Test emitting events without IPC (no error)."""
        handler = CommandHandler()
        event = Event(EventType.NORMALIZING, "Test message")
        # Should not raise
        handler._emit(event)

    def test_emit_log_with_ipc(self):
        """Test emitting log messages with IPC."""
        ipc = MagicMock(spec=IPCProtocol)
        handler = CommandHandler(ipc=ipc)

        handler._emit_log("Log message")

        ipc.send_log.assert_called_once_with("Log message")

    def test_emit_log_without_ipc(self):
        """Test emitting log messages without IPC."""
        handler = CommandHandler()
        # Should not raise
        handler._emit_log("Log message")


class TestAnalyzeComponent:
    """Test analyze_component method."""

    @pytest.fixture
    def mock_orchestrator(self):
        return MagicMock(spec=Orchestrator)

    def test_analyze_yields_normalizing_event(self, mock_orchestrator):
        """Test that analyze yields normalizing event first."""
        mock_orchestrator.process_input.return_value = []
        handler = CommandHandler(orchestrator=mock_orchestrator)

        events = list(handler.analyze_component("Intel i7"))

        assert len(events) >= 1
        assert events[0].type == EventType.NORMALIZING

    def test_analyze_needs_selection(self, mock_orchestrator):
        """Test analyze when user selection is needed."""
        candidate = ResolveCandidate(
            canonical={"brand": "Intel", "model": "i7"},
            source_name="Amazon",
            source_url="https://amazon.com/i7",
            score=0.85,
            spider_name="amazon",
        )
        orch_event = OrchestratorEvent(
            status="NEEDS_USER_SELECTION",
            log="Multiple matches found",
            progress=50,
            candidates=[candidate],
        )
        mock_orchestrator.process_input.return_value = [orch_event]
        handler = CommandHandler(orchestrator=mock_orchestrator)

        gen = handler.analyze_component("Intel i7")
        events = []
        result = None
        for event in gen:
            events.append(event)

        # Get return value by exhausting generator
        gen = handler.analyze_component("Intel i7")
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

        assert result["status"] == "needs_selection"
        assert len(result["candidates"]) == 1

    def test_analyze_error_recoverable(self, mock_orchestrator):
        """Test analyze when recoverable error occurs."""
        orch_event = OrchestratorEvent(
            status="ERROR_RECOVERABLE",
            log="Rate limited",
            progress=0,
        )
        mock_orchestrator.process_input.return_value = [orch_event]
        handler = CommandHandler(orchestrator=mock_orchestrator)

        gen = handler.analyze_component("Intel i7")
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

        assert result["status"] == "error"
        assert result["recoverable"] is True

    def test_analyze_success(self, mock_orchestrator):
        """Test successful component analysis."""
        component = ComponentRecord(
            component_id="cpu-001",
            input_raw="Intel i7",
            input_normalized="intel i7",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel", "model": "i7"},
            source_confidence=0.95,
            specs=[],
        )
        orch_event = OrchestratorEvent(
            status="READY_TO_ADD",
            log="Ready",
            progress=100,
            component_result=component,
        )
        mock_orchestrator.process_input.return_value = [orch_event]
        handler = CommandHandler(orchestrator=mock_orchestrator)

        gen = handler.analyze_component("Intel i7")
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

        assert result["status"] == "success"
        assert "component" in result


class TestSelectCandidate:
    """Test select_candidate method."""

    @pytest.fixture
    def mock_orchestrator(self):
        return MagicMock(spec=Orchestrator)

    def test_select_yields_event(self, mock_orchestrator):
        """Test that select yields candidate selected event."""
        mock_orchestrator.select_candidate.return_value = []
        handler = CommandHandler(orchestrator=mock_orchestrator)

        events = list(handler.select_candidate(0))

        assert len(events) >= 1
        assert events[0].type == EventType.CANDIDATE_SELECTED

    def test_select_error_recoverable(self, mock_orchestrator):
        """Test select when error occurs."""
        orch_event = OrchestratorEvent(
            status="ERROR_RECOVERABLE",
            log="Invalid selection",
            progress=0,
        )
        mock_orchestrator.select_candidate.return_value = [orch_event]
        handler = CommandHandler(orchestrator=mock_orchestrator)

        gen = handler.select_candidate(0)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

        assert result["status"] == "error"
        assert result["recoverable"] is True

    def test_select_success(self, mock_orchestrator):
        """Test successful candidate selection."""
        component = ComponentRecord(
            component_id="cpu-001",
            input_raw="Intel i7",
            input_normalized="intel i7",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel", "model": "i7"},
            source_confidence=0.95,
            specs=[],
        )
        orch_event = OrchestratorEvent(
            status="READY_TO_ADD",
            log="Selected",
            progress=100,
            component_result=component,
        )
        mock_orchestrator.select_candidate.return_value = [orch_event]
        handler = CommandHandler(orchestrator=mock_orchestrator)

        gen = handler.select_candidate(0)
        try:
            while True:
                next(gen)
        except StopIteration as e:
            result = e.value

        assert result["status"] == "success"
        assert "component" in result


class TestAddToFicha:
    """Test add_to_ficha method."""

    def test_add_no_component(self):
        """Test adding when no component analyzed."""
        handler = CommandHandler()
        result = handler.add_to_ficha()
        assert result["status"] == "error"
        assert "No component" in result["message"]

    def test_add_with_component(self):
        """Test adding after successful analysis."""
        handler = CommandHandler()
        handler._last_component = ComponentRecord(
            component_id="cpu-001",
            input_raw="Intel CPU",
            input_normalized="intel cpu",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel"},
            source_confidence=0.9,
            specs=[],
        )

        result = handler.add_to_ficha()

        assert result["status"] == "success"
        assert handler._last_component is None
        assert "ficha" in result


class TestShowFicha:
    """Test show_ficha method."""

    def test_show_ficha(self):
        """Test showing ficha state."""
        handler = CommandHandler()
        result = handler.show_ficha()
        assert result["status"] == "success"
        assert "ficha" in result


class TestExportFicha:
    """Test export_ficha method."""

    def test_export_empty_ficha(self):
        """Test exporting empty ficha."""
        handler = CommandHandler()
        result = handler.export_ficha("csv")
        assert result["status"] == "error"
        assert "No components" in result["message"]

    def test_export_csv(self, tmp_path):
        """Test CSV export."""
        handler = CommandHandler()
        handler._ficha_manager.add_component(
            ComponentRecord(
                component_id="cpu-001",
                input_raw="Intel CPU",
                input_normalized="intel cpu",
                component_type=ComponentType.CPU,
                canonical={"brand": "Intel"},
                source_confidence=0.9,
                specs=[],
            )
        )

        output_path = tmp_path / "test.csv"
        result = handler.export_ficha("csv", str(output_path))

        assert result["status"] == "success"
        assert result["path"] == str(output_path)

    def test_export_with_error(self):
        """Test export with invalid format/path."""
        handler = CommandHandler()
        handler._ficha_manager.add_component(
            ComponentRecord(
                component_id="cpu-001",
                input_raw="Unknown CPU",
                input_normalized="unknown cpu",
                component_type=ComponentType.CPU,
                canonical={},
                source_confidence=0.9,
                specs=[],
            )
        )

        # Invalid path that should fail
        result = handler.export_ficha("csv", "/nonexistent/path/file.csv")
        assert result["status"] == "error"


class TestResetFicha:
    """Test reset_ficha method."""

    def test_reset_ficha(self):
        """Test resetting ficha."""
        handler = CommandHandler()
        handler._ficha_manager.add_component(
            ComponentRecord(
                component_id="cpu-001",
                input_raw="Intel CPU",
                input_normalized="intel cpu",
                component_type=ComponentType.CPU,
                canonical={},
                source_confidence=0.9,
                specs=[],
            )
        )
        handler._last_component = MagicMock()

        result = handler.reset_ficha()

        assert result["status"] == "success"
        assert handler._ficha_manager.component_count == 0
        assert handler._last_component is None


class TestConvertOrchestratorEvent:
    """Test _convert_orchestrator_event method."""

    def test_convert_normalize_event(self):
        """Test converting NORMALIZE_INPUT event."""
        handler = CommandHandler()
        orch_event = OrchestratorEvent(
            status="NORMALIZE_INPUT",
            log="Normalizing",
            progress=10,
        )

        event = handler._convert_orchestrator_event(orch_event)

        assert event.type == EventType.NORMALIZED
        assert event.message == "Normalizing"
        assert event.progress == 10

    def test_convert_classify_event(self):
        """Test converting CLASSIFY_COMPONENT event."""
        handler = CommandHandler()
        orch_event = OrchestratorEvent(
            status="CLASSIFY_COMPONENT",
            log="Classifying",
            progress=30,
        )

        event = handler._convert_orchestrator_event(orch_event)

        assert event.type == EventType.CLASSIFIED

    def test_convert_needs_selection_event(self):
        """Test converting NEEDS_USER_SELECTION event."""
        handler = CommandHandler()
        candidates = [
            ResolveCandidate(
                canonical={"brand": "Intel"},
                source_name="Test",
                source_url="https://test.com",
                score=0.9,
                spider_name="test",
            )
        ]
        orch_event = OrchestratorEvent(
            status="NEEDS_USER_SELECTION",
            log="Select one",
            progress=50,
            candidates=candidates,
        )

        event = handler._convert_orchestrator_event(orch_event)

        assert event.type == EventType.NEEDS_SELECTION
        assert event.data is not None
        assert "candidates" in event.data

    def test_convert_unknown_status(self):
        """Test converting unknown status defaults to NORMALIZING."""
        handler = CommandHandler()
        orch_event = OrchestratorEvent(
            status="UNKNOWN_STATUS",
            log="Unknown",
            progress=0,
        )

        event = handler._convert_orchestrator_event(orch_event)

        assert event.type == EventType.NORMALIZING


class TestCandidateToDict:
    """Test _candidate_to_dict method."""

    def test_candidate_to_dict(self):
        """Test converting candidate to dictionary."""
        handler = CommandHandler()
        candidate = ResolveCandidate(
            canonical={
                "brand": "Intel",
                "model": "Core i7-12700K",
                "part_number": "BX123",
            },
            source_name="Amazon",
            source_url="https://amazon.com/i7",
            score=0.95,
            spider_name="amazon",
        )

        d = handler._candidate_to_dict(candidate)

        assert d["brand"] == "Intel"
        assert d["model"] == "Core i7-12700K"
        assert d["part_number"] == "BX123"
        assert d["source_name"] == "Amazon"
        assert d["source_url"] == "https://amazon.com/i7"
        assert d["score"] == 0.95

    def test_candidate_to_dict_missing_fields(self):
        """Test converting candidate with missing fields."""
        handler = CommandHandler()
        candidate = ResolveCandidate(
            canonical={},
            source_name="Test",
            source_url="https://test.com",
            score=0.5,
            spider_name="test",
        )

        d = handler._candidate_to_dict(candidate)

        assert d["brand"] == ""
        assert d["model"] == ""
        assert d["part_number"] == ""


class TestComponentToDict:
    """Test _component_to_dict method."""

    def test_component_to_dict(self):
        """Test converting component to dictionary."""
        handler = CommandHandler()
        component = ComponentRecord(
            component_id="cpu-001",
            input_raw="Intel i7-12700K",
            input_normalized="intel i7 12700k",
            component_type=ComponentType.CPU,
            canonical={
                "brand": "Intel",
                "model": "i7-12700K",
                "part_number": "BX123",
            },
            source_confidence=0.95,
            specs=[
                SpecField(
                    key="cores",
                    label="Cores",
                    value="12",
                    unit="cores",
                    status=SpecStatus.EXTRACTED_OFFICIAL,
                    source_tier=SourceTier.OFFICIAL,
                    source_name="Amazon",
                    source_url="https://amazon.com",
                )
            ],
        )

        d = handler._component_to_dict(component)

        assert d["component_id"] == "cpu-001"
        assert d["type"] == "CPU"
        assert d["brand"] == "Intel"
        assert d["model"] == "i7-12700K"
        assert d["source_confidence"] == 0.95
        assert len(d["specs"]) == 1
        assert d["specs"][0]["key"] == "cores"

    def test_component_to_dict_none(self):
        """Test converting None component."""
        handler = CommandHandler()
        d = handler._component_to_dict(None)
        assert d == {}
