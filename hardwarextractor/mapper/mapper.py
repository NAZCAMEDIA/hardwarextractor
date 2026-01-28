from __future__ import annotations

from typing import Dict, List, Optional

from hardwarextractor.models.schemas import ComponentRecord, SpecField, SpecStatus, SourceTier, TemplateField
from hardwarextractor.utils.calculations import (
    bw_gpu_internal_gbs,
    bw_pcie_external_gbs,
    bw_ram_gbs,
    bw_sata_gbs,
    bw_usb_gbs,
)


_PRECEDENCE = {
    SpecStatus.EXTRACTED_OFFICIAL: 3,
    SpecStatus.EXTRACTED_REFERENCE: 2,
    SpecStatus.CALCULATED: 1,
    SpecStatus.NA: 0,
    SpecStatus.UNKNOWN: 0,
}


def _spec_by_key(specs: List[SpecField]) -> Dict[str, List[SpecField]]:
    grouped: Dict[str, List[SpecField]] = {}
    for spec in specs:
        grouped.setdefault(spec.key, []).append(spec)
    return grouped


def _pick_spec(specs: List[SpecField]) -> Optional[SpecField]:
    if not specs:
        return None
    return sorted(specs, key=lambda s: (-_PRECEDENCE.get(s.status, 0), -s.confidence))[0]


def _unknown_field(section: str, field: str, component_id: Optional[str]) -> TemplateField:
    return TemplateField(
        section=section,
        field=field,
        value="UNKNOWN",
        unit=None,
        status=SpecStatus.UNKNOWN,
        source_tier=SourceTier.NONE,
        source_name=None,
        source_url=None,
        confidence=0.0,
        component_id=component_id,
    )


def _na_field(section: str, field: str, component_id: Optional[str]) -> TemplateField:
    return TemplateField(
        section=section,
        field=field,
        value="NA",
        unit=None,
        status=SpecStatus.NA,
        source_tier=SourceTier.NONE,
        source_name=None,
        source_url=None,
        confidence=0.0,
        component_id=component_id,
    )


def _field_from_spec(section: str, field: str, spec: SpecField, component_id: Optional[str]) -> TemplateField:
    return TemplateField(
        section=section,
        field=field,
        value=spec.value,
        unit=spec.unit,
        status=spec.status,
        source_tier=spec.source_tier,
        source_name=spec.source_name,
        source_url=spec.source_url,
        confidence=spec.confidence,
        component_id=component_id,
    )


def _calculated_field(section: str, field: str, value: float | str, unit: Optional[str], component_id: Optional[str], inputs_used: Dict[str, float] | None = None) -> TemplateField:
    return TemplateField(
        section=section,
        field=field,
        value=value,
        unit=unit,
        status=SpecStatus.CALCULATED,
        source_tier=SourceTier.NONE,
        source_name="CALCULATED",
        source_url="CALCULATED",
        confidence=0.8,
        component_id=component_id,
    )


def map_component_to_template(component: ComponentRecord) -> List[TemplateField]:
    specs_by_key = _spec_by_key(component.specs)
    fields: List[TemplateField] = []

    if component.component_type.value == "CPU":
        fields.extend(_map_cpu(component, specs_by_key))
    elif component.component_type.value == "MAINBOARD":
        fields.extend(_map_mainboard(component, specs_by_key))
    elif component.component_type.value == "RAM":
        fields.extend(_map_ram(component, specs_by_key))
    elif component.component_type.value == "GPU":
        fields.extend(_map_gpu(component, specs_by_key))
    elif component.component_type.value == "DISK":
        fields.extend(_map_disk(component, specs_by_key))

    return fields


