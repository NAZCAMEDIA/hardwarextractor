"""Requests-based fetch engine for simple HTTP fetching."""

from __future__ import annotations

import time
from typing import Optional

import requests

from hardwarextractor.scrape.engines.base import BaseFetchEngine, FetchResult


# Realistic browser headers
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}


class RequestsEngine(BaseFetchEngine):
    """Fast, lightweight fetch engine using requests library.

    Best for:
    - Sites without JavaScript requirements
    - Sites without aggressive anti-bot measures
    - Quick lookups and API calls

    Limitations:
    - Cannot execute JavaScript
    - Cannot bypass sophisticated anti-bot measures
    """

    def __init__(
        self,
        headers: Optional[dict] = None,
        session: Optional[requests.Session] = None
    ):
        """Initialize the requests engine.

        Args:
            headers: Custom headers to use (merged with defaults)
            session: Optional requests.Session for connection pooling
        """
        self._headers = {**DEFAULT_HEADERS, **(headers or {})}
        self._session = session or requests.Session()
        self._session.headers.update(self._headers)

    @property
    def name(self) -> str:
        return "requests"

    def fetch(self, url: str, timeout: int = 15000) -> FetchResult:
        """Fetch HTML content from a URL.

        Args:
            url: The URL to fetch
            timeout: Timeout in milliseconds

        Returns:
            FetchResult with HTML content or error
        """
        timeout_secs = timeout / 1000

        try:
            response = self._session.get(
                url,
                timeout=timeout_secs,
                allow_redirects=True
            )

            return FetchResult(
                html=response.text,
                status_code=response.status_code,
                engine_used=self.name,
                url=response.url
            )

        except requests.Timeout:
            return FetchResult(
                html="",
                status_code=0,
                engine_used=self.name,
                url=url,
                error="timeout"
            )

        except requests.ConnectionError as e:
            return FetchResult(
                html="",
                status_code=0,
                engine_used=self.name,
                url=url,
                error=f"connection_error: {str(e)[:100]}"
            )

        except requests.RequestException as e:
            return FetchResult(
                html="",
                status_code=0,
                engine_used=self.name,
                url=url,
                error=f"request_error: {str(e)[:100]}"
            )

    def fetch_with_retry(
        self,
        url: str,
        timeout: int = 15000,
        retries: int = 2,
        retry_delay: float = 0.5
    ) -> FetchResult:
        """Fetch with automatic retry on failure.

        Args:
            url: The URL to fetch
            timeout: Timeout in milliseconds
            retries: Number of retries
            retry_delay: Delay between retries in seconds

        Returns:
            FetchResult from the last attempt
        """
        last_result = None

        for attempt in range(retries + 1):
            result = self.fetch(url, timeout)

            if result.success:
                return result

            last_result = result

            # Don't retry on certain errors
            if result.status_code in (403, 404, 410):
                return result

            if attempt < retries:
                time.sleep(retry_delay)

        return last_result or FetchResult(
            html="",
            status_code=0,
            engine_used=self.name,
            url=url,
            error="max_retries_exceeded"
        )

    def close(self) -> None:
        """Close the session."""
        if self._session:
            self._session.close()
