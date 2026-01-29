"""Tests for core/events.py - Event system."""

import pytest
from hardwarextractor.core.events import Event, EventType, PHASE_PROGRESS


class TestEventType:
    """Test EventType enum."""

    def test_normalizing_type(self):
        """Test NORMALIZING event type."""
        assert EventType.NORMALIZING.value == "normalizing"

    def test_normalized_type(self):
        """Test NORMALIZED event type."""
        assert EventType.NORMALIZED.value == "normalized"

    def test_classifying_type(self):
        """Test CLASSIFYING event type."""
        assert EventType.CLASSIFYING.value == "classifying"

    def test_classified_type(self):
        """Test CLASSIFIED event type."""
        assert EventType.CLASSIFIED.value == "classified"

    def test_resolving_type(self):
        """Test RESOLVING event type."""
        assert EventType.RESOLVING.value == "resolving"

    def test_candidates_found_type(self):
        """Test CANDIDATES_FOUND event type."""
        assert EventType.CANDIDATES_FOUND.value == "candidates_found"

    def test_source_chain_types(self):
        """Test source chain event types."""
        assert EventType.SOURCE_CHAIN_START.value == "source_chain_start"
        assert EventType.SOURCE_TRYING.value == "source_trying"
        assert EventType.SOURCE_SUCCESS.value == "source_success"
        assert EventType.SOURCE_FAILED.value == "source_failed"
        assert EventType.SOURCE_ANTIBOT.value == "source_antibot"
        assert EventType.SOURCE_TIMEOUT.value == "source_timeout"

    def test_extraction_types(self):
        """Test extraction event types."""
        assert EventType.EXTRACTING.value == "extracting"
        assert EventType.EXTRACTED.value == "extracted"

    def test_validation_types(self):
        """Test validation event types."""
        assert EventType.VALIDATING.value == "validating"
        assert EventType.VALIDATED.value == "validated"
        assert EventType.VALIDATION_WARNING.value == "validation_warning"

    def test_final_types(self):
        """Test final state event types."""
        assert EventType.COMPLETE.value == "complete"
        assert EventType.COMPLETE_PARTIAL.value == "complete_partial"
        assert EventType.FAILED.value == "failed"

    def test_error_types(self):
        """Test error event types."""
        assert EventType.ERROR_RECOVERABLE.value == "error_recoverable"
        assert EventType.ERROR_FATAL.value == "error_fatal"

    def test_ficha_types(self):
        """Test ficha operation event types."""
        assert EventType.FICHA_COMPONENT_ADDED.value == "ficha_component_added"
        assert EventType.FICHA_EXPORTED.value == "ficha_exported"
        assert EventType.FICHA_RESET.value == "ficha_reset"


class TestPhaseProgress:
    """Test PHASE_PROGRESS dictionary."""

    def test_normalizing_progress(self):
        """Test normalizing progress value."""
        assert PHASE_PROGRESS[EventType.NORMALIZING] == 5

    def test_complete_progress(self):
        """Test complete progress is 100."""
        assert PHASE_PROGRESS[EventType.COMPLETE] == 100

    def test_failed_progress(self):
        """Test failed progress is 100."""
        assert PHASE_PROGRESS[EventType.FAILED] == 100


class TestEventCreation:
    """Test Event dataclass creation."""

    def test_create_basic_event(self):
        """Test creating a basic event."""
        event = Event(EventType.NORMALIZING, "Test message")
        assert event.type == EventType.NORMALIZING
        assert event.message == "Test message"

    def test_event_auto_progress(self):
        """Test progress is auto-calculated from phase."""
        event = Event(EventType.NORMALIZING, "Test")
        assert event.progress == 5

    def test_event_manual_progress(self):
        """Test manual progress overrides auto."""
        event = Event(EventType.NORMALIZING, "Test", progress=50)
        assert event.progress == 50

    def test_event_with_data(self):
        """Test event with data."""
        event = Event(EventType.CLASSIFIED, "Test", data={"type": "CPU"})
        assert event.data == {"type": "CPU"}

    def test_event_with_source_info(self):
        """Test event with source info."""
        event = Event(
            EventType.SOURCE_TRYING,
            "Trying source",
            source_index=1,
            source_total=5,
            source_name="intel_ark"
        )
        assert event.source_index == 1
        assert event.source_total == 5
        assert event.source_name == "intel_ark"

    def test_event_with_error(self):
        """Test event with error."""
        event = Event(
            EventType.ERROR_RECOVERABLE,
            "Error message",
            error="Details",
            recoverable=True
        )
        assert event.error == "Details"
        assert event.recoverable is True

    def test_event_default_values(self):
        """Test event default attribute values."""
        event = Event(EventType.CLASSIFYING, "Classifying...")
        assert event.progress == PHASE_PROGRESS[EventType.CLASSIFYING]
        assert event.source_index is None
        assert event.source_total is None
        assert event.source_name is None
        assert event.error is None
        assert event.recoverable is True  # Default is True
        assert event.data is None