def _map_cpu(component: ComponentRecord, specs_by_key: Dict[str, List[SpecField]]) -> List[TemplateField]:
    section = "Procesador"
    fields: List[TemplateField] = []

    def add_from_key(field_name: str, key: str):
        spec = _pick_spec(specs_by_key.get(key, []))
        if spec:
            fields.append(_field_from_spec(section, field_name, spec, component.component_id))
        else:
            fields.append(_unknown_field(section, field_name, component.component_id))

    add_from_key("Velocidad interna", "cpu.base_clock_mhz")
    add_from_key("Núcleos físicos", "cpu.cores_physical")
    add_from_key("Núcleos lógicos", "cpu.threads_logical")
    add_from_key("Memoria caché L1", "cpu.cache_l1_kb")
    add_from_key("Memoria caché L2", "cpu.cache_l2_kb")
    add_from_key("Memoria caché L3", "cpu.cache_l3_kb")

    memory_type = _pick_spec(specs_by_key.get("cpu.memory_type_supported", []))
    max_memory = _pick_spec(specs_by_key.get("cpu.max_memory_gb", []))
    max_speed = _pick_spec(specs_by_key.get("cpu.max_memory_speed_mt_s", []))
    channels = _pick_spec(specs_by_key.get("cpu.memory_channels_max", []))
    if memory_type and max_memory and max_speed and channels:
        value = f"{memory_type.value}, {max_memory.value} GB, {max_speed.value} MT/s, {channels.value} channels"
        fields.append(_field_from_spec(section, "RAM soportada", SpecField(
            key="cpu.memory_supported",
            label="RAM soportada",
            value=value,
            unit=None,
            status=memory_type.status,
            source_tier=memory_type.source_tier,
            source_name=memory_type.source_name,
            source_url=memory_type.source_url,
            confidence=min(memory_type.confidence, max_memory.confidence, max_speed.confidence, channels.confidence),
        ), component.component_id))
    else:
        fields.append(_unknown_field(section, "RAM soportada", component.component_id))

    mt_s = max_speed.value if max_speed else None
    channels_val = channels.value if channels else None
    bw_ram = bw_ram_gbs(mt_s, channels_val)
    if bw_ram is not None:
        fields.append(_calculated_field(section, "Ancho de banda de la RAM", bw_ram, "GB/s", component.component_id))
    else:
        fields.append(_unknown_field(section, "Ancho de banda de la RAM", component.component_id))

    add_from_key("Tipo de bus del sistema", "cpu.interconnect.type")
    add_from_key("Velocidad del bus del sistema", "cpu.interconnect.speed")
    add_from_key("Ancho de banda del bus del sistema", "cpu.interconnect.bandwidth")

    pcie_version = _pick_spec(specs_by_key.get("cpu.pcie.version_max", []))
    pcie_lanes = _pick_spec(specs_by_key.get("cpu.pcie.lanes_max", []))
    bw_pcie = bw_pcie_external_gbs(pcie_version.value if pcie_version else None, pcie_lanes.value if pcie_lanes else None)
    if bw_pcie is not None:
        fields.append(_calculated_field(section, "Ancho de banda de gráficas añadidas", bw_pcie, "GB/s", component.component_id))
    else:
        fields.append(_unknown_field(section, "Ancho de banda de gráficas añadidas", component.component_id))

    if bw_ram is not None and bw_pcie is not None:
        total = bw_ram + bw_pcie
        fields.append(_calculated_field(section, "Ancho de banda total del procesador", total, "GB/s", component.component_id))
    else:
        fields.append(_unknown_field(section, "Ancho de banda total del procesador", component.component_id))

    return fields


