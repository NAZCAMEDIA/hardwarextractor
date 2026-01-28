# CLI_SPEC — HXTRACTOR CLI (Interfaz de consola)

**Fecha:** 2026-01-28  
**Versión:** 1.0 (MVP)

## 1) Objetivo
`hxtractor` es un CLI interactivo que permite:
- analizar **un componente por vez** (input arbitrario),
- mostrar specs con trazabilidad por campo (OFFICIAL/REFERENCE/CALCULATED/UNKNOWN/NA),
- decidir si **guardar** el componente en una **ficha agregada**,
- exportar la ficha a **CSV / XLSX / MD**,
- repetir búsquedas.

El CLI se distribuye vía **npm/npx** como `hxtractor`.

---

## 2) Flujos de usuario

### 2.1 Menú principal
Al iniciar:
- `1) Analizar componente`
- `2) Ver ficha agregada`
- `3) Exportar ficha`
- `4) Reset ficha`
- `5) Salir`

### 2.2 Flujo “Analizar componente”
1) Prompt: `Introduce modelo/PN/EAN/Texto:`
2) Mostrar progreso por etapas:
   - Normalizando
   - Clasificando
   - Resolviendo
   - Scrapeando
   - Normalizando/Validando
   - Mapeando
3) Si hay ambigüedad:
   - Mostrar lista de candidatos (ordenados por score) con:
     - `brand`, `model`, `part_number` (si existe), `source_domain`, `score`
   - Prompt: `Selecciona candidato (1..N) o 0 para cancelar:`
4) Mostrar resultado del componente:
   - Encabezado: `TIPO: <TYPE> | Canonical: <brand> <model> (<PN>)`
   - Tabla de campos extraídos del componente (no la ficha completa), con columnas:
     - Campo | Valor | Status | Tier | Fuente
   - Regla: si `status` es UNKNOWN/NA, Fuente puede quedar vacía.
   - Regla: si `tier` es REFERENCE en cualquier campo, mostrar aviso local:
     - `WARNING: Este componente incluye datos no oficiales (REFERENCE).`
5) Prompt: `¿Añadir este componente a la ficha agregada? (Y/n)`
6) Prompt: `¿Exportar ahora? (No / CSV / XLSX / MD)`
7) Prompt: `¿Hacer otra búsqueda? (Y/n)` → si Y vuelve a 2.2; si n vuelve al menú.

### 2.3 “Ver ficha agregada”
- Renderiza la ficha completa por secciones del FIELD_CATALOG.
- Para cada campo:
  - mostrar Valor + Status/Tier
  - si aplica, mostrar Fuente (URL)
- Si existe cualquier campo con `source_tier=REFERENCE`:
  - banner global: `WARNING: La ficha contiene datos no oficiales (REFERENCE).`

### 2.4 “Exportar ficha”
- Prompt: formato `CSV/XLSX/MD`
- Prompt: ruta de salida (default: `./hxtractor_export_<timestamp>.<ext>`)
- Confirmación:
  - `Exportado: <path>`

### 2.5 “Reset ficha”
- Confirmación: `Esto borrará la ficha actual. ¿Continuar? (y/N)`
- Si y: limpia ficha y confirma.

---

## 3) Reglas de presentación (CLI)
- Siempre mostrar `status` y `tier` por campo:
  - `EXTRACTED_OFFICIAL` → OFFICIAL
  - `EXTRACTED_REFERENCE` → REFERENCE
  - `CALCULATED` → CALCULATED
  - `UNKNOWN` / `NA` → UNKNOWN / NA
- No imprimir URLs kilométricas por defecto:
  - truncar visualmente pero conservar completa para export.
- Logs deben ser “humanos” y no ruidosos:
  - 1 línea por etapa y, opcionalmente, dominio consultado.

---

## 4) Contrato CLI ↔ Engine (IPC)
IPC recomendado: mensajes JSON line-delimited por stdout del engine hacia CLI:

- `{"type":"status","value":"Resolviendo"}`
- `{"type":"progress","value":45}`
- `{"type":"log","value":"Consultando intel.com"}`
- `{"type":"candidates","value":[...]}`
- `{"type":"result","value":{ComponentRecord}}`
- `{"type":"ficha_update","value":{FichaAggregated}}`
- `{"type":"error","value":{"message":"...","recoverable":true}}`

Comandos mínimos (CLI → engine):
- `analyze_component`
- `select_candidate`
- `add_to_ficha`
- `show_ficha`
- `export_ficha`
- `reset_ficha`

---

## 5) Export MD (requisito)
El export Markdown debe incluir:
- Encabezado: fecha, resumen de componentes añadidos
- Secciones del FIELD_CATALOG en orden
- Por sección: tabla
  - Campo | Valor | Status | Tier | Fuente
- Banner en el MD si hay REFERENCE en cualquier campo.
