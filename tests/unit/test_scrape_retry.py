from __future__ import annotations

import pytest

from hardwarextractor.scrape.service import ScrapeError, _fetch_with_fallback
from hardwarextractor.scrape.engines import FetchResult


def test_fetch_with_fallback_returns_result(monkeypatch):
    """Test that _fetch_with_fallback returns FetchResult."""
    mock_result = FetchResult(
        html="<html><body>Test</body></html>",
        status_code=200,
        engine_used="requests",
        url="https://example.com/",
    )

    class MockEngine:
        def fetch_with_retry(self, url, timeout=15000, retries=2, retry_delay=0.5):
            return mock_result

        def close(self):
            pass

    monkeypatch.setattr(
        "hardwarextractor.scrape.service.RequestsEngine",
        lambda: MockEngine(),
    )

    result = _fetch_with_fallback("https://example.com/", use_playwright_fallback=False)
    assert result.success
    assert result.html == "<html><body>Test</body></html>"


def test_fetch_with_fallback_error(monkeypatch):
    """Test that _fetch_with_fallback handles errors."""
    mock_result = FetchResult(
        html="",
        status_code=0,
        engine_used="requests",
        url="https://example.com/",
        error="connection_error",
    )

    class MockEngine:
        def fetch_with_retry(self, url, timeout=15000, retries=2, retry_delay=0.5):
            return mock_result

        def close(self):
            pass

    monkeypatch.setattr(
        "hardwarextractor.scrape.service.RequestsEngine",
        lambda: MockEngine(),
    )

    result = _fetch_with_fallback("https://example.com/", use_playwright_fallback=False)
    assert not result.success
    assert result.error == "connection_error"


def test_fetch_with_fallback_antibot_detection(monkeypatch):
    """Test that _fetch_with_fallback detects anti-bot blocks."""
    # Simulate a Cloudflare challenge page
    mock_result = FetchResult(
        html="<html><body>Please wait while we checking your browser</body></html>",
        status_code=200,
        engine_used="requests",
        url="https://example.com/",
    )

    class MockEngine:
        def fetch_with_retry(self, url, timeout=15000, retries=2, retry_delay=0.5):
            return mock_result

        def close(self):
            pass

    monkeypatch.setattr(
        "hardwarextractor.scrape.service.RequestsEngine",
        lambda: MockEngine(),
    )

    # Without Playwright fallback, should return blocked content
    result = _fetch_with_fallback("https://example.com/", use_playwright_fallback=False)
    assert result.html  # Returns the blocked HTML since no fallback


def test_fetch_with_fallback_403_no_playwright(monkeypatch):
    """Test handling of 403 status without Playwright fallback."""
    mock_result = FetchResult(
        html="<html><body>Access Denied</body></html>",
        status_code=403,
        engine_used="requests",
        url="https://example.com/",
    )

    class MockEngine:
        def fetch_with_retry(self, url, timeout=15000, retries=2, retry_delay=0.5):
            return mock_result

        def close(self):
            pass

    monkeypatch.setattr(
        "hardwarextractor.scrape.service.RequestsEngine",
        lambda: MockEngine(),
    )

    result = _fetch_with_fallback("https://example.com/", use_playwright_fallback=False)
    assert result.status_code == 403


def test_fetch_with_fallback_playwright_fallback(monkeypatch):
    """Test Playwright fallback when requests fails with anti-bot."""
    # First call returns blocked content
    requests_result = FetchResult(
        html="<html><body>Checking your browser...</body></html>",
        status_code=200,
        engine_used="requests",
        url="https://example.com/",
    )

    # Playwright returns good content
    playwright_result = FetchResult(
        html="<html><body><h1>Product Page</h1></body></html>",
        status_code=200,
        engine_used="playwright",
        url="https://example.com/",
    )

    class MockRequestsEngine:
        def fetch_with_retry(self, url, timeout=15000, retries=2, retry_delay=0.5):
            return requests_result

        def close(self):
            pass

    class MockPlaywrightEngine:
        def fetch(self, url, timeout=15000):
            return playwright_result

        def close(self):
            pass

    monkeypatch.setattr(
        "hardwarextractor.scrape.service.RequestsEngine",
        lambda: MockRequestsEngine(),
    )
    monkeypatch.setattr(
        "hardwarextractor.scrape.engines.get_playwright_engine",
        lambda: MockPlaywrightEngine(),
    )

    result = _fetch_with_fallback("https://example.com/", use_playwright_fallback=True)
    assert result.engine_used == "playwright"
    assert "Product Page" in result.html
