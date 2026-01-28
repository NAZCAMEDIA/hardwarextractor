from __future__ import annotations

from parsel import Selector

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.extractors import parse_labeled_fields
from hardwarextractor.scrape.mappings import LABEL_MAP_GPU


def test_parse_pcie_version_from_text():
    html = "<table><tr><th>Bus Interface</th><td>PCIe 4.0 x16</td></tr></table>"
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_GPU, "NVIDIA", "https://nvidia.com", SourceTier.OFFICIAL)
    assert any(spec.key == "gpu.pcie.version" and spec.value in {4.0, "4.0"} for spec in specs)
