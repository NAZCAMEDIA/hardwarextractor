# HardwareXtractor

[![PyPI version](https://badge.fury.io/py/hardwarextractor.svg)](https://pypi.org/project/hardwarextractor/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Completa fichas técnicas de hardware en minutos. Introduce el modelo de cada componente y obtén especificaciones verificadas con trazabilidad completa.

## Características

- **Extracción automatizada** de specs desde fuentes oficiales y de referencia
- **Trazabilidad completa**: cada valor incluye origen, URL y nivel de confianza
- **Sistema de fallback**: si una fuente falla, intenta automáticamente la siguiente
- **Detección anti-bot**: identifica protecciones Cloudflare/CAPTCHA y usa Playwright como fallback
- **Múltiples interfaces**: GUI (Tkinter) y CLI interactivo
- **Exportación flexible**: CSV, XLSX (con colores por tier) y Markdown

## Instalación

### macOS (Homebrew)

En macOS moderno, Python está protegido contra instalaciones globales. Usa `pipx` (recomendado):

```bash
# Instalar pipx si no lo tienes
brew install pipx

# Instalar hardwarextractor
pipx install hardwarextractor

# Actualizar a nueva versión
pipx upgrade hardwarextractor
```

### Linux

#### Opción 1: pipx (recomendado)

```bash
# Instalar pipx
sudo apt install pipx  # Debian/Ubuntu
# o
sudo dnf install pipx  # Fedora

# Instalar hardwarextractor
pipx install hardwarextractor
```

#### Opción 2: pip directo

```bash
pip install hardwarextractor
```

#### Opción 3: Entorno virtual

```bash
python3 -m venv ~/.venvs/hxtractor
source ~/.venvs/hxtractor/bin/activate
pip install hardwarextractor
```

### Windows

#### Opción 1: pip (recomendado)

```powershell
pip install hardwarextractor
```

#### Opción 2: Entorno virtual

```powershell
python -m venv %USERPROFILE%\venvs\hxtractor
%USERPROFILE%\venvs\hxtractor\Scripts\activate
pip install hardwarextractor
```

### Dependencias opcionales

```bash
# Para sitios con protección anti-bot (Playwright)
pipx inject hardwarextractor playwright  # o pip install hardwarextractor[browser]

# Para exportación a Excel
pipx inject hardwarextractor openpyxl    # o pip install hardwarextractor[excel]

# Instalación completa (pip)
pip install hardwarextractor[full]
```

### Desde código fuente

```bash
git clone https://github.com/NAZCAMEDIA/hardwarextractor.git
cd hardwarextractor
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# o .venv\Scripts\activate en Windows
pip install -e ".[full]"
```

### Actualización

```bash
# Con pipx
pipx upgrade hardwarextractor

# Con pip
pip install --upgrade hardwarextractor

# Forzar reinstalación
pipx uninstall hardwarextractor && pipx install hardwarextractor
```

## Uso

### CLI (línea de comandos)

```bash
hxtractor
```

Muestra el menú interactivo:

```
  ██╗  ██╗██╗  ██╗████████╗██████╗  █████╗  ██████╗████████╗ ██████╗ ██████╗
  ██║  ██║╚██╗██╔╝╚══██╔══╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗
  ███████║ ╚███╔╝    ██║   ██████╔╝███████║██║        ██║   ██║   ██║██████╔╝
  ██╔══██║ ██╔██╗    ██║   ██╔══██╗██╔══██║██║        ██║   ██║   ██║██╔══██╗
  ██║  ██║██╔╝ ██╗   ██║   ██║  ██║██║  ██║╚██████╗   ██║   ╚██████╔╝██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝

                           v0.2.0 - Hardware Specs Extractor
                              © 2026 NAZCAMEDIA

  ┌─────────────────────────────────────────────────────────┐
  │  VERSIÓN BETA - Tu feedback es importante              │
  │  Reporta problemas: Menú > Enviar feedback             │
  └─────────────────────────────────────────────────────────┘

  1) Analizar componente
  2) Exportar ficha
  3) Reset ficha
  4) Enviar feedback
  5) Salir
```

### GUI (interfaz gráfica)

```bash
hxtractor-gui
```

### Características del CLI

- **Spinner animado** con tiempo transcurrido durante el análisis
- **Mensajes de estado** descriptivos: "Normalizando...", "Clasificando...", "Extrayendo..."
- **Información completa** de cada componente con fuentes y URLs
- **Fuentes de consulta manual** para verificar datos
- **Leyenda de colores** para identificar el origen de cada dato
- **Auto-agregado** a la ficha técnica

### Flujo básico

1. Introduce un componente (ej. `CMK32GX5M2B6000C36` o `intel i7`)
2. El spinner muestra el progreso con tiempo transcurrido
3. El sistema clasifica el tipo (RAM, CPU, GPU, etc.)
4. Busca en fuentes oficiales primero, luego referencias
5. Muestra especificaciones con indicador de tier y fuente
6. Muestra fuentes de consulta manual para verificar
7. Agrega automáticamente a la ficha
8. Repite con más componentes
9. Exporta a CSV/XLSX/MD

### Búsquedas soportadas

- **Por modelo específico**: `i9-14900K`, `RTX 4090`, `CMK32GX5M2B6000C36`
- **Por familia de procesador**: `intel i7`, `intel i5`, `ryzen 9`, `amd ryzen 7`
- **Por part number**: `CMK32GX5M2B5600C36`
- **Por URL**: URL directa a specs del fabricante

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

## Fuentes de consulta

El CLI y GUI muestran enlaces a fuentes oficiales y de referencia para cada tipo de componente:

| Tipo | Fuentes oficiales | Referencias |
|------|-------------------|-------------|
| CPU | Intel ARK, AMD | TechPowerUp, WikiChip, CPU-World, PassMark |
| GPU | NVIDIA, AMD, Intel Arc | TechPowerUp, GPU-Specs, PassMark |
| RAM | Corsair, Kingston, G.Skill, Crucial | PassMark, UserBenchmark |
| Motherboard | ASUS, MSI, Gigabyte, ASRock | PCPartPicker |
| Storage | Samsung, WD, Seagate | PassMark, UserBenchmark |

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
# Desde CLI: opción 2 > csv > ruta
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
# Clonar repositorio
git clone https://github.com/NAZCAMEDIA/hardwarextractor.git
cd hardwarextractor

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest

# Tests con cobertura
pytest --cov=hardwarextractor --cov-report=term-missing
```

## Descargas (macOS)

Binarios precompilados disponibles en [Releases](https://github.com/NAZCAMEDIA/hardwarextractor/releases):
- `HardwareXtractor.dmg` - Imagen de disco para macOS
- `HardwareXtractor.app` - Aplicación standalone

## Links

- **PyPI**: https://pypi.org/project/hardwarextractor/
- **GitHub**: https://github.com/NAZCAMEDIA/hardwarextractor
- **Issues**: https://github.com/NAZCAMEDIA/hardwarextractor/issues

## Licencia

MIT License - Copyright (c) 2026 [NAZCAMEDIA](https://www.nazcamedia.net)

Ver `LICENSE` para más detalles.

## Changelog

### v0.2.0 (Beta)
- Sistema de feedback integrado para reportar problemas
- Banner de beta al inicio con recordatorio cada 5 búsquedas
- Pregunta post-búsqueda "¿Funcionó correctamente?"
- Envío automático de reportes a GitHub Issues
- Nueva opción de menú "Enviar feedback" (CLI y GUI)
- Mensaje de agradecimiento tras enviar feedback
- 49 nuevos tests con 82% de cobertura

### v0.1.0 (Beta)
- Primera release pública en PyPI
- CLI interactivo con menú y colores ANSI
- GUI con Tkinter
- Panel de fuentes de consulta manual
- Intel ARK Extractor con 29+ specs por CPU
- Búsqueda por familia de procesador (intel i7, ryzen 9, etc.)
- Sistema SourceChain con fallback automático
- Detección de anti-bot (Cloudflare, CAPTCHA)
- Exportación a CSV, XLSX y Markdown
- Soporte para Playwright en sitios protegidos
- macOS App bundle con DMG
- GitHub Actions para publicación automática en PyPI
