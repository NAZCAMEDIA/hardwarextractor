from __future__ import annotations

from typing import Dict, List, Optional

import time
from urllib.parse import urlparse

from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.models.schemas import SpecField
from hardwarextractor.scrape.engines import RequestsEngine, AntiBotDetector, FetchResult
from hardwarextractor.scrape.spiders import SPIDERS
from hardwarextractor.utils.allowlist import classify_tier, is_allowlisted


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
    # Try with RequestsEngine first (faster)
    engine = RequestsEngine()
    try:
        result = engine.fetch_with_retry(url, timeout=timeout, retries=retries)

        # Check if successful
        if result.success:
            # Verify not blocked by content analysis
            detection = AntiBotDetector.detect(result.html, result.status_code)
            if not detection.blocked:
                return result

        # If blocked or failed, try Playwright
        if use_playwright_fallback:
            # Only import if needed (heavy dependency)
            from hardwarextractor.scrape.engines import get_playwright_engine

            playwright_engine = get_playwright_engine()
            try:
                playwright_result = playwright_engine.fetch(url, timeout=timeout)
                if playwright_result.success:
                    # Verify Playwright result isn't blocked either
                    detection = AntiBotDetector.detect(
                        playwright_result.html, playwright_result.status_code
                    )
                    if not detection.blocked:
                        return playwright_result
                return playwright_result
            finally:
                playwright_engine.close()

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
    if not is_allowlisted(url):
        raise ScrapeError(f"URL not allowlisted: {url}")
    if not enable_tier2 and classify_tier(url) == "REFERENCE":
        raise ScrapeError("Tier 2 disabled for this run")

    cache_key = f"{spider_name}:{url}"
    if cache:
        cached = cache.get_specs(cache_key)
        if cached:
            return [SpecField(**spec) for spec in cached["specs"]]

    spider = SPIDERS.get(spider_name)
    if not spider:
        raise ScrapeError(f"Unknown spider: {spider_name}")

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
            raise ScrapeError(f"Fetch failed: {result.error}")
        html = result.html

    specs = spider.parse_html(html, url)
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
