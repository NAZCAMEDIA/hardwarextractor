from __future__ import annotations

from hardwarextractor.models.schemas import ComponentType
from hardwarextractor.resolver.url_resolver import resolve_from_url


def test_resolve_from_url_official():
    result = resolve_from_url("https://www.intel.com/products/sku/134599", ComponentType.CPU)
    assert result is not None
    assert result.exact
    assert result.candidates[0].spider_name == "intel_ark_spider"


def test_resolve_from_url_blocked():
    result = resolve_from_url("https://example.com/", ComponentType.CPU)
    assert result is None
