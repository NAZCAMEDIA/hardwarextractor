"""Playwright-based fetch engine for JavaScript-heavy and anti-bot protected sites."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

from hardwarextractor.scrape.engines.base import BaseFetchEngine, FetchResult


def _setup_playwright_for_pyinstaller() -> None:
    """Configure Playwright paths when running from PyInstaller bundle.

    Browsers are stored in ~/Library/Caches/ms-playwright/ (standard location).
    The driver is bundled with the app.
    """
    # Always set browser path to system cache (standard Playwright location)
    browsers_path = Path.home() / "Library" / "Caches" / "ms-playwright"
    if browsers_path.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(browsers_path)

    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        meipass = Path(sys._MEIPASS)

        # Check for bundled driver
        driver_path = meipass / "playwright" / "driver"
        if driver_path.exists():
            os.environ["PLAYWRIGHT_DRIVER_PATH"] = str(driver_path)


def check_chromium_installed() -> bool:
    """Check if Chromium is installed for Playwright."""
    browsers_path = Path.home() / "Library" / "Caches" / "ms-playwright"
    if not browsers_path.exists():
        return False
    chromium_dirs = list(browsers_path.glob("chromium-*"))
    return len(chromium_dirs) > 0


# Configure Playwright paths at import time
_setup_playwright_for_pyinstaller()


# Realistic user agent
REALISTIC_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class PlaywrightEngine(BaseFetchEngine):
    """Full browser fetch engine using Playwright.

    Best for:
    - Sites with JavaScript-rendered content
    - Sites with anti-bot measures (Cloudflare, etc.)
    - Dynamic single-page applications

    Limitations:
    - Slower than RequestsEngine (~3-5s vs ~0.5s)
    - Higher memory usage (~200MB)
    - Requires playwright to be installed

    Usage:
        engine = PlaywrightEngine()
        result = engine.fetch("https://example.com")
        engine.close()  # Important: clean up browser resources
    """

    def __init__(self, headless: bool = True):
        """Initialize the Playwright engine.

        Args:
            headless: Whether to run browser in headless mode
        """
        self._headless = headless
        self._playwright = None
        self._browser = None
        self._context = None
        self._initialized = False

    @property
    def name(self) -> str:
        return "playwright"

    def _ensure_initialized(self) -> None:
        """Ensure the browser is initialized (lazy initialization)."""
        if self._initialized:
            return

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "Playwright is not installed. Install with: "
                "pip install playwright && playwright install chromium"
            )

        # Check if Chromium is available
        if not check_chromium_installed():
            raise ImportError(
                "Chromium browser not found. Please run: playwright install chromium"
            )

        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
            ]
        )
        self._context = self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=REALISTIC_USER_AGENT,
            locale="en-US",
            timezone_id="America/New_York",
        )

        # Add stealth scripts to avoid detection
        self._context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Mock plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Mock languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'es']
            });

            // Mock chrome object
            window.chrome = {
                runtime: {}
            };
        """)

        self._initialized = True

    def fetch(self, url: str, timeout: int = 15000) -> FetchResult:
        """Fetch HTML content from a URL using a real browser.

        Args:
            url: The URL to fetch
            timeout: Timeout in milliseconds

        Returns:
            FetchResult with HTML content or error
        """
        try:
            self._ensure_initialized()
        except ImportError as e:
            return FetchResult(
                html="",
                status_code=0,
                engine_used=self.name,
                url=url,
                error=str(e)
            )

        page = None
        try:
            page = self._context.new_page()

            # Navigate with timeout
            response = page.goto(
                url,
                timeout=timeout,
                wait_until="networkidle"
            )

            status_code = response.status if response else 0

            # Wait a bit for any final JS to execute
            page.wait_for_timeout(500)

            # Get the final HTML
            html = page.content()

            return FetchResult(
                html=html,
                status_code=status_code,
                engine_used=self.name,
                url=page.url
            )

        except Exception as e:
            error_msg = str(e)

            # Categorize the error
            if "timeout" in error_msg.lower():
                error_type = "timeout"
            elif "net::" in error_msg.lower():
                error_type = "network_error"
            else:
                error_type = f"playwright_error: {error_msg[:100]}"

            return FetchResult(
                html="",
                status_code=0,
                engine_used=self.name,
                url=url,
                error=error_type
            )

        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass

    def fetch_with_scroll(
        self,
        url: str,
        timeout: int = 15000,
        scroll_count: int = 3
    ) -> FetchResult:
        """Fetch with scrolling to trigger lazy-loaded content.

        Args:
            url: The URL to fetch
            timeout: Timeout in milliseconds
            scroll_count: Number of scroll actions

        Returns:
            FetchResult with HTML content
        """
        try:
            self._ensure_initialized()
        except ImportError as e:
            return FetchResult(
                html="",
                status_code=0,
                engine_used=self.name,
                url=url,
                error=str(e)
            )

        page = None
        try:
            page = self._context.new_page()

            response = page.goto(
                url,
                timeout=timeout,
                wait_until="domcontentloaded"
            )

            status_code = response.status if response else 0

            # Scroll to trigger lazy loading
            for _ in range(scroll_count):
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                page.wait_for_timeout(300)

            # Scroll back to top
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(500)

            html = page.content()

            return FetchResult(
                html=html,
                status_code=status_code,
                engine_used=self.name,
                url=page.url
            )

        except Exception as e:
            return FetchResult(
                html="",
                status_code=0,
                engine_used=self.name,
                url=url,
                error=f"playwright_error: {str(e)[:100]}"
            )

        finally:
            if page:
                try:
                    page.close()
                except Exception:
                    pass

    def close(self) -> None:
        """Clean up browser resources."""
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        self._initialized = False

    def __del__(self):
        """Destructor to clean up resources."""
        self.close()
