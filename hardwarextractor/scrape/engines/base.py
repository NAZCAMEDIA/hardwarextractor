"""Base class for fetch engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class FetchResult:
    """Result of a fetch operation.

    Attributes:
        html: The fetched HTML content
        status_code: HTTP status code
        engine_used: Name of the engine that fetched this
        url: Final URL after redirects
        error: Error message if fetch failed
    """
    html: str
    status_code: int = 200
    engine_used: str = "unknown"
    url: Optional[str] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.status_code == 200


class BaseFetchEngine(ABC):
    """Abstract base class for fetch engines.

    Fetch engines are responsible for retrieving HTML content from URLs.
    Different engines have different capabilities:
    - RequestsEngine: Fast, lightweight, but can't handle JS or anti-bot
    - PlaywrightEngine: Full browser, handles JS and some anti-bot measures
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name for logging."""
        pass

    @abstractmethod
    def fetch(self, url: str, timeout: int = 15000) -> FetchResult:
        """Fetch HTML content from a URL.

        Args:
            url: The URL to fetch
            timeout: Timeout in milliseconds

        Returns:
            FetchResult with HTML content or error
        """
        pass

    def close(self) -> None:
        """Clean up resources. Override in subclasses if needed."""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