class TestEventToIpc:
    """Test Event to_ipc method."""

    def test_to_ipc_basic(self):
        """Test basic IPC conversion."""
        event = Event(EventType.NORMALIZING, "Test message", progress=10)
        ipc = event.to_ipc()
        assert ipc["type"] == "status"
        assert ipc["value"] == "Test message"
        assert ipc["progress"] == 10

    def test_to_ipc_error(self):
        """Test error IPC conversion."""
        event = Event(
            EventType.ERROR_RECOVERABLE,
            "Error",
            error="Error details",
            recoverable=True
        )
        ipc = event.to_ipc()
        assert ipc["type"] == "error"
        assert ipc["error"] == "Error details"
        assert ipc["recoverable"] is True

    def test_to_ipc_candidates(self):
        """Test candidates IPC conversion."""
        event = Event(
            EventType.CANDIDATES_FOUND,
            "Found 2 candidates",
            data={"candidates": []}
        )
        ipc = event.to_ipc()
        assert ipc["type"] == "candidates"

    def test_to_ipc_result(self):
        """Test complete IPC conversion."""
        event = Event(EventType.COMPLETE, "Done")
        ipc = event.to_ipc()
        assert ipc["type"] == "result"

    def test_to_ipc_ficha(self):
        """Test ficha IPC conversion."""
        event = Event(EventType.FICHA_COMPONENT_ADDED, "Added")
        ipc = event.to_ipc()
        assert ipc["type"] == "ficha_update"