def _map_mainboard(component: ComponentRecord, specs_by_key: Dict[str, List[SpecField]]) -> List[TemplateField]:
    section = "Placa base"
    fields: List[TemplateField] = []

    def add_from_key(field_name: str, key: str):
        spec = _pick_spec(specs_by_key.get(key, []))
        if spec:
            fields.append(_field_from_spec(section, field_name, spec, component.component_id))
        else:
            fields.append(_unknown_field(section, field_name, component.component_id))

    add_from_key("Tipo de bus del sistema", "mb.bus.type")
    add_from_key("Ancho de banda máximo del bus del sistema", "mb.bus.bandwidth")
    add_from_key("RAM máxima soportada", "mb.max_memory_gb")

    max_speed = _pick_spec(specs_by_key.get("mb.max_memory_speed_mt_s", []))
    channels = _pick_spec(specs_by_key.get("mb.memory_channels", []))
    bw_ram = bw_ram_gbs(max_speed.value if max_speed else None, channels.value if channels else None)
    if bw_ram is not None:
        fields.append(_calculated_field(section, "Ancho de banda de la RAM", bw_ram, "GB/s", component.component_id))
    else:
        fields.append(_unknown_field(section, "Ancho de banda de la RAM", component.component_id))

    add_from_key("Procesador máximo que soporta", "mb.cpu_support.families")
    add_from_key("Zócalo", "mb.socket")
    add_from_key("Tarjeta gráfica integrada", "mb.igpu")

    if bw_ram is not None:
        fields.append(_calculated_field(section, "Ancho de banda de la TG integrada", bw_ram, "GB/s", component.component_id))
    else:
        fields.append(_unknown_field(section, "Ancho de banda de la TG integrada", component.component_id))

    sata_ver = _pick_spec(specs_by_key.get("mb.storage.sata.version_max", []))
    if sata_ver:
        fields.append(_field_from_spec(section, "Tipo de SATA", sata_ver, component.component_id))
        bw_sata = bw_sata_gbs(sata_ver.value)
        if bw_sata is not None:
            fields.append(_calculated_field(section, "Ancho de banda SATA", bw_sata, "Gb/s", component.component_id))
        else:
            fields.append(_unknown_field(section, "Ancho de banda SATA", component.component_id))
    else:
        fields.append(_unknown_field(section, "Tipo de SATA", component.component_id))
        fields.append(_unknown_field(section, "Ancho de banda SATA", component.component_id))

    usb_ver = _pick_spec(specs_by_key.get("mb.usb.version_max", []))
    if usb_ver:
        fields.append(_field_from_spec(section, "Tipo de USB", usb_ver, component.component_id))
        bw_usb = bw_usb_gbs(usb_ver.value)
        if bw_usb is not None:
            fields.append(_calculated_field(section, "Ancho de banda USB", bw_usb, "Gb/s", component.component_id))
        else:
            fields.append(_unknown_field(section, "Ancho de banda USB", component.component_id))
    else:
        fields.append(_unknown_field(section, "Tipo de USB", component.component_id))
        fields.append(_unknown_field(section, "Ancho de banda USB", component.component_id))

    add_from_key("Tarjeta de red integrada", "mb.lan.controller")
    add_from_key("Ancho de banda de la red integrada", "mb.lan.speed_mbps")
    add_from_key("Chipset de la placa base", "mb.chipset")
    add_from_key("Esquema del chipset", "mb.chipset.diagram_url")
    add_from_key("Comentario 1", "mb.notes")

    return fields


def _map_ram(component: ComponentRecord, specs_by_key: Dict[str, List[SpecField]]) -> List[TemplateField]:
    section = "RAM"
    fields: List[TemplateField] = []

    def add_from_key(field_name: str, key: str):
        spec = _pick_spec(specs_by_key.get(key, []))
        if spec:
            fields.append(_field_from_spec(section, field_name, spec, component.component_id))
        else:
            fields.append(_unknown_field(section, field_name, component.component_id))

    add_from_key("Tipo de RAM", "ram.type")
    add_from_key("Voltaje", "ram.voltage_v")
    add_from_key("Número de pines", "ram.pins")

    clock_real = _pick_spec(specs_by_key.get("ram.clock_real_mhz", []))
    speed_eff = _pick_spec(specs_by_key.get("ram.speed_effective_mt_s", []))
    if clock_real:
        fields.append(_field_from_spec(section, "Velocidad real", clock_real, component.component_id))
    elif speed_eff:
        fields.append(_calculated_field(section, "Velocidad real", round(speed_eff.value / 2, 2), "MHz", component.component_id))
    else:
        fields.append(_unknown_field(section, "Velocidad real", component.component_id))

    if speed_eff:
        fields.append(_field_from_spec(section, "Velocidad efectiva", speed_eff, component.component_id))
    else:
        fields.append(_unknown_field(section, "Velocidad efectiva", component.component_id))

    add_from_key("Latencia", "ram.latency_cl")

    mt_s = speed_eff.value if speed_eff else None
    for channels, field_name in [(1, "Ancho de banda (single channel)"), (2, "Ancho de banda (dual channel)"), (3, "Ancho de banda (triple channel)")]:
        bw_val = bw_ram_gbs(mt_s, channels) if mt_s is not None else None
        if bw_val is not None:
            fields.append(_calculated_field(section, field_name, bw_val, "GB/s", component.component_id))
        else:
            fields.append(_unknown_field(section, field_name, component.component_id))

    latency = _pick_spec(specs_by_key.get("ram.latency_cl", []))
    if speed_eff and latency and latency.value:
        ratio = round(speed_eff.value / latency.value, 2)
        fields.append(_calculated_field(section, "Velocidad efectiva / Latencia", ratio, None, component.component_id))
    else:
        fields.append(_unknown_field(section, "Velocidad efectiva / Latencia", component.component_id))

    add_from_key("Comentario", "ram.notes")

    return fields


