"""IPC protocol for CLI communication using JSON-lines."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Optional, TextIO


class MessageType(str, Enum):
    """Types of IPC messages."""
    # Engine -> CLI
    STATUS = "status"
    PROGRESS = "progress"
    LOG = "log"
    CANDIDATES = "candidates"
    RESULT = "result"
    RESULT_PARTIAL = "result_partial"
    FICHA_UPDATE = "ficha_update"
    ERROR = "error"
    EXPORT_COMPLETE = "export_complete"

    # CLI -> Engine
    CMD_ANALYZE = "analyze_component"
    CMD_SELECT = "select_candidate"
    CMD_ADD = "add_to_ficha"
    CMD_SHOW = "show_ficha"
    CMD_EXPORT = "export_ficha"
    CMD_RESET = "reset_ficha"
    CMD_QUIT = "quit"


@dataclass
class IPCMessage:
    """A message in the IPC protocol.

    Attributes:
        type: The message type
        value: The message payload
        progress: Optional progress percentage (0-100)
        data: Optional additional data
        error: Optional error information
        recoverable: For errors, whether it's recoverable
    """
    type: MessageType
    value: Any
    progress: Optional[int] = None
    data: Optional[dict] = None
    error: Optional[str] = None
    recoverable: bool = True

    def to_json(self) -> str:
        """Convert to JSON string for IPC."""
        obj = {"type": self.type.value, "value": self.value}

        if self.progress is not None:
            obj["progress"] = self.progress

        if self.data is not None:
            obj["data"] = self.data

        if self.error is not None:
            obj["error"] = self.error
            obj["recoverable"] = self.recoverable

        return json.dumps(obj, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> IPCMessage:
        """Parse a JSON string into an IPCMessage."""
        obj = json.loads(json_str)

        msg_type = obj.get("type", "")
        # Try to match to MessageType enum
        try:
            msg_type = MessageType(msg_type)
        except ValueError:
            msg_type = MessageType.LOG

        return cls(
            type=msg_type,
            value=obj.get("value"),
            progress=obj.get("progress"),
            data=obj.get("data"),
            error=obj.get("error"),
            recoverable=obj.get("recoverable", True),
        )

    # Factory methods for common messages
    @classmethod
    def status(cls, status: str, progress: int = 0) -> IPCMessage:
        return cls(MessageType.STATUS, status, progress=progress)

    @classmethod
    def log(cls, message: str) -> IPCMessage:
        return cls(MessageType.LOG, message)

    @classmethod
    def progress(cls, percent: int) -> IPCMessage:
        return cls(MessageType.PROGRESS, percent, progress=percent)

    @classmethod
    def candidates(cls, candidates: list) -> IPCMessage:
        return cls(MessageType.CANDIDATES, candidates)

    @classmethod
    def result(cls, component: dict) -> IPCMessage:
        return cls(MessageType.RESULT, component)

    @classmethod
    def error(cls, message: str, recoverable: bool = True) -> IPCMessage:
        return cls(
            MessageType.ERROR,
            message,
            error=message,
            recoverable=recoverable
        )

    @classmethod
    def ficha_update(cls, ficha: dict) -> IPCMessage:
        return cls(MessageType.FICHA_UPDATE, ficha)


class IPCProtocol:
    """Handles IPC communication over stdin/stdout.

    Usage:
        protocol = IPCProtocol()

        # Send messages to CLI
        protocol.send(IPCMessage.log("Processing..."))

        # Receive commands from CLI
        cmd = protocol.receive()
    """

    def __init__(
        self,
        stdin: Optional[TextIO] = None,
        stdout: Optional[TextIO] = None
    ):
        """Initialize the IPC protocol.

        Args:
            stdin: Input stream (default: sys.stdin)
            stdout: Output stream (default: sys.stdout)
        """
        self._stdin = stdin or sys.stdin
        self._stdout = stdout or sys.stdout

    def send(self, message: IPCMessage) -> None:
        """Send a message to the CLI.

        Args:
            message: The message to send
        """
        self._stdout.write(message.to_json() + "\n")
        self._stdout.flush()

    def send_log(self, text: str) -> None:
        """Send a log message."""
        self.send(IPCMessage.log(text))

    def send_status(self, status: str, progress: int = 0) -> None:
        """Send a status update."""
        self.send(IPCMessage.status(status, progress))

    def send_error(self, message: str, recoverable: bool = True) -> None:
        """Send an error message."""
        self.send(IPCMessage.error(message, recoverable))

    def send_candidates(self, candidates: list) -> None:
        """Send candidate list for selection."""
        self.send(IPCMessage.candidates(candidates))

    def send_result(self, component: dict) -> None:
        """Send component result."""
        self.send(IPCMessage.result(component))

    def send_ficha(self, ficha: dict) -> None:
        """Send ficha update."""
        self.send(IPCMessage.ficha_update(ficha))

    def receive(self) -> Optional[IPCMessage]:
        """Receive a command from the CLI.

        Returns:
            IPCMessage or None if EOF
        """
        try:
            line = self._stdin.readline()
            if not line:
                return None
            return IPCMessage.from_json(line.strip())
        except (json.JSONDecodeError, KeyError) as e:
            return IPCMessage.error(f"Invalid command: {e}")

    def receive_command(self) -> tuple[str, dict]:
        """Receive and parse a command.

        Returns:
            Tuple of (command_name, parameters)
        """
        msg = self.receive()
        if msg is None:
            return ("quit", {})

        if msg.type == MessageType.ERROR:
            return ("error", {"message": msg.error})

        # Parse command from value
        if isinstance(msg.value, dict):
            cmd = msg.value.get("cmd", msg.type.value)
            params = {k: v for k, v in msg.value.items() if k != "cmd"}
        else:
            cmd = msg.type.value
            params = {"value": msg.value}

        return (cmd, params)
