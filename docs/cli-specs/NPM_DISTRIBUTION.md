# NPM_DISTRIBUTION — Distribución npm/npx de HXTRACTOR

**Fecha:** 2026-01-28  
**Versión:** 1.0 (MVP)

## 1) Objetivo
Publicar `hxtractor` en npm de forma que el usuario pueda ejecutar:
- `npx hxtractor`

y obtener un CLI interactivo funcional.

---

## 2) Arquitectura de distribución
El CLI es Node/TypeScript (interfaz de consola) y el engine es Python (Scrapy).

Hay dos estrategias válidas:

### Estrategia A (recomendada para fricción mínima)
**npm incluye o descarga un binario del engine** (PyInstaller) para macOS.
- El paquete npm trae un wrapper `hxtractor` y un binario `hxtractor-engine`.
- Al ejecutar `npx hxtractor`, el wrapper:
  1) detecta arquitectura (`arm64` / `x64`)
  2) localiza el binario correspondiente
  3) lanza el engine y comunica por IPC (stdin/stdout JSON)

**Ventajas**
- No requiere Python instalado.
- Experiencia “plug-and-play”.

**Costes**
- Tamaño del paquete o descarga on-demand.
- Gestión de binarios por arquitectura.

### Estrategia B (alternativa de mantenimiento mínimo)
**npm requiere Python 3** en el sistema.
- `npx hxtractor` verifica `python3`.
- Ejecuta `python -m hxtractor_engine` (y guía instalación de deps si faltan).

**Ventajas**
- Paquete pequeño.
- Sin binarios por arquitectura.

**Costes**
- Fricción (Python + deps).

---

## 3) Requisito del MVP de distribución
El MVP puede arrancar con Estrategia B para velocidad de entrega, pero el diseño debe permitir migrar a A sin romper el contrato IPC.

---

## 4) Contrato de ejecución
El wrapper Node debe soportar modo “servicio”:
- inicia el engine una vez por sesión
- reusa proceso para múltiples comandos
- el engine mantiene el estado de ficha y persiste cache SQLite

---

## 5) Estructura del paquete npm (propuesta)
- `package.json`
  - `name`: `hxtractor`
  - `bin`: `{"hxtractor":"dist/cli.js"}`
- `dist/cli.js` (CLI compilado)
- `dist/engine/`
  - (A) binarios por arquitectura
  - (B) scripts de bootstrap/verificación python
- `LICENSE`, `README`

---

## 6) Publicación y versionado
SemVer:
- patch: fixes parsers/spiders sin cambios de contrato
- minor: nuevos dominios oficiales/formatos/flags compatibles
- major: cambios incompatibles IPC/modelo de datos

---

## 7) Checklist de release (hard gate)
1) Tests Python green + cobertura ≥80%
2) Tests CLI green
3) Smoke test:
   - `npx hxtractor` inicia
   - analiza un input
   - muestra include status/tier por campo
   - guarda a ficha
   - exporta CSV y MD
4) Allowlist enforced (SOURCE_POLICY)
5) Docs actualizadas: CLI_SPEC.md + ACCEPTANCE_TESTS.md
