from __future__ import annotations

LABEL_MAP_CPU = {
    # Base clocks
    "base clock": "cpu.base_clock_mhz",
    "performance-core base frequency": "cpu.base_clock_mhz",
    "efficient-core base frequency": "cpu.e_core_base_clock_mhz",
    "processor base frequency": "cpu.base_clock_mhz",
    # Boost/Turbo clocks
    "max turbo frequency": "cpu.boost_clock_mhz",
    "max. boost clock": "cpu.boost_clock_mhz",
    "max boost clock": "cpu.boost_clock_mhz",
    "performance-core max turbo frequency": "cpu.p_core_boost_clock_mhz",
    "efficient-core max turbo frequency": "cpu.e_core_boost_clock_mhz",
    "intel turbo boost max technology 3.0 frequency": "cpu.turbo_boost_3_mhz",
    "intel thermal velocity boost frequency": "cpu.thermal_velocity_boost_mhz",
    # Cores and threads
    "cores": "cpu.cores_physical",
    "total cores": "cpu.cores_physical",
    "# of cpu cores": "cpu.cores_physical",
    "# of performance-cores": "cpu.p_cores",
    "# of efficient-cores": "cpu.e_cores",
    "threads": "cpu.threads_logical",
    "total threads": "cpu.threads_logical",
    "# of threads": "cpu.threads_logical",
    # Cache
    "l1 cache": "cpu.cache_l1_kb",
    "l2 cache": "cpu.cache_l2_kb",
    "l3 cache": "cpu.cache_l3_kb",
    "cache": "cpu.cache_l3_kb",
    "total l2 cache": "cpu.cache_l2_mb",
    # Memory
    "memory types": "cpu.memory_type_supported",
    "system memory type": "cpu.memory_type_supported",
    "max memory": "cpu.max_memory_gb",
    "max memory size dependent on memory type": "cpu.max_memory_gb",
    "max memory size": "cpu.max_memory_gb",
    "memory channels": "cpu.memory_channels_max",
    "max of memory channels": "cpu.memory_channels_max",
    "max # of memory channels": "cpu.memory_channels_max",
    "max memory speed": "cpu.max_memory_speed_mt_s",
    "max memory speed mt s": "cpu.max_memory_speed_mt_s",
    "max memory bandwidth": "cpu.memory_bandwidth_gbs",
    "memory bandwidth": "cpu.memory_bandwidth_gbs",
    # PCIe
    "pcie version": "cpu.pcie.version_max",
    "pci express revision": "cpu.pcie.version_max",
    "pcie lanes": "cpu.pcie.lanes_max",
    "max of pci express lanes": "cpu.pcie.lanes_max",
    "max # of pci express lanes": "cpu.pcie.lanes_max",
    "native pcie lanes total usable": "cpu.pcie.lanes_max",
    "native pcie lanes": "cpu.pcie.lanes_max",
    "pci express configurations": "cpu.pcie.configurations",
    # Interconnect
    "dmi": "cpu.interconnect.type",
    "dmi version": "cpu.interconnect.type",
    "direct media interface dmi revision": "cpu.dmi.version",
    "max # of dmi lanes": "cpu.dmi.lanes",
    "bus speed": "cpu.interconnect.speed",
    "system bus speed": "cpu.interconnect.speed",
    # Power
    "processor base power": "cpu.tdp_w",
    "maximum turbo power": "cpu.max_turbo_power_w",
    "tdp": "cpu.tdp_w",
    # Other Intel ARK specific
    "processor number": "cpu.model_number",
    "code name": "cpu.codename",
    "lithography": "cpu.process_nm",
    "sockets supported": "cpu.socket",
    "t": "cpu.max_temp_c",
    "max operating temperature": "cpu.max_temp_c",
    "instruction set": "cpu.architecture_bits",
    "instruction set extensions": "cpu.instruction_extensions",
    "launch date": "cpu.launch_date",
    "recommended customer price": "cpu.msrp_usd",
}

LABEL_MAP_RAM = {
    "memory type": "ram.type",
    "voltage": "ram.voltage_v",
    "pins": "ram.pins",
    "speed": "ram.speed_effective_mt_s",
    "max memory speed": "ram.speed_effective_mt_s",
    "speed mhz": "ram.clock_real_mhz",
    "latency": "ram.latency_cl",
    "capacity": "ram.capacity_gb",
    "module size": "ram.capacity_gb",
    "form factor": "ram.form_factor",
}

