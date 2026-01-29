from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from hardwarextractor.scrape.service import ScrapeError, scrape_specs, _throttle


def test_scrape_service_allowlist_block():
    with pytest.raises(ScrapeError, match="URL not allowlisted"):
        scrape_specs("intel_ark_spider", "https://example.com", html_override="<html></html>")


def test_scrape_service_html_override():
    html = "<div data-spec-key=\"cpu.cores_physical\" data-spec-value=\"8\"></div>"
    specs = scrape_specs("intel_ark_spider", "https://www.intel.com/product", html_override=html)
    assert specs[0].key == "cpu.cores_physical"


def test_scrape_service_unknown_spider():
    """Test error when spider doesn't exist."""
    with pytest.raises(ScrapeError, match="Unknown spider"):
        scrape_specs("nonexistent_spider", "https://www.intel.com/product", html_override="<html></html>")


def test_scrape_service_tier2_disabled():
    """Test that tier2 disabled blocks REFERENCE tier URLs."""
    # techpowerup.com is classified as REFERENCE tier
    with pytest.raises(ScrapeError, match="Tier 2 disabled"):
        scrape_specs(
            "techpowerup_spider",
            "https://www.techpowerup.com/product/123",
            html_override="<html></html>",
            enable_tier2=False
        )


def test_scrape_service_cache_hit():
    """Test that cached specs are returned."""
    mock_cache = MagicMock()
    mock_cache.get_specs.return_value = {
        "specs": [{"key": "cached_key", "label": "Cached", "value": "cached_value"}]
    }

    specs = scrape_specs(
        "intel_ark_spider",
        "https://www.intel.com/product",
        cache=mock_cache,
        html_override="<html></html>"
    )

    mock_cache.get_specs.assert_called_once()
    assert specs[0].key == "cached_key"


def test_scrape_service_cache_miss_and_store():
    """Test that cache miss fetches and stores."""
    mock_cache = MagicMock()
    mock_cache.get_specs.return_value = None

    html = "<div data-spec-key=\"cpu.cores_physical\" data-spec-value=\"8\"></div>"
    specs = scrape_specs(
        "intel_ark_spider",
        "https://www.intel.com/product",
        cache=mock_cache,
        html_override=html
    )

    assert len(specs) > 0
    mock_cache.set_specs.assert_called_once()


def test_throttle_no_config():
    """Test throttle with no config does nothing."""
    _throttle("https://example.com", None)
    _throttle("https://example.com", {})


def test_throttle_no_matching_domain():
    """Test throttle with non-matching domain."""
    throttle_config = {"other-domain.com": 1.0}
    _throttle("https://example.com", throttle_config)
