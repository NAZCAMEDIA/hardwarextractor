# HardwareXtractor - Reestructuración de Scraping y UX

**Fecha:** 2026-01-29
**Versión:** 1.0
**Estado:** Aprobado

---

## 1. Resumen Ejecutivo

Este documento describe la reestructuración del sistema de scraping de HardwareXtractor para:

1. **Resolver el problema de protección anti-bot** (Corsair, G.Skill, etc.)
2. **Mejorar la UX con feedback progresivo** en tiempo real
3. **Implementar CLI interactiva** según CLI_SPEC.md
4. **Agregar sistema de exportación** (CSV/XLSX/MD) con trazabilidad

### Decisiones clave

| Decisión | Elección | Razón |
|----------|----------|-------|
| Estrategia de fallback | Pipeline con cadena de fuentes | Máxima cobertura + graceful degradation |
| Browser automation | Playwright local | Gratuito, sin costos recurrentes |
| Prioridad de fuentes | Oficial → Referencia → Catálogo | Mantiene trazabilidad |
| UX | Logs en tiempo real | Transparencia sin interrumpir flujo |

---

## 2. Arquitectura

### 2.1 Diagrama general

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERFACES                              │
│  ┌─────────────────────┐         ┌─────────────────────────┐   │
│  │   CLI (npx hxtractor)│         │   UI Tkinter           │   │
│  │   - Menú interactivo │         │   - Panel de logs      │   │
│  │   - Export CSV/XLSX/MD         │   - Vista de resultados│   │
│  └──────────┬──────────┘         └───────────┬─────────────┘   │
│             │ IPC JSON-lines                  │ directo        │
│             └──────────────┬──────────────────┘                │
└────────────────────────────┼────────────────────────────────────┘
                             ▼
┌────────────────────────────────────────────────────────────────┐
│                      ENGINE PYTHON                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Orchestrator v2                         │  │
│  │  - Emite eventos detallados (SOURCE_TRYING, etc.)        │  │
│  │  - Coordina clasificación → resolución → scraping        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                   │
│        ┌────────────────────┼────────────────────┐             │
│        ▼                    ▼                    ▼             │
│  ┌───────────┐      ┌─────────────┐      ┌────────────┐       │
│  │Classifier │      │SourceChain  │      │FichaManager│       │
│  │(mejorado) │      │  Manager    │      │  (estado)  │       │
│  └───────────┘      └──────┬──────┘      └────────────┘       │
│                            │                                   │
│         ┌──────────────────┼──────────────────┐               │
│         ▼                  ▼                  ▼               │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐          │
│  │  Requests  │    │ Playwright │    │  Catalog   │          │
│  │  Engine    │    │  Engine    │    │  (embed)   │          │
│  └────────────┘    └────────────┘    └────────────┘          │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Exporters                              │  │
│  │     CSV          XLSX          Markdown                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

### 2.2 Protocolo IPC (CLI ↔ Engine)

**Engine → CLI (stdout JSON-lines):**
```json
{"type":"status","value":"Clasificando"}
{"type":"log","value":"Detectado: RAM (95%) - patrón Corsair DDR5"}
{"type":"log","value":"Fuente 1/4: corsair.com... bloqueado (403)"}
{"type":"log","value":"Fuente 2/4: techpowerup.com... OK"}
{"type":"candidates","value":[{"brand":"Corsair","model":"Dominator","score":0.95}]}
{"type":"result","value":{"type":"RAM","fields":[...]}}
{"type":"error","value":{"message":"Timeout","recoverable":true}}
```

**CLI → Engine (stdin):**
```json
{"cmd":"analyze_component","input":"CMP32GX5M2X7200C34"}
{"cmd":"select_candidate","index":1}
{"cmd":"add_to_ficha"}
{"cmd":"show_ficha"}
{"cmd":"export_ficha","format":"CSV","path":"./export.csv"}
{"cmd":"reset_ficha"}
```

---

## 3. SourceChain - Sistema de Fallback

### 3.1 Modelo de datos

```python
@dataclass
class Source:
    name: str                    # Identificador único
    type: SourceType             # API | SCRAPE | CATALOG
    tier: SourceTier             # OFFICIAL | REFERENCE | EMBEDDED
    provider: str                # "intel_ark", "techpowerup", etc.
    engine: FetchEngine          # REQUESTS | PLAYWRIGHT
    url_template: str | None     # Template de URL para búsqueda
    spider_name: str | None      # Para scraping
    priority: int                # Menor = mayor prioridad

class SourceType(Enum):
    API = "api"
    SCRAPE = "scrape"
    CATALOG = "catalog"

class FetchEngine(Enum):
    REQUESTS = "requests"
    PLAYWRIGHT = "playwright"
```

### 3.2 Cadenas por tipo de componente

