# EQUIPOS INFORMÁTICOS — Documentación de Especificaciones (Bundle)

Este bundle contiene la documentación **spec-driven** para implementar una app local (macOS) que:
- procesa **inputs individuales** de componentes (CPU/Placa/RAM/GPU/Disco),
- resuelve producto exacto,
- extrae specs (Scrapy) desde fuentes **OFICIALES** con fallback **REFERENCE** (marcado),
- rellena una **ficha agregada** con trazabilidad por campo,
- exporta **CSV por ficha** (y XLSX opcional).

## Archivos incluidos
- `PRD.md` — Product Requirements Document
- `TECH_SPEC.md` — Especificación técnica
- `FIELD_CATALOG.md` — Catálogo canónico de campos (plantilla)
- `MAPPING_MATRIX.md` — Matriz de mapeo plantilla → spec-keys + reglas
- `SOURCE_POLICY.md` — Whitelist de dominios + reglas Tier 1/Tier 2 (SEALED v1.0)
- `SPIDER_SCOPE.md` — Alcance de spiders del MVP (SEALED v1.0)
- `ACCEPTANCE_TESTS.md` — Criterios de aceptación (Given/When/Then)
- `SEAL.md` — Sello del bundle (hash)

## Sello
Ver `SEAL.md`.
