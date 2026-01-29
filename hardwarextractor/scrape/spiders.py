from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from parsel import Selector

from hardwarextractor.models.schemas import SpecField, SourceTier
from hardwarextractor.scrape.extractors import parse_data_spec_fields, parse_labeled_fields
from hardwarextractor.scrape.mappings import (
    LABEL_MAP_CPU,
    LABEL_MAP_DISK,
    LABEL_MAP_GPU,
    LABEL_MAP_MAINBOARD,
    LABEL_MAP_RAM,
    LABEL_MAP_REFERENCE,
)


@dataclass
class BaseSpecSpider:
    name: str
    allowed_domains: List[str]
    source_name: str
    source_tier: SourceTier
    label_map: Dict[str, str] = field(default_factory=dict)

    def parse_html(self, html: str, url: str) -> List[SpecField]:
        selector = Selector(text=html)
        fields = []
        fields.extend(parse_data_spec_fields(selector, self.source_name, url, self.source_tier))
        if self.label_map:
            fields.extend(parse_labeled_fields(selector, self.label_map, self.source_name, url, self.source_tier))
        return fields


SPIDERS = {
    "intel_ark_spider": BaseSpecSpider("intel_ark_spider", ["intel.com"], "Intel ARK", SourceTier.OFFICIAL, LABEL_MAP_CPU),
    "amd_cpu_specs_spider": BaseSpecSpider("amd_cpu_specs_spider", ["amd.com"], "AMD", SourceTier.OFFICIAL, LABEL_MAP_CPU),
    "asus_mainboard_spider": BaseSpecSpider("asus_mainboard_spider", ["asus.com"], "ASUS", SourceTier.OFFICIAL, LABEL_MAP_MAINBOARD),
    "msi_mainboard_spider": BaseSpecSpider("msi_mainboard_spider", ["msi.com"], "MSI", SourceTier.OFFICIAL, LABEL_MAP_MAINBOARD),
    "gigabyte_mainboard_spider": BaseSpecSpider("gigabyte_mainboard_spider", ["gigabyte.com"], "Gigabyte", SourceTier.OFFICIAL, LABEL_MAP_MAINBOARD),
    "asrock_mainboard_spider": BaseSpecSpider("asrock_mainboard_spider", ["asrock.com"], "ASRock", SourceTier.OFFICIAL, LABEL_MAP_MAINBOARD),
    "kingston_ram_spider": BaseSpecSpider("kingston_ram_spider", ["kingston.com"], "Kingston", SourceTier.OFFICIAL, LABEL_MAP_RAM),
    "crucial_ram_spider": BaseSpecSpider("crucial_ram_spider", ["crucial.com", "micron.com"], "Crucial", SourceTier.OFFICIAL, LABEL_MAP_RAM),
    "corsair_ram_spider": BaseSpecSpider("corsair_ram_spider", ["corsair.com"], "Corsair", SourceTier.OFFICIAL, LABEL_MAP_RAM),
    "gskill_ram_spider": BaseSpecSpider("gskill_ram_spider", ["gskill.com"], "G.Skill", SourceTier.OFFICIAL, LABEL_MAP_RAM),
    "nvidia_gpu_chip_spider": BaseSpecSpider("nvidia_gpu_chip_spider", ["nvidia.com"], "NVIDIA", SourceTier.OFFICIAL, LABEL_MAP_GPU),
    "amd_gpu_chip_spider": BaseSpecSpider("amd_gpu_chip_spider", ["amd.com"], "AMD", SourceTier.OFFICIAL, LABEL_MAP_GPU),
    "intel_arc_gpu_chip_spider": BaseSpecSpider("intel_arc_gpu_chip_spider", ["intel.com"], "Intel", SourceTier.OFFICIAL, LABEL_MAP_GPU),
    "asus_gpu_aib_spider": BaseSpecSpider("asus_gpu_aib_spider", ["asus.com"], "ASUS", SourceTier.OFFICIAL, LABEL_MAP_GPU),
    "samsung_storage_spider": BaseSpecSpider("samsung_storage_spider", ["samsung.com", "semiconductors.samsung.com"], "Samsung", SourceTier.OFFICIAL, LABEL_MAP_DISK),
    "wdc_storage_spider": BaseSpecSpider("wdc_storage_spider", ["wdc.com", "western-digital.com", "sandisk.com"], "Western Digital", SourceTier.OFFICIAL, LABEL_MAP_DISK),
    "seagate_storage_spider": BaseSpecSpider("seagate_storage_spider", ["seagate.com"], "Seagate", SourceTier.OFFICIAL, LABEL_MAP_DISK),
    "techpowerup_reference_spider": BaseSpecSpider("techpowerup_reference_spider", ["techpowerup.com"], "TechPowerUp", SourceTier.REFERENCE, LABEL_MAP_REFERENCE),
    "wikichip_reference_spider": BaseSpecSpider("wikichip_reference_spider", ["wikichip.org"], "WikiChip", SourceTier.REFERENCE, LABEL_MAP_REFERENCE),
}
