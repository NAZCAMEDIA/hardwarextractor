from __future__ import annotations

from parsel import Selector

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.extractors import parse_labeled_fields
from hardwarextractor.scrape.mappings import LABEL_MAP_CPU


def test_extract_label_value_data_attrs():
    html = "<div data-label=\"Base Clock\" data-value=\"3600\"></div>"
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_CPU, "Intel", "https://intel.com", SourceTier.OFFICIAL)
    assert any(spec.key == "cpu.base_clock_mhz" for spec in specs)
