"""Sistema de feedback para versión beta.

Captura contexto de búsquedas y genera reportes para GitHub Issues.
"""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from hardwarextractor.core.logger import LOG_FILE


@dataclass
class SearchContext:
    """Contexto de una búsqueda para feedback."""
    input_text: str
    component_type: str
    result: str  # "success", "no_results", "error"
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    log_entries: List[str] = field(default_factory=list)


class FeedbackCollector:
    """Recopila feedback de búsquedas para la versión beta.

    Mantiene contexto de la última búsqueda y contador para
    mostrar recordatorios periódicos.
    """

    VERSION = "0.2.0"
    REMINDER_INTERVAL = 5  # Recordatorio cada N búsquedas

    def __init__(self):
        self.search_count = 0
        self.last_search: Optional[SearchContext] = None

    def capture_search(
        self,
        input_text: str,
        component_type: str,
        result: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Captura el contexto de una búsqueda.

        Args:
            input_text: Texto de entrada del usuario
            component_type: Tipo de componente detectado
            result: Resultado ("success", "no_results", "error")
            error_message: Mensaje de error si aplica
        """
        self.search_count += 1

        # Obtener últimas líneas del log
        log_entries = self._get_recent_log_entries()

        self.last_search = SearchContext(
            input_text=input_text,
            component_type=component_type,
            result=result,
            error_message=error_message,
            log_entries=log_entries,
        )

    def should_show_reminder(self) -> bool:
        """Determina si mostrar recordatorio de beta."""
        return self.search_count > 0 and self.search_count % self.REMINDER_INTERVAL == 0

    def generate_report(self, user_comment: str = "") -> dict:
        """Genera un reporte para GitHub Issue.

        Args:
            user_comment: Comentario opcional del usuario

        Returns:
            dict con title, body, labels para crear issue
        """
        if not self.last_search:
            return {}

        ctx = self.last_search

        # Título
        input_truncated = ctx.input_text[:30] + "..." if len(ctx.input_text) > 30 else ctx.input_text
        title = f"[Feedback Beta] Búsqueda fallida: {ctx.component_type} - {input_truncated}"

        # Información del sistema
        os_info = f"{platform.system()} {platform.release()}"
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

        # Resultado legible
        result_map = {
            "success": "Éxito",
            "no_results": "No se encontraron resultados",
            "error": f"Error: {ctx.error_message or 'desconocido'}",
        }
        result_text = result_map.get(ctx.result, ctx.result)

        # Comentario del usuario
        user_section = ""
        if user_comment.strip():
            user_section = f"""
## Descripción del usuario
> {user_comment}
"""

        # Log
        log_text = "\n".join(ctx.log_entries) if ctx.log_entries else "No hay logs disponibles"

        # Cuerpo del issue
        body = f"""## Información del sistema
- **Versión:** {self.VERSION}
- **OS:** {os_info}
- **Python:** {python_version}

## Búsqueda
- **Input:** `{ctx.input_text}`
- **Tipo detectado:** {ctx.component_type or "No detectado"}
- **Resultado:** {result_text}
- **Timestamp:** {ctx.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
{user_section}
## Log de la búsqueda
```
{log_text}
```

---
*Reporte automático de HardwareXtractor Beta v{self.VERSION}*
"""

        return {
            "title": title,
            "body": body,
            "labels": ["beta-feedback", "auto-generated"],
        }

    def _get_recent_log_entries(self, max_lines: int = 50) -> List[str]:
        """Obtiene las últimas líneas del log actual.

        Args:
            max_lines: Máximo de líneas a obtener

        Returns:
            Lista de líneas del log
        """
        try:
            if not LOG_FILE.exists():
                return []

            with open(LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # Últimas N líneas
            return [line.rstrip() for line in lines[-max_lines:]]
        except Exception:
            return []

    def reset(self) -> None:
        """Resetea el contador y contexto."""
        self.search_count = 0
        self.last_search = None


# Instancia global para compartir entre CLI y GUI
_collector: Optional[FeedbackCollector] = None


def get_feedback_collector() -> FeedbackCollector:
    """Obtiene la instancia global del collector."""
    global _collector
    if _collector is None:
        _collector = FeedbackCollector()
    return _collector