LABEL_MAP_GPU = {
    # PCI Express
    "bus interface": "gpu.pcie.version",
    "pci express gen": "gpu.pcie.version",
    "pci express gen 4": "gpu.pcie.version",
    "pcie lanes": "gpu.pcie.lanes",
    # Memory
    "memory size": "gpu.vram_gb",
    "standard memory config": "gpu.vram_gb",
    "memory bus": "gpu.mem.bus_width_bits",
    "memory interface width": "gpu.mem.bus_width_bits",
    "memory speed": "gpu.mem.speed_gbps",
    "memory bandwidth": "gpu.mem.bandwidth_gbps",
    "memory type": "gpu.vram_type",
    "vram": "gpu.vram_gb",
    # Clocks
    "base clock ghz": "gpu.base_clock_ghz",
    "boost clock": "gpu.boost_clock_ghz",
    "boost clock ghz": "gpu.boost_clock_ghz",
    # NVIDIA specific labels (from nvidia.com tables)
    "nvidia cuda cores": "gpu.cuda_cores",
    "nvidia cuda cores": "gpu.cuda_cores",
    "cuda cores": "gpu.cuda_cores",
    "shader cores": "gpu.shader_tflops",
    "ray tracing cores": "gpu.rt_tflops",
    "tensor cores ai": "gpu.tensor_tops",
    "tensor cores": "gpu.tensor_cores",
    "rt cores": "gpu.rt_cores",
    # Architecture
    "architecture": "gpu.architecture",
    "nvidia architecture": "gpu.architecture",
    "gpu engine specs": "gpu.engine_specs",
    # Power
    "total graphics power w": "gpu.tdp_w",
    "average gaming power w": "gpu.gaming_power_w",
    "required system power w": "gpu.recommended_psu_w",
    "supplementary power connectors": "gpu.power_connectors",
    "maximum gpu temperature in c": "gpu.max_temp_c",
    # Display
    "standard display connectors": "gpu.display_outputs",
    "multi monitor": "gpu.max_monitors",
    "hdcp": "gpu.hdcp_version",
    # Dimensions
    "length": "gpu.length_mm",
    "width": "gpu.width_mm",
    "slots": "gpu.slots",
    # Features
    "ray tracing": "gpu.ray_tracing",
    "nvidia dlss": "gpu.dlss",
    "directx": "gpu.directx_version",
    "cuda capability": "gpu.cuda_capability",
}

LABEL_MAP_MAINBOARD = {
    "socket": "mb.socket",
    "cpu socket": "mb.socket",
    "chipset": "mb.chipset",
    "max memory": "mb.max_memory_gb",
    "max memory gb": "mb.max_memory_gb",
    "memory": "mb.max_memory_gb",
    "memory speed": "mb.max_memory_speed_mt_s",
    "sata": "mb.storage.sata.version_max",
    "sata 6gb s ports": "mb.storage.sata.version_max",
    "usb": "mb.usb.version_max",
    "usb ports": "mb.usb.version_max",
    "lan": "mb.lan.controller",
    "lan speed": "mb.lan.speed_mbps",
    "ethernet": "mb.lan.controller",
    "ethernet speed": "mb.lan.speed_mbps",
}

LABEL_MAP_DISK = {
    "interface": "disk.interface",
    "rpm": "disk.rpm",
    "cache": "disk.cache_mb",
    "type": "disk.type",
}

LABEL_MAP_REFERENCE = {
    **LABEL_MAP_CPU,
    **LABEL_MAP_GPU,
}

# Extended mappings for community reference sites
LABEL_MAP_TECHPOWERUP_GPU = {
    **LABEL_MAP_GPU,
    "gpu name": "gpu.model",
    "architecture": "gpu.architecture",
    "foundry": "gpu.foundry",
    "process size": "gpu.process_nm",
    "transistors": "gpu.transistors_millions",
    "die size": "gpu.die_size_mm2",
    "shaders": "gpu.shaders",
    "tmus": "gpu.tmus",
    "rops": "gpu.rops",
    "compute units": "gpu.compute_units",
    "sm count": "gpu.sm_count",
    "tensor cores": "gpu.tensor_cores",
    "rt cores": "gpu.rt_cores",
    "l1 cache": "gpu.cache_l1_kb",
    "l2 cache": "gpu.cache_l2_kb",
    "pixel rate": "gpu.pixel_rate_gpixels",
    "texture rate": "gpu.texture_rate_gtexels",
    "fp32": "gpu.fp32_tflops",
    "fp16": "gpu.fp16_tflops",
    "tdp": "gpu.tdp_w",
    "suggested psu": "gpu.recommended_psu_w",
    "power connectors": "gpu.power_connectors",
    "outputs": "gpu.display_outputs",
    "directx": "gpu.directx_version",
    "opengl": "gpu.opengl_version",
    "vulkan": "gpu.vulkan_version",
    "opencl": "gpu.opencl_version",
    "launch date": "gpu.launch_date",
    "launch price": "gpu.launch_price_usd",
}

