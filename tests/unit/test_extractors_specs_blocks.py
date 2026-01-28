from __future__ import annotations

from parsel import Selector

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.extractors import parse_labeled_fields
from hardwarextractor.scrape.mappings import LABEL_MAP_CPU


def test_extract_specs_block():
    html = """
    <div class="specifications">
      Base Clock: 3600 MHz\nCores: 8\nThreads: 16
    </div>
    """
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_CPU, "Intel", "https://intel.com", SourceTier.OFFICIAL)
    keys = {spec.key for spec in specs}
    assert "cpu.base_clock_mhz" in keys
    assert "cpu.cores_physical" in keys
