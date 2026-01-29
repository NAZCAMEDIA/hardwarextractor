"""Tests for export factory module."""

from __future__ import annotations

import pytest

from hardwarextractor.export.factory import ExporterFactory
from hardwarextractor.export.csv_exporter import CSVExporter
from hardwarextractor.export.md_exporter import MarkdownExporter


class TestExporterFactory:
    """Tests for ExporterFactory."""

    def setup_method(self):
        # Clear the registry before each test
        ExporterFactory._exporters = {}

    def test_register_and_get(self):
        ExporterFactory.register("csv", CSVExporter)
        exporter = ExporterFactory.get("csv")
        assert isinstance(exporter, CSVExporter)

    def test_get_case_insensitive(self):
        ExporterFactory.register("csv", CSVExporter)
        exporter = ExporterFactory.get("CSV")
        assert isinstance(exporter, CSVExporter)

    def test_get_lazy_loads(self):
        # Registry is empty, should lazy load
        assert ExporterFactory._exporters == {}
        exporter = ExporterFactory.get("csv")
        assert isinstance(exporter, CSVExporter)
        # Registry should now have exporters
        assert len(ExporterFactory._exporters) > 0

    def test_get_unsupported_format(self):
        with pytest.raises(ValueError) as exc_info:
            ExporterFactory.get("unsupported")
        assert "Unsupported format" in str(exc_info.value)

    def test_supported_formats(self):
        formats = ExporterFactory.supported_formats()
        assert "csv" in formats
        assert "md" in formats

    def test_supported_formats_lazy_loads(self):
        # Clear registry
        ExporterFactory._exporters = {}
        formats = ExporterFactory.supported_formats()
        # Should lazy load and return formats
        assert len(formats) > 0

    def test_get_md_exporter(self):
        exporter = ExporterFactory.get("md")
        assert isinstance(exporter, MarkdownExporter)
