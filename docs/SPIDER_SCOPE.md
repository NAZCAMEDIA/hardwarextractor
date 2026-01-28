# SPIDER_SCOPE — Alcance de spiders del MVP (SEALED v1.0)

**Fecha:** 2026-01-28  
**Estado:** SEALED  
**Versión:** 1.0

## 1) Alcance MVP
Debe cubrir CPU, MAINBOARD, RAM, GPU, DISK + agregación y export CSV con provenance por campo.

---

## 2) Spiders Tier 1 (OFFICIAL) obligatorios

### CPU
1) `intel_ark_spider` — `intel.com`
2) `amd_cpu_specs_spider` — `amd.com`

### MAINBOARD
3) `asus_mainboard_spider` — `asus.com`
4) `msi_mainboard_spider` — `msi.com`
5) `gigabyte_mainboard_spider` — `gigabyte.com`
6) `asrock_mainboard_spider` — `asrock.com`

### RAM
7) `kingston_ram_spider` — `kingston.com`
8) `crucial_ram_spider` — `crucial.com` (+ `micron.com` si enlazado oficial)

### GPU (chip + mínimo 1 AIB)
9) `nvidia_gpu_chip_spider` — `nvidia.com`
10) `amd_gpu_chip_spider` — `amd.com`
11) `intel_arc_gpu_chip_spider` — `intel.com`
12) `asus_gpu_aib_spider` — `asus.com`

### DISK
13) `samsung_storage_spider` — `samsung.com`, `semiconductors.samsung.com`
14) `wdc_storage_spider` — `wdc.com`, `western-digital.com`, `sandisk.com`
15) `seagate_storage_spider` — `seagate.com`

---

## 3) Spiders Tier 2 (REFERENCE) obligatorios (fallback only)
16) `techpowerup_reference_spider` — `techpowerup.com`
17) `wikichip_reference_spider` — `wikichip.org`

Regla: marcar REFERENCE por campo; OFFICIAL siempre prevalece.

---

## 4) Módulos engine obligatorios
- Normalizer
- Classifier
- Resolver (exact match vs candidates)
- Pipelines (raw → spec-keys)
- Validator
- Mapper (matriz)
- Aggregator (ficha multi-input)
- Exporter (CSV por ficha)
- Cache SQLite

---

## 5) Tests (hard gate)
Cada spider debe incluir fixtures + test de parseo. Sin fixtures+tests no se acepta.

---

## 6) Config
Config obligatorio:
- enable/disable Tier 2
- throttling por dominio
- user-agent
- TTL cache