class TestEventFactoryMethods:
    """Test Event factory methods."""

    def test_normalizing(self):
        """Test normalizing factory."""
        event = Event.normalizing("Intel i7-12700K")
        assert event.type == EventType.NORMALIZING
        assert "Intel i7" in event.message

    def test_normalized(self):
        """Test normalized factory."""
        event = Event.normalized("intel i7 12700k")
        assert event.type == EventType.NORMALIZED
        assert "intel i7 12700k" in event.message

    def test_classifying(self):
        """Test classifying factory."""
        event = Event.classifying()
        assert event.type == EventType.CLASSIFYING

    def test_classified(self):
        """Test classified factory."""
        event = Event.classified("CPU", 0.95, "pattern match")
        assert event.type == EventType.CLASSIFIED
        assert "CPU" in event.message
        assert "95%" in event.message
        assert event.data["type"] == "CPU"
        assert event.data["confidence"] == 0.95

    def test_classified_with_reason(self):
        """Test classified event with reason."""
        event = Event.classified("CPU", 0.8, "pattern match")
        assert "pattern match" in event.message
        assert event.data["reason"] == "pattern match"

    def test_resolving(self):
        """Test resolving factory."""
        event = Event.resolving()
        assert event.type == EventType.RESOLVING

    def test_candidates_found(self):
        """Test candidates_found factory."""
        candidates = [{"brand": "Intel"}, {"brand": "AMD"}]
        event = Event.candidates_found(2, candidates)
        assert event.type == EventType.CANDIDATES_FOUND
        assert "2" in event.message
        assert event.data["candidates"] == candidates

    def test_exact_match(self):
        """Test exact_match factory."""
        candidate = {"brand": "Intel", "model": "i7-12700K"}
        event = Event.exact_match(candidate)
        assert event.type == EventType.EXACT_MATCH
        assert "Intel" in event.message
        assert "i7-12700K" in event.message

    def test_needs_selection(self):
        """Test needs_selection factory."""
        candidates = [{"brand": "Intel"}, {"brand": "AMD"}]
        event = Event.needs_selection(candidates)
        assert event.type == EventType.NEEDS_SELECTION
        assert event.data["candidates"] == candidates

    def test_source_chain_start(self):
        """Test source_chain_start factory."""
        event = Event.source_chain_start(5)
        assert event.type == EventType.SOURCE_CHAIN_START
        assert "5" in event.message

    def test_source_trying_with_index(self):
        """Test source_trying with index."""
        event = Event.source_trying("intel_ark", "https://ark.intel.com", 1, 5)
        assert event.type == EventType.SOURCE_TRYING
        assert "1/5" in event.message
        assert event.source_index == 1
        assert event.source_total == 5
        assert event.source_name == "intel_ark"

    def test_source_trying_without_index(self):
        """Test source_trying without index."""
        event = Event.source_trying("intel_ark")
        assert event.type == EventType.SOURCE_TRYING
        assert "intel_ark" in event.message

    def test_source_success(self):
        """Test source_success factory."""
        event = Event.source_success("intel_ark", 15)
        assert event.type == EventType.SOURCE_SUCCESS
        assert "intel_ark" in event.message
        assert "15" in event.message

    def test_source_failed(self):
        """Test source_failed factory."""
        event = Event.source_failed("intel_ark", "Connection timeout")
        assert event.type == EventType.SOURCE_FAILED
        assert event.error == "Connection timeout"

    def test_source_antibot(self):
        """Test source_antibot factory."""
        event = Event.source_antibot("corsair", "cloudflare")
        assert event.type == EventType.SOURCE_ANTIBOT
        assert "bloqueado" in event.message
        assert "cloudflare" in event.message

    def test_source_antibot_no_reason(self):
        """Test source_antibot event without reason."""
        event = Event.source_antibot("gskill")
        assert event.type == EventType.SOURCE_ANTIBOT
        assert event.error == "anti-bot"

    def test_source_timeout(self):
        """Test source_timeout factory."""
        event = Event.source_timeout("intel_ark")
        assert event.type == EventType.SOURCE_TIMEOUT
        assert event.error == "timeout"

    def test_source_upgrading(self):
        """Test source_upgrading factory."""
        event = Event.source_upgrading("corsair")
        assert event.type == EventType.SOURCE_UPGRADING
        assert "Playwright" in event.message

    def test_source_skipped(self):
        """Test source_skipped factory."""
        event = Event.source_skipped("intel_ark", "domain blocked")
        assert event.type == EventType.SOURCE_SKIPPED
        assert "omitido" in event.message

    def test_source_empty(self):
        """Test source_empty factory."""
        event = Event.source_empty("intel_ark")
        assert event.type == EventType.SOURCE_EMPTY
        assert "sin datos" in event.message

    def test_chain_exhausted(self):
        """Test chain_exhausted factory."""
        event = Event.chain_exhausted(5)
        assert event.type == EventType.CHAIN_EXHAUSTED
        assert "5" in event.message
        assert event.recoverable is False

    def test_extracting(self):
        """Test extracting factory."""
        event = Event.extracting("https://ark.intel.com/product/123")
        assert event.type == EventType.EXTRACTING
        assert "ark.intel.com" in event.message

    def test_extracted(self):
        """Test extracted factory."""
        event = Event.extracted(15)
        assert event.type == EventType.EXTRACTED
        assert "15" in event.message

    def test_validating(self):
        """Test validating factory."""
        event = Event.validating()
        assert event.type == EventType.VALIDATING

    def test_validated(self):
        """Test validated factory."""
        event = Event.validated(12, 15)
        assert event.type == EventType.VALIDATED
        assert "12/15" in event.message

    def test_mapping(self):
        """Test mapping factory."""
        event = Event.mapping()
        assert event.type == EventType.MAPPING

    def test_mapped(self):
        """Test mapped factory."""
        event = Event.mapped(20)
        assert event.type == EventType.MAPPED
        assert "20" in event.message

    def test_calculating(self):
        """Test calculating factory."""
        event = Event.calculating()
        assert event.type == EventType.CALCULATING

    def test_calculated(self):
        """Test calculated factory."""
        event = Event.calculated(5)
        assert event.type == EventType.CALCULATED
        assert "5" in event.message

    def test_complete(self):
        """Test complete factory."""
        event = Event.complete("CPU", "Intel", "i7-12700K")
        assert event.type == EventType.COMPLETE
        assert "CPU" in event.message
        assert "Intel" in event.message
        assert "i7-12700K" in event.message

    def test_complete_partial(self):
        """Test complete_partial factory."""
        event = Event.complete_partial("missing some specs")
        assert event.type == EventType.COMPLETE_PARTIAL
        assert "missing some specs" in event.message

    def test_failed(self):
        """Test failed factory."""
        event = Event.failed("No sources available")
        assert event.type == EventType.FAILED
        assert event.error == "No sources available"
        assert event.recoverable is False

    def test_error_recoverable(self):
        """Test error_recoverable factory."""
        event = Event.error_recoverable("Rate limited, retry later")
        assert event.type == EventType.ERROR_RECOVERABLE
        assert event.error == "Rate limited, retry later"
        assert event.recoverable is True

    def test_candidate_selected(self):
        """Test candidate_selected factory."""
        event = Event.candidate_selected(0, "https://example.com")
        assert event.type == EventType.CANDIDATE_SELECTED
        assert "#1" in event.message  # index 0 becomes #1

    def test_ready_to_add(self):
        """Test ready_to_add event creation."""
        component_data = {
            "component_id": "123",
            "type": "RAM",
            "brand": "Corsair",
            "model": "Vengeance",
            "specs_count": 15,
        }
        event = Event.ready_to_add(component_data)
        assert event.type == EventType.COMPLETE
        assert "RAM" in event.message
        assert "Corsair" in event.message
        assert event.data == component_data

    def test_ficha_component_added(self):
        """Test ficha_component_added factory."""
        event = Event.ficha_component_added("CPU", "cpu-123")
        assert event.type == EventType.FICHA_COMPONENT_ADDED
        assert event.data["type"] == "CPU"
        assert event.data["id"] == "cpu-123"

    def test_ficha_exported(self):
        """Test ficha_exported factory."""
        event = Event.ficha_exported("csv", "/path/to/file.csv", 50)
        assert event.type == EventType.FICHA_EXPORTED
        assert event.data["format"] == "csv"
        assert event.data["path"] == "/path/to/file.csv"
        assert event.data["rows"] == 50

    def test_ficha_reset(self):
        """Test ficha_reset factory."""
        event = Event.ficha_reset()
        assert event.type == EventType.FICHA_RESET


