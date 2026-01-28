from __future__ import annotations

from hardwarextractor.mapper.mapper import map_component_to_template
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


def test_mapper_mainboard_fields():
    specs = [
        _spec("mb.socket", "AM4"),
        _spec("mb.chipset", "B550"),
        _spec("mb.max_memory_gb", 128),
        _spec("mb.max_memory_speed_mt_s", 6400),
        _spec("mb.memory_channels", 2),
        _spec("mb.storage.sata.version_max", "SATA III"),
        _spec("mb.usb.version_max", "USB 3.2"),
        _spec("mb.lan.controller", "Realtek"),
        _spec("mb.lan.speed_mbps", 2500),
    ]
    component = ComponentRecord(
        component_id="mb-1",
        input_raw="B550",
        input_normalized="b550",
        component_type=ComponentType.MAINBOARD,
        classification_confidence=0.9,
        canonical={"brand": "ASUS", "model": "B550"},
        specs=specs,
    )
    fields = map_component_to_template(component)
    assert any(f.field == "Zócalo" and f.value == "AM4" for f in fields)
    assert any(f.field == "Ancho de banda SATA" and f.status == SpecStatus.CALCULATED for f in fields)


def test_mapper_gpu_fields():
    specs = [
        _spec("gpu.pcie.version", "4.0"),
        _spec("gpu.pcie.lanes", 16),
        _spec("gpu.mem.bus_width_bits", 192),
        _spec("gpu.mem.speed_gbps", 21),
        _spec("gpu.vram_gb", 12),
    ]
    component = ComponentRecord(
        component_id="gpu-1",
        input_raw="RTX",
        input_normalized="rtx",
        component_type=ComponentType.GPU,
        classification_confidence=0.9,
        canonical={"brand": "NVIDIA", "model": "RTX"},
        specs=specs,
    )
    fields = map_component_to_template(component)
    assert any(f.field == "Ancho de banda interno" for f in fields)


def test_mapper_disk_fields():
    specs = [
        _spec("disk.type", "SSD"),
        _spec("disk.interface", "SATA III"),
        _spec("disk.cache_mb", 256),
    ]
    component = ComponentRecord(
        component_id="disk-1",
        input_raw="SSD",
        input_normalized="ssd",
        component_type=ComponentType.DISK,
        classification_confidence=0.9,
        canonical={"brand": "Samsung", "model": "SSD"},
        specs=specs,
    )
    fields = map_component_to_template(component)
    rpm = [f for f in fields if f.field == "RPM"][0]
    assert rpm.status == SpecStatus.NA
