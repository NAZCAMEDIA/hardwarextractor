# ACCEPTANCE_TESTS — Criterios de aceptación (MVP ficha completa)

**Fecha:** 2026-01-28  
**Versión:** 1.0

## A) Principios de aceptación
- Ningún valor se inventa.
- Todo valor no UNKNOWN/NA tiene fuente (URL) y tier.
- REFERENCE activa banner y queda marcado por campo.
- Resolver determinista.

---

## B) Casos Given/When/Then

### Test 1 — CPU oficial (Intel)
**Given** un input de CPU Intel mainstream (modelo claro)  
**When** proceso el input  
**Then**
- se clasifica como CPU con confidence alta
- se resuelve exact match o candidato #1 inequívoco
- se extraen: cores, threads, caches (si oficiales), RAM soportada (si oficial), PCIe si oficial
- los campos extraídos llevan OFFICIAL + URL
- se mapea la sección CPU y queda lista para “Añadir a ficha”

### Test 2 — RAM por Part Number (Kingston o Crucial)
**Given** un PN real de RAM de Kingston/Crucial  
**When** proceso el input  
**Then**
- se clasifica RAM
- se resuelve a página oficial del fabricante
- se extrae tipo, MT/s, voltaje/pines/latencia si publicado
- BW single/dual/triple se calcula y se marca CALCULATED
- se mapea la sección RAM correctamente

### Test 3 — Disco SSD (Samsung/WD/Seagate)
**Given** un modelo comercial o PN de SSD  
**When** proceso el input  
**Then**
- se clasifica DISK
- se extrae interfaz (SATA/NVMe) y, si HDD, RPM y buffer
- “RPM” es NA en SSD
- “Velocidad con chipset” se calcula por tabla según interfaz (CALCULATED)

### Test 4 — GPU chip vendor (NVIDIA/AMD/Intel)
**Given** un input que identifica claramente un chip GPU  
**When** proceso el input  
**Then**
- se clasifica GPU
- se extrae VRAM (si oficial), PCIe (si oficial), y BW interno si oficial
- BW externo solo si lanes/version oficiales; si no → UNKNOWN
- se mapea sección GPU

### Test 5 — MAINBOARD (ASUS/MSI/Gigabyte/ASRock)
**Given** un modelo exacto de placa base  
**When** proceso el input  
**Then**
- se clasifica MAINBOARD
- se extrae socket, chipset, max RAM, USB, SATA, LAN
- “esquema chipset” es URL oficial si existe, si no UNKNOWN
- se mapea sección MAINBOARD

### Test 6 — Ambigüedad / candidatos
**Given** un input ambiguo que produce 2+ candidatos  
**When** proceso el input  
**Then**
- se emite estado NEEDS_USER_SELECTION con lista ordenada por score
- no se habilita “Añadir a ficha” hasta seleccionar candidato
- tras seleccionar, se ejecuta scrape y mapeo

### Test 7 — Uso de referencia (Tier 2)
**Given** un input donde OFFICIAL no publica un campo crítico y REFERENCE sí  
**When** proceso el input  
**Then**
- el campo se rellena con `source_tier=REFERENCE` y `status=EXTRACTED_REFERENCE`
- banner global se activa en ficha agregada
- si luego aparece OFFICIAL para ese campo, se reemplaza automáticamente

### Test 8 — Export CSV por ficha agregada
**Given** una ficha agregada con CPU+MB+RAM+GPU+DISK añadidos  
**When** exporto CSV  
**Then**
- el CSV contiene 1 fila por campo del catálogo
- cada fila tiene: section, field, value, status, tier, url, confidence, component_id
- UNKNOWN/NA no requieren URL
- el CSV es estable entre ejecuciones con mismos inputs (cache)

---

## C) Criterios de “no pasar”
- Cualquier valor sin status/tier/URL (si aplica) → FAIL
- Asumir lanes PCIe sin oficial → FAIL
- REFERENCE sin marcar/advertir → FAIL
- Spiders sin tests/fixtures → FAIL
