# HardwareXtractor

Completa fichas técnicas de hardware en minutos. Introduce el modelo de cada componente y obtén especificaciones verificadas con trazabilidad completa.

## Características

- **Extracción automatizada** de specs desde fuentes oficiales y de referencia
- **Trazabilidad completa**: cada valor incluye origen, URL y nivel de confianza
- **Sistema de fallback**: si una fuente falla, intenta automáticamente la siguiente
- **Detección anti-bot**: identifica protecciones Cloudflare/CAPTCHA y usa Playwright como fallback
- **Múltiples interfaces**: GUI (Tkinter) y CLI interactivo
- **Exportación flexible**: CSV, XLSX (con colores por tier) y Markdown

## Instalación

### Desde PyPI (recomendado)

```bash
pip install hardwarextractor
```

### Dependencias opcionales

```bash
# Para sitios con protección anti-bot (Playwright)
pip install hardwarextractor[browser]

# Para exportación a Excel
pip install hardwarextractor[excel]

# Instalación completa
pip install hardwarextractor[full]
```

### Desde código fuente

```bash
git clone https://github.com/NAZCAMEDIA/hardwarextractor.git
cd hardwarextractor
pip install -e ".[full]"
```

## Uso

### GUI (interfaz gráfica)

```bash
hxtractor
```

### CLI (línea de comandos)

```bash
hxtractor --cli
# o
hxtractor-cli
```

### Flujo básico

1. Introduce un componente (ej. `Corsair CMK32GX4M2B3200C16`)
2. El sistema clasifica el tipo (RAM, CPU, GPU, etc.)
3. Busca en fuentes oficiales primero, luego referencias
4. Muestra candidatos si hay ambigüedad
5. Agrega a la ficha con todos los specs extraídos
6. Repite con más componentes
7. Exporta a CSV/XLSX/MD

## Sistema de Tiers

| Tier | Descripción | Indicador |
|------|-------------|-----------|
| OFFICIAL | Datos del fabricante | ● verde |
| REFERENCE | Bases de datos técnicas (TechPowerUp, WikiChip) | ◐ naranja |
| CALCULATED | Valores derivados de otros campos | ◇ azul |
| UNKNOWN | Sin fuente verificable | gris |

## Componentes soportados

- **CPU**: Intel, AMD
- **RAM**: Corsair, Kingston, G.Skill, Crucial, Samsung
- **GPU**: NVIDIA, AMD, Intel
- **Motherboard**: ASUS, MSI, Gigabyte, ASRock
- **Storage**: Samsung, WD, Seagate, Crucial, Kingston

## Arquitectura

```
hardwarextractor/
├── app/           # Orchestrator principal
├── core/          # Eventos y SourceChain
├── cli/           # Interfaz de línea de comandos
├── ui/            # Interfaz gráfica Tkinter
├── scrape/        # Spiders y engines (Requests/Playwright)
├── engine/        # FichaManager, IPC, Commands
├── export/        # Exportadores (CSV, XLSX, MD)
└── models/        # Schemas y tipos
```

## Exportación

### CSV
```bash
# Desde CLI: opción 3 > csv > ruta
```

### Excel (XLSX)
Incluye:
- Colores por tier (verde=oficial, naranja=referencia)
- Banner de advertencia si hay datos REFERENCE
- Columnas: Sección, Campo, Valor, Unidad, Status, Tier, Fuente, URL

### Markdown
Tabla formateada con secciones y leyenda de tiers.

## Configuración

Archivo `~/.config/hardwarextractor/config.yaml`:

```yaml
enable_tier2: true          # Permitir fuentes REFERENCE
user_agent: "HardwareXtractor/0.2"
retries: 2
throttle_seconds_by_domain:
  crucial.com: 1.0
  corsair.com: 2.0
```

## Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Tests con cobertura
pytest --cov=hardwarextractor --cov-report=term-missing
```

## Descargas (macOS)

Binarios precompilados disponibles en:
- `downloads/HardwareXtractor.dmg`
- `downloads/HardwareXtractor.app`

## Licencia

Propietario. Ver `LICENSE`.

## Changelog

### v0.2.0
- CLI interactivo con menú y colores ANSI
- Sistema SourceChain con fallback automático
- Detección de anti-bot (Cloudflare, CAPTCHA)
- Exportación a XLSX y Markdown
- Eventos detallados para logging en tiempo real
- Soporte para Playwright en sitios protegidos

### v0.1.0
- Release inicial con GUI Tkinter
- Exportación CSV
- Soporte básico para CPU, RAM, GPU, Motherboard, Storage
