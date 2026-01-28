# TECH_SPEC — Especificación Técnica

**Fecha:** 2026-01-28  
**Versión:** 1.0 (MVP ficha completa)

---

## 1. Arquitectura
UI (Python) ↔ Orchestrator (state machine) ↔ Resolver ↔ Scrapy (spiders) ↔ Pipelines ↔ Normalization/Validation ↔ Mapper ↔ Aggregator ↔ Exporter ↔ SQLite Cache

### 1.1 Principios
- Scrapy es el motor de extracción.
- Spiders por dominio (no universal).
- Modelo de datos normalizado con provenance por campo.
- Cache local SQLite para rendimiento y reproducibilidad.
- Determinismo del resolver y reglas de precedencia OFFICIAL > REFERENCE.

---

## 2. State Machine (orchestrator)
Fases:
1) NORMALIZE_INPUT
2) CLASSIFY_COMPONENT
3) RESOLVE_ENTITY
4) (si ambiguity) NEEDS_USER_SELECTION
5) SCRAPE
6) NORMALIZE_VALIDATE
7) MAP_TO_TEMPLATE
8) READY_TO_ADD
9) ERROR_RECOVERABLE / ERROR_FATAL

Eventos emitidos (contrato UI):
- `status` (string)
- `progress` (0–100)
- `log` (string)
- `candidates` (lista)
- `component_result` (ComponentRecord normalizado)
- `ficha_update` (FichaAggregated incremental)

---

## 3. Contratos de datos (schemas)
### 3.1 ComponentRecord
- `component_id` (uuid)
- `input_raw`, `input_normalized`
- `component_type` (CPU|MAINBOARD|RAM|GPU|DISK|GENERAL)
- `classification_confidence` (0–1)
- `canonical`: brand/model/part_number/ean_upc
- `specs[]`: lista de SpecField

### 3.2 SpecField
- `key` (spec-key interna)
- `label`
- `value`
- `unit` (nullable)
- `status`: EXTRACTED_OFFICIAL | EXTRACTED_REFERENCE | CALCULATED | NA | UNKNOWN
- `source_tier`: OFFICIAL | REFERENCE | NONE
- `source_name`
- `source_url`
- `confidence` (0–1)
- `notes` (nullable)

### 3.3 FichaAggregated
- `ficha_id` (uuid)
- `general.system_name` (nullable)
- `components[]` (ComponentRecord)
- `fields_by_template[]`:
  - `section`, `field`, `value`, `unit`
  - `status`, `source_tier`, `source_name`, `source_url`, `confidence`
  - `component_id`

---

## 4. Resolver (entity resolution)
### 4.1 Salidas
- Exact match: canonical listo.
- Candidates: lista ordenada por score; UI debe elegir.
- No match: error recuperable.

### 4.2 Scoring mínimo
- Coincidencia exacta de PN/EAN en dominio OFFICIAL: 0.95–1.0
- Marca+modelo exacto en OFFICIAL: 0.75–0.95
- Match parcial: <0.75 → requiere selección explícita

### 4.3 Determinismo
- Normalización consistente
- Orden estable de candidatos
- Cache por fingerprint

---

## 5. Scrapy Layer
### 5.1 Principios
- 1 spider por dominio.
- Fixtures HTML/PDF y tests por spider obligatorios.
- Rate limiting por dominio + retries + timeouts.
- Solo dominios allowlisted por SOURCE_POLICY.

### 5.2 Output esperado
Cada spider produce un `RawExtract` con:
- campos extraídos
- URL exacta
- evidencia mínima
Luego pipeline lo convierte a SpecField[] con units y provenance.

---

## 6. Normalización y validación
- Unidades estándar (GB, MB, MHz, MT/s, Gb/s, W, nm).
- Validación de rangos básicos (evitar parse basura).
- Conversión “single source of truth” para números.

---

## 7. Mapper (plantilla ↔ spec-keys)
- Implementa la matriz definida en MAPPING_MATRIX.md.
- Precedencia: OFFICIAL > REFERENCE > CALCULATED > UNKNOWN/NA.
- CALCULATED debe guardar inputs usados y notas.

---

## 8. Aggregator
- CPU/MAINBOARD/GPU: un activo por tipo (reemplazo por defecto).
- RAM/DISK: múltiples; suma capacidades si aplica.
- Recompute de campos dependientes al añadir componentes (p.ej. iGPU y BW RAM).

---

## 9. Exporter
### 9.1 CSV por ficha (obligatorio)
1 fila por campo de plantilla:
- `section,field,value,unit,status,source_tier,source_name,source_url,confidence,component_id`

### 9.2 XLSX (opcional)
- Hojas por sección
- Columna adicional “Fuente”

---

## 10. Cache SQLite
- Tabla por fingerprint de input → resultado
- Tabla por canonical_id → specs
- TTL configurable
- Persistencia de provenance y timestamps
