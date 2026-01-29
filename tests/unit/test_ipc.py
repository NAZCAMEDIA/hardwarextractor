"""Tests for engine/ipc.py - IPC protocol."""

import json
import pytest
from io import StringIO

from hardwarextractor.engine.ipc import (
    MessageType,
    IPCMessage,
    IPCProtocol,
)


class TestMessageType:
    """Test MessageType enum."""

    def test_status_message_type(self):
        """Test STATUS message type."""
        assert MessageType.STATUS.value == "status"

    def test_progress_message_type(self):
        """Test PROGRESS message type."""
        assert MessageType.PROGRESS.value == "progress"

    def test_log_message_type(self):
        """Test LOG message type."""
        assert MessageType.LOG.value == "log"

    def test_candidates_message_type(self):
        """Test CANDIDATES message type."""
        assert MessageType.CANDIDATES.value == "candidates"

    def test_result_message_type(self):
        """Test RESULT message type."""
        assert MessageType.RESULT.value == "result"

    def test_error_message_type(self):
        """Test ERROR message type."""
        assert MessageType.ERROR.value == "error"

    def test_command_message_types(self):
        """Test command message types."""
        assert MessageType.CMD_ANALYZE.value == "analyze_component"
        assert MessageType.CMD_SELECT.value == "select_candidate"
        assert MessageType.CMD_ADD.value == "add_to_ficha"
        assert MessageType.CMD_SHOW.value == "show_ficha"
        assert MessageType.CMD_EXPORT.value == "export_ficha"
        assert MessageType.CMD_RESET.value == "reset_ficha"
        assert MessageType.CMD_QUIT.value == "quit"


class TestIPCMessage:
    """Test IPCMessage dataclass."""

    def test_create_message(self):
        """Test creating a message."""
        msg = IPCMessage(MessageType.LOG, "Test message")
        assert msg.type == MessageType.LOG
        assert msg.value == "Test message"
        assert msg.progress is None
        assert msg.data is None
        assert msg.error is None
        assert msg.recoverable is True

    def test_create_message_with_all_fields(self):
        """Test creating a message with all fields."""
        msg = IPCMessage(
            type=MessageType.ERROR,
            value="Error occurred",
            progress=50,
            data={"key": "value"},
            error="Error details",
            recoverable=False,
        )
        assert msg.type == MessageType.ERROR
        assert msg.value == "Error occurred"
        assert msg.progress == 50
        assert msg.data == {"key": "value"}
        assert msg.error == "Error details"
        assert msg.recoverable is False


class TestIPCMessageToJson:
    """Test IPCMessage JSON serialization."""

    def test_to_json_basic(self):
        """Test basic JSON serialization."""
        msg = IPCMessage(MessageType.LOG, "Test")
        json_str = msg.to_json()
        parsed = json.loads(json_str)
        assert parsed["type"] == "log"
        assert parsed["value"] == "Test"

    def test_to_json_with_progress(self):
        """Test JSON with progress."""
        msg = IPCMessage(MessageType.PROGRESS, 50, progress=50)
        json_str = msg.to_json()
        parsed = json.loads(json_str)
        assert parsed["progress"] == 50

    def test_to_json_with_data(self):
        """Test JSON with data."""
        msg = IPCMessage(MessageType.RESULT, "result", data={"key": "value"})
        json_str = msg.to_json()
        parsed = json.loads(json_str)
        assert parsed["data"] == {"key": "value"}

    def test_to_json_with_error(self):
        """Test JSON with error."""
        msg = IPCMessage(
            MessageType.ERROR,
            "Error",
            error="Error details",
            recoverable=False
        )
        json_str = msg.to_json()
        parsed = json.loads(json_str)
        assert parsed["error"] == "Error details"
        assert parsed["recoverable"] is False