```python
SOURCE_CHAINS = {
    ComponentType.CPU: [
        Source("intel_ark", SCRAPE, OFFICIAL, REQUESTS, priority=1),
        Source("amd_specs", SCRAPE, OFFICIAL, REQUESTS, priority=2),
        Source("wikichip", SCRAPE, REFERENCE, REQUESTS, priority=3),
        Source("techpowerup", SCRAPE, REFERENCE, REQUESTS, priority=4),
        Source("embedded", CATALOG, EMBEDDED, REQUESTS, priority=99),
    ],

    ComponentType.RAM: [
        Source("crucial", SCRAPE, OFFICIAL, REQUESTS, priority=1),
        Source("kingston", SCRAPE, OFFICIAL, REQUESTS, priority=2),
        Source("corsair", SCRAPE, OFFICIAL, PLAYWRIGHT, priority=3),
        Source("gskill", SCRAPE, OFFICIAL, PLAYWRIGHT, priority=4),
        Source("techpowerup", SCRAPE, REFERENCE, REQUESTS, priority=5),
        Source("embedded", CATALOG, EMBEDDED, REQUESTS, priority=99),
    ],

    ComponentType.GPU: [
        Source("techpowerup_gpu", SCRAPE, REFERENCE, REQUESTS, priority=1),
        Source("nvidia_official", SCRAPE, OFFICIAL, REQUESTS, priority=2),
        Source("amd_official", SCRAPE, OFFICIAL, REQUESTS, priority=3),
        Source("embedded", CATALOG, EMBEDDED, REQUESTS, priority=99),
    ],

    ComponentType.MAINBOARD: [
        Source("asus", SCRAPE, OFFICIAL, REQUESTS, priority=1),
        Source("msi", SCRAPE, OFFICIAL, REQUESTS, priority=2),
        Source("gigabyte", SCRAPE, OFFICIAL, REQUESTS, priority=3),
        Source("asrock", SCRAPE, OFFICIAL, REQUESTS, priority=4),
        Source("embedded", CATALOG, EMBEDDED, REQUESTS, priority=99),
    ],

    ComponentType.DISK: [
        Source("samsung", SCRAPE, OFFICIAL, REQUESTS, priority=1),
        Source("wdc", SCRAPE, OFFICIAL, REQUESTS, priority=2),
        Source("seagate", SCRAPE, OFFICIAL, REQUESTS, priority=3),
        Source("techpowerup_ssd", SCRAPE, REFERENCE, REQUESTS, priority=4),
        Source("embedded", CATALOG, EMBEDDED, REQUESTS, priority=99),
    ],
}
```

### 3.3 Lógica del SourceChain Manager

```python
class SourceChainManager:
    """Ejecuta la cadena de fuentes con fallback automático."""

    def resolve_and_fetch(
        self,
        component_type: ComponentType,
        query: str,
        candidates: list[ResolveCandidate]
    ) -> Generator[OrchestratorEvent, None, SpecResult]:

        chain = SOURCE_CHAINS[component_type]
        attempted = []

        for i, source in enumerate(chain):
            yield Event(SOURCE_TRYING,
                f"Fuente {i+1}/{len(chain)}: {source.provider}...")

            try:
                matching = [c for c in candidates
                           if self._matches_source(c, source)]

                if not matching and source.type != CATALOG:
                    yield Event(SOURCE_SKIPPED,
                        f"{source.provider}: sin candidatos")
                    continue

                specs = self._fetch_from_source(source, matching, query)

                if specs and len(specs) > 0:
                    yield Event(SOURCE_SUCCESS,
                        f"{source.provider}: {len(specs)} specs")
                    return SpecResult(specs=specs, source=source)
                else:
                    yield Event(SOURCE_EMPTY,
                        f"{source.provider}: sin datos")

            except AntiBot403:
                yield Event(SOURCE_FAILED,
                    f"{source.provider}: bloqueado (403)")
                attempted.append((source, "anti-bot"))

            except TimeoutError:
                yield Event(SOURCE_FAILED,
                    f"{source.provider}: timeout")
                attempted.append((source, "timeout"))

        yield Event(CHAIN_EXHAUSTED,
            f"Agotadas {len(chain)} fuentes sin éxito")
        return SpecResult(specs=[], source=None, errors=attempted)
```

---

## 4. Integración de Playwright

### 4.1 Arquitectura de engines

```python
class BaseFetchEngine(ABC):
    @abstractmethod
    async def fetch(self, url: str, timeout: int = 15000) -> str:
        pass

class RequestsEngine(BaseFetchEngine):
    """Engine rápido para sitios sin protección."""
    async def fetch(self, url: str, timeout: int = 15000) -> str:
        response = requests.get(url, timeout=timeout/1000, headers=HEADERS)
        response.raise_for_status()
        return response.text

class PlaywrightEngine(BaseFetchEngine):
    """Engine con browser headless para sitios con JS/anti-bot."""
    async def fetch(self, url: str, timeout: int = 15000) -> str:
        # Lazy init del browser
        if not self._browser:
            await self._init_browser()

        page = await self._context.new_page()
        try:
            await page.goto(url, timeout=timeout, wait_until="networkidle")
            return await page.content()
        finally:
            await page.close()
```

