# HardwareXtractor - Auditoría Completa y Plan de Desarrollo v1.0

**Fecha:** 2026-01-29
**Versión actual:** 0.2.0
**Estado:** MVP con funcionalidad limitada

---

## PARTE I: AUDITORÍA TÉCNICA COMPLETA

### 1. Resumen Ejecutivo

| Métrica | Estado Actual | Objetivo |
|---------|---------------|----------|
| Tests | 199/199 (100%) | Mantener |
| Cobertura | 80.13% | >85% |
| Funcionalidad Real | ~20% | 100% |
| Modelos en Catálogo | 15 | 500+ |
| Spiders Funcionales | 3/15 | 15/15 |
| Anti-bot Resuelto | No | Sí |

### 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         HARDWAREXTRACTOR v0.2.0                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │  INPUT   │──▶│NORMALIZE │──▶│ CLASSIFY │──▶│ RESOLVE  │            │
│  │ (string) │   │  input   │   │heuristic │   │ catalog  │            │
│  └──────────┘   └──────────┘   └──────────┘   └────┬─────┘            │
│                                                     │                   │
│                              ┌──────────────────────┴────────┐         │
│                              ▼                               ▼         │
│                    ┌─────────────────┐           ┌───────────────┐    │
│                    │  EXACT MATCH    │           │ NEEDS_SELECT  │    │
│                    │   (auto pick)   │           │ (user choice) │    │
│                    └────────┬────────┘           └───────┬───────┘    │
│                              └────────────┬──────────────┘            │
│                                           ▼                            │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    SOURCE CHAIN MANAGER                          │  │
│  │  ┌────────┐   ┌────────┐   ┌────────┐   ┌────────┐             │  │
│  │  │Source 1│──▶│Source 2│──▶│Source 3│──▶│Catalog │             │  │
│  │  │OFFICIAL│   │OFFICIAL│   │REFERENC│   │EMBEDDED│             │  │
│  │  └────────┘   └────────┘   └────────┘   └────────┘             │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                           │                            │
│                    ┌──────────────────────┴───────────────────┐       │
│                    ▼                                          ▼       │
│          ┌─────────────────┐                      ┌─────────────────┐ │
│          │ REQUESTS ENGINE │                      │PLAYWRIGHT ENGINE│ │
│          │   (default)     │──anti-bot detect──▶ │   (fallback)    │ │
│          └────────┬────────┘                      └────────┬────────┘ │
│                    └──────────────────┬───────────────────┘          │
│                                       ▼                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐          │
│  │ EXTRACT  │──▶│ VALIDATE │──▶│   MAP    │──▶│AGGREGATE │          │
│  │ (spider) │   │  specs   │   │ template │   │  ficha   │          │
│  └──────────┘   └──────────┘   └──────────┘   └────┬─────┘          │
│                                                     │                 │
│                    ┌────────────────────────────────┴─────────┐      │
│                    ▼                    ▼                     ▼      │
│            ┌────────────┐      ┌────────────┐        ┌────────────┐ │
│            │ CSV Export │      │XLSX Export │        │ MD Export  │ │
│            └────────────┘      └────────────┘        └────────────┘ │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 3. Estado por Componente

#### 3.1 Clasificador (`classifier/heuristic.py`)

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Funcionalidad | ⚠️ Parcial | Reconoce 5 tipos básicos |
| Patrones | ❌ Insuficientes | Falta 70% de marcas |
| Confianza | ⚠️ Baja | 10-40% típico |
| Tests | ✅ | 93% cobertura |

**Patrones actuales:**
```python
CPU: [intel, amd, ryzen, xeon, i[3579]-, threadripper]
RAM: [ddr[3-5], sodimm, dram, memory, mt/s]
GPU: [rtx, gfx, radeon, arc, geforce, gpu]
MAINBOARD: [motherboard, mainboard, mb, z[0-9]{3}, b[0-9]{3}, x[0-9]{3}, prime, rog]
DISK: [ssd, hdd, nvme, m.2, sata, seagate, wd, samsung]
```

**Patrones FALTANTES:**
```python
# RAM - Marcas
[corsair, kingston, gskill, crucial, teamgroup, patriot, lexar]
# RAM - Part numbers típicos
[cmk, kf4, kf5, f4-, f5-, ct]

# CPU - Modelos específicos
[core, athlon, epyc, opteron]

# GPU - Modelos
[rx [0-9]{4}, gtx, quadro, firepro, titan]

# DISK - Modelos
[evo, qvo, 970, 980, 990, sn[0-9]{3}, barracuda, ironwolf]

# MAINBOARD - Más chipsets
[h[0-9]{3}, a[0-9]{3}, x[0-9]{3}e]
```