class TestIPCMessageFromJson:
    """Test IPCMessage JSON deserialization."""

    def test_from_json_basic(self):
        """Test basic JSON deserialization."""
        json_str = '{"type": "log", "value": "Test message"}'
        msg = IPCMessage.from_json(json_str)
        assert msg.type == MessageType.LOG
        assert msg.value == "Test message"

    def test_from_json_with_progress(self):
        """Test deserialization with progress."""
        json_str = '{"type": "progress", "value": 50, "progress": 50}'
        msg = IPCMessage.from_json(json_str)
        assert msg.type == MessageType.PROGRESS
        assert msg.progress == 50

    def test_from_json_with_data(self):
        """Test deserialization with data."""
        json_str = '{"type": "result", "value": "ok", "data": {"key": "value"}}'
        msg = IPCMessage.from_json(json_str)
        assert msg.data == {"key": "value"}

    def test_from_json_unknown_type(self):
        """Test deserialization with unknown type defaults to LOG."""
        json_str = '{"type": "unknown_type", "value": "test"}'
        msg = IPCMessage.from_json(json_str)
        assert msg.type == MessageType.LOG

    def test_from_json_with_error(self):
        """Test deserialization with error."""
        json_str = '{"type": "error", "value": "err", "error": "details", "recoverable": false}'
        msg = IPCMessage.from_json(json_str)
        assert msg.type == MessageType.ERROR
        assert msg.error == "details"
        assert msg.recoverable is False


class TestIPCMessageFactoryMethods:
    """Test IPCMessage factory methods."""

    def test_status_factory(self):
        """Test status factory method."""
        msg = IPCMessage.status("Processing", 50)
        assert msg.type == MessageType.STATUS
        assert msg.value == "Processing"
        assert msg.progress == 50

    def test_log_factory(self):
        """Test log factory method."""
        msg = IPCMessage.log("Log message")
        assert msg.type == MessageType.LOG
        assert msg.value == "Log message"

    def test_progress_factory(self):
        """Test progress factory method."""
        msg = IPCMessage.make_progress(75)
        assert msg.type == MessageType.PROGRESS
        assert msg.value == 75
        assert msg.progress == 75

    def test_candidates_factory(self):
        """Test candidates factory method."""
        candidates = [{"name": "Option 1"}, {"name": "Option 2"}]
        msg = IPCMessage.candidates(candidates)
        assert msg.type == MessageType.CANDIDATES
        assert msg.value == candidates

    def test_result_factory(self):
        """Test result factory method."""
        component = {"id": "123", "type": "CPU"}
        msg = IPCMessage.result(component)
        assert msg.type == MessageType.RESULT
        assert msg.value == component

    def test_error_factory(self):
        """Test error factory method."""
        msg = IPCMessage.make_error("Something went wrong", recoverable=False)
        assert msg.type == MessageType.ERROR
        assert msg.value == "Something went wrong"
        assert msg.error == "Something went wrong"
        assert msg.recoverable is False

    def test_error_factory_default_recoverable(self):
        """Test error factory with default recoverable."""
        msg = IPCMessage.make_error("Error")
        assert msg.recoverable is True

    def test_ficha_update_factory(self):
        """Test ficha_update factory method."""
        ficha = {"id": "ficha-123", "components": []}
        msg = IPCMessage.ficha_update(ficha)
        assert msg.type == MessageType.FICHA_UPDATE
        assert msg.value == ficha


class TestIPCProtocol:
    """Test IPCProtocol class."""

    def test_create_protocol(self):
        """Test creating a protocol instance."""
        protocol = IPCProtocol()
        assert protocol is not None

    def test_create_protocol_with_custom_streams(self):
        """Test creating protocol with custom streams."""
        stdin = StringIO()
        stdout = StringIO()
        protocol = IPCProtocol(stdin=stdin, stdout=stdout)
        assert protocol._stdin is stdin
        assert protocol._stdout is stdout


