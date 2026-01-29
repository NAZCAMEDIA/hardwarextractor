"""Base exporter class and result type."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hardwarextractor.engine.ficha_manager import FichaManager


@dataclass
class ExportResult:
    """Result of an export operation.

    Attributes:
        path: Path to the exported file
        format: Export format used
        rows: Number of rows exported
        success: Whether export succeeded
        error: Error message if failed
    """
    path: Path
    format: str
    rows: int = 0
    success: bool = True
    error: str | None = None


class BaseExporter(ABC):
    """Abstract base class for exporters."""

    @property
    @abstractmethod
    def format(self) -> str:
        """The format this exporter handles."""
        pass

    @abstractmethod
    def export(self, ficha_manager: "FichaManager", path: Path) -> ExportResult:
        """Export the ficha to a file.

        Args:
            ficha_manager: The ficha manager with data to export
            path: Output file path

        Returns:
            ExportResult with export information
        """
        pass

    def _get_header_info(self, ficha_manager: "FichaManager") -> dict:
        """Get header information for export.

        Args:
            ficha_manager: The ficha manager

        Returns:
            Dictionary with header information
        """
        return {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ficha_id": ficha_manager.ficha_id,
            "component_count": ficha_manager.component_count,
            "has_reference": ficha_manager.has_reference_data(),
        }

    def _truncate_url(self, url: str | None, max_len: int = 50) -> str:
        """Truncate a URL for display.

        Args:
            url: The URL to truncate
            max_len: Maximum length

        Returns:
            Truncated URL string
        """
        if not url:
            return ""
        if len(url) <= max_len:
            return url
        return url[:max_len - 3] + "..."