LABEL_MAP_TECHPOWERUP_CPU = {
    **LABEL_MAP_CPU,
    "processor name": "cpu.model",
    "codename": "cpu.codename",
    "architecture": "cpu.architecture",
    "family": "cpu.family",
    "foundry": "cpu.foundry",
    "process size": "cpu.process_nm",
    "transistors": "cpu.transistors_millions",
    "die size": "cpu.die_size_mm2",
    "package": "cpu.socket",
    "performance cores": "cpu.cores_performance",
    "efficiency cores": "cpu.cores_efficiency",
    "smt": "cpu.hyperthreading",
    "tdp": "cpu.tdp_w",
    "launch date": "cpu.launch_date",
    "launch price": "cpu.launch_price_usd",
}

LABEL_MAP_PASSMARK = {
    # CPU fields
    "cpu mark": "cpu.benchmark_passmark",
    "single thread": "cpu.benchmark_single_thread",
    "cross-platform rating": "cpu.benchmark_cross_platform",
    "samples": "cpu.benchmark_samples",
    "cpu value": "cpu.value_score",
    "price": "cpu.price_usd",
    "socket": "cpu.socket",
    "tdp": "cpu.tdp_w",
    "cores": "cpu.cores_physical",
    "threads": "cpu.threads_logical",
    "turbo clock": "cpu.boost_clock_mhz",
    "base clock": "cpu.base_clock_mhz",
    # GPU fields
    "g3d mark": "gpu.benchmark_passmark",
    "g2d mark": "gpu.benchmark_2d",
    "gpu value": "gpu.value_score",
    "memory size": "gpu.vram_gb",
    "memory type": "gpu.vram_type",
    "memory bus": "gpu.mem.bus_width_bits",
    "tdp": "gpu.tdp_w",
    # RAM fields
    "memory mark": "ram.benchmark_passmark",
    "read cached": "ram.read_cached_mbs",
    "read uncached": "ram.read_uncached_mbs",
    "write": "ram.write_mbs",
    "latency": "ram.latency_ns",
    # Disk fields
    "disk mark": "disk.benchmark_passmark",
    "sequential read": "disk.read_seq_mbps",
    "sequential write": "disk.write_seq_mbps",
    "4k random read": "disk.read_4k_mbps",
    "4k random write": "disk.write_4k_mbps",
}