#### 3.2 Resolver (`resolver/`)

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Catálogo | ❌ Mínimo | Solo 15 modelos |
| URL Resolver | ✅ | Funciona con allowlist |
| Fuzzy Match | ❌ | No implementado |
| Scoring | ⚠️ | Básico pero funcional |

**Modelos en catálogo actual:**

| Tipo | Cantidad | Marcas |
|------|----------|--------|
| CPU | 4 | Intel, AMD |
| RAM | 3 | Kingston, Corsair |
| GPU | 4 | NVIDIA, AMD |
| MAINBOARD | 2 | ASUS |
| DISK | 2 | Samsung |
| **TOTAL** | **15** | |

**Necesario para 100%:** 500+ modelos

#### 3.3 Spiders (`scrape/`)

| Spider | Estado | Anti-bot | Specs Extraídas |
|--------|--------|----------|-----------------|
| intel_ark_spider | ❌ 403 | Necesita Playwright | 0 |
| amd_cpu_specs_spider | ⚠️ | No | 0 (match incorrecto) |
| kingston_ram_spider | ✅ | No | 1 |
| crucial_ram_spider | ⚠️ | No | No probado |
| corsair_ram_spider | ❌ | SÍ (Cloudflare) | 0 |
| gskill_ram_spider | ❌ | SÍ (Cloudflare) | 0 |
| nvidia_gpu_spider | ⚠️ | No | 3 (match incorrecto) |
| amd_gpu_spider | ⚠️ | No | No probado |
| asus_mainboard_spider | ⚠️ | No | 0 |
| techpowerup_reference | ⚠️ | No | No integrado |
| wikichip_reference | ⚠️ | No | No integrado |

#### 3.4 Mapper (`mapper/mapper.py`)

| Tipo | Campos Mapeados | Campos Requeridos | % |
|------|-----------------|-------------------|---|
| CPU | 6 | 14 | 43% |
| RAM | 0 | 11 | 0% |
| GPU | 0 | 4 | 0% |
| MAINBOARD | 0 | 16 | 0% |
| DISK | 0 | 3 | 0% |

**Campos del template (48 total):**
- Datos generales: 1
- Procesador: 14
- Placa base: 16
- RAM: 11
- Gráfica: 4
- Disco duro: 3

#### 3.5 SourceChain (`core/source_chain.py`)

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Definición | ✅ | 15 fuentes definidas |
| Manager | ✅ | Implementado |
| Integración | ❌ | NO conectado a Orchestrator |
| Fallback | ❌ | NO implementado |
| Anti-bot detect | ⚠️ | Detecta pero no actúa |

#### 3.6 Cache (`cache/sqlite_cache.py`)

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Implementación | ✅ | SQLite funcional |
| TTL | ✅ | 7 días default |
| Integración | ⚠️ | Parcial en scrape_specs |
| Estadísticas | ❌ | Sin hits/misses |

#### 3.7 Exportadores (`export/`)

| Formato | Estado | Funcionalidad |
|---------|--------|---------------|
| CSV | ✅ 100% | Completo |
| XLSX | ⚠️ 60% | Falta formateo avanzado |
| MD | ✅ 90% | Completo |
| JSON | ❌ | No existe |

#### 3.8 Configuración (`app/config.py`)

| Aspecto | Estado | Detalle |
|---------|--------|---------|
| Defaults | ✅ | Definidos |
| Archivo externo | ❌ | NO implementado |
| CLI overrides | ❌ | NO implementado |
| Validación | ❌ | Sin validación |

---

### 4. Problemas Críticos Identificados

#### P1: Catálogo de Modelos Insuficiente
```
Impacto: CRÍTICO
Síntoma: "No candidates found" en 80% de búsquedas
Causa: Solo 15 modelos en resolver_index.json
Solución: Expandir a 500+ modelos
```

#### P2: Anti-Bot No Resuelto
```
Impacto: CRÍTICO
Síntoma: 403 Forbidden en Intel, Corsair, G.Skill
Causa: Playwright no integrado como fallback
Solución: Implementar fallback automático
```

#### P3: SourceChain No Integrado
```
Impacto: CRÍTICO
Síntoma: Sin fallback entre fuentes
Causa: Orchestrator llama directo a scrape_specs()
Solución: Integrar SourceChainManager en Orchestrator
```

#### P4: Mapper Incompleto
```
Impacto: ALTO
Síntoma: specs=[]; en la mayoría de respuestas
Causa: Solo CPU tiene mapeo parcial
Solución: Implementar mapeo para todos los tipos
```

