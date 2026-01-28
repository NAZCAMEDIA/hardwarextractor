# HardwareXtractor

Herramienta local para rellenar fichas técnicas de equipos informáticos en minutos, no horas. Solo ingresas el modelo de cada componente (CPU, placa base, RAM, GPU y disco) y el sistema completa la ficha con las especificaciones verificadas, indicando la fuente de cada dato.

## ¿Para quién es?
- Técnicos e integradores que necesitan documentar equipos rápido.
- Operaciones de inventario que requieren trazabilidad por campo.

## Qué hace
- Identifica el componente a partir del texto que ingresas.
- Encuentra la ficha oficial cuando existe.
- Extrae y normaliza especificaciones.
- Completa la ficha técnica con trazabilidad por campo.
- Exporta a CSV para integraciones o carga masiva.

## Descarga (macOS)
Carpeta estándar de descargas:
- DMG: `downloads/HardwareXtractor.dmg`
- Ejecutable directo: `downloads/HardwareXtractor`

## Cómo usar
1) Abre la app.
2) Ingresa un componente (ej. “Intel Core i7-12700K”, “ASUS B550-F”, “Samsung 970 EVO Plus”).
3) Repite con los demás componentes.
4) Exporta la ficha a CSV.

## Importante
- No se inventan datos: si no hay fuente confiable, se muestra como UNKNOWN/NA.
- Cada valor incluye su origen (URL y tipo de fuente).
- Las fuentes oficiales tienen prioridad sobre referencias.

## Licencia
MIT. Ver `LICENSE`.
