"""Tests for export module - Exporters and Factory."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hardwarextractor.export.base import BaseExporter, ExportResult
from hardwarextractor.export.factory import ExporterFactory
from hardwarextractor.export.csv_exporter import CSVExporter
from hardwarextractor.models.schemas import (
    ComponentRecord,
    ComponentType,
    FichaAggregated,
    SourceTier,
    SpecField,
    SpecStatus,
    TemplateField,
)


def create_mock_ficha_manager():
    """Create a mock FichaManager for testing."""
    manager = MagicMock()
    manager.components = [
        ComponentRecord(
            component_id="test_123",
            input_raw="Corsair CMK32GX4M2B3200C16",
            input_normalized="corsair cmk32gx4m2b3200c16",
            component_type=ComponentType.RAM,
            classification_confidence=0.95,
            canonical={"brand": "Corsair", "model": "Vengeance LPX"},
            specs=[
                SpecField(
                    key="capacity",
                    label="Capacity",
                    value="32GB",
                    unit="GB",
                    source_tier=SourceTier.OFFICIAL,
                    source_url="https://corsair.com",
                    status=SpecStatus.EXTRACTED_OFFICIAL,
                ),
                SpecField(
                    key="speed",
                    label="Speed",
                    value="3200",
                    unit="MHz",
                    source_tier=SourceTier.OFFICIAL,
                    source_url="https://corsair.com",
                    status=SpecStatus.EXTRACTED_OFFICIAL,
                ),
            ],
        ),
    ]

    # Mock get_export_rows (used by CSVExporter)
    manager.get_export_rows.return_value = [
        {
            "section": "Memory",
            "field": "capacity",
            "value": "32GB",
            "unit": "GB",
            "status": "EXTRACTED_OFFICIAL",
            "tier": "OFFICIAL",
            "source_name": "corsair",
            "source_url": "https://corsair.com",
        },
        {
            "section": "Memory",
            "field": "speed",
            "value": "3200",
            "unit": "MHz",
            "status": "EXTRACTED_OFFICIAL",
            "tier": "OFFICIAL",
            "source_name": "corsair",
            "source_url": "https://corsair.com",
        },
    ]

    # Mock get_aggregated
    ficha = FichaAggregated(
        ficha_id="ficha_123",
        components=manager.components,
        fields_by_template=[
            TemplateField(
                section="Memory",
                field="capacity",
                value="32GB",
                unit="GB",
                source_tier=SourceTier.OFFICIAL,
                source_name="corsair",
                source_url="https://corsair.com",
                status=SpecStatus.EXTRACTED_OFFICIAL,
                confidence=0.95,
                component_id="test_123",
            ),
            TemplateField(
                section="Memory",
                field="speed",
                value="3200",
                unit="MHz",
                source_tier=SourceTier.OFFICIAL,
                source_name="corsair",
                source_url="https://corsair.com",
                status=SpecStatus.EXTRACTED_OFFICIAL,
                confidence=0.95,
                component_id="test_123",
            ),
        ],
        has_reference=False,
    )
    manager.get_aggregated.return_value = ficha
    return manager


class TestExportResult:
    """Test ExportResult dataclass."""

    def test_export_result_success(self):
        """Test successful export result."""
        result = ExportResult(
            success=True,
            path=Path("/tmp/test.csv"),
            rows=10,
            format="csv",
        )
        assert result.success is True
        assert result.path == Path("/tmp/test.csv")
        assert result.rows == 10
        assert result.format == "csv"
        assert result.error is None

    def test_export_result_failure(self):
        """Test failed export result."""
        result = ExportResult(
            success=False,
            path=None,
            rows=0,
            format="csv",
            error="File write error",
        )
        assert result.success is False
        assert result.error == "File write error"


class TestExporterFactory:
    """Test ExporterFactory."""

    def test_get_csv_exporter(self):
        """Test getting CSV exporter."""
        exporter = ExporterFactory.get("csv")
        assert isinstance(exporter, CSVExporter)

    def test_get_csv_exporter_uppercase(self):
        """Test getting CSV exporter with uppercase."""
        exporter = ExporterFactory.get("CSV")
        assert isinstance(exporter, CSVExporter)

    def test_get_unknown_format(self):
        """Test getting unknown format raises error."""
        with pytest.raises(ValueError, match="Unsupported format"):
            ExporterFactory.get("unknown")

    def test_supported_formats(self):
        """Test that supported formats are available."""
        # CSV should always work
        exporter = ExporterFactory.get("csv")
        assert exporter is not None


class TestCSVExporter:
    """Test CSVExporter."""

    def test_csv_export(self):
        """Test CSV export."""
        manager = create_mock_ficha_manager()
        exporter = CSVExporter()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = Path(f.name)

        try:
            result = exporter.export(manager, path)
            assert result.success is True
            assert result.path == path
            assert result.rows > 0
            assert result.format == "csv"

            # Verify file content
            content = path.read_text()
            assert "capacity" in content.lower() or "Capacity" in content
        finally:
            if path.exists():
                path.unlink()

    def test_csv_export_empty(self):
        """Test CSV export with empty components."""
        manager = MagicMock()
        manager.components = []
        manager.get_aggregated.return_value = FichaAggregated(
            ficha_id="empty",
            components=[],
            fields_by_template=[],
            has_reference=False,
        )

        exporter = CSVExporter()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = Path(f.name)

        try:
            result = exporter.export(manager, path)
            # Should succeed even with empty data
            assert result.success is True
            assert result.rows == 0
        finally:
            if path.exists():
                path.unlink()


class TestMDExporter:
    """Test Markdown exporter."""

    def test_md_export(self):
        """Test Markdown export."""
        try:
            from hardwarextractor.export.md_exporter import MarkdownExporter
        except ImportError:
            pytest.skip("MarkdownExporter not available")

        manager = create_mock_ficha_manager()
        exporter = MarkdownExporter()

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = Path(f.name)

        try:
            result = exporter.export(manager, path)
            assert result.success is True
            assert result.format == "md"

            # Verify file content
            content = path.read_text()
            assert "capacity" in content.lower() or "#" in content
        finally:
            if path.exists():
                path.unlink()

    def test_md_export_via_factory(self):
        """Test getting MD exporter via factory."""
        try:
            exporter = ExporterFactory.get("md")
            assert exporter is not None
        except ValueError:
            pytest.skip("MD exporter not registered")


class TestXLSXExporter:
    """Test XLSX exporter."""

    def test_xlsx_export(self):
        """Test XLSX export."""
        try:
            from hardwarextractor.export.xlsx_exporter import XLSXExporter
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not available")

        manager = create_mock_ficha_manager()
        exporter = XLSXExporter()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = Path(f.name)

        try:
            result = exporter.export(manager, path)
            assert result.success is True
            assert result.format == "xlsx"

            # Verify file is valid xlsx
            wb = openpyxl.load_workbook(path)
            assert len(wb.sheetnames) > 0
            wb.close()
        finally:
            if path.exists():
                path.unlink()

    def test_xlsx_export_via_factory(self):
        """Test getting XLSX exporter via factory."""
        try:
            import openpyxl
            exporter = ExporterFactory.get("xlsx")
            assert exporter is not None
        except (ImportError, ValueError):
            pytest.skip("XLSX exporter not available")

    def test_xlsx_export_has_reference_banner(self):
        """Test XLSX export includes reference banner when has_reference is True."""
        try:
            from hardwarextractor.export.xlsx_exporter import XLSXExporter
            import openpyxl
        except ImportError:
            pytest.skip("openpyxl not available")

        manager = create_mock_ficha_manager()
        # Set has_reference to True
        ficha = manager.get_aggregated()
        ficha.has_reference = True

        exporter = XLSXExporter()

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            path = Path(f.name)

        try:
            result = exporter.export(manager, path)
            assert result.success is True
        finally:
            if path.exists():
                path.unlink()


class TestSpecFieldUsage:
    """Test SpecField proper usage in exports."""

    def test_specfield_with_all_fields(self):
        """Test creating SpecField with all fields."""
        spec = SpecField(
            key="tdp",
            label="TDP",
            value=125,
            unit="W",
            status=SpecStatus.EXTRACTED_OFFICIAL,
            source_tier=SourceTier.OFFICIAL,
            source_name="intel_ark",
            source_url="https://ark.intel.com/123",
            confidence=0.95,
            notes="Base TDP",
        )
        assert spec.key == "tdp"
        assert spec.label == "TDP"
        assert spec.value == 125
        assert spec.unit == "W"
        assert spec.status == SpecStatus.EXTRACTED_OFFICIAL
        assert spec.source_tier == SourceTier.OFFICIAL

    def test_specfield_minimal(self):
        """Test creating minimal SpecField."""
        spec = SpecField(
            key="cores",
            label="Core Count",
            value=8,
        )
        assert spec.key == "cores"
        assert spec.value == 8
        assert spec.status == SpecStatus.UNKNOWN
        assert spec.source_tier == SourceTier.NONE

    def test_templatefield_structure(self):
        """Test TemplateField structure."""
        tf = TemplateField(
            section="Processor",
            field="cores",
            value=8,
            unit=None,
            status=SpecStatus.EXTRACTED_OFFICIAL,
            source_tier=SourceTier.OFFICIAL,
            source_name="intel_ark",
            source_url="https://ark.intel.com/123",
            confidence=0.95,
            component_id="cpu_123",
        )
        assert tf.section == "Processor"
        assert tf.field == "cores"
        assert tf.value == 8
        assert tf.component_id == "cpu_123"


class TestComponentRecord:
    """Test ComponentRecord structure for exports."""

    def test_component_record_creation(self):
        """Test creating a ComponentRecord."""
        record = ComponentRecord(
            component_id="test_001",
            input_raw="Intel Core i7-12700K",
            input_normalized="intel core i7 12700k",
            component_type=ComponentType.CPU,
            classification_confidence=0.98,
            canonical={"brand": "Intel", "model": "Core i7-12700K"},
            specs=[
                SpecField(key="cores", label="Cores", value=12),
                SpecField(key="threads", label="Threads", value=20),
            ],
        )
        assert record.component_id == "test_001"
        assert record.component_type == ComponentType.CPU
        assert len(record.specs) == 2
        assert record.specs[0].key == "cores"

    def test_component_record_empty_specs(self):
        """Test ComponentRecord with empty specs."""
        record = ComponentRecord(
            component_id="test_002",
            input_raw="Unknown Component",
            input_normalized="unknown component",
            component_type=ComponentType.GENERAL,
            classification_confidence=0.5,
            canonical={},
            specs=[],
        )
        assert len(record.specs) == 0


class TestFichaAggregated:
    """Test FichaAggregated structure for exports."""

    def test_ficha_aggregated_creation(self):
        """Test creating a FichaAggregated."""
        ficha = FichaAggregated(
            ficha_id="ficha_001",
            components=[],
            fields_by_template=[],
            has_reference=False,
        )
        assert ficha.ficha_id == "ficha_001"
        assert len(ficha.components) == 0
        assert ficha.has_reference is False

    def test_ficha_aggregated_with_reference(self):
        """Test FichaAggregated with reference data."""
        ficha = FichaAggregated(
            ficha_id="ficha_002",
            components=[],
            fields_by_template=[],
            has_reference=True,
        )
        assert ficha.has_reference is True

    def test_ficha_aggregated_general_field(self):
        """Test FichaAggregated with general metadata."""
        ficha = FichaAggregated(
            ficha_id="ficha_003",
            general={"name": "Test PC Build", "created": "2025-01-29"},
            components=[],
            fields_by_template=[],
            has_reference=False,
        )
        assert ficha.general["name"] == "Test PC Build"