#### P5: Match de Modelo Incorrecto
```
Impacto: ALTO
Síntoma: RTX 4090 → RTX 4070
Causa: Resolver toma primer match parcial
Solución: Implementar fuzzy matching con validación
```

#### P6: Clasificador Débil
```
Impacto: MEDIO
Síntoma: Corsair RAM → GENERAL (10%)
Causa: Patrones no incluyen marcas
Solución: Expandir patrones de clasificación
```

---

## PARTE II: PLAN DE DESARROLLO DETALLADO

### Fases del Proyecto

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ROADMAP HARDWAREXTRACTOR                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  FASE 1: FUNDAMENTOS (Semana 1-2)                                      │
│  ├── [P1] Expandir catálogo de modelos                                 │
│  ├── [P6] Mejorar clasificador                                         │
│  └── [P5] Implementar fuzzy matching                                   │
│                                                                         │
│  FASE 2: SCRAPING (Semana 2-3)                                         │
│  ├── [P2] Integrar Playwright fallback                                 │
│  ├── [P3] Conectar SourceChain a Orchestrator                          │
│  └── Completar spiders faltantes                                       │
│                                                                         │
│  FASE 3: PROCESAMIENTO (Semana 3-4)                                    │
│  ├── [P4] Completar mapper para todos los tipos                        │
│  ├── Integrar cálculos derivados                                       │
│  └── Mejorar validación de specs                                       │
│                                                                         │
│  FASE 4: INTERFACES (Semana 4-5)                                       │
│  ├── Arreglar CLI interactiva                                          │
│  ├── Mejorar UI Tkinter                                                │
│  └── Implementar config externo                                        │
│                                                                         │
│  FASE 5: PULIDO (Semana 5-6)                                           │
│  ├── Tests de integración end-to-end                                   │
│  ├── Fixtures para spiders                                             │
│  └── Documentación y ejemplos                                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### FASE 1: FUNDAMENTOS

#### Tarea 1.1: Expandir Catálogo de Modelos
**Archivo:** `hardwarextractor/data/resolver_index.json`

**Objetivo:** 500+ modelos organizados por tipo

**Estructura por tipo:**

```
CPU (100 modelos):
├── Intel Core (i3, i5, i7, i9) - Gen 10-14: 40
├── Intel Xeon: 10
├── AMD Ryzen (3, 5, 7, 9) - Gen 3000-7000: 40
├── AMD Threadripper: 5
└── AMD EPYC: 5

RAM (150 modelos):
├── Corsair Vengeance/Dominator DDR4/DDR5: 40
├── Kingston Fury/HyperX DDR4/DDR5: 30
├── G.Skill Trident/Ripjaws DDR4/DDR5: 30
├── Crucial Ballistix DDR4/DDR5: 20
├── Samsung/SK Hynix: 15
└── TeamGroup/Patriot: 15

GPU (100 modelos):
├── NVIDIA GeForce RTX 30/40 series: 30
├── NVIDIA GeForce GTX 16 series: 10
├── AMD Radeon RX 6000/7000 series: 30
├── Intel Arc: 10
└── Workstation (Quadro, FirePro): 20

MAINBOARD (100 modelos):
├── ASUS ROG/Prime/TUF (Intel/AMD): 30
├── MSI MEG/MPG/MAG: 25
├── Gigabyte AORUS/Gaming: 25
└── ASRock Phantom/Steel: 20

DISK (50 modelos):
├── Samsung 970/980/990 Pro/EVO: 15
├── WD Black/Blue/Red: 15
├── Seagate Barracuda/FireCuda: 10
└── Crucial/Kingston NVMe: 10
```

**Formato de entrada:**
```json
{
  "component_type": "CPU",
  "brand": "Intel",
  "model": "Core i7-14700K",
  "part_number": "BX8071514700K",
  "score": 0.98,
  "source_url": "https://ark.intel.com/content/www/us/en/ark/products/236783/intel-core-i714700k-processor-33m-cache-up-to-5-60-ghz.html",
  "spider_name": "intel_ark_spider",
  "source_name": "intel_ark"
}
```

#### Tarea 1.2: Mejorar Clasificador
**Archivo:** `hardwarextractor/classifier/heuristic.py`

**Nuevos patrones a agregar:**

