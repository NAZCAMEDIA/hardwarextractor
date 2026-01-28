# SOURCE_POLICY — Whitelist + reglas (SEALED v1.0)

**Fecha:** 2026-01-28  
**Estado:** SEALED  
**Versión:** 1.0

## 1) Propósito
Definir fuentes permitidas por Tier:
- Tier 1 OFFICIAL: fabricante / bases oficiales / PDFs oficiales.
- Tier 2 REFERENCE: fallback reputado, marcado por campo.

## 2) Reglas obligatorias
1) Allowlist por dominio. Fetch fuera de allowlist: bloqueado.
2) OFFICIAL pisa REFERENCE por campo.
3) REFERENCE solo si OFFICIAL no existe o es incompleto para ese campo.
4) REFERENCE: `status=EXTRACTED_REFERENCE` y `confidence<=0.85` por defecto.
5) Prohibido asumir lanes/bus/bandwidth sin oficial o cálculo a partir de inputs oficiales.
6) PDFs: Tier 1 solo si alojados en dominios OFFICIAL.
7) Rate limit conservador + retries. Captcha/bloqueo: error recuperable.
8) Todo valor no UNKNOWN/NA debe incluir `source_url` y `source_tier`.

---

## 3) Tier 1 (OFFICIAL) — Allowlist de dominios

### CPU / Platform
- `intel.com`
- `amd.com`
- `apple.com`

### GPU chip vendors
- `nvidia.com`
- `amd.com`
- `intel.com`

### Mainboard vendors
- `asus.com`
- `msi.com`
- `gigabyte.com`
- `asrock.com`
- `supermicro.com`
- `biostar.com`

### RAM vendors
- `kingston.com`
- `crucial.com`
- `micron.com`
- `corsair.com`
- `gskill.com`
- `teamgroupinc.com`
- `patriotmemory.com`
- `adata.com`
- `lexar.com`

### Storage vendors
- `samsung.com`
- `semiconductors.samsung.com`
- `wdc.com`
- `western-digital.com`
- `sandisk.com`
- `seagate.com`
- `crucial.com`
- `micron.com`
- `kingston.com`
- `toshiba-storage.com`
- `kioxia.com`

### Networking (si aplica)
- `realtek.com`
- `intel.com`
- `broadcom.com`
- `marvell.com`

---

## 4) Tier 2 (REFERENCE) — Allowlist (STRICT)
- `techpowerup.com`
- `wikichip.org`

---

## 5) Discovery-only (NO FIELD FILL) — deshabilitado por defecto
- `google.com`
- `duckduckgo.com`

---

## 6) Control de cambios
Cambios requieren:
- bump de versión
- rationale
- tests de spiders afectados
