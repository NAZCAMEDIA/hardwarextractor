"""GitHub Issue reporter para feedback beta.

Envía reportes de feedback automáticamente a GitHub Issues.
"""

from __future__ import annotations

import base64
import os
import time
from datetime import datetime
from typing import Optional

import requests

from hardwarextractor.core.logger import get_logger

logger = get_logger("github_reporter")


class GitHubReporter:
    """Crea issues en GitHub para feedback de beta.

    Usa un token con permisos limitados (solo public_repo)
    para crear issues en el repositorio del proyecto.
    """

    REPO_OWNER = "NAZCAMEDIA"
    REPO_NAME = "hardwarextractor"
    API_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues"

    # Rate limiting
    MIN_INTERVAL_SECONDS = 60  # Mínimo 1 minuto entre reportes

    # Token ofuscado (scope: public_repo - solo crear issues)
    # Configurar via variable de entorno HXTRACTOR_GITHUB_TOKEN
    # o reemplazar _TOKEN_PARTS con token dividido
    _TOKEN_PARTS: list[str] = []  # ["ghp_", "part1", "part2", "part3"]

    def __init__(self):
        self._last_report_time: Optional[datetime] = None

    def _get_token(self) -> Optional[str]:
        """Obtiene el token de GitHub.

        Primero intenta variable de entorno, luego token embebido.

        Returns:
            Token o None si no está configurado
        """
        # Preferir variable de entorno
        env_token = os.environ.get("HXTRACTOR_GITHUB_TOKEN")
        if env_token:
            return env_token

        # Token embebido (si está configurado)
        if self._TOKEN_PARTS:
            return "".join(self._TOKEN_PARTS)

        return None

    def can_report(self) -> tuple[bool, str]:
        """Verifica si se puede enviar un reporte.

        Returns:
            (puede_reportar, mensaje_razón)
        """
        token = self._get_token()
        if not token:
            return False, "Token de GitHub no configurado"

        # Rate limiting
        if self._last_report_time:
            elapsed = (datetime.now() - self._last_report_time).total_seconds()
            if elapsed < self.MIN_INTERVAL_SECONDS:
                remaining = int(self.MIN_INTERVAL_SECONDS - elapsed)
                return False, f"Espera {remaining}s antes de enviar otro reporte"

        return True, ""

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
    ) -> dict:
        """Crea un issue en GitHub.

        Args:
            title: Título del issue
            body: Cuerpo del issue (markdown)
            labels: Lista de labels opcionales

        Returns:
            dict con status, issue_url, issue_number, o error
        """
        can_send, reason = self.can_report()
        if not can_send:
            logger.warning(f"No se puede enviar reporte: {reason}")
            return {"status": "error", "message": reason}

        token = self._get_token()
        if not token:
            return {"status": "error", "message": "Token no configurado"}

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "HardwareXtractor-Beta/0.1.0",
        }

        payload = {
            "title": title,
            "body": body,
        }

        if labels:
            payload["labels"] = labels

        try:
            logger.info(f"Enviando issue a GitHub: {title[:50]}...")

            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code == 201:
                data = response.json()
                self._last_report_time = datetime.now()

                logger.info(f"Issue creado: #{data['number']}")

                return {
                    "status": "success",
                    "issue_url": data["html_url"],
                    "issue_number": data["number"],
                }

            elif response.status_code == 401:
                logger.error("Token de GitHub inválido")
                return {"status": "error", "message": "Token inválido"}

            elif response.status_code == 403:
                logger.error("Sin permisos para crear issues")
                return {"status": "error", "message": "Sin permisos"}

            elif response.status_code == 422:
                logger.error(f"Datos inválidos: {response.text}")
                return {"status": "error", "message": "Datos inválidos"}

            else:
                logger.error(f"Error inesperado: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"Error HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con GitHub")
            return {"status": "error", "message": "Timeout de conexión"}

        except requests.exceptions.ConnectionError:
            logger.error("Error de conexión con GitHub")
            return {"status": "error", "message": "Sin conexión a internet"}

        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return {"status": "error", "message": str(e)}


# Instancia global
_reporter: Optional[GitHubReporter] = None


def get_github_reporter() -> GitHubReporter:
    """Obtiene la instancia global del reporter."""
    global _reporter
    if _reporter is None:
        _reporter = GitHubReporter()
    return _reporter


def send_feedback_report(title: str, body: str, labels: Optional[list[str]] = None) -> dict:
    """Función de conveniencia para enviar un reporte.

    Args:
        title: Título del issue
        body: Cuerpo del issue
        labels: Labels opcionales

    Returns:
        Resultado de la operación
    """
    reporter = get_github_reporter()
    return reporter.create_issue(title, body, labels)