```python
_PATTERNS = {
    ComponentType.CPU: [
        # Existentes
        r"\bintel\b", r"\bamd\b", r"\bryzen\b", r"\bxeon\b",
        r"\bi[3579]-", r"\bthreadripper\b",
        # NUEVOS
        r"\bcore\b", r"\bathlon\b", r"\bepyc\b", r"\bopteron\b",
        r"\b[0-9]{4}[kfx]?\b",  # Modelo numérico (12700K, 5900X)
        r"\bprocessor\b", r"\bcpu\b",
    ],
    ComponentType.RAM: [
        # Existentes
        r"\bddr[3-5]\b", r"\bsodimm\b", r"\bdram\b", r"\bmemory\b", r"\bmt\/s\b",
        # NUEVOS - Marcas
        r"\bcorsair\b", r"\bkingston\b", r"\bgskill\b", r"\bg\.skill\b",
        r"\bcrucial\b", r"\bteamgroup\b", r"\bpatriot\b", r"\blexar\b",
        # NUEVOS - Part numbers
        r"\bcmk[0-9]+\b", r"\bkf[45]-\b", r"\bf[45]-\b", r"\bct[0-9]+\b",
        # NUEVOS - Líneas de producto
        r"\bvengeance\b", r"\bdominator\b", r"\bfury\b", r"\btrident\b",
        r"\bripjaws\b", r"\bballistix\b",
    ],
    ComponentType.GPU: [
        # Existentes
        r"\brtx\b", r"\bgfx\b", r"\bradeon\b", r"\barc\b", r"\bgeforce\b", r"\bgpu\b",
        # NUEVOS
        r"\bgtx\b", r"\brx\s*[0-9]{4}\b", r"\bquadro\b", r"\bfirepro\b",
        r"\btitan\b", r"\bnvidia\b", r"\b[0-9]{4}\s*ti\b",
    ],
    ComponentType.MAINBOARD: [
        # Existentes
        r"\bmotherboard\b", r"\bmainboard\b", r"\bmb\b",
        r"\bz[0-9]{3}\b", r"\bb[0-9]{3}\b", r"\bx[0-9]{3}\b",
        r"\bprime\b", r"\brog\b",
        # NUEVOS
        r"\bh[0-9]{3}\b", r"\ba[0-9]{3}\b",  # Chipsets
        r"\basus\b", r"\bmsi\b", r"\bgigabyte\b", r"\basrock\b",
        r"\baorus\b", r"\btuf\b", r"\bmeg\b", r"\bmpg\b",
        r"\bstrix\b", r"\bcrossfire\b", r"\bphantom\b",
    ],
    ComponentType.DISK: [
        # Existentes
        r"\bssd\b", r"\bhdd\b", r"\bnvme\b", r"\bm\.2\b", r"\bsata\b",
        r"\bseagate\b", r"\bwd\b", r"\bsamsung\b",
        # NUEVOS
        r"\bevo\b", r"\bqvo\b", r"\b9[789]0\s*pro\b",
        r"\bsn[0-9]{3}\b", r"\bbarracuda\b", r"\bironwolf\b",
        r"\bfirecuda\b", r"\bblack\b", r"\bblue\b", r"\bred\b",
        r"\bcrucial\b", r"\bkingston\b", r"\bkioxia\b",
        r"\b[0-9]+\s*[gt]b\b",  # Capacidad
    ],
}
```

**Mejorar scoring:**
```python
def classify_component(input_normalized: str) -> Tuple[ComponentType, float]:
    best_type = ComponentType.GENERAL
    best_score = 0.0

    for component_type, patterns in _PATTERNS.items():
        matches = 0
        for pattern in patterns:
            if re.search(pattern, input_normalized, re.IGNORECASE):
                matches += 1

        # Scoring mejorado: más matches = más confianza
        if matches > 0:
            score = min(0.3 + (matches * 0.15), 0.95)
            if score > best_score:
                best_score = score
                best_type = component_type

    if best_score == 0.0:
        return ComponentType.GENERAL, 0.1

    return best_type, best_score
```

#### Tarea 1.3: Implementar Fuzzy Matching
**Archivo:** `hardwarextractor/resolver/resolver.py`

