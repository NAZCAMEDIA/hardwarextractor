# Documentacion Tecnica - HardwareXtractor

## Arquitectura del Sistema

```
+------------------+
|     USUARIO      |
+--------+---------+
         |
         v
+--------+---------+
|   NORMALIZADOR   |  <- Limpia input
+--------+---------+
         |
         v
+--------+---------+
|  CLASIFICADOR    |  <- Detecta CPU/GPU/RAM/DISK/MAINBOARD
+--------+---------+
         |
         v
+--------+---------+
| SOURCE CHAIN     |  <- Lista de fuentes con fallback
|                  |  <- CPU: Intel ARK -> AMD -> TechPowerUp
+--------+---------+
         |
         v
+--------+---------+
|  FETCH ENGINE    |  <- Requests -> Anti-Bot -> Playwright
+--------+---------+
         |
         v
+--------+---------+
|    PARSER        |  <- Extrae specs del HTML
+--------+---------+
         |
         v
+--------+---------+
| CROSS-VALIDATOR  |  <- Compara fuentes, asigna confianza
+--------+---------+
         |
         v
+--------+---------+
|     UI           |  <- Muestra specs al usuario
+------------------+
```

## Sistema de Scraping

### Engines Disponibles

| Engine | Velocidad | Uso |
|--------|-----------|-----|
| Requests | 0.5s | Primera opcion |
| Playwright | 3-5s | Fallback anti-bot |

### Flujo Anti-Bot

```
Request -> Check HTTP status
    |
    +-- 403/429 --> Rate Limited --> Playwright
    |
    +-- CAPTCHA --> Skip source
    |
    +-- HTML --> Return content
```

## Problemas Conocidos

### 1. Bloqueo por CAPTCHA

| Sitio | Tipo | Solucion |
|-------|------|----------|
| AMD.com | reCAPTCHA | ❌ Sin solucion |
| PassMark | hCAPTCHA | ❌ Sin solucion |
| UserBenchmark | Custom | ❌ Sin solucion |

### 2. URLs Dinamicas

| Sitio | Problema | Frecuencia |
|-------|----------|------------|
| Samsung SSD | URLs 404 | 30% |
| Corsair RAM | Redirects | 50% |

### 3. Estructura HTML Inconsistente

| Fabricante | Formato | Specs |
|------------|---------|-------|
| Intel ARK | `<table class="specs">` | 27 |
| NVIDIA | Meta + JSON-LD | 20 |
| AMD | JS renderizado | 5-10 |

### 4. Rate Limiting

| Sitio | Limite | Throttle |
|-------|--------|----------|
| Intel ARK | 10/min | 1.0s |
| TechPowerUp | 5/min | 3.0s |

### 5. Sin APIs Oficiales

| Fabricante | API | Notas |
|------------|-----|-------|
| Intel | Si | Documentada |
| AMD | No | Solo HTML |
| NVIDIA | Parcial | Docs devs |

## Comparativa de Fuentes

### CPUs (specs promedio)

```
Intel ARK:          27 specs
marvic2409/AllCPUs:  9 specs
TechPowerUp:         5 specs
AMD.com:             0 specs (CAPTCHA)
```

### GPUs (specs promedio)

```
NVIDIA datacenter:  28 specs
ATI historicas:     24 specs
NVIDIA consumer:    23 specs
AMD.com:             0 specs (CAPTCHA)
```

### Tasa de Exito

```
Intel ARK:          100%
NVIDIA datacenter:   90%
TechPowerUp:         70%
GitHub datasets:     60%
AMD.com:              0%
PassMark:             0%
```

## Lecciones Aprendidas

1. SIEMPRE usa fallbacks - no confies en una sola fuente
2. Cachea todo - los sitios cambian frecuentemente
3. Maneja errores explicitamente - no silencies excepciones
4. Respeta robots.txt - verificalo antes de scrapeer

## Estado del Catalogo

| Categoria | Componentes | Promedio specs |
|-----------|-------------|----------------|
| CPU | 132 | 10.7 |
| GPU | 92 | 20.5 |
| RAM | 0 | - |
| MAINBOARD | 0 | - |
| DISK | 0 | - |

Total: 224 componentes

## Scripts de Desarrollo

| Script | Proposito |
|--------|-----------|
| enrich_from_public_sources.py | Carga desde GitHub |
| test_sources_with_playwright.py | Testea fuentes |
| enrich_catalog.py | Enrichment completo |

## Recursos

- Intel ARK API: https://ark.intel.com/docs/api
- Playwright: https://playwright.dev/python/docs/intro
- Datasets: gmasse/gpu-specs, reox007/RightNow-GPU-DB
