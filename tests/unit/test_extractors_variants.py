from __future__ import annotations

from parsel import Selector

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.extractors import parse_labeled_fields
from hardwarextractor.scrape.mappings import LABEL_MAP_RAM


def test_extract_table_nested_text():
    html = "<table><tr><th>Memory Type</th><td><span>DDR5</span></td></tr></table>"
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_RAM, "Kingston", "https://kingston.com", SourceTier.OFFICIAL)
    assert any(spec.key == "ram.type" for spec in specs)


def test_extract_data_title_value():
    html = '<div data-title="Memory Type" data-value="DDR4"></div>'
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_RAM, "Kingston", "https://kingston.com", SourceTier.OFFICIAL)
    assert any(spec.key == "ram.type" for spec in specs)


def test_extract_ddr_speed_mt_s():
    html = '<table><tr><th>Max Memory Speed</th><td>3200 MT/s</td></tr></table>'
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_RAM, "Kingston", "https://kingston.com", SourceTier.OFFICIAL)
    assert any(spec.key == "ram.speed_effective_mt_s" and spec.value == 3200 for spec in specs)