```python
from difflib import SequenceMatcher

def fuzzy_match_score(s1: str, s2: str) -> float:
    """Calcula similitud entre dos strings (0.0 - 1.0)."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()

def resolve_component(input_raw: str, component_type: ComponentType) -> ResolveResult:
    url_result = resolve_from_url(input_raw, component_type)
    if url_result:
        return url_result

    normalized = normalize_input(input_raw)
    candidates: List[ResolveCandidate] = []

    for candidate in catalog_by_type(component_type):
        model = normalize_input(candidate.canonical.get("model", ""))
        pn = normalize_input(candidate.canonical.get("part_number", ""))
        brand = normalize_input(candidate.canonical.get("brand", ""))

        # Match exacto por part_number (máxima prioridad)
        if pn and pn in normalized:
            candidate.score = 0.98
            candidates.append(candidate)
            continue

        # Match exacto por modelo
        if model and model in normalized:
            candidate.score = 0.95
            candidates.append(candidate)
            continue

        # NUEVO: Fuzzy match por modelo
        if model:
            similarity = fuzzy_match_score(model, normalized)
            if similarity > 0.7:
                candidate.score = similarity * 0.9  # Escalar a max 0.9
                candidates.append(candidate)
                continue

        # NUEVO: Fuzzy match por part_number
        if pn:
            similarity = fuzzy_match_score(pn, normalized)
            if similarity > 0.8:
                candidate.score = similarity * 0.85
                candidates.append(candidate)
                continue

        # Match por marca + tokens
        if brand and brand in normalized:
            tokens_in_model = [t for t in normalized.split() if t in model and len(t) > 3]
            if tokens_in_model:
                candidate.score = 0.6 + (len(tokens_in_model) * 0.1)
                candidates.append(candidate)

    # Ordenar por score descendente
    candidates = sorted(candidates, key=lambda c: -c.score)

    # Filtrar candidatos con score bajo
    candidates = [c for c in candidates if c.score > 0.5]

    exact = len(candidates) == 1 and candidates[0].score >= 0.95

    return ResolveResult(exact=exact, candidates=candidates[:5])  # Max 5 candidatos
```

---

### FASE 2: SCRAPING

#### Tarea 2.1: Integrar Playwright Fallback
**Archivo:** `hardwarextractor/scrape/service.py`

```python
from hardwarextractor.scrape.engines.detector import AntiBotDetector
from hardwarextractor.scrape.engines.requests_engine import RequestsEngine
from hardwarextractor.scrape.engines.playwright_engine import PlaywrightEngine

def scrape_specs(
    spider_name: str,
    url: str,
    cache: Optional[SQLiteCache] = None,
    enable_tier2: bool = True,
    user_agent: str = "HardwareXtractor/0.2",
    retries: int = 2,
    throttle_seconds_by_domain: Optional[Dict[str, float]] = None,
    force_playwright: bool = False,
) -> List[SpecField]:
    """Scrape specs con fallback automático a Playwright."""

    # Intentar con Requests primero (a menos que force_playwright)
    if not force_playwright:
        try:
            html = RequestsEngine.fetch(url, user_agent=user_agent, retries=retries)

            # Verificar si hay anti-bot
            antibot_result = AntiBotDetector.detect(html)
            if antibot_result.blocked:
                # Intentar con Playwright
                return _scrape_with_playwright(spider_name, url, cache, user_agent)

            # Extraer specs
            specs = _extract_specs(spider_name, html, url)
            if specs:
                return specs

        except Exception as e:
            if AntiBotDetector.is_antibot_error(str(e)):
                return _scrape_with_playwright(spider_name, url, cache, user_agent)
            raise

    # Fallback a Playwright
    return _scrape_with_playwright(spider_name, url, cache, user_agent)

def _scrape_with_playwright(
    spider_name: str,
    url: str,
    cache: Optional[SQLiteCache],
    user_agent: str,
) -> List[SpecField]:
    """Scrape usando Playwright para sitios con anti-bot."""
    try:
        html = PlaywrightEngine.fetch(url, user_agent=user_agent)
        return _extract_specs(spider_name, html, url)
    except ImportError:
        raise RuntimeError(
            "Playwright no instalado. Instala con: pip install hardwarextractor[browser]"
        )
```

#### Tarea 2.2: Conectar SourceChain a Orchestrator
**Archivo:** `hardwarextractor/app/orchestrator.py`