def _map_gpu(component: ComponentRecord, specs_by_key: Dict[str, List[SpecField]]) -> List[TemplateField]:
    section = "Gráfica"
    fields: List[TemplateField] = []

    pcie_ver = _pick_spec(specs_by_key.get("gpu.pcie.version", []))
    pcie_lanes = _pick_spec(specs_by_key.get("gpu.pcie.lanes", []))
    if pcie_ver:
        value = pcie_ver.value
        if pcie_lanes:
            value = f"{pcie_ver.value} x{pcie_lanes.value}"
        fields.append(_field_from_spec(section, "Tipo de PCI-E", SpecField(
            key="gpu.pcie",
            label="Tipo de PCI-E",
            value=value,
            unit=None,
            status=pcie_ver.status,
            source_tier=pcie_ver.source_tier,
            source_name=pcie_ver.source_name,
            source_url=pcie_ver.source_url,
            confidence=pcie_ver.confidence,
        ), component.component_id))
    else:
        fields.append(_unknown_field(section, "Tipo de PCI-E", component.component_id))

    bw_ext = bw_pcie_external_gbs(pcie_ver.value if pcie_ver else None, pcie_lanes.value if pcie_lanes else None)
    if bw_ext is not None:
        fields.append(_calculated_field(section, "Ancho de banda externo", bw_ext, "GB/s", component.component_id))
    else:
        fields.append(_unknown_field(section, "Ancho de banda externo", component.component_id))

    bw_internal_spec = _pick_spec(specs_by_key.get("gpu.mem.bandwidth_gbps", []))
    if bw_internal_spec:
        fields.append(_field_from_spec(section, "Ancho de banda interno", bw_internal_spec, component.component_id))
    else:
        mem_speed = _pick_spec(specs_by_key.get("gpu.mem.speed_gbps", []))
        mem_bus = _pick_spec(specs_by_key.get("gpu.mem.bus_width_bits", []))
        bw_int = bw_gpu_internal_gbs(mem_speed.value if mem_speed else None, mem_bus.value if mem_bus else None)
        if bw_int is not None:
            fields.append(_calculated_field(section, "Ancho de banda interno", bw_int, "GB/s", component.component_id))
        else:
            fields.append(_unknown_field(section, "Ancho de banda interno", component.component_id))

    vram = _pick_spec(specs_by_key.get("gpu.vram_gb", []))
    if vram:
        fields.append(_field_from_spec(section, "Cantidad de RAM", vram, component.component_id))
    else:
        fields.append(_unknown_field(section, "Cantidad de RAM", component.component_id))

    return fields


def _map_disk(component: ComponentRecord, specs_by_key: Dict[str, List[SpecField]]) -> List[TemplateField]:
    section = "Disco duro"
    fields: List[TemplateField] = []

    interface = _pick_spec(specs_by_key.get("disk.interface", []))
    pcie_ver = _pick_spec(specs_by_key.get("disk.interface.pcie.version", []))
    pcie_lanes = _pick_spec(specs_by_key.get("disk.interface.pcie.lanes", []))

    bw_val = None
    if interface and "SATA" in str(interface.value).upper():
        bw_val = bw_sata_gbs(interface.value)
    elif pcie_ver and pcie_lanes:
        bw_val = bw_pcie_external_gbs(pcie_ver.value, pcie_lanes.value)

    if bw_val is not None:
        fields.append(_calculated_field(section, "Velocidad con chipset", bw_val, "Gb/s", component.component_id))
    else:
        fields.append(_unknown_field(section, "Velocidad con chipset", component.component_id))

    disk_type = _pick_spec(specs_by_key.get("disk.type", []))
    rpm = _pick_spec(specs_by_key.get("disk.rpm", []))
    if disk_type and str(disk_type.value).upper() == "SSD":
        fields.append(_na_field(section, "RPM", component.component_id))
    elif rpm:
        fields.append(_field_from_spec(section, "RPM", rpm, component.component_id))
    else:
        fields.append(_unknown_field(section, "RPM", component.component_id))

    cache = _pick_spec(specs_by_key.get("disk.cache_mb", []))
    if cache:
        fields.append(_field_from_spec(section, "Búfer", cache, component.component_id))
    else:
        fields.append(_unknown_field(section, "Búfer", component.component_id))

    return fields
