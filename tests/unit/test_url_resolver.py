from __future__ import annotations

from hardwarextractor.models.schemas import ComponentType
from hardwarextractor.resolver.url_resolver import resolve_from_url, _spider_for_domain


def test_resolve_from_url_official():
    result = resolve_from_url("https://www.intel.com/products/sku/134599", ComponentType.CPU)
    assert result is not None
    assert result.exact
    assert result.candidates[0].spider_name == "intel_ark_spider"


def test_resolve_from_url_blocked():
    result = resolve_from_url("https://example.com/", ComponentType.CPU)
    assert result is None


def test_resolve_from_url_non_http():
    """Test that non-http URLs return None."""
    result = resolve_from_url("ftp://intel.com/product", ComponentType.CPU)
    assert result is None
    result = resolve_from_url("not_a_url", ComponentType.CPU)
    assert result is None


def test_resolve_from_url_reference_tier():
    """Test that reference tier URLs get lower score."""
    result = resolve_from_url("https://www.techpowerup.com/gpu-specs/123", ComponentType.GPU)
    if result:  # Only if spider exists for this domain
        assert result.candidates[0].score <= 0.9


def test_spider_for_domain_no_match():
    """Test _spider_for_domain with unknown domain."""
    spider = _spider_for_domain("unknown.example.com", ComponentType.CPU)
    assert spider is None


def test_spider_for_domain_general_match():
    """Test _spider_for_domain returns general spider when no specific type match."""
    spider = _spider_for_domain("www.intel.com", ComponentType.GENERAL)
    assert spider is not None
