"""Exporter factory for creating exporters by format."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hardwarextractor.export.base import BaseExporter


class ExporterFactory:
    """Factory for creating exporters by format."""

    _exporters: dict[str, type["BaseExporter"]] = {}

    @classmethod
    def register(cls, format: str, exporter_class: type["BaseExporter"]) -> None:
        """Register an exporter for a format.

        Args:
            format: The format name (e.g., "csv", "xlsx")
            exporter_class: The exporter class
        """
        cls._exporters[format.lower()] = exporter_class

    @classmethod
    def get(cls, format: str) -> "BaseExporter":
        """Get an exporter instance for a format.

        Args:
            format: The format name

        Returns:
            An exporter instance

        Raises:
            ValueError: If format is not supported
        """
        format_lower = format.lower()

        # Lazy load exporters if registry is empty
        if not cls._exporters:
            cls._load_exporters()

        if format_lower not in cls._exporters:
            supported = ", ".join(cls._exporters.keys())
            raise ValueError(
                f"Unsupported format: {format}. Supported formats: {supported}"
            )

        return cls._exporters[format_lower]()

    @classmethod
    def _load_exporters(cls) -> None:
        """Load and register all exporters."""
        from hardwarextractor.export.csv_exporter import CSVExporter
        from hardwarextractor.export.md_exporter import MarkdownExporter
        from hardwarextractor.export.xlsx_exporter import XLSXExporter

        cls.register("csv", CSVExporter)
        cls.register("md", MarkdownExporter)
        cls.register("xlsx", XLSXExporter)

    @classmethod
    def supported_formats(cls) -> list[str]:
        """Get list of supported formats.

        Returns:
            List of format names
        """
        if not cls._exporters:
            cls._load_exporters()
        return list(cls._exporters.keys())
