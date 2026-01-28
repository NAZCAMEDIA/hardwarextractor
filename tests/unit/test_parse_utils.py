from __future__ import annotations

from parsel import Selector

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape import parse_utils


def test_parse_utils_exports():
    html = "<div data-spec-key=\"cpu.cores_physical\" data-spec-value=\"8\"></div>"
    selector = Selector(text=html)
    specs = parse_utils.parse_data_spec_fields(selector, "Intel", "https://intel.com", SourceTier.OFFICIAL)
    assert specs[0].key == "cpu.cores_physical"
