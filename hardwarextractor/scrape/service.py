from __future__ import annotations

from typing import Dict, List, Optional

import time
from urllib.parse import urlparse

import requests

from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.models.schemas import SpecField
from hardwarextractor.scrape.spiders import SPIDERS
from hardwarextractor.utils.allowlist import classify_tier, is_allowlisted


class ScrapeError(Exception):
    pass


def scrape_specs(
    spider_name: str,
    url: str,
    cache: Optional[SQLiteCache] = None,
    html_override: Optional[str] = None,
    enable_tier2: bool = True,
    user_agent: str = "HardwareXtractor/0.1",
    retries: int = 2,
    throttle_seconds_by_domain: Optional[Dict[str, float]] = None,
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
        html = _fetch_with_retries(url, user_agent=user_agent, retries=retries)

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


def _fetch_with_retries(url: str, user_agent: str, retries: int) -> str:
    attempts = max(1, retries + 1)
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            response = requests.get(url, timeout=15, headers={"User-Agent": user_agent})
            response.raise_for_status()
            return response.text
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            time.sleep(0.5)
    raise ScrapeError(f"Fetch failed after retries: {last_error}")
