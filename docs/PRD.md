# PRD — Product Requirements Document

**Producto:** Aplicación local en macOS para auto-rellenar una ficha técnica de equipos informáticos a partir de inputs individuales (uno por uno) de componentes, extrayendo información técnica desde fuentes oficiales y (si es necesario) fuentes de referencia con advertencias.

**Fecha:** 2026-01-28  
**Versión:** 1.0 (MVP ficha completa)

---

## 1. Resumen
La app permite:
1) introducir un identificador arbitrario de un componente (modelo, PN, EAN/UPC, texto),
2) detectar el tipo de componente,
3) resolver el producto exacto (o pedir selección),
4) scrapear specs con Scrapy desde una whitelist de dominios,
5) normalizar/validar datos,
6) mapear a los campos exactos de la ficha,
7) agregar múltiples componentes en una única ficha,
8) exportar un CSV por ficha con trazabilidad por campo.

---

## 2. Objetivos
- Automatizar el rellenado de ficha con reducción drástica de tiempo operativo.
- Mantener **veracidad**: no inventar datos; usar UNKNOWN/NA cuando corresponda.
- Mantener **auditoría**: cada valor con fuente, tier y confianza.
- Mantener **mantenibilidad**: spiders por dominio con fixtures y tests.

---

## 3. Usuarios
- Técnico/operador de inventariado y documentación.
- Integrador que necesita export CSV consistente.

---

## 4. Alcance MVP (ficha completa)
Componentes obligatorios:
- CPU
- Placa base (MAINBOARD)
- RAM
- GPU
- Disco (HDD/SSD/NVMe)
+ Datos generales (nombre del equipo; opcionalmente otros metadatos manuales).

---

## 5. Requisitos funcionales (FR)
**FR-1 Entrada individual:** procesar una entrada cada vez.  
**FR-2 Clasificación:** detectar tipo de componente con confidence.  
**FR-3 Resolución:** exact match o lista de candidatos; sin selección no se añade a ficha.  
**FR-4 Scraping:** usar Scrapy; spiders por dominio.  
**FR-5 Fuentes:** Tier 1 OFFICIAL y Tier 2 REFERENCE (fallback) con advertencias por campo.  
**FR-6 Normalización:** unidades y claves internas estándar.  
**FR-7 Mapeo:** rellenar campos exactos del catálogo de la ficha (FIELD_CATALOG).  
**FR-8 Agregación:** construir ficha agregada multi-input; RAM/Disco admiten múltiples entradas.  
**FR-9 Export:** CSV por ficha agregada, 1 fila por campo + provenance. XLSX opcional.  
**FR-10 UI:** minimalista, con progreso, log, componente actual, ficha agregada, banner REFERENCE, export.

---

## 6. Requisitos de UI (UX mínimo)
- Campo input + botón Procesar
- Barra de progreso por fases + estado + log tiempo real
- Vista componente actual (tipo, canonical, campos + badges OFFICIAL/REFERENCE/CALCULATED/UNKNOWN/NA)
- Botón “Añadir a ficha”
- Vista ficha agregada por secciones
- Banner global si existe cualquier campo Tier 2
- Export CSV / Export XLSX (opcional)

---

## 7. Reglas de calidad (no negociables)
- 0 alucinación: todo campo exportado debe ser EXTRACTED/CALCULATED o quedar UNKNOWN/NA.
- OFFICIAL siempre prevalece sobre REFERENCE por campo.
- CALCULATED siempre marcado como tal y con inputs trazables.
- No asumir lanes PCIe ni buses no publicados oficialmente.
- Resolver determinista: misma entrada → mismo resultado/candidatos ordenados.

---

## 8. Métricas de éxito (MVP)
- ≥80% de entradas comunes resolubles con intervención mínima.
- 100% de valores no UNKNOWN/NA con `source_url` y `source_tier`.
- Export CSV siempre válido, estable y auditable.

---

## 9. Fuera de alcance (MVP)
- Gestión multi-equipo a escala (inventario masivo).
- Integración cloud.
- OCR de etiquetas físicas.
- Compatibilidad Windows/Linux empaquetada (solo macOS en MVP).