LABEL_MAP_PCPARTPICKER = {
    # CPU
    "core count": "cpu.cores_physical",
    "thread count": "cpu.threads_logical",
    "performance core clock": "cpu.base_clock_mhz",
    "performance boost clock": "cpu.boost_clock_mhz",
    "l2 cache": "cpu.cache_l2_kb",
    "l3 cache": "cpu.cache_l3_kb",
    "tdp": "cpu.tdp_w",
    "integrated graphics": "cpu.integrated_graphics",
    "smt": "cpu.hyperthreading",
    # GPU
    "chipset": "gpu.chip",
    "memory": "gpu.vram_gb",
    "memory type": "gpu.vram_type",
    "core clock": "gpu.base_clock_mhz",
    "boost clock": "gpu.boost_clock_mhz",
    "effective memory clock": "gpu.mem.speed_effective_mhz",
    "interface": "gpu.pcie.version",
    "length": "gpu.length_mm",
    "tdp": "gpu.tdp_w",
    "external power": "gpu.power_connectors",
    "hdmi outputs": "gpu.outputs_hdmi",
    "displayport outputs": "gpu.outputs_dp",
    # RAM
    "speed": "ram.speed_effective_mt_s",
    "form factor": "ram.form_factor",
    "modules": "ram.modules",
    "price / gb": "ram.price_per_gb",
    "color": "ram.color",
    "first word latency": "ram.latency_first_word_ns",
    "cas latency": "ram.latency_cl",
    "voltage": "ram.voltage_v",
    "timing": "ram.timings",
    "ecc / registered": "ram.ecc",
    "heat spreader": "ram.heatspreader",
    # Storage
    "capacity": "disk.capacity_gb",
    "price / gb": "disk.price_per_gb",
    "type": "disk.type",
    "cache": "disk.cache_mb",
    "form factor": "disk.form_factor",
    "interface": "disk.interface",
    "nvme": "disk.nvme",
    # Motherboard
    "socket / cpu": "mb.socket",
    "form factor": "mb.form_factor",
    "chipset": "mb.chipset",
    "memory max": "mb.max_memory_gb",
    "memory type": "mb.memory_type",
    "memory slots": "mb.memory_slots",
    "memory speed": "mb.max_memory_speed_mt_s",
    "pcie x16 slots": "mb.pcie_x16_slots",
    "pcie x4 slots": "mb.pcie_x4_slots",
    "pcie x1 slots": "mb.pcie_x1_slots",
    "m.2 slots": "mb.m2_slots",
    "sata 6.0 gb/s": "mb.sata_ports",
    "usb 2.0 headers": "mb.usb2_headers",
    "usb 3.2 gen 1 headers": "mb.usb3_headers",
    "usb 3.2 gen 2 headers": "mb.usb32_headers",
    "usb 3.2 gen 2x2 headers": "mb.usb32x2_headers",
    "supports ecc": "mb.ecc_support",
    "wireless networking": "mb.wifi",
}

LABEL_MAP_USERBENCHMARK = {
    # Generic benchmark fields
    "user rating": "benchmark.user_rating",
    "market share": "benchmark.market_share",
    "price": "benchmark.price_usd",
    "value": "benchmark.value_score",
    "average bench": "benchmark.average",
    "samples": "benchmark.samples",
    # CPU specific
    "1-core": "cpu.benchmark_single_core",
    "2-core": "cpu.benchmark_dual_core",
    "4-core": "cpu.benchmark_quad_core",
    "8-core": "cpu.benchmark_octa_core",
    "64-core": "cpu.benchmark_64_core",
    # GPU specific
    "lighting": "gpu.benchmark_lighting",
    "reflection": "gpu.benchmark_reflection",
    "parallax": "gpu.benchmark_parallax",
    "mrender": "gpu.benchmark_mrender",
    "gravity": "gpu.benchmark_gravity",
    "splatting": "gpu.benchmark_splatting",
}

LABEL_MAP_NOTEBOOKCHECK = {
    # GPU
    "architecture": "gpu.architecture",
    "pipelines": "gpu.pipelines",
    "core speed": "gpu.base_clock_mhz",
    "memory speed": "gpu.mem.speed_mhz",
    "memory bus width": "gpu.mem.bus_width_bits",
    "memory type": "gpu.vram_type",
    "max. amount of memory": "gpu.vram_max_gb",
    "shared memory": "gpu.shared_memory",
    "directx": "gpu.directx_version",
    "technology": "gpu.process_nm",
    "features": "gpu.features",
    "date of announcement": "gpu.announcement_date",
    # CPU
    "series": "cpu.series",
    "cores / threads": "cpu.cores_threads",
    "power consumption": "cpu.tdp_w",
    "gpu": "cpu.integrated_graphics",
    "64 bit": "cpu.architecture_64bit",
    "announced": "cpu.announcement_date",
}


# Label maps for retailer sites (Newegg, PCPartPicker)
LABEL_MAP_RETAIL_RAM = {
    # RAM specs for retailer sites
    "memory type": "ram.type",
    "memory speed": "ram.speed_mhz",
    "memory speed (xmp)": "ram.speed_mhz",
    "memory speed (docp)": "ram.speed_mhz",
    "capacity": "ram.capacity_gb",
    "module capacity": "ram.capacity_gb",
    "kit capacity": "ram.capacity_gb",
    "kit type": "ram.type",
    "latency": "ram.latency_cl",
    "cas latency": "ram.latency_cl",
    "voltage": "ram.voltage_v",
    "timing": "ram.timing",
    "heat spreader": "ram.heat_spreader",
    "led lighting": "ram.led",
    "color": "ram.color",
    "form factor": "ram.form_factor",
    "pins": "ram.pins",
}