### 4.2 Detección de anti-bot

```python
class AntiBotDetector:
    PATTERNS = [
        (r"Checking your browser", "cloudflare_challenge"),
        (r"cf-browser-verification", "cloudflare_challenge"),
        (r"captcha", "captcha"),
        (r"rate.?limit", "rate_limit"),
        (r"access.?denied", "access_denied"),
    ]

    @classmethod
    def detect(cls, html: str, status_code: int) -> AntiBotResult:
        if status_code in (403, 429):
            return AntiBotResult(blocked=True, reason=f"http_{status_code}")

        for pattern, reason in cls.PATTERNS:
            if re.search(pattern, html.lower()):
                return AntiBotResult(blocked=True, reason=reason)

        return AntiBotResult(blocked=False)
```

### 4.3 Upgrade automático de engine

```python
class ScrapeService:
    def __init__(self):
        self._requests = RequestsEngine()
        self._playwright = None  # Lazy init
        self._blocked_domains: set[str] = set()

    async def fetch(self, source: Source, url: str) -> FetchResult:
        domain = urlparse(url).netloc

        # Si ya sabemos que bloquea, ir directo a Playwright
        if domain in self._blocked_domains:
            return await self._fetch_with_playwright(url)

        if source.engine == FetchEngine.PLAYWRIGHT:
            return await self._fetch_with_playwright(url)

        # Intentar requests primero
        try:
            html = await self._requests.fetch(url)
            if AntiBotDetector.detect(html, 200).blocked:
                self._blocked_domains.add(domain)
                return await self._fetch_with_playwright(url)
            return FetchResult(html=html, engine_used="requests")
        except requests.HTTPError as e:
            if e.response.status_code in (403, 429):
                self._blocked_domains.add(domain)
                return await self._fetch_with_playwright(url)
            raise
```

### 4.4 Performance

| Engine | Tiempo típico | RAM | Uso |
|--------|--------------|-----|-----|
| requests | ~0.5s | ~5MB | Sitios sin protección |
| playwright | ~3-5s | ~200MB | Sitios con JS/anti-bot |

---

## 5. Sistema de Eventos

### 5.1 Tipos de eventos

```python
class EventType(Enum):
    # Clasificación
    NORMALIZING = "normalizing"
    CLASSIFYING = "classifying"
    CLASSIFIED = "classified"

    # Resolución
    RESOLVING = "resolving"
    CANDIDATES_FOUND = "candidates_found"
    CANDIDATE_SELECTED = "candidate_selected"

    # SourceChain
    SOURCE_TRYING = "source_trying"
    SOURCE_SKIPPED = "source_skipped"
    SOURCE_SUCCESS = "source_success"
    SOURCE_EMPTY = "source_empty"
    SOURCE_FAILED = "source_failed"
    CHAIN_EXHAUSTED = "chain_exhausted"

    # Extracción
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    MAPPING = "mapping"

    # Resultado
    COMPLETE = "complete"
    COMPLETE_PARTIAL = "complete_partial"
    FAILED = "failed"
```

### 5.2 Ejemplo de flujo de eventos

```
→ Analizando código: CMP32GX5M2X7200C34
→ Detectado: RAM (95%) - patrón Corsair DDR5
→ Fuente 1/4: corsair.com... bloqueado (403)
→ Fuente 2/4: techpowerup.com... OK (8 specs)
→ Validando specs...
→ Completado
```

---

## 6. Sistema de Exportación

### 6.1 Formatos soportados

- **CSV**: Tabla plana con trazabilidad
- **XLSX**: Excel con colores por tier y formato
- **MD**: Markdown con tablas y warnings

### 6.2 Columnas de exportación

| Campo | Valor | Status | Tier | Fuente |
|-------|-------|--------|------|--------|
| Tipo | DDR5 | EXTRACTED | REFERENCE | techpowerup.com |
| Velocidad | 7200 MT/s | EXTRACTED | REFERENCE | techpowerup.com |
| BW | 57.6 GB/s | CALCULATED | - | - |

### 6.3 Banners de warning

Si cualquier campo tiene `tier=REFERENCE`:
```
⚠ ADVERTENCIA: Esta ficha contiene datos de fuentes no oficiales (REFERENCE).
```

---

## 7. Estructura de Archivos

### 7.1 Nuevos archivos