```python
def _process_candidate(
    self,
    candidate: ResolveCandidate,
    component_type: ComponentType,
    confidence: float,
) -> List[OrchestratorEvent]:
    """Procesa candidato usando SourceChain con fallback."""
    events: List[OrchestratorEvent] = []

    # Obtener fuentes para este tipo de componente
    chain = self._source_chain_manager.get_chain(component_type)

    # Encontrar fuente que coincida con el candidato
    primary_source = self._source_chain_manager.get_source_for_candidate(
        component_type, candidate
    )

    specs = []
    last_error = None

    # Intentar con fuente primaria
    if primary_source:
        self._emit(Event.source_trying(primary_source.provider, candidate.source_url))
        try:
            use_playwright = self._source_chain_manager.should_use_playwright(
                primary_source, candidate.source_url
            )
            specs = self.scrape_fn(
                candidate.spider_name,
                candidate.source_url,
                cache=self.cache,
                force_playwright=use_playwright,
            )
            if specs:
                self._emit(Event.source_success(primary_source.provider, len(specs)))
        except Exception as e:
            last_error = str(e)
            self._emit(Event.source_failed(primary_source.provider, last_error))

            # Marcar dominio como bloqueado si es anti-bot
            if self._antibot_detector.is_antibot_error(last_error):
                domain = candidate.source_url.split("/")[2]
                self._source_chain_manager.mark_domain_blocked(domain)

    # Si falló, intentar con fuentes de referencia (fallback)
    if not specs and self.config.enable_tier2:
        reference_sources = self._source_chain_manager.get_reference_sources(component_type)

        for ref_source in reference_sources:
            self._emit(Event.source_trying(ref_source.provider, ""))
            try:
                # Buscar URL de referencia para este modelo
                ref_url = self._find_reference_url(candidate, ref_source)
                if ref_url:
                    specs = self.scrape_fn(
                        ref_source.spider_name,
                        ref_url,
                        cache=self.cache,
                    )
                    if specs:
                        self._emit(Event.source_success(ref_source.provider, len(specs)))
                        break
            except Exception as e:
                self._emit(Event.source_failed(ref_source.provider, str(e)))

    if not specs:
        self._emit(Event.chain_exhausted(len(chain)))
        events.append(OrchestratorEvent(
            status="ERROR_RECOVERABLE",
            progress=100,
            log=last_error or "No se pudieron obtener specs"
        ))
        return events

    # Continuar con el resto del procesamiento...
    validate_specs(specs)
    # ...
```

#### Tarea 2.3: Completar Spiders Faltantes

**Spider Corsair RAM** (`scrape/spiders/corsair_ram_spider.py`):
```python
# Requiere Playwright por Cloudflare
CORSAIR_RAM_SELECTORS = {
    "capacity": "//span[@data-spec='capacity']",
    "speed": "//span[@data-spec='speed']",
    "latency": "//span[@data-spec='latency']",
    "voltage": "//span[@data-spec='voltage']",
    "form_factor": "//span[@data-spec='form-factor']",
}
```

**Spider G.Skill RAM** (`scrape/spiders/gskill_ram_spider.py`):
```python
# Requiere Playwright por protección
GSKILL_RAM_SELECTORS = {
    "speed": ".spec-table tr:contains('Speed') td:last",
    "latency": ".spec-table tr:contains('Latency') td:last",
    "voltage": ".spec-table tr:contains('Voltage') td:last",
}
```

---

### FASE 3: PROCESAMIENTO

#### Tarea 3.1: Completar Mapper
**Archivo:** `hardwarextractor/mapper/mapper.py`

