from __future__ import annotations

from hardwarextractor.mapper.mapper import map_component_to_template
from hardwarextractor.models.schemas import ComponentRecord, ComponentType, SpecField, SpecStatus, SourceTier


def _spec(key, value, status, tier, url="https://example.com"):
    return SpecField(
        key=key,
        label=key,
        value=value,
        unit=None,
        status=status,
        source_tier=tier,
        source_name="Test",
        source_url=url,
        confidence=0.9,
    )


def test_mapper_precedence_and_calculated_cpu():
    specs = [
        _spec("cpu.base_clock_mhz", 3600, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.cores_physical", 8, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.threads_logical", 16, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.cache_l1_kb", 512, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.cache_l2_kb", 2048, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.cache_l3_kb", 16384, SpecStatus.EXTRACTED_REFERENCE, SourceTier.REFERENCE),
        _spec("cpu.cache_l3_kb", 32768, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.memory_type_supported", "DDR5", SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.max_memory_gb", 128, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.max_memory_speed_mt_s", 5600, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.memory_channels_max", 2, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.pcie.version_max", "4.0", SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("cpu.pcie.lanes_max", 16, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
    ]
    component = ComponentRecord(
        component_id="cpu-1",
        input_raw="Intel i7",
        input_normalized="intel i7",
        component_type=ComponentType.CPU,
        source_confidence=0.9,
        canonical={"brand": "Intel", "model": "i7"},
        specs=specs,
    )
    fields = map_component_to_template(component)
    l3_fields = [f for f in fields if f.field == "Memoria caché L3"]
    assert l3_fields[0].value == 32768

    bw_ram = [f for f in fields if f.field == "Ancho de banda de la RAM"][0]
    assert bw_ram.status == SpecStatus.CALCULATED
    assert bw_ram.value > 0

    bw_pcie = [f for f in fields if f.field == "Ancho de banda de gráficas añadidas"][0]
    assert bw_pcie.status == SpecStatus.CALCULATED


def test_mapper_ram_calculations():
    specs = [
        _spec("ram.type", "DDR4", SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("ram.speed_effective_mt_s", 3200, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
        _spec("ram.latency_cl", 16, SpecStatus.EXTRACTED_OFFICIAL, SourceTier.OFFICIAL),
    ]
    component = ComponentRecord(
        component_id="ram-1",
        input_raw="DDR4 3200",
        input_normalized="ddr4 3200",
        component_type=ComponentType.RAM,
        source_confidence=0.8,
        canonical={"brand": "Kingston", "model": "Test"},
        specs=specs,
    )
    fields = map_component_to_template(component)
    ratio = [f for f in fields if f.field == "Velocidad efectiva / Latencia"][0]
    assert ratio.status == SpecStatus.CALCULATED
    assert ratio.value == 200.0
