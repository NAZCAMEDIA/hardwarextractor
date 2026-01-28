from __future__ import annotations

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.extractors import _extract_numeric_with_unit, parse_labeled_fields
from hardwarextractor.scrape.mappings import LABEL_MAP_GPU
from parsel import Selector


def test_extract_numeric_with_unit():
    value, unit = _extract_numeric_with_unit("192-bit")
    assert value == 192
    assert unit == "bit"


def test_parse_labeled_fields_numeric_unit():
    html = "<table><tr><th>Memory Bus</th><td>192-bit</td></tr></table>"
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_GPU, "NVIDIA", "https://nvidia.com", SourceTier.OFFICIAL)
    assert specs[0].value == 192
