"""Logging centralizado para HardwareXtractor.

Sistema de logging detallado para depuración de desarrollo.
Los logs se escriben a ~/Library/Logs/HardwareXtractor/

Niveles:
- DEBUG: Detalles internos (valores de variables, flujo)
- INFO: Eventos importantes (inicio/fin de procesos)
- WARNING: Situaciones inesperadas pero manejables
- ERROR: Errores que afectan funcionalidad
- CRITICAL: Errores fatales
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# Directorio de logs
if sys.platform == "darwin":
    LOG_DIR = Path.home() / "Library" / "Logs" / "HardwareXtractor"
else:
    LOG_DIR = Path.home() / ".hardwarextractor" / "logs"

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Archivo de log con fecha
LOG_FILE = LOG_DIR / f"hxtractor_{datetime.now().strftime('%Y%m%d')}.log"

# Formato detallado para archivo
FILE_FORMAT = (
    "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-25s | "
    "%(funcName)-20s:%(lineno)-4d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Logger raíz configurado
_root_logger: Optional[logging.Logger] = None


def setup_logging(level: int = logging.DEBUG) -> logging.Logger:
    """Configura el sistema de logging.

    Args:
        level: Nivel mínimo de logging (default: DEBUG)

    Returns:
        Logger raíz configurado
    """
    global _root_logger

    if _root_logger is not None:
        return _root_logger

    # Logger raíz para la app
    logger = logging.getLogger("hxtractor")
    logger.setLevel(level)

    # Evitar duplicados
    if logger.handlers:
        return logger

    # Handler para archivo (detallado)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FILE_FORMAT, DATE_FORMAT))
    logger.addHandler(file_handler)

    # No propagar al logger root de Python
    logger.propagate = False

    _root_logger = logger

    # Log inicial
    logger.info("=" * 80)
    logger.info(f"HardwareXtractor iniciado - Log: {LOG_FILE}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Platform: {sys.platform}")
    logger.info("=" * 80)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger hijo para un módulo específico.

    Args:
        name: Nombre del módulo (ej: "orchestrator", "scraper")

    Returns:
        Logger configurado
    """
    # Asegurar que el logger raíz está configurado
    setup_logging()

    return logging.getLogger(f"hxtractor.{name}")


class ProcessLogger:
    """Logger contextual para seguimiento de procesos.

    Permite agrupar logs relacionados a un proceso específico
    con un ID único para facilitar depuración.

    Uso:
        with ProcessLogger("scrape", url=url) as plog:
            plog.debug("Iniciando fetch")
            plog.info("Specs extraídos", count=5)
    """

    def __init__(self, process_name: str, **context: Any):
        """Inicializa el logger de proceso.

        Args:
            process_name: Nombre del proceso (scrape, resolve, map, etc.)
            **context: Contexto adicional (url, component_type, etc.)
        """
        self.process_name = process_name
        self.context = context
        self.process_id = datetime.now().strftime("%H%M%S%f")[:10]
        self.logger = get_logger(process_name)
        self.start_time = None

    def __enter__(self) -> "ProcessLogger":
        self.start_time = datetime.now()
        ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
        self.logger.info(f"[{self.process_id}] START {self.process_name} | {ctx_str}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if exc_type:
            self.logger.error(
                f"[{self.process_id}] FAILED {self.process_name} | "
                f"elapsed={elapsed:.3f}s | error={exc_val}"
            )
        else:
            self.logger.info(
                f"[{self.process_id}] END {self.process_name} | elapsed={elapsed:.3f}s"
            )
        return False  # No suprimir excepciones

    def _format_msg(self, msg: str, **kwargs: Any) -> str:
        """Formatea mensaje con contexto."""
        if kwargs:
            extra = " | " + ", ".join(f"{k}={v}" for k, v in kwargs.items())
        else:
            extra = ""
        return f"[{self.process_id}] {msg}{extra}"

    def debug(self, msg: str, **kwargs: Any) -> None:
        self.logger.debug(self._format_msg(msg, **kwargs))

    def info(self, msg: str, **kwargs: Any) -> None:
        self.logger.info(self._format_msg(msg, **kwargs))

    def warning(self, msg: str, **kwargs: Any) -> None:
        self.logger.warning(self._format_msg(msg, **kwargs))

    def error(self, msg: str, **kwargs: Any) -> None:
        self.logger.error(self._format_msg(msg, **kwargs))

    def data(self, label: str, data: Any) -> None:
        """Log de datos estructurados (para depuración profunda)."""
        self.logger.debug(f"[{self.process_id}] DATA {label}:\n{data}")


# Funciones de conveniencia
def log_debug(msg: str, module: str = "general") -> None:
    get_logger(module).debug(msg)

def log_info(msg: str, module: str = "general") -> None:
    get_logger(module).info(msg)

def log_warning(msg: str, module: str = "general") -> None:
    get_logger(module).warning(msg)

def log_error(msg: str, module: str = "general") -> None:
    get_logger(module).error(msg)


# Inicializar al importar
setup_logging()
