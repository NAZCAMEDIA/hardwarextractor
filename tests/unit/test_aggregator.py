from __future__ import annotations

from hardwarextractor.aggregate.aggregator import aggregate_components
from hardwarextractor.models.schemas import ComponentRecord, ComponentType, SpecField, SpecStatus, SourceTier


def _spec(key, value, status=SpecStatus.EXTRACTED_OFFICIAL, tier=SourceTier.OFFICIAL):
    return SpecField(
        key=key,
        label=key,
        value=value,
        unit=None,
        status=status,
        source_tier=tier,
        source_name="Test",
        source_url="https://example.com",
        confidence=0.9,
    )


def test_aggregate_reference_flag():
    component = ComponentRecord(
        component_id="gpu-1",
        input_raw="RTX",
        input_normalized="rtx",
        component_type=ComponentType.GPU,
        source_confidence=0.9,
        canonical={"brand": "NVIDIA", "model": "RTX"},
        specs=[_spec("gpu.vram_gb", 8, SpecStatus.EXTRACTED_REFERENCE, SourceTier.REFERENCE)],
    )
    ficha = aggregate_components([component])
    assert ficha.has_reference is True


def test_aggregate_unknown_fills():
    component = ComponentRecord(
        component_id="cpu-1",
        input_raw="Intel",
        input_normalized="intel",
        component_type=ComponentType.CPU,
        source_confidence=0.9,
        canonical={"brand": "Intel", "model": "i7"},
        specs=[],
    )
    ficha = aggregate_components([component], system_name=None)
    assert any(field.value == "UNKNOWN" for field in ficha.fields_by_template)
