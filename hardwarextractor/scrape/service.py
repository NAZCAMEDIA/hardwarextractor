from __future__ import annotations

from typing import Callable, Dict, List, Optional

import time
import logging
from urllib.parse import urlparse

from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.models.schemas import SpecField
from hardwarextractor.scrape.engines import RequestsEngine, AntiBotDetector, FetchResult
from hardwarextractor.scrape.spiders import SPIDERS
from hardwarextractor.utils.allowlist import classify_tier, is_allowlisted

# Logger para verbose output
logger = logging.getLogger(__name__)

# Callback opcional para logs en UI
_log_callback: Optional[Callable[[str, str], None]] = None


def set_log_callback(callback: Callable[[str, str], None]) -> None:
    """Set a callback for logging to UI."""
    global _log_callback
    _log_callback = callback


def _log(level: str, message: str) -> None:
    """Log a message to both logger and UI callback."""
    if level == "debug":
        logger.debug(message)
    elif level == "info":
        logger.info(message)
    elif level == "warning":
        logger.warning(message)
    elif level == "error":
        logger.error(message)

    if _log_callback:
        _log_callback(level, message)


class ScrapeError(Exception):
    pass


def _fetch_with_fallback(
    url: str,
    timeout: int = 15000,
    retries: int = 2,
    use_playwright_fallback: bool = True,
) -> FetchResult:
    """Fetch URL with automatic Playwright fallback on anti-bot detection.

    Args:
        url: URL to fetch
        timeout: Timeout in milliseconds
        retries: Number of retries for requests engine
        use_playwright_fallback: Whether to try Playwright if blocked

    Returns:
        FetchResult with HTML content
    """
    _log("debug", f"[FETCH] Iniciando fetch de {url}")

    # Try with RequestsEngine first (faster)
    engine = RequestsEngine()
    try:
        _log("debug", f"[FETCH] Usando RequestsEngine...")
        result = engine.fetch_with_retry(url, timeout=timeout, retries=retries)
        _log("debug", f"[FETCH] Requests result: status={result.status_code}, success={result.success}, html_len={len(result.html) if result.html else 0}")

        # Check if successful
        if result.success:
            # Verify not blocked by content analysis
            detection = AntiBotDetector.detect(result.html, result.status_code)
            _log("debug", f"[FETCH] Anti-bot detection: blocked={detection.blocked}, reason={detection.reason}")

            if not detection.blocked:
                _log("info", f"[FETCH] Requests exitoso sin bloqueo")
                return result
            else:
                _log("warning", f"[FETCH] Anti-bot detectado: {detection.reason}")

        # If blocked or failed, try Playwright
        if use_playwright_fallback:
            _log("info", f"[FETCH] Intentando con Playwright...")
            # Only import if needed (heavy dependency)
            from hardwarextractor.scrape.engines import get_playwright_engine

            playwright_engine = get_playwright_engine()
            try:
                playwright_result = playwright_engine.fetch(url, timeout=timeout)
                _log("debug", f"[FETCH] Playwright result: status={playwright_result.status_code}, success={playwright_result.success}, html_len={len(playwright_result.html) if playwright_result.html else 0}")

                if playwright_result.success:
                    # Verify Playwright result isn't blocked either
                    detection = AntiBotDetector.detect(
                        playwright_result.html, playwright_result.status_code
                    )
                    _log("debug", f"[FETCH] Playwright anti-bot: blocked={detection.blocked}, reason={detection.reason}")

                    if not detection.blocked:
                        _log("info", f"[FETCH] Playwright exitoso sin bloqueo")
                        return playwright_result
                    else:
                        _log("warning", f"[FETCH] Playwright también bloqueado: {detection.reason}")
                return playwright_result
            finally:
                playwright_engine.close()
        else:
            _log("debug", f"[FETCH] Playwright fallback deshabilitado")

        return result
    finally:
        engine.close()


def scrape_specs(
    spider_name: str,
    url: str,
    cache: Optional[SQLiteCache] = None,
    html_override: Optional[str] = None,
    enable_tier2: bool = True,
    user_agent: str = "HardwareXtractor/0.1",
    retries: int = 2,
    throttle_seconds_by_domain: Optional[Dict[str, float]] = None,
    use_playwright_fallback: bool = True,
) -> List[SpecField]:
    _log("info", f"[SCRAPE] Iniciando scrape: spider={spider_name}, url={url[:80]}...")

    if not is_allowlisted(url):
        _log("error", f"[SCRAPE] URL no permitida: {url}")
        raise ScrapeError(f"URL not allowlisted: {url}")

    tier = classify_tier(url)
    _log("debug", f"[SCRAPE] URL tier: {tier}")

    if not enable_tier2 and tier == "REFERENCE":
        _log("error", f"[SCRAPE] Tier 2 deshabilitado")
        raise ScrapeError("Tier 2 disabled for this run")

    cache_key = f"{spider_name}:{url}"
    if cache:
        cached = cache.get_specs(cache_key)
        if cached:
            _log("info", f"[SCRAPE] Cache hit: {len(cached['specs'])} specs")
            return [SpecField(**spec) for spec in cached["specs"]]

    spider = SPIDERS.get(spider_name)
    if not spider:
        _log("error", f"[SCRAPE] Spider desconocido: {spider_name}")
        raise ScrapeError(f"Unknown spider: {spider_name}")

    _log("debug", f"[SCRAPE] Usando spider: {spider.name}, label_map keys: {len(spider.label_map)}")

    html = html_override
    if html is None:
        _throttle(url, throttle_seconds_by_domain)
        result = _fetch_with_fallback(
            url,
            timeout=15000,
            retries=retries,
            use_playwright_fallback=use_playwright_fallback,
        )
        if result.error:
            _log("error", f"[SCRAPE] Fetch falló: {result.error}")
            raise ScrapeError(f"Fetch failed: {result.error}")
        html = result.html
        _log("debug", f"[SCRAPE] HTML obtenido: {len(html)} bytes")

    specs = spider.parse_html(html, url)
    _log("info", f"[SCRAPE] Specs parseados: {len(specs)}")

    if specs:
        _log("debug", f"[SCRAPE] Primeros specs: {[(s.key, s.value) for s in specs[:5]]}")
    else:
        # Log para diagnóstico cuando no hay specs
        _log("warning", f"[SCRAPE] 0 specs extraídos. HTML preview: {html[:500] if html else 'None'}...")

    if cache:
        cache.set_specs(cache_key, {"specs": [spec.__dict__ for spec in specs]})

    return specs


_LAST_ACCESS: Dict[str, float] = {}


def _throttle(url: str, throttle_seconds_by_domain: Optional[Dict[str, float]]) -> None:
    if not throttle_seconds_by_domain:
        return
    host = urlparse(url).hostname or ""
    throttle = 0.0
    for domain, seconds in throttle_seconds_by_domain.items():
        if host == domain or host.endswith("." + domain):
            throttle = max(throttle, seconds)
    if throttle <= 0:
        return
    last = _LAST_ACCESS.get(host, 0.0)
    elapsed = time.time() - last
    if elapsed < throttle:
        time.sleep(throttle - elapsed)
    _LAST_ACCESS[host] = time.time()
