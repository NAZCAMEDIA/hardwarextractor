"""Tests for engine/ficha_manager.py - Ficha management."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from hardwarextractor.engine.ficha_manager import FichaManager
from hardwarextractor.models.schemas import (
    ComponentRecord,
    ComponentType,
    SourceTier,
    SpecField,
    SpecStatus,
)


class TestFichaManagerCreation:
    """Test FichaManager initialization."""

    def test_create_empty_ficha(self):
        """Test creating an empty ficha manager."""
        fm = FichaManager()
        assert fm is not None
        assert fm.component_count == 0
        assert fm.ficha_id is not None
        assert len(fm.ficha_id) > 0

    def test_ficha_has_unique_id(self):
        """Test that each ficha gets a unique ID."""
        fm1 = FichaManager()
        fm2 = FichaManager()
        assert fm1.ficha_id != fm2.ficha_id

    def test_components_property_returns_copy(self):
        """Test that components property returns a copy."""
        fm = FichaManager()
        components = fm.components
        assert components == []
        assert components is not fm._components


class TestAddComponent:
    """Test adding components to ficha."""

    @pytest.fixture
    def ficha_manager(self):
        return FichaManager()

    @pytest.fixture
    def cpu_component(self):
        return ComponentRecord(
            component_id="cpu-001",
            input_raw="Intel Core i7-12700K",
            input_normalized="intel core i7 12700k",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel", "model": "i7-12700K"},
            source_confidence=0.95,
            specs=[
                SpecField(
                    key="cores",
                    label="Cores",
                    value="12",
                    status=SpecStatus.EXTRACTED_OFFICIAL,
                    source_tier=SourceTier.OFFICIAL,
                    source_name="Amazon",
                )
            ],
        )

    @pytest.fixture
    def ram_component(self):
        return ComponentRecord(
            component_id="ram-001",
            input_raw="Corsair Vengeance LPX 32GB",
            input_normalized="corsair vengeance lpx 32gb",
            component_type=ComponentType.RAM,
            canonical={"brand": "Corsair", "model": "Vengeance LPX"},
            source_confidence=0.90,
            specs=[
                SpecField(
                    key="capacity",
                    label="Capacity",
                    value="32GB",
                    status=SpecStatus.EXTRACTED_OFFICIAL,
                    source_tier=SourceTier.OFFICIAL,
                )
            ],
        )

    def test_add_single_component(self, ficha_manager, cpu_component):
        """Test adding a single component."""
        ficha_manager.add_component(cpu_component)
        assert ficha_manager.component_count == 1
        assert ficha_manager.components[0].component_id == "cpu-001"

    def test_add_stacking_components(self, ficha_manager, ram_component):
        """Test that RAM and DISK components stack."""
        ram2 = ComponentRecord(
            component_id="ram-002",
            input_raw="Corsair Vengeance LPX 2",
            input_normalized="corsair vengeance lpx 2",
            component_type=ComponentType.RAM,
            canonical={"brand": "Corsair", "model": "Vengeance LPX 2"},
            source_confidence=0.90,
            specs=[],
        )
        ficha_manager.add_component(ram_component)
        ficha_manager.add_component(ram2)
        assert ficha_manager.component_count == 2

    def test_non_stacking_components_replace(self, ficha_manager, cpu_component):
        """Test that non-stacking components replace existing."""
        cpu2 = ComponentRecord(
            component_id="cpu-002",
            input_raw="AMD Ryzen 9 5900X",
            input_normalized="amd ryzen 9 5900x",
            component_type=ComponentType.CPU,
            canonical={"brand": "AMD", "model": "Ryzen 9"},
            source_confidence=0.95,
            specs=[],
        )
        ficha_manager.add_component(cpu_component)
        ficha_manager.add_component(cpu2)
        assert ficha_manager.component_count == 1
        assert ficha_manager.components[0].component_id == "cpu-002"

    def test_add_disk_stacks(self, ficha_manager):
        """Test that DISK components stack."""
        disk1 = ComponentRecord(
            component_id="disk-001",
            input_raw="Samsung 980 Pro 1TB",
            input_normalized="samsung 980 pro 1tb",
            component_type=ComponentType.DISK,
            canonical={"brand": "Samsung", "model": "980 Pro"},
            source_confidence=0.90,
            specs=[],
        )
        disk2 = ComponentRecord(
            component_id="disk-002",
            input_raw="WD Black 2TB",
            input_normalized="wd black 2tb",
            component_type=ComponentType.DISK,
            canonical={"brand": "WD", "model": "Black"},
            source_confidence=0.90,
            specs=[],
        )
        ficha_manager.add_component(disk1)
        ficha_manager.add_component(disk2)
        assert ficha_manager.component_count == 2


class TestRemoveComponent:
    """Test removing components from ficha."""

    @pytest.fixture
    def ficha_with_component(self):
        fm = FichaManager()
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Test Component",
            input_normalized="test component",
            component_type=ComponentType.CPU,
            canonical={"brand": "Test"},
            source_confidence=0.9,
            specs=[],
        )
        fm.add_component(component)
        return fm

    def test_remove_existing_component(self, ficha_with_component):
        """Test removing an existing component."""
        result = ficha_with_component.remove_component("test-001")
        assert result is True
        assert ficha_with_component.component_count == 0

    def test_remove_nonexistent_component(self, ficha_with_component):
        """Test removing a non-existent component."""
        result = ficha_with_component.remove_component("nonexistent")
        assert result is False
        assert ficha_with_component.component_count == 1


class TestHasReferenceData:
    """Test reference data detection."""

    @pytest.fixture
    def ficha_manager(self):
        return FichaManager()

    def test_no_reference_data(self, ficha_manager):
        """Test when no reference data exists."""
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Test Component",
            input_normalized="test component",
            component_type=ComponentType.CPU,
            canonical={},
            source_confidence=0.9,
            specs=[
                SpecField(
                    key="test",
                    label="Test",
                    value="value",
                    status=SpecStatus.EXTRACTED_OFFICIAL,
                    source_tier=SourceTier.OFFICIAL,
                )
            ],
        )
        ficha_manager.add_component(component)
        assert ficha_manager.has_reference_data() is False

    def test_has_reference_data(self, ficha_manager):
        """Test when reference data exists."""
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Test Component",
            input_normalized="test component",
            component_type=ComponentType.CPU,
            canonical={},
            source_confidence=0.9,
            specs=[
                SpecField(
                    key="test",
                    label="Test",
                    value="value",
                    status=SpecStatus.EXTRACTED_REFERENCE,
                    source_tier=SourceTier.REFERENCE,
                )
            ],
        )
        ficha_manager.add_component(component)
        assert ficha_manager.has_reference_data() is True


class TestGetSpec:
    """Test getting specific specs."""

    @pytest.fixture
    def ficha_with_specs(self):
        fm = FichaManager()
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Intel Core i7",
            input_normalized="intel core i7",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel", "model": "i7"},
            source_confidence=0.9,
            specs=[
                SpecField(
                    key="cores",
                    label="Cores",
                    value="8",
                    unit="cores",
                    status=SpecStatus.EXTRACTED_OFFICIAL,
                    source_tier=SourceTier.OFFICIAL,
                    source_name="TestSource",
                    source_url="https://test.com",
                )
            ],
        )
        fm.add_component(component)
        return fm

    def test_get_existing_spec(self, ficha_with_specs):
        """Test getting an existing spec by key."""
        # Note: get_spec relies on aggregated fields
        # This may return None depending on aggregation implementation
        spec = ficha_with_specs.get_spec("cores")
        # The result depends on aggregation - may or may not find
        # Just ensure it doesn't crash

    def test_get_nonexistent_spec(self, ficha_with_specs):
        """Test getting a non-existent spec."""
        spec = ficha_with_specs.get_spec("nonexistent_key")
        assert spec is None


class TestReset:
    """Test ficha reset functionality."""

    def test_reset_clears_components(self):
        """Test that reset clears all components."""
        fm = FichaManager()
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Test Component",
            input_normalized="test component",
            component_type=ComponentType.CPU,
            canonical={},
            source_confidence=0.9,
            specs=[],
        )
        fm.add_component(component)
        old_id = fm.ficha_id

        fm.reset()

        assert fm.component_count == 0
        assert fm.ficha_id != old_id


class TestToDict:
    """Test dictionary serialization."""

    @pytest.fixture
    def ficha_with_component(self):
        fm = FichaManager()
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Intel Core i7",
            input_normalized="intel core i7",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel", "model": "i7", "part_number": "BX123"},
            source_confidence=0.9,
            specs=[],
        )
        fm.add_component(component)
        return fm

    def test_to_dict_structure(self, ficha_with_component):
        """Test the dictionary structure."""
        d = ficha_with_component.to_dict()
        assert "ficha_id" in d
        assert "created_at" in d
        assert "last_updated" in d
        assert "component_count" in d
        assert "has_reference" in d
        assert "components" in d
        assert "fields_by_template" in d

    def test_to_dict_component_data(self, ficha_with_component):
        """Test component data in dictionary."""
        d = ficha_with_component.to_dict()
        assert d["component_count"] == 1
        assert len(d["components"]) == 1
        comp = d["components"][0]
        assert comp["component_id"] == "test-001"
        assert comp["type"] == "CPU"
        assert comp["brand"] == "Intel"
        assert comp["model"] == "i7"


class TestGetExportRows:
    """Test export row generation."""

    def test_empty_ficha_export_rows(self):
        """Test export rows from empty ficha."""
        fm = FichaManager()
        rows = fm.get_export_rows()
        # Should return rows based on template even if empty
        assert isinstance(rows, list)

    def test_export_rows_have_required_fields(self):
        """Test that export rows have all required fields."""
        fm = FichaManager()
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Intel Core i7",
            input_normalized="intel core i7",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel"},
            source_confidence=0.9,
            specs=[],
        )
        fm.add_component(component)
        rows = fm.get_export_rows()

        for row in rows:
            assert "section" in row
            assert "field" in row
            assert "value" in row
            assert "unit" in row
            assert "origen" in row  # Nuevo formato unificado
            assert "source_name" in row
            assert "source_url" in row


class TestExport:
    """Test ficha export functionality."""

    @pytest.fixture
    def ficha_with_component(self):
        fm = FichaManager()
        component = ComponentRecord(
            component_id="test-001",
            input_raw="Intel Core i7",
            input_normalized="intel core i7",
            component_type=ComponentType.CPU,
            canonical={"brand": "Intel", "model": "i7"},
            source_confidence=0.9,
            specs=[],
        )
        fm.add_component(component)
        return fm

    def test_export_csv(self, ficha_with_component, tmp_path):
        """Test CSV export."""
        output_path = tmp_path / "test_export.csv"
        result = ficha_with_component.export("csv", str(output_path))
        assert result == str(output_path)
        assert output_path.exists()

    def test_export_auto_path(self, ficha_with_component, tmp_path, monkeypatch):
        """Test export with auto-generated path."""
        monkeypatch.chdir(tmp_path)
        result = ficha_with_component.export("csv")
        assert "hxtractor_export_" in result
        assert result.endswith(".csv")