class TestIPCProtocolSend:
    """Test IPCProtocol send methods."""

    @pytest.fixture
    def protocol_with_output(self):
        stdout = StringIO()
        protocol = IPCProtocol(stdout=stdout)
        return protocol, stdout

    def test_send_message(self, protocol_with_output):
        """Test sending a message."""
        protocol, stdout = protocol_with_output
        msg = IPCMessage.log("Test")
        protocol.send(msg)
        output = stdout.getvalue()
        assert "log" in output
        assert "Test" in output
        assert output.endswith("\n")

    def test_send_log(self, protocol_with_output):
        """Test send_log convenience method."""
        protocol, stdout = protocol_with_output
        protocol.send_log("Log message")
        output = stdout.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["type"] == "log"
        assert parsed["value"] == "Log message"

    def test_send_status(self, protocol_with_output):
        """Test send_status convenience method."""
        protocol, stdout = protocol_with_output
        protocol.send_status("Processing", 50)
        output = stdout.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["type"] == "status"
        assert parsed["value"] == "Processing"
        assert parsed["progress"] == 50

    def test_send_error(self, protocol_with_output):
        """Test send_error convenience method."""
        protocol, stdout = protocol_with_output
        protocol.send_error("Error occurred", recoverable=False)
        output = stdout.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["type"] == "error"
        assert parsed["error"] == "Error occurred"
        assert parsed["recoverable"] is False

    def test_send_candidates(self, protocol_with_output):
        """Test send_candidates convenience method."""
        protocol, stdout = protocol_with_output
        candidates = [{"id": 1}, {"id": 2}]
        protocol.send_candidates(candidates)
        output = stdout.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["type"] == "candidates"
        assert parsed["value"] == candidates

    def test_send_result(self, protocol_with_output):
        """Test send_result convenience method."""
        protocol, stdout = protocol_with_output
        component = {"type": "CPU", "brand": "Intel"}
        protocol.send_result(component)
        output = stdout.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["type"] == "result"
        assert parsed["value"] == component

    def test_send_ficha(self, protocol_with_output):
        """Test send_ficha convenience method."""
        protocol, stdout = protocol_with_output
        ficha = {"id": "ficha-123"}
        protocol.send_ficha(ficha)
        output = stdout.getvalue()
        parsed = json.loads(output.strip())
        assert parsed["type"] == "ficha_update"
        assert parsed["value"] == ficha


class TestIPCProtocolReceive:
    """Test IPCProtocol receive methods."""

    def test_receive_message(self):
        """Test receiving a message."""
        stdin = StringIO('{"type": "log", "value": "Test"}\n')
        protocol = IPCProtocol(stdin=stdin, stdout=StringIO())
        msg = protocol.receive()
        assert msg is not None
        assert msg.type == MessageType.LOG
        assert msg.value == "Test"

    def test_receive_eof(self):
        """Test receiving EOF."""
        stdin = StringIO("")
        protocol = IPCProtocol(stdin=stdin, stdout=StringIO())
        msg = protocol.receive()
        assert msg is None

    def test_receive_invalid_json(self):
        """Test receiving invalid JSON."""
        stdin = StringIO("not valid json\n")
        protocol = IPCProtocol(stdin=stdin, stdout=StringIO())
        msg = protocol.receive()
        assert msg.type == MessageType.ERROR


class TestIPCProtocolReceiveCommand:
    """Test IPCProtocol receive_command method."""

    def test_receive_command_eof(self):
        """Test receive_command on EOF."""
        stdin = StringIO("")
        protocol = IPCProtocol(stdin=stdin, stdout=StringIO())
        cmd, params = protocol.receive_command()
        assert cmd == "quit"
        assert params == {}

    def test_receive_command_error(self):
        """Test receive_command on error message."""
        stdin = StringIO('{"type": "error", "value": "err", "error": "details"}\n')
        protocol = IPCProtocol(stdin=stdin, stdout=StringIO())
        cmd, params = protocol.receive_command()
        assert cmd == "error"
        assert "message" in params

    def test_receive_command_with_dict_value(self):
        """Test receive_command with dictionary value."""
        stdin = StringIO('{"type": "log", "value": {"cmd": "test_cmd", "arg1": "val1"}}\n')
        protocol = IPCProtocol(stdin=stdin, stdout=StringIO())
        cmd, params = protocol.receive_command()
        assert cmd == "test_cmd"
        assert params.get("arg1") == "val1"

    def test_receive_command_with_simple_value(self):
        """Test receive_command with simple value."""
        stdin = StringIO('{"type": "analyze_component", "value": "Intel i7"}\n')
        protocol = IPCProtocol(stdin=stdin, stdout=StringIO())
        cmd, params = protocol.receive_command()
        assert cmd == "analyze_component"
        assert params.get("value") == "Intel i7"
