# Sistema de Feedback Beta

**Fecha:** 2025-01-30
**Estado:** Aprobado
**Versión:** 0.1.0 Beta

## Objetivo

Implementar un sistema de feedback para la versión beta que permita:
1. Informar al usuario que está usando una versión beta
2. Recopilar feedback después de cada búsqueda
3. Enviar reportes automáticos a GitHub Issues cuando algo falla

## Decisiones de diseño

| Aspecto | Decisión |
|---------|----------|
| Destino de reportes | GitHub Issues |
| Información incluida | Estándar: log + versión + SO + tipo componente |
| Flujo feedback | Siempre preguntar (beta activa) |
| Banner beta | Inicio + recordatorio cada 5 búsquedas |
| Autenticación GitHub | Token embebido con permisos limitados |

## Componentes

### 1. FeedbackCollector (`hardwarextractor/core/feedback.py`)

Responsabilidades:
- Capturar contexto de cada búsqueda (input, tipo, resultado, errores)
- Mantener contador de búsquedas para recordatorios
- Generar reporte formateado para GitHub

```python
class FeedbackCollector:
    def __init__(self):
        self.search_count = 0
        self.last_search_context = None

    def capture_search(self, input_text, component_type, result, log_entries):
        """Captura contexto de una búsqueda."""

    def should_show_reminder(self) -> bool:
        """True cada 5 búsquedas."""

    def generate_report(self, user_comment: str = "") -> dict:
        """Genera reporte para GitHub Issue."""
```

### 2. GitHubReporter (`hardwarextractor/core/github_reporter.py`)

Responsabilidades:
- Crear issues via GitHub API
- Manejar rate limiting (1 reporte/minuto)
- Gestionar errores de red gracefully

```python
class GitHubReporter:
    REPO = "NAZCAMEDIA/hardwarextractor"
    LABELS = ["beta-feedback", "auto-generated"]

    def create_issue(self, title, body, labels) -> dict:
        """Crea issue en GitHub."""

    def _get_token(self) -> str:
        """Obtiene token ofuscado."""
```

### 3. Integración CLI (`hardwarextractor/cli/interactive.py`)

Cambios:
- Banner beta al inicio
- Pregunta "¿Funcionó correctamente?" después de cada búsqueda
- Pregunta opcional "¿Qué salió mal?"
- Recordatorio cada 5 búsquedas
- Mensaje de agradecimiento tras enviar

### 4. Integración GUI (`hardwarextractor/ui/app.py`)

Cambios:
- Banner visual amarillo/naranja en parte superior
- Diálogo de feedback con campo de texto
- Popup de agradecimiento

## Flujo de usuario

```
Búsqueda completada
       ↓
"¿Funcionó correctamente? (S/n)"
       ↓ (si N)
"¿Qué salió mal? (opcional):"
> [usuario escribe comentario]
       ↓
"Enviando reporte..."
       ↓
"¡Gracias por tu feedback! Tu reporte nos ayuda a mejorar."
"Issue #123 creado: github.com/NAZCAMEDIA/hardwarextractor/issues/123"
```

## Formato del Issue

**Título:** `[Feedback Beta] Búsqueda fallida: {tipo_componente} - {input_truncado}`

**Labels:** `beta-feedback`, `auto-generated`

**Cuerpo:**
```markdown
## Información del sistema
- **Versión:** 0.1.0
- **OS:** macOS 14.2 / Windows 11 / Ubuntu 22.04
- **Python:** 3.11.5

## Búsqueda
- **Input:** CMK32GX5M2B6000C36
- **Tipo detectado:** RAM
- **Resultado:** No se encontraron specs

## Descripción del usuario
> Buscaba RAM Corsair pero no encontró nada

## Log de la búsqueda
```
2024-01-30 15:23:45 | INFO | Normalizando input...
2024-01-30 15:23:46 | ERROR | Timeout en corsair.com
```

---
*Reporte automático de HardwareXtractor Beta*
```

## Mensajes de UI

### Banner inicio (CLI)
```
⚠️  VERSIÓN BETA - Necesitamos tu feedback
Si algo no funciona, te preguntaremos al final de cada búsqueda.
Tus reportes nos ayudan a mejorar. ¡Gracias por probar!
```

### Recordatorio cada 5 búsquedas
```
📊 Llevas 5 búsquedas. ¿Todo bien hasta ahora?
   Recuerda: estamos en beta, tu feedback es valioso.
```

### Agradecimiento
```
¡Gracias por tu feedback! Tu reporte nos ayuda a mejorar.
Issue #123 creado: github.com/NAZCAMEDIA/hardwarextractor/issues/123
```

## Seguridad

### Token GitHub
- Scope: `public_repo` (solo crear issues en repos públicos)
- Ofuscación básica (base64 + dividido)
- Rate limiting: máximo 1 reporte por minuto

### Datos enviados
- Sin información personal identificable
- Solo logs técnicos de la búsqueda
- Comentario voluntario del usuario

## Archivos a crear

| Archivo | Descripción |
|---------|-------------|
| `hardwarextractor/core/feedback.py` | FeedbackCollector |
| `hardwarextractor/core/github_reporter.py` | GitHubReporter |

## Archivos a modificar

| Archivo | Cambios |
|---------|---------|
| `hardwarextractor/cli/interactive.py` | Banner, preguntas feedback, recordatorio |
| `hardwarextractor/cli/renderer.py` | Métodos beta_banner, feedback_prompt, etc. |
| `hardwarextractor/ui/app.py` | Banner visual, diálogo feedback |

## Requisitos previos

1. Crear token GitHub con scope `public_repo`
2. El token debe tener acceso al repo NAZCAMEDIA/hardwarextractor
