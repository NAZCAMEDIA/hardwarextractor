"""Engine modules for CLI and IPC communication."""

from hardwarextractor.engine.ficha_manager import FichaManager
from hardwarextractor.engine.ipc import IPCProtocol, IPCMessage
from hardwarextractor.engine.commands import CommandHandler

__all__ = [
    "FichaManager",
    "IPCProtocol",
    "IPCMessage",
    "CommandHandler",
]
