from __future__ import annotations

import pytest

from hardwarextractor.scrape.service import ScrapeError, scrape_specs


def test_scrape_service_allowlist_block():
    with pytest.raises(ScrapeError):
        scrape_specs("intel_ark_spider", "https://example.com", html_override="<html></html>")


def test_scrape_service_html_override():
    html = "<div data-spec-key=\"cpu.cores_physical\" data-spec-value=\"8\"></div>"
    specs = scrape_specs("intel_ark_spider", "https://www.intel.com/product", html_override=html)
    assert specs[0].key == "cpu.cores_physical"
