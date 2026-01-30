# Cross-Validation Web Search Architecture

## Status: IMPLEMENTED ✓

## Objetivo
Implementar validación cruzada de datos de web search donde:
1. Cada búsqueda consulta 2+ fuentes independientes
2. Solo se validan datos que coinciden entre fuentes
3. Datos validados se agregan al catálogo automáticamente
4. Fichas de specs muestran TODOS los campos posibles (unknown para faltantes)

## Arquitectura Implementada

### 1. CrossValidator Component
```
hardwarextractor/core/cross_validator.py
```

**Clases:**
- `SourceResult`: Resultado de una sola fuente
- `ValidatedSpec`: Spec validado por múltiples fuentes
- `CrossValidationResult`: Resultado completo de validación cruzada
- `CrossValidator`: Orquestador de validación multi-fuente

**Responsabilidades:**
- Consultar múltiples fuentes para el mismo componente
- Comparar specs entre fuentes con reglas de comparación
- Determinar consenso (qué datos coinciden)
- Calcular confianza basada en número de fuentes que coinciden

### 2. Catalog Persistence Layer
```
hardwarextractor/data/catalog_writer.py
```

**Funciones:**
- `add_validated_component()`: Agregar componente validado al catálogo
- `get_validated_component()`: Buscar componente en catálogo
- `list_validated_components()`: Listar todos los componentes
- `get_catalog_stats()`: Estadísticas del catálogo

**Responsabilidades:**
- Escribir nuevos componentes validados al catálogo
- Merge de datos existentes con nuevos datos
- Versionado de datos (fecha de última actualización)
- Backup automático antes de guardar

### 3. Spec Templates
```
hardwarextractor/data/spec_templates.py
```

**Templates completos por tipo:**
- `CPU_SPEC_TEMPLATE`: 51 campos
- `RAM_SPEC_TEMPLATE`: 27 campos
- `GPU_SPEC_TEMPLATE`: 56 campos
- `MAINBOARD_SPEC_TEMPLATE`: 24 campos
- `DISK_SPEC_TEMPLATE`: 15 campos

**Funciones:**
- `get_template_for_type()`: Obtener template por tipo
- `apply_template_to_specs()`: Aplicar template, llenar faltantes con "unknown"
- `get_template_keys()`: Obtener claves del template

### 4. Flujo de Validación Cruzada

```
Input: "CT2K16G56C46U5"
    ↓
[Classify] → RAM
    ↓
[Catalog Search] → No match
    ↓
[CrossValidator.validate_from_sources()]
    ├── Newegg → {latency: CL46, voltage: 1.1V}
    ├── PCPartPicker → {latency: CL46, voltage: 1.1V, capacity: 32GB}
    └── TechPowerUp → timeout
    ↓
[CrossValidator._find_consensus()]
    → Consenso: {latency: CL46, voltage: 1.1V} (2/2 fuentes)
    → Parcial: {capacity: 32GB} (1/2 fuentes, no válido)
    ↓
[CatalogWriter.add_validated_component()]
    → Agregar a validated_catalog.json
    ↓
[apply_template_to_specs()]
    → Añadir campos faltantes con "unknown"
    ↓
[Return result with complete specs]
```

### 5. Reglas de Consenso

| # Fuentes Coincidentes | Acción |
|------------------------|--------|
| 0 | No agregar a catálogo |
| 1 | No agregar (sin validación) |
| 2+ | Agregar al catálogo con confidence = n/total |

### 6. Reglas de Comparación

```python
COMPARISON_RULES = {
    "exact": lambda a, b: str(a).lower().strip() == str(b).lower().strip(),
    "numeric_5pct": lambda a, b: _numeric_compare(a, b, 0.05),
    "numeric_10pct": lambda a, b: _numeric_compare(a, b, 0.10),
}

SPEC_COMPARISON_MAP = {
    "ram.latency_cl": "exact",
    "ram.voltage_v": "numeric_5pct",
    "cpu.cores_physical": "exact",
    "cpu.clock_mhz": "numeric_5pct",
    "gpu.vram_gb": "exact",
    ...
}
```

### 7. Estructura del Catálogo Validado

```json
{
  "CPU": [],
  "RAM": [
    {
      "brand": "Crucial",
      "model": "CT2K16G56C46U5",
      "validated": true,
      "validation_sources": ["newegg", "pcpartpicker"],
      "validation_date": "2026-01-30",
      "confidence": 0.85,
      "specs": {
        "ram.latency_cl": {
          "value": "CL46",
          "sources": ["newegg", "pcpartpicker"],
          "confidence": 1.0
        }
      }
    }
  ],
  "_metadata": {
    "created": "2026-01-30",
    "last_updated": "2026-01-30",
    "total_entries": 1
  }
}
```

## Archivos Creados/Modificados

### Nuevos:
1. `hardwarextractor/core/cross_validator.py` - ✓
2. `hardwarextractor/data/catalog_writer.py` - ✓
3. `hardwarextractor/data/spec_templates.py` - ✓
4. `hardwarextractor/data/validated_catalog.json` - Auto-creado

### Modificados:
1. `hardwarextractor/app/orchestrator.py`:
   - Integrado `CrossValidator` en `_search_web_sources()`
   - Usa múltiples fuentes para validación cruzada
   - Persiste datos validados automáticamente

2. `hardwarextractor/cli_engine.py`:
   - Añadido `get_complete_specs()` para obtener todos los campos
   - `_component_to_dict()` acepta `include_all_specs=True`

## Uso

### Desde CLI Engine:
```python
session = EngineSession()
session.analyze_component("CT2K16G56C46U5")
session.get_complete_specs()  # Retorna specs con TODOS los campos
```

### Desde Orchestrator:
```python
orchestrator = Orchestrator(cache=cache)
events = orchestrator.process_input("CT2K16G56C46U5")
# Si hay web search, automáticamente:
# 1. Consulta múltiples fuentes
# 2. Valida datos coincidentes
# 3. Persiste al catálogo si pasa umbral de confianza
```

### Consultar Catálogo Validado:
```python
from hardwarextractor.data.catalog_writer import (
    get_validated_component,
    list_validated_components,
    get_catalog_stats,
)

# Buscar componente
result = get_validated_component(ComponentType.RAM, "CT2K16G56C46U5")

# Listar todos
all_ram = list_validated_components(ComponentType.RAM)

# Estadísticas
stats = get_catalog_stats()
```