```
hardwarextractor/
├── core/
│   ├── events.py              # Tipos de eventos detallados
│   └── source_chain.py        # SourceChain manager
├── scrape/
│   └── engines/
│       ├── __init__.py
│       ├── base.py            # BaseFetchEngine
│       ├── requests_engine.py
│       ├── playwright_engine.py
│       └── detector.py        # AntiBotDetector
├── engine/
│   ├── __init__.py
│   ├── ipc.py                 # Protocolo JSON-lines
│   ├── ficha_manager.py       # Estado de ficha
│   └── commands.py            # Handlers de comandos
├── cli/
│   ├── __init__.py
│   ├── interactive.py         # Menú interactivo
│   └── renderer.py            # Formateo terminal
└── export/
    ├── xlsx_exporter.py       # Nuevo
    └── md_exporter.py         # Nuevo
```

### 7.2 Archivos a modificar

```
hardwarextractor/
├── app/orchestrator.py        # Usar SourceChain + nuevos eventos
├── scrape/service.py          # Usar engines abstraídos
├── export/csv_exporter.py     # Nuevo formato con trazabilidad
├── ui/app.py                  # Consumir nuevos eventos
├── __main__.py                # Dispatch CLI vs UI
└── pyproject.toml             # Dependencias opcionales
```

---

## 8. Plan de Implementación

### Fase 1: Core refactor (3-4 días)
- [ ] 1.1 Crear `core/events.py` con tipos detallados
- [ ] 1.2 Refactorizar Orchestrator para emitir eventos granulares
- [ ] 1.3 Implementar `SourceChainManager`
- [ ] 1.4 Tests unitarios para SourceChain

### Fase 2: Engines de fetch (2-3 días)
- [ ] 2.1 Crear `scrape/engines/` con BaseEngine
- [ ] 2.2 Implementar RequestsEngine (refactor del actual)
- [ ] 2.3 Implementar PlaywrightEngine
- [ ] 2.4 Implementar AntiBotDetector
- [ ] 2.5 Tests con mocks para ambos engines
- [ ] 2.6 Actualizar dependencias (playwright opcional)

### Fase 3: CLI interactiva (2-3 días)
- [ ] 3.1 Crear `engine/ipc.py` (protocolo JSON-lines)
- [ ] 3.2 Crear `engine/ficha_manager.py`
- [ ] 3.3 Crear `engine/commands.py`
- [ ] 3.4 Crear `cli/interactive.py`
- [ ] 3.5 Tests de integración CLI

### Fase 4: Exportadores (1-2 días)
- [ ] 4.1 Refactorizar CSVExporter con nuevo formato
- [ ] 4.2 Implementar XLSXExporter
- [ ] 4.3 Implementar MarkdownExporter
- [ ] 4.4 Tests de exportación

### Fase 5: UI Tkinter update (1 día)
- [ ] 5.1 Adaptar UI para consumir nuevos eventos
- [ ] 5.2 Mejorar panel de logs con colores/iconos
- [ ] 5.3 Agregar opciones de exportación

### Fase 6: Integración y QA (2 días)
- [ ] 6.1 Tests end-to-end
- [ ] 6.2 Smoke tests con componentes reales
- [ ] 6.3 Documentación actualizada
- [ ] 6.4 Release build (DMG + npm package)

**Total estimado: 11-15 días**

---

## 9. Criterios de Éxito

- [ ] Tests: ≥80% coverage mantenido
- [ ] CLI smoke test: `python -m hardwarextractor --cli` funciona
- [ ] Fallback chain: CMP32GX5M2X7200C34 obtiene datos via fallback
- [ ] Exportación: CSV/XLSX/MD con trazabilidad completa
- [ ] Eventos: Logs muestran cada paso del pipeline
- [ ] Performance: <5s para componente con Playwright, <1s sin él

---

## 10. Dependencias

### Nuevas dependencias

```toml
[project.optional-dependencies]
browser = ["playwright>=1.40.0"]
excel = ["openpyxl>=3.1.0"]

# Instalación completa:
# pip install hardwarextractor[browser,excel]
# playwright install chromium
```

---

## Apéndice: Fuentes de Datos

| Tipo | Fuente | Protección | Engine recomendado |
|------|--------|------------|-------------------|
| CPU | Intel ARK | Baja | requests |
| CPU | AMD Product DB | Media | requests |
| CPU | WikiChip | Ninguna | requests |
| RAM | Crucial | Baja | requests |
| RAM | Kingston | Baja | requests |
| RAM | Corsair | Alta | playwright |
| RAM | G.Skill | Alta | playwright |
| GPU | TechPowerUp | Ninguna | requests |
| MB | ASUS/MSI/Gigabyte | Baja-Media | requests |
| Disk | Samsung/WD/Seagate | Baja | requests |

---

*Documento generado durante sesión de brainstorming con Claude Code*