LABEL_MAP_RETAIL_DISK = {
    # Storage specs for retailer sites
    "capacity": "disk.capacity_gb",
    "storage capacity": "disk.capacity_gb",
    "interface": "disk.interface",
    "storage interface": "disk.interface",
    "drive type": "disk.type",
    "drive width": "disk.form_factor",
    "form factor": "disk.form_factor",
    "sequential read": "disk.read_speed_mb",
    "sequential write": "disk.write_speed_mb",
    "read speed": "disk.read_speed_mb",
    "write speed": "disk.write_speed_mb",
    "cache": "disk.cache_mb",
    "nvmf": "disk.nvmf",
    "tbw": "disk.tbw",
    "dwpd": "disk.dwpd",
    "mtbf": "disk.mtbf",
    "warranty": "disk.warranty_years",
}

LABEL_MAP_RETAIL_MAINBOARD = {
    # Motherboard specs for retailer sites
    "socket": "mb.socket",
    "cpu socket": "mb.socket",
    "form factor": "mb.form_factor",
    "form factor": "mb.form_factor",
    "chipset": "mb.chipset",
    "memory slots": "mb.memory_slots",
    "memory type": "mb.memory_type",
    "memory speed (oc)": "mb.memory_oc_speed",
    "pcie x16 slots": "mb.pcie_x16_slots",
    "pcie x8 slots": "mb.pcie_x8_slots",
    "pcie x4 slots": "mb.pcie_x4_slots",
    "pcie x1 slots": "mb.pcie_x1_slots",
    "m.2 slots": "mb.m2_slots",
    "sata 6gb/s": "mb.sata_ports",
    "onboard ethernet": "mb.ethernet",
    "onboard video": "mb.video_output",
    "usb 3.2 gen 2": "mb.usb_10g",
    "usb 3.2 gen 1": "mb.usb_5g",
    "usb 2.0": "mb.usb_480m",
    "audio codec": "mb.audio_codec",
    " wireless": "mb.wifi",
    "bluetooth": "mb.bluetooth",
}

LABEL_MAP_NEWEGG_RAM = {
    # Newegg-specific RAM labels
    "memory type": "ram.type",
    "memory speed": "ram.speed_mhz",
    "capacity": "ram.capacity_gb",
    "module count": "ram.modules_count",
    "voltage": "ram.voltage_v",
    "latency": "ram.latency_cl",
    "timing": "ram.timing",
    "color": "ram.color",
    "led": "ram.led",
    "features": "ram.features",
}

LABEL_MAP_NEWEGG_DISK = {
    # Newegg-specific storage labels
    "capacity": "disk.capacity_gb",
    "interface": "disk.interface",
    "drive type": "disk.type",
    "form factor": "disk.form_factor",
    "sequential read": "disk.read_speed_mb",
    "sequential write": "disk.write_speed_mb",
    "cache": "disk.cache_mb",
}

LABEL_MAP_NEWEGG_MAINBOARD = {
    # Newegg-specific motherboard labels
    "cpu socket": "mb.socket",
    "chipset": "mb.chipset",
    "form factor": "mb.form_factor",
    "memory slots": "mb.memory_slots",
    "memory type": "mb.memory_type",
    "m.2": "mb.m2_slots",
    "sata": "mb.sata_ports",
}

LABEL_MAP_PCPARTPICKER_RAM = {
    # PCPartPicker-specific RAM labels
    "type": "ram.type",
    "speed": "ram.speed_mhz",
    "modules": "ram.capacity_gb",
    "color": "ram.color",
    "latency": "ram.latency_cl",
    "voltage": "ram.voltage_v",
    "timing": "ram.timing",
    "heat spreader": "ram.heat_spreader",
}

LABEL_MAP_PCPARTPICKER_DISK = {
    # PCPartPicker-specific storage labels
    "capacity": "disk.capacity_gb",
    "type": "disk.type",
    "interface": "disk.interface",
    "form factor": "disk.form_factor",
    "sequential read": "disk.read_speed_mb",
    "sequential write": "disk.write_speed_mb",
}

LABEL_MAP_PCPARTPICKER_MAINBOARD = {
    # PCPartPicker-specific motherboard labels
    "socket": "mb.socket",
    "form factor": "mb.form_factor",
    "memory slots": "mb.memory_slots",
    "memory type": "mb.memory_type",
    "m.2 slots": "mb.m2_slots",
    "sata ports": "mb.sata_ports",
}
