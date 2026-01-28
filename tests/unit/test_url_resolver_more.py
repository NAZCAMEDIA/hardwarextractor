from __future__ import annotations

from hardwarextractor.models.schemas import ComponentType
from hardwarextractor.resolver.url_resolver import resolve_from_url


def test_resolve_from_url_gpu():
    result = resolve_from_url("https://www.nvidia.com/en-us/geforce/", ComponentType.GPU)
    assert result is not None
    assert result.candidates[0].spider_name == "nvidia_gpu_chip_spider"