```python
def _map_ram(
    add_from_key: Callable,
    add_calculated: Callable,
    specs_dict: Dict[str, SpecField],
) -> None:
    """Mapea specs de RAM al template."""
    add_from_key("Tipo de RAM", "ram.type")
    add_from_key("Voltaje", "ram.voltage_v")
    add_from_key("Número de pines", "ram.pins")
    add_from_key("Velocidad real", "ram.speed_mhz")
    add_from_key("Velocidad efectiva", "ram.effective_speed_mhz")
    add_from_key("Latencia", "ram.latency")

    # Cálculos derivados
    speed = specs_dict.get("ram.effective_speed_mhz")
    if speed and speed.value:
        # Ancho de banda single channel = speed * 8 / 1000 (GB/s)
        bw_single = (float(speed.value) * 8) / 1000
        add_calculated("Ancho de banda (single channel)", f"{bw_single:.1f}", "GB/s")
        add_calculated("Ancho de banda (dual channel)", f"{bw_single * 2:.1f}", "GB/s")
        add_calculated("Ancho de banda (triple channel)", f"{bw_single * 3:.1f}", "GB/s")

    # Ratio velocidad/latencia
    latency = specs_dict.get("ram.latency")
    if speed and latency and speed.value and latency.value:
        try:
            ratio = float(speed.value) / float(latency.value.replace("CL", ""))
            add_calculated("Velocidad efectiva / Latencia", f"{ratio:.1f}", None)
        except (ValueError, ZeroDivisionError):
            pass

def _map_gpu(
    add_from_key: Callable,
    add_calculated: Callable,
    specs_dict: Dict[str, SpecField],
) -> None:
    """Mapea specs de GPU al template."""
    add_from_key("Tipo de PCI-E", "gpu.pcie_version")
    add_from_key("Cantidad de RAM", "gpu.vram_gb")

    # Ancho de banda externo (PCIe)
    pcie = specs_dict.get("gpu.pcie_version")
    if pcie and pcie.value:
        # PCIe 4.0 x16 = 32 GB/s, PCIe 5.0 x16 = 64 GB/s
        pcie_bw = {"3.0": 16, "4.0": 32, "5.0": 64}.get(str(pcie.value), 0)
        if pcie_bw:
            add_calculated("Ancho de banda externo", str(pcie_bw), "GB/s")

    # Ancho de banda interno (memoria)
    bus_width = specs_dict.get("gpu.mem.bus_width_bits")
    mem_speed = specs_dict.get("gpu.mem.speed_gbps")
    if bus_width and mem_speed and bus_width.value and mem_speed.value:
        try:
            bw_internal = (float(bus_width.value) * float(mem_speed.value)) / 8
            add_calculated("Ancho de banda interno", f"{bw_internal:.0f}", "GB/s")
        except ValueError:
            pass

def _map_mainboard(
    add_from_key: Callable,
    add_calculated: Callable,
    specs_dict: Dict[str, SpecField],
) -> None:
    """Mapea specs de placa base al template."""
    add_from_key("Zócalo", "mb.socket")
    add_from_key("Chipset de la placa base", "mb.chipset")
    add_from_key("RAM máxima soportada", "mb.max_memory_gb")
    add_from_key("Tipo de bus del sistema", "mb.bus_type")
    add_from_key("Tipo de SATA", "mb.sata_version")
    add_from_key("Tipo de USB", "mb.usb_version")
    add_from_key("Tarjeta de red integrada", "mb.lan_speed")
    add_from_key("Tarjeta gráfica integrada", "mb.integrated_gpu")

    # Ancho de banda RAM
    ram_type = specs_dict.get("mb.memory_type")
    ram_speed = specs_dict.get("mb.max_memory_speed_mhz")
    if ram_type and ram_speed:
        try:
            channels = 2 if "dual" in str(ram_type.value).lower() else 1
            bw = (float(ram_speed.value) * 8 * channels) / 1000
            add_calculated("Ancho de banda de la RAM", f"{bw:.1f}", "GB/s")
        except ValueError:
            pass

def _map_disk(
    add_from_key: Callable,
    add_calculated: Callable,
    specs_dict: Dict[str, SpecField],
) -> None:
    """Mapea specs de disco al template."""
    add_from_key("RPM", "disk.rpm")
    add_from_key("Búfer", "disk.cache_mb")

    # Velocidad según interfaz
    interface = specs_dict.get("disk.interface")
    if interface and interface.value:
        iface = str(interface.value).upper()
        speeds = {
            "SATA III": "600 MB/s",
            "SATA 3": "600 MB/s",
            "NVME": "Varía",
            "PCIE 3.0": "3,500 MB/s",
            "PCIE 4.0": "7,000 MB/s",
            "PCIE 5.0": "14,000 MB/s",
        }
        for key, speed in speeds.items():
            if key in iface:
                add_calculated("Velocidad con chipset", speed, None)
                break
```

---

### FASE 4: INTERFACES

#### Tarea 4.1: Arreglar CLI Interactiva
**Archivo:** `hardwarextractor/cli/interactive.py`

```python
class InteractiveCLI:
    """CLI interactiva mejorada."""

    def __init__(self):
        self.orchestrator = Orchestrator()
        self.ficha = None

    def run(self):
        """Loop principal de la CLI."""
        self._print_header()

        while True:
            try:
                choice = self._show_menu()

                if choice == "1":
                    self._analyze_component()
                elif choice == "2":
                    self._show_ficha()
                elif choice == "3":
                    self._export_ficha()
                elif choice == "4":
                    self._reset_ficha()
                elif choice == "5" or choice.lower() == "q":
                    print("\nHasta luego!")
                    break
                else:
                    print("Opción no válida")

            except KeyboardInterrupt:
                print("\n\nInterrumpido por el usuario")
                break
```

#### Tarea 4.2: Implementar Config Externo
**Archivo:** `hardwarextractor/app/config.py`

```python
import yaml
from pathlib import Path

def load_config() -> AppConfig:
    """Carga configuración desde archivo o usa defaults."""
    config_path = Path.home() / ".config" / "hardwarextractor" / "config.yaml"

    if config_path.exists():
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f)
                return AppConfig(
                    enable_tier2=data.get("enable_tier2", True),
                    user_agent=data.get("user_agent", "HardwareXtractor/0.2"),
                    cache_ttl_seconds=data.get("cache_ttl_seconds", 60*60*24*7),
                    retries=data.get("retries", 2),
                    throttle_seconds_by_domain=data.get("throttle_seconds_by_domain", {}),
                )
        except Exception as e:
            print(f"Warning: Error loading config: {e}")

    return DEFAULT_CONFIG
```

