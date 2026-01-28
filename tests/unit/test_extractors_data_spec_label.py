from __future__ import annotations

from parsel import Selector

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.extractors import parse_labeled_fields
from hardwarextractor.scrape.mappings import LABEL_MAP_RAM


def test_extract_data_spec_label():
    html = '<div data-spec-label="Memory Type" data-spec-value="DDR4"></div>'
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_RAM, "Kingston", "https://kingston.com", SourceTier.OFFICIAL)
    assert any(spec.key == "ram.type" for spec in specs)
