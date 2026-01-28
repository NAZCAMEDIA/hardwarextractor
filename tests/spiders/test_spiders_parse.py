from __future__ import annotations

from pathlib import Path

import pytest

from hardwarextractor.models.schemas import SourceTier
from hardwarextractor.scrape.spiders import SPIDERS


FIXTURE_BASE = Path(__file__).resolve().parent / "fixtures"


@pytest.mark.parametrize(
    "spider_name,fixture_rel,expected_tier",
    [
        ("intel_ark_spider", "intel_ark_spider/sample.html", SourceTier.OFFICIAL),
        ("amd_cpu_specs_spider", "amd_cpu_specs_spider/sample.html", SourceTier.OFFICIAL),
        ("asus_mainboard_spider", "asus_mainboard_spider/sample.html", SourceTier.OFFICIAL),
        ("msi_mainboard_spider", "msi_mainboard_spider/sample.html", SourceTier.OFFICIAL),
        ("gigabyte_mainboard_spider", "gigabyte_mainboard_spider/sample.html", SourceTier.OFFICIAL),
        ("asrock_mainboard_spider", "asrock_mainboard_spider/sample.html", SourceTier.OFFICIAL),
        ("kingston_ram_spider", "kingston_ram_spider/sample.html", SourceTier.OFFICIAL),
        ("crucial_ram_spider", "crucial_ram_spider/sample.html", SourceTier.OFFICIAL),
        ("nvidia_gpu_chip_spider", "nvidia_gpu_chip_spider/sample.html", SourceTier.OFFICIAL),
        ("amd_gpu_chip_spider", "amd_gpu_chip_spider/sample.html", SourceTier.OFFICIAL),
        ("intel_arc_gpu_chip_spider", "intel_arc_gpu_chip_spider/sample.html", SourceTier.OFFICIAL),
        ("asus_gpu_aib_spider", "asus_gpu_aib_spider/sample.html", SourceTier.OFFICIAL),
        ("samsung_storage_spider", "samsung_storage_spider/sample.html", SourceTier.OFFICIAL),
        ("wdc_storage_spider", "wdc_storage_spider/sample.html", SourceTier.OFFICIAL),
        ("seagate_storage_spider", "seagate_storage_spider/sample.html", SourceTier.OFFICIAL),
        ("techpowerup_reference_spider", "techpowerup_reference_spider/sample.html", SourceTier.REFERENCE),
        ("wikichip_reference_spider", "wikichip_reference_spider/sample.html", SourceTier.REFERENCE),
    ],
)

def test_spider_parse(spider_name, fixture_rel, expected_tier):
    spider = SPIDERS[spider_name]
    html = (FIXTURE_BASE / fixture_rel).read_text(encoding="utf-8")
    specs = spider.parse_html(html, "https://example.com")
    assert specs, f"{spider_name} returned empty specs"
    assert any(spec.source_tier == expected_tier for spec in specs)
