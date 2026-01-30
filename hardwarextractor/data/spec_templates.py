"""Spec templates for complete component specification sheets.

Defines all possible specification fields per component type.
Missing specs will be marked as 'unknown' in output.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from hardwarextractor.models.schemas import ComponentType, SpecField, SpecStatus, SourceTier


@dataclass
class SpecTemplate:
    """Template for a specification field."""
    key: str
    label: str
    unit: Optional[str] = None
    section: str = "General"


# Complete CPU specification template based on Intel ARK + TechPowerUp + PassMark
CPU_SPEC_TEMPLATE: List[SpecTemplate] = [
    # Identification
    SpecTemplate("brand", "Marca", section="Identificación"),
    SpecTemplate("model", "Modelo", section="Identificación"),
    SpecTemplate("cpu.model_number", "Número de Procesador", section="Identificación"),
    SpecTemplate("cpu.codename", "Nombre Código", section="Identificación"),
    SpecTemplate("cpu.family", "Familia", section="Identificación"),
    SpecTemplate("cpu.architecture", "Arquitectura", section="Identificación"),
    SpecTemplate("cpu.launch_date", "Fecha de Lanzamiento", section="Identificación"),
    SpecTemplate("cpu.msrp_usd", "Precio MSRP", "USD", section="Identificación"),

    # Cores & Threads
    SpecTemplate("cpu.cores_physical", "Núcleos Físicos", section="Núcleos"),
    SpecTemplate("cpu.threads_logical", "Hilos Lógicos", section="Núcleos"),
    SpecTemplate("cpu.p_cores", "Núcleos P (Performance)", section="Núcleos"),
    SpecTemplate("cpu.e_cores", "Núcleos E (Eficiencia)", section="Núcleos"),
    SpecTemplate("cpu.hyperthreading", "Hyper-Threading/SMT", section="Núcleos"),

    # Clocks
    SpecTemplate("cpu.base_clock_mhz", "Frecuencia Base", "MHz", section="Frecuencias"),
    SpecTemplate("cpu.boost_clock_mhz", "Frecuencia Boost", "MHz", section="Frecuencias"),
    SpecTemplate("cpu.p_core_base_clock_mhz", "Frecuencia Base P-Core", "MHz", section="Frecuencias"),
    SpecTemplate("cpu.p_core_boost_clock_mhz", "Frecuencia Boost P-Core", "MHz", section="Frecuencias"),
    SpecTemplate("cpu.e_core_base_clock_mhz", "Frecuencia Base E-Core", "MHz", section="Frecuencias"),
    SpecTemplate("cpu.e_core_boost_clock_mhz", "Frecuencia Boost E-Core", "MHz", section="Frecuencias"),
    SpecTemplate("cpu.turbo_boost_3_mhz", "Intel Turbo Boost 3.0", "MHz", section="Frecuencias"),
    SpecTemplate("cpu.thermal_velocity_boost_mhz", "Thermal Velocity Boost", "MHz", section="Frecuencias"),

    # Cache
    SpecTemplate("cpu.cache_l1_kb", "Caché L1", "KB", section="Caché"),
    SpecTemplate("cpu.cache_l2_kb", "Caché L2", "KB", section="Caché"),
    SpecTemplate("cpu.cache_l2_mb", "Caché L2 Total", "MB", section="Caché"),
    SpecTemplate("cpu.cache_l3_kb", "Caché L3", "KB", section="Caché"),

    # Memory
    SpecTemplate("cpu.memory_type_supported", "Tipos de Memoria", section="Memoria"),
    SpecTemplate("cpu.max_memory_gb", "Memoria Máxima", "GB", section="Memoria"),
    SpecTemplate("cpu.memory_channels_max", "Canales de Memoria", section="Memoria"),
    SpecTemplate("cpu.max_memory_speed_mt_s", "Velocidad Máxima Memoria", "MT/s", section="Memoria"),
    SpecTemplate("cpu.memory_bandwidth_gbs", "Ancho de Banda Memoria", "GB/s", section="Memoria"),

    # PCIe
    SpecTemplate("cpu.pcie.version_max", "Versión PCIe", section="PCIe"),
    SpecTemplate("cpu.pcie.lanes_max", "Líneas PCIe", section="PCIe"),
    SpecTemplate("cpu.pcie.configurations", "Configuraciones PCIe", section="PCIe"),

    # Interconnect
    SpecTemplate("cpu.interconnect.type", "Tipo de Interconexión", section="Interconexión"),
    SpecTemplate("cpu.interconnect.speed", "Velocidad de Bus", section="Interconexión"),
    SpecTemplate("cpu.dmi.version", "Versión DMI", section="Interconexión"),
    SpecTemplate("cpu.dmi.lanes", "Líneas DMI", section="Interconexión"),

    # Power & Thermal
    SpecTemplate("cpu.tdp_w", "TDP", "W", section="Energía"),
    SpecTemplate("cpu.max_turbo_power_w", "Potencia Turbo Máxima", "W", section="Energía"),
    SpecTemplate("cpu.max_temp_c", "Temperatura Máxima", "°C", section="Energía"),

    # Manufacturing
    SpecTemplate("cpu.process_nm", "Proceso de Fabricación", "nm", section="Fabricación"),
    SpecTemplate("cpu.foundry", "Fundición", section="Fabricación"),
    SpecTemplate("cpu.transistors_millions", "Transistores", "M", section="Fabricación"),
    SpecTemplate("cpu.die_size_mm2", "Tamaño del Die", "mm²", section="Fabricación"),
    SpecTemplate("cpu.socket", "Socket", section="Fabricación"),

    # Features
    SpecTemplate("cpu.architecture_bits", "Arquitectura (bits)", section="Características"),
    SpecTemplate("cpu.instruction_extensions", "Extensiones de Instrucciones", section="Características"),
    SpecTemplate("cpu.integrated_graphics", "Gráficos Integrados", section="Características"),

    # Benchmarks
    SpecTemplate("cpu.benchmark_passmark", "PassMark Score", section="Benchmarks"),
    SpecTemplate("cpu.benchmark_single_thread", "Single Thread Score", section="Benchmarks"),
    SpecTemplate("cpu.benchmark_cross_platform", "Cross-Platform Score", section="Benchmarks"),
]

# Complete RAM specification template
RAM_SPEC_TEMPLATE: List[SpecTemplate] = [
    # Identification
    SpecTemplate("brand", "Marca", section="Identificación"),
    SpecTemplate("model", "Modelo", section="Identificación"),
    SpecTemplate("part_number", "Número de Parte", section="Identificación"),

    # Type & Form Factor
    SpecTemplate("ram.type", "Tipo de RAM", section="Tipo"),
    SpecTemplate("ram.form_factor", "Factor de Forma", section="Tipo"),
    SpecTemplate("ram.pins", "Número de Pines", section="Tipo"),
    SpecTemplate("ram.modules", "Módulos", section="Tipo"),

    # Capacity
    SpecTemplate("ram.capacity_gb", "Capacidad", "GB", section="Capacidad"),

    # Speed
    SpecTemplate("ram.clock_real_mhz", "Velocidad Real", "MHz", section="Velocidad"),
    SpecTemplate("ram.speed_effective_mt_s", "Velocidad Efectiva", "MT/s", section="Velocidad"),

    # Timings
    SpecTemplate("ram.latency_cl", "Latencia CL", section="Timings"),
    SpecTemplate("ram.timings", "Timings Completos", section="Timings"),
    SpecTemplate("ram.latency_first_word_ns", "First Word Latency", "ns", section="Timings"),
    SpecTemplate("ram.latency_ns", "Latencia Total", "ns", section="Timings"),

    # Voltage
    SpecTemplate("ram.voltage_v", "Voltaje", "V", section="Eléctrico"),

    # Performance
    SpecTemplate("ram.bandwidth_single_gbs", "Ancho Banda (Single)", "GB/s", section="Rendimiento"),
    SpecTemplate("ram.bandwidth_dual_gbs", "Ancho Banda (Dual)", "GB/s", section="Rendimiento"),
    SpecTemplate("ram.read_cached_mbs", "Lectura Cached", "MB/s", section="Rendimiento"),
    SpecTemplate("ram.read_uncached_mbs", "Lectura Uncached", "MB/s", section="Rendimiento"),
    SpecTemplate("ram.write_mbs", "Escritura", "MB/s", section="Rendimiento"),

    # Features
    SpecTemplate("ram.ecc", "ECC", section="Características"),
    SpecTemplate("ram.heatspreader", "Disipador", section="Características"),
    SpecTemplate("ram.color", "Color", section="Características"),
    SpecTemplate("ram.rgb", "RGB", section="Características"),

    # Benchmarks
    SpecTemplate("ram.benchmark_passmark", "PassMark Score", section="Benchmarks"),

    # Price
    SpecTemplate("ram.price_per_gb", "Precio por GB", "USD", section="Precio"),
]

# Complete GPU specification template based on NVIDIA + TechPowerUp + PassMark
GPU_SPEC_TEMPLATE: List[SpecTemplate] = [
    # Identification
    SpecTemplate("brand", "Marca", section="Identificación"),
    SpecTemplate("model", "Modelo", section="Identificación"),
    SpecTemplate("gpu.chip", "Chip GPU", section="Identificación"),
    SpecTemplate("gpu.architecture", "Arquitectura", section="Identificación"),
    SpecTemplate("gpu.launch_date", "Fecha de Lanzamiento", section="Identificación"),
    SpecTemplate("gpu.launch_price_usd", "Precio de Lanzamiento", "USD", section="Identificación"),

    # Shaders & Cores
    SpecTemplate("gpu.cuda_cores", "CUDA Cores", section="Núcleos"),
    SpecTemplate("gpu.shaders", "Shaders", section="Núcleos"),
    SpecTemplate("gpu.compute_units", "Compute Units", section="Núcleos"),
    SpecTemplate("gpu.sm_count", "SM Count", section="Núcleos"),
    SpecTemplate("gpu.tmus", "TMUs", section="Núcleos"),
    SpecTemplate("gpu.rops", "ROPs", section="Núcleos"),
    SpecTemplate("gpu.tensor_cores", "Tensor Cores", section="Núcleos"),
    SpecTemplate("gpu.rt_cores", "RT Cores", section="Núcleos"),

    # Clocks
    SpecTemplate("gpu.base_clock_mhz", "Frecuencia Base", "MHz", section="Frecuencias"),
    SpecTemplate("gpu.boost_clock_mhz", "Frecuencia Boost", "MHz", section="Frecuencias"),
    SpecTemplate("gpu.base_clock_ghz", "Frecuencia Base", "GHz", section="Frecuencias"),
    SpecTemplate("gpu.boost_clock_ghz", "Frecuencia Boost", "GHz", section="Frecuencias"),

    # Memory
    SpecTemplate("gpu.vram_gb", "VRAM", "GB", section="Memoria"),
    SpecTemplate("gpu.vram_type", "Tipo de VRAM", section="Memoria"),
    SpecTemplate("gpu.mem.bus_width_bits", "Bus de Memoria", "bit", section="Memoria"),
    SpecTemplate("gpu.mem.speed_gbps", "Velocidad de Memoria", "Gbps", section="Memoria"),
    SpecTemplate("gpu.mem.bandwidth_gbps", "Ancho de Banda", "GB/s", section="Memoria"),
    SpecTemplate("gpu.mem.speed_effective_mhz", "Velocidad Efectiva", "MHz", section="Memoria"),

    # Cache
    SpecTemplate("gpu.cache_l1_kb", "Caché L1", "KB", section="Caché"),
    SpecTemplate("gpu.cache_l2_kb", "Caché L2", "KB", section="Caché"),

    # Performance
    SpecTemplate("gpu.fp32_tflops", "FP32 Performance", "TFLOPS", section="Rendimiento"),
    SpecTemplate("gpu.fp16_tflops", "FP16 Performance", "TFLOPS", section="Rendimiento"),
    SpecTemplate("gpu.shader_tflops", "Shader Performance", "TFLOPS", section="Rendimiento"),
    SpecTemplate("gpu.rt_tflops", "Ray Tracing Performance", "TFLOPS", section="Rendimiento"),
    SpecTemplate("gpu.tensor_tops", "Tensor Performance", "TOPS", section="Rendimiento"),
    SpecTemplate("gpu.pixel_rate_gpixels", "Pixel Rate", "GPixel/s", section="Rendimiento"),
    SpecTemplate("gpu.texture_rate_gtexels", "Texture Rate", "GTexel/s", section="Rendimiento"),

    # PCIe
    SpecTemplate("gpu.pcie.version", "Versión PCIe", section="PCIe"),
    SpecTemplate("gpu.pcie.lanes", "Líneas PCIe", section="PCIe"),

    # Power
    SpecTemplate("gpu.tdp_w", "TDP", "W", section="Energía"),
    SpecTemplate("gpu.gaming_power_w", "Potencia Gaming", "W", section="Energía"),
    SpecTemplate("gpu.recommended_psu_w", "PSU Recomendada", "W", section="Energía"),
    SpecTemplate("gpu.power_connectors", "Conectores de Energía", section="Energía"),
    SpecTemplate("gpu.max_temp_c", "Temperatura Máxima", "°C", section="Energía"),

    # Display
    SpecTemplate("gpu.display_outputs", "Salidas de Video", section="Display"),
    SpecTemplate("gpu.outputs_hdmi", "Salidas HDMI", section="Display"),
    SpecTemplate("gpu.outputs_dp", "Salidas DisplayPort", section="Display"),
    SpecTemplate("gpu.max_monitors", "Monitores Máximos", section="Display"),
    SpecTemplate("gpu.hdcp_version", "Versión HDCP", section="Display"),

    # Dimensions
    SpecTemplate("gpu.length_mm", "Longitud", "mm", section="Dimensiones"),
    SpecTemplate("gpu.width_mm", "Ancho", "mm", section="Dimensiones"),
    SpecTemplate("gpu.slots", "Slots", section="Dimensiones"),

    # Manufacturing
    SpecTemplate("gpu.process_nm", "Proceso", "nm", section="Fabricación"),
    SpecTemplate("gpu.foundry", "Fundición", section="Fabricación"),
    SpecTemplate("gpu.transistors_millions", "Transistores", "M", section="Fabricación"),
    SpecTemplate("gpu.die_size_mm2", "Tamaño del Die", "mm²", section="Fabricación"),

    # Features
    SpecTemplate("gpu.ray_tracing", "Ray Tracing", section="Características"),
    SpecTemplate("gpu.dlss", "DLSS", section="Características"),
    SpecTemplate("gpu.directx_version", "DirectX", section="Características"),
    SpecTemplate("gpu.opengl_version", "OpenGL", section="Características"),
    SpecTemplate("gpu.vulkan_version", "Vulkan", section="Características"),
    SpecTemplate("gpu.opencl_version", "OpenCL", section="Características"),
    SpecTemplate("gpu.cuda_capability", "CUDA Capability", section="Características"),

    # Benchmarks
    SpecTemplate("gpu.benchmark_passmark", "PassMark G3D Score", section="Benchmarks"),
    SpecTemplate("gpu.benchmark_2d", "PassMark G2D Score", section="Benchmarks"),
]

# Complete Mainboard specification template
MAINBOARD_SPEC_TEMPLATE: List[SpecTemplate] = [
    # Identification
    SpecTemplate("brand", "Marca", section="Identificación"),
    SpecTemplate("model", "Modelo", section="Identificación"),

    # Form Factor & Socket
    SpecTemplate("mb.form_factor", "Factor de Forma", section="Físico"),
    SpecTemplate("mb.socket", "Socket CPU", section="Físico"),
    SpecTemplate("mb.chipset", "Chipset", section="Físico"),

    # Memory
    SpecTemplate("mb.max_memory_gb", "Memoria Máxima", "GB", section="Memoria"),
    SpecTemplate("mb.memory_type", "Tipo de Memoria", section="Memoria"),
    SpecTemplate("mb.memory_slots", "Slots de Memoria", section="Memoria"),
    SpecTemplate("mb.max_memory_speed_mt_s", "Velocidad Máxima", "MT/s", section="Memoria"),
    SpecTemplate("mb.ecc_support", "Soporte ECC", section="Memoria"),

    # Expansion
    SpecTemplate("mb.pcie_x16_slots", "Slots PCIe x16", section="Expansión"),
    SpecTemplate("mb.pcie_x4_slots", "Slots PCIe x4", section="Expansión"),
    SpecTemplate("mb.pcie_x1_slots", "Slots PCIe x1", section="Expansión"),
    SpecTemplate("mb.m2_slots", "Slots M.2", section="Expansión"),

    # Storage
    SpecTemplate("mb.sata_ports", "Puertos SATA", section="Almacenamiento"),
    SpecTemplate("mb.storage.sata.version_max", "Versión SATA", section="Almacenamiento"),

    # USB
    SpecTemplate("mb.usb.version_max", "Versión USB Máxima", section="USB"),
    SpecTemplate("mb.usb2_headers", "Headers USB 2.0", section="USB"),
    SpecTemplate("mb.usb3_headers", "Headers USB 3.2 Gen1", section="USB"),
    SpecTemplate("mb.usb32_headers", "Headers USB 3.2 Gen2", section="USB"),
    SpecTemplate("mb.usb32x2_headers", "Headers USB 3.2 Gen2x2", section="USB"),

    # Network
    SpecTemplate("mb.lan.controller", "Controlador LAN", section="Red"),
    SpecTemplate("mb.lan.speed_mbps", "Velocidad LAN", "Mbps", section="Red"),
    SpecTemplate("mb.wifi", "WiFi", section="Red"),

    # Audio
    SpecTemplate("mb.audio.codec", "Codec de Audio", section="Audio"),
    SpecTemplate("mb.audio.channels", "Canales de Audio", section="Audio"),
]

# Complete Disk specification template
DISK_SPEC_TEMPLATE: List[SpecTemplate] = [
    # Identification
    SpecTemplate("brand", "Marca", section="Identificación"),
    SpecTemplate("model", "Modelo", section="Identificación"),

    # Capacity & Type
    SpecTemplate("disk.capacity_gb", "Capacidad", "GB", section="Capacidad"),
    SpecTemplate("disk.type", "Tipo", section="Tipo"),
    SpecTemplate("disk.form_factor", "Factor de Forma", section="Tipo"),
    SpecTemplate("disk.interface", "Interfaz", section="Tipo"),
    SpecTemplate("disk.nvme", "NVMe", section="Tipo"),

    # Performance
    SpecTemplate("disk.read_seq_mbps", "Lectura Secuencial", "MB/s", section="Rendimiento"),
    SpecTemplate("disk.write_seq_mbps", "Escritura Secuencial", "MB/s", section="Rendimiento"),
    SpecTemplate("disk.read_4k_mbps", "Lectura 4K Random", "MB/s", section="Rendimiento"),
    SpecTemplate("disk.write_4k_mbps", "Escritura 4K Random", "MB/s", section="Rendimiento"),

    # HDD Specific
    SpecTemplate("disk.rpm", "RPM", section="HDD"),
    SpecTemplate("disk.cache_mb", "Caché", "MB", section="HDD"),

    # Benchmarks
    SpecTemplate("disk.benchmark_passmark", "PassMark Score", section="Benchmarks"),

    # Price
    SpecTemplate("disk.price_per_gb", "Precio por GB", "USD", section="Precio"),
]


# Map ComponentType to template
SPEC_TEMPLATES: Dict[ComponentType, List[SpecTemplate]] = {
    ComponentType.CPU: CPU_SPEC_TEMPLATE,
    ComponentType.RAM: RAM_SPEC_TEMPLATE,
    ComponentType.GPU: GPU_SPEC_TEMPLATE,
    ComponentType.MAINBOARD: MAINBOARD_SPEC_TEMPLATE,
    ComponentType.DISK: DISK_SPEC_TEMPLATE,
}


def get_template_for_type(component_type: ComponentType) -> List[SpecTemplate]:
    """Get the spec template for a component type."""
    return SPEC_TEMPLATES.get(component_type, [])


def apply_template_to_specs(
    component_type: ComponentType,
    specs: List[SpecField],
    canonical: Dict[str, Any],
) -> List[SpecField]:
    """Apply template to specs, filling missing fields with 'unknown'.

    Args:
        component_type: Type of component
        specs: Extracted specs
        canonical: Canonical data (brand, model, etc.)

    Returns:
        Complete list of specs with all template fields
    """
    template = get_template_for_type(component_type)
    if not template:
        return specs

    # Build lookup of existing specs
    spec_lookup: Dict[str, SpecField] = {s.key: s for s in specs}

    # Add canonical data to lookup
    for key, value in canonical.items():
        if key not in spec_lookup and value:
            spec_lookup[key] = SpecField(
                key=key,
                label=key.replace("_", " ").title(),
                value=value,
                status=SpecStatus.EXTRACTED_REFERENCE,
                source_tier=SourceTier.CATALOG,
            )

    result: List[SpecField] = []

    for tmpl in template:
        if tmpl.key in spec_lookup:
            # Use existing spec
            result.append(spec_lookup[tmpl.key])
        else:
            # Create unknown placeholder
            result.append(SpecField(
                key=tmpl.key,
                label=tmpl.label,
                value="unknown",
                unit=tmpl.unit,
                status=SpecStatus.UNKNOWN,
                source_tier=SourceTier.NONE,
                confidence=0.0,
            ))

    return result


def get_template_keys(component_type: ComponentType) -> List[str]:
    """Get all template keys for a component type."""
    template = get_template_for_type(component_type)
    return [t.key for t in template]
