from __future__ import annotations

from parsel import Selector

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.extractors import parse_labeled_fields
from hardwarextractor.scrape.mappings import LABEL_MAP_CPU, LABEL_MAP_GPU


def test_parse_pcie_lanes_from_x():
    html = "<table><tr><th>PCIe Lanes</th><td>x16</td></tr></table>"
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_CPU, "Intel", "https://intel.com", SourceTier.OFFICIAL)
    assert any(spec.key.endswith("lanes_max") and spec.value == 16 for spec in specs)


def test_parse_ddr_speed_from_text():
    html = "<table><tr><th>Max Memory Speed</th><td>DDR5-5600</td></tr></table>"
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_CPU, "Intel", "https://intel.com", SourceTier.OFFICIAL)
    assert any(spec.key == "cpu.max_memory_speed_mt_s" and spec.value == 5600 for spec in specs)


def test_parse_gpu_lanes_from_text():
    html = "<table><tr><th>PCIe Lanes</th><td>16 lanes</td></tr></table>"
    selector = Selector(text=html)
    specs = parse_labeled_fields(selector, LABEL_MAP_GPU, "NVIDIA", "https://nvidia.com", SourceTier.OFFICIAL)
    assert any(spec.key == "gpu.pcie.lanes" and spec.value == 16 for spec in specs)
