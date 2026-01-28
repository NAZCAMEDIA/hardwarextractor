# MAPPING_MATRIX — Plantilla → Spec-Keys + reglas

**Fecha:** 2026-01-28  
**Versión:** 1.0

## 0) Convenciones
- Precedencia por campo: OFFICIAL > REFERENCE > CALCULATED > UNKNOWN/NA.
- Cualquier cálculo se marca `CALCULATED` y registra inputs usados.
- Prohibido suponer lanes PCIe si no es oficial.
- UNKNOWN = podría aplicar pero no hay dato fiable.
- NA = no aplica (ej. RPM en SSD).

### 0.1 Fórmulas (MVP)
**BW RAM (GB/s) teórico:** `MTs * 8 * channels / 1000`  
**GPU BW interno (GB/s):** preferir oficial; si no: `speed_gbps * bus_width_bits / 8`  
**PCIe BW externo:** tabla interna por versión y lanes (reportar por dirección).

---

## A) Spec-keys internas (resumen)
### Metadatos / provenance
- `meta.*` (input_raw, input_normalized, component_type, canonical.*)
- `provenance.*` (source_tier, source_name, source_url, confidence, status)

### CPU
- `cpu.base_clock_mhz`, `cpu.boost_clock_mhz`
- `cpu.cores_physical`, `cpu.threads_logical`
- `cpu.cache_l1_kb`, `cpu.cache_l2_kb`, `cpu.cache_l3_kb`
- `cpu.memory_type_supported`, `cpu.max_memory_gb`, `cpu.max_memory_speed_mt_s`, `cpu.memory_channels_max`
- `cpu.interconnect.type`, `cpu.interconnect.speed`, `cpu.interconnect.bandwidth`
- `cpu.pcie.version_max`, `cpu.pcie.lanes_max`

### MAINBOARD
- `mb.socket`, `mb.chipset`, `mb.cpu_support.families`
- `mb.max_memory_gb`, `mb.memory_type_supported`, `mb.max_memory_speed_mt_s`
- `mb.storage.sata.version_max`, `mb.usb.version_max`
- `mb.lan.controller`, `mb.lan.speed_mbps`
- `mb.chipset.diagram_url`, `mb.notes`

### RAM
- `ram.type`, `ram.form_factor`, `ram.pins`, `ram.voltage_v`
- `ram.clock_real_mhz`, `ram.speed_effective_mt_s`, `ram.latency_cl`
- `ram.capacity_gb`, `ram.kit.modules_count`, `ram.notes`

### GPU
- `gpu.pcie.version`, `gpu.pcie.lanes`
- `gpu.vram_gb`
- `gpu.mem.bus_width_bits`, `gpu.mem.speed_gbps`, `gpu.mem.bandwidth_gbps`
- `gpu.notes`

### DISK
- `disk.type`, `disk.interface`
- `disk.interface.pcie.version`, `disk.interface.pcie.lanes`
- `disk.rpm`, `disk.cache_mb`, `disk.notes`

---

## 1) Datos generales
- **Nombre del equipo montado** ← `general.system_name` (manual usuario)  
  - si vacío → UNKNOWN

---

## 2) Procesador (CPU)
- Velocidad interna ← `cpu.base_clock_mhz` (fallback boost) → EXTRACTED  
- Núcleos físicos ← `cpu.cores_physical` → EXTRACTED  
- Núcleos lógicos ← `cpu.threads_logical` → EXTRACTED  
- Caché L1/L2/L3 ← `cpu.cache_l*_kb` → EXTRACTED (o REFERENCE si falta)  
- RAM soportada ← composición de `cpu.memory_type_supported`, `cpu.max_memory_gb`, `cpu.max_memory_speed_mt_s`, `cpu.memory_channels_max`  
- Ancho de banda RAM ← CALCULATED con `cpu.max_memory_speed_mt_s` + `cpu.memory_channels_max`  
- Tipo/velocidad/BW bus sistema ← `cpu.interconnect.*` (si no oficial → UNKNOWN)  
- BW gráficas añadidas ← CALCULATED con `cpu.pcie.version_max` + `cpu.pcie.lanes_max`  
- BW total procesador ← CALCULATED = BW_RAM + BW_PCIe (+BW_interconnect si oficial), con nota de ambigüedad

---

## 3) Placa base (MAINBOARD)
- Tipo bus sistema ← EXTRACTED texto (chipset/link) o UNKNOWN  
- BW máx bus sistema ← EXTRACTED si existe; si no, CALCULATED solo si parámetros oficiales  
- RAM máx ← `mb.max_memory_gb` → EXTRACTED  
- BW RAM ← CALCULATED usando `mb.max_memory_speed_mt_s` + canales (si CPU presente); si no → UNKNOWN  
- CPU máx soporta ← `mb.cpu_support.families` → EXTRACTED (no “máximo absoluto”)  
- Zócalo ← `mb.socket` → EXTRACTED  
- iGPU integrada ← derivado de CPU presente; si no CPU → UNKNOWN  
- BW iGPU ← si iGPU usa RAM: BW_RAM (CALCULATED)  
- SATA tipo/BW ← `mb.storage.sata.version_max` (EXTRACTED) + tabla (CALCULATED)  
- USB tipo/BW ← `mb.usb.version_max` (EXTRACTED) + tabla (CALCULATED)  
- LAN integrada/BW ← `mb.lan.controller` + `mb.lan.speed_mbps` → EXTRACTED  
- Chipset ← `mb.chipset` → EXTRACTED  
- Esquema chipset ← `mb.chipset.diagram_url` → EXTRACTED (URL) o UNKNOWN  
- Comentario 1 ← `mb.notes` (manual/auto)

---

## 4) RAM
- Tipo/Voltaje/Pines ← `ram.type`, `ram.voltage_v`, `ram.pins` → EXTRACTED/REFERENCE si falta  
- Velocidad efectiva ← `ram.speed_effective_mt_s` → EXTRACTED  
- Velocidad real ← `ram.clock_real_mhz` o CALCULATED = MT/s / 2  
- Latencia ← `ram.latency_cl` → EXTRACTED/REFERENCE  
- BW single/dual/triple ← CALCULATED con MT/s  
- Velocidad efectiva / Latencia ← CALCULATED  
- Comentario ← `ram.notes`

---

## 5) GPU
- Tipo PCI-E ← `gpu.pcie.version` (+lanes si oficial) → EXTRACTED  
- BW externo ← CALCULATED con versión+lanes (si lanes no oficial → UNKNOWN)  
- BW interno ← `gpu.mem.bandwidth_gbps` (EXTRACTED) o CALCULATED con bus_width+speed  
- VRAM ← `gpu.vram_gb` → EXTRACTED

---

## 6) Disco
- Velocidad con chipset ← EXTRACTED interfaz + CALCULATED por tabla SATA/PCIe  
- RPM ← `disk.rpm` → EXTRACTED; si SSD → NA  
- Búfer ← `disk.cache_mb` → EXTRACTED/REFERENCE
