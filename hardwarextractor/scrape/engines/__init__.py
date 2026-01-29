"""Fetch engines for scraping."""

from hardwarextractor.scrape.engines.base import BaseFetchEngine, FetchResult
from hardwarextractor.scrape.engines.requests_engine import RequestsEngine
from hardwarextractor.scrape.engines.detector import AntiBotDetector, AntiBotResult

__all__ = [
    "BaseFetchEngine",
    "FetchResult",
    "RequestsEngine",
    "AntiBotDetector",
    "AntiBotResult",
]

# Lazy import for PlaywrightEngine to avoid loading heavy dependencies
def get_playwright_engine():
    """Get PlaywrightEngine instance (lazy import)."""
    from hardwarextractor.scrape.engines.playwright_engine import PlaywrightEngine
    return PlaywrightEngine()