---

### FASE 5: PULIDO

#### Tarea 5.1: Tests de Integración End-to-End

```python
# tests/integration/test_full_pipeline.py

def test_full_pipeline_cpu_intel():
    """Test completo: Intel CPU desde input hasta export."""
    orchestrator = Orchestrator()
    events = orchestrator.process_input("Intel Core i7-12700K")

    # Debe clasificar como CPU
    assert any(e.status == "CLASSIFY_COMPONENT" for e in events)

    # Debe encontrar candidatos o resolver
    assert any(e.status in ("RESOLVE_ENTITY", "NEEDS_USER_SELECTION") for e in events)

def test_full_pipeline_ram_corsair():
    """Test completo: RAM Corsair con Playwright fallback."""
    # ...

def test_export_all_formats():
    """Test exportación a CSV, XLSX, MD."""
    # ...
```

#### Tarea 5.2: Fixtures para Spiders

```
tests/spiders/fixtures/
├── intel_ark/
│   ├── i7-12700k.html
│   └── expected_specs.json
├── amd_specs/
│   ├── ryzen-9-5900x.html
│   └── expected_specs.json
├── kingston_ram/
│   ├── fury-beast-ddr5.html
│   └── expected_specs.json
└── nvidia_gpu/
    ├── rtx-4090.html
    └── expected_specs.json
```

---

## PARTE III: MÉTRICAS DE ÉXITO

### Criterios de Aceptación por Fase

| Fase | Criterio | Métrica |
|------|----------|---------|
| 1 | Catálogo expandido | 500+ modelos |
| 1 | Clasificador mejorado | >70% confianza promedio |
| 1 | Fuzzy matching | >80% matches correctos |
| 2 | Anti-bot resuelto | Corsair/G.Skill funcionan |
| 2 | SourceChain integrado | Fallback automático funciona |
| 3 | Mapper completo | >80% campos mapeados |
| 4 | CLI funcional | Todas las opciones funcionan |
| 5 | Tests E2E | >90% pass rate |

### Métricas Finales Objetivo

| Métrica | Actual | Objetivo |
|---------|--------|----------|
| Tests passing | 100% | 100% |
| Cobertura | 80% | >85% |
| Modelos en catálogo | 15 | 500+ |
| Spiders funcionales | 20% | 90% |
| Campos mapeados | 12% | 90% |
| Anti-bot resuelto | No | Sí |
| CLI funcional | No | Sí |
| Precisión de clasificación | 30% | >80% |
| Precisión de resolución | 20% | >85% |

---

## PARTE IV: ESTIMACIÓN DE ESFUERZO

| Fase | Tareas | Esfuerzo Estimado |
|------|--------|-------------------|
| **Fase 1** | Catálogo + Clasificador + Fuzzy | 3-4 días |
| **Fase 2** | Playwright + SourceChain + Spiders | 4-5 días |
| **Fase 3** | Mapper completo | 2-3 días |
| **Fase 4** | CLI + Config | 2 días |
| **Fase 5** | Tests + Fixtures + Docs | 2-3 días |
| **TOTAL** | | **13-17 días** |

---

## APÉNDICE A: Archivos a Modificar/Crear

### Modificar
- `hardwarextractor/classifier/heuristic.py`
- `hardwarextractor/resolver/resolver.py`
- `hardwarextractor/data/resolver_index.json`
- `hardwarextractor/scrape/service.py`
- `hardwarextractor/app/orchestrator.py`
- `hardwarextractor/mapper/mapper.py`
- `hardwarextractor/cli/interactive.py`
- `hardwarextractor/app/config.py`

### Crear
- `hardwarextractor/scrape/spiders/corsair_ram_spider.py`
- `hardwarextractor/scrape/spiders/gskill_ram_spider.py`
- `tests/integration/test_full_pipeline.py`
- `tests/spiders/fixtures/**/*.html`

---

## APÉNDICE B: Dependencias Adicionales

```toml
# pyproject.toml - agregar a dependencies
[project.dependencies]
pyyaml = ">=6.0"  # Para config externo

[project.optional-dependencies]
browser = [
    "playwright>=1.40.0",
]
```

---

*Documento generado el 2026-01-29*
*HardwareXtractor v0.2.0 → v1.0.0 Roadmap*