class TestEventAttributes:
    """Test Event dataclass attributes."""

    def test_event_progress(self):
        """Test event progress attribute."""
        event = Event(EventType.EXTRACTING, "Extracting...", progress=50)
        assert event.progress == 50

    def test_event_source_index(self):
        """Test event source_index attribute."""
        event = Event(EventType.SOURCE_TRYING, "Trying...", source_index=2)
        assert event.source_index == 2

    def test_event_source_total(self):
        """Test event source_total attribute."""
        event = Event(EventType.SOURCE_CHAIN_START, "Starting...", source_total=5)
        assert event.source_total == 5

    def test_event_source_name(self):
        """Test event source_name attribute."""
        event = Event(EventType.SOURCE_SUCCESS, "Success", source_name="intel")
        assert event.source_name == "intel"

    def test_event_error(self):
        """Test event error attribute."""
        event = Event(EventType.ERROR_FATAL, "Error", error="Network timeout")
        assert event.error == "Network timeout"

    def test_event_recoverable(self):
        """Test event recoverable attribute."""
        event = Event(EventType.ERROR_RECOVERABLE, "Error", recoverable=True)
        assert event.recoverable is True

    def test_event_data(self):
        """Test event data attribute."""
        data = {"key": "value", "count": 10}
        event = Event(EventType.COMPLETE, "Done", data=data)
        assert event.data == data
