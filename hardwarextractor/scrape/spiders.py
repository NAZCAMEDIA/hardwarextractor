from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from parsel import Selector

from hardwarextractor.models.schemas import SpecField, SourceTier
from hardwarextractor.scrape.extractors import (
    parse_data_spec_fields,
    parse_labeled_fields,
    parse_og_description_specs,
)
from hardwarextractor.scrape.mappings import (
    LABEL_MAP_CPU,
    LABEL_MAP_DISK,
    LABEL_MAP_GPU,
    LABEL_MAP_MAINBOARD,
    LABEL_MAP_RAM,
    LABEL_MAP_REFERENCE,
    LABEL_MAP_TECHPOWERUP_GPU,
    LABEL_MAP_TECHPOWERUP_CPU,
    LABEL_MAP_PASSMARK,
    LABEL_MAP_PCPARTPICKER,
    LABEL_MAP_USERBENCHMARK,
    LABEL_MAP_NOTEBOOKCHECK,
    LABEL_MAP_RETAIL_RAM,
    LABEL_MAP_RETAIL_DISK,
    LABEL_MAP_RETAIL_MAINBOARD,
    LABEL_MAP_NEWEGG_RAM,
    LABEL_MAP_NEWEGG_DISK,
    LABEL_MAP_NEWEGG_MAINBOARD,
    LABEL_MAP_PCPARTPICKER_RAM,
    LABEL_MAP_PCPARTPICKER_DISK,
    LABEL_MAP_PCPARTPICKER_MAINBOARD,
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
        fields.extend(
            parse_data_spec_fields(selector, self.source_name, url, self.source_tier)
        )
        if self.label_map:
            fields.extend(
                parse_labeled_fields(
                    selector, self.label_map, self.source_name, url, self.source_tier
                )
            )
        return fields


@dataclass
class TechPowerUpSpider(BaseSpecSpider):
    """Specialized spider for TechPowerUp pages.

    TechPowerUp has different formats for CPUs and GPUs.
    - CPUs: specs in <section class="details"><table> format
    - GPUs: specs in og:description meta tag
    """

    def _parse_cpu_from_og_description(self, selector: Selector) -> List[SpecField]:
        """Extract CPU specs from og:description when full HTML is blocked.

        CPU og:description format: "Raphael, 8 Cores, 16 Threads, 4.2 GHz, 120 W"
        """
        import re
        from hardwarextractor.scrape.extractors import _field_from_value

        fields: List[SpecField] = []
        og_desc = selector.css('meta[property="og:description"]::attr(content)').get()
        if not og_desc:
            return fields

        parts = [p.strip() for p in og_desc.split(",")]

        for part in parts:
            part_lower = part.lower()

            # Codename (first part like "Raphael")
            if part == parts[0]:
                fields.append(
                    _field_from_value(
                        key="cpu.codename",
                        label="Codename",
                        value=part,
                        unit=None,
                        source_name=self.source_name,
                        source_url="",  # Will be set by caller
                        source_tier=self.source_tier,
                    )
                )
                continue

            # Physical Cores (e.g., "8 Cores")
            if "cores" in part_lower and "threads" not in part_lower:
                match = re.search(r"([0-9]+)\s*cores", part_lower)
                if match:
                    fields.append(
                        _field_from_value(
                            key="cpu.cores_physical",
                            label="Cores",
                            value=match.group(1),
                            unit=None,
                            source_name=self.source_name,
                            source_url="",
                            source_tier=self.source_tier,
                        )
                    )
                continue

            # Threads (e.g., "16 Threads")
            if "threads" in part_lower:
                match = re.search(r"([0-9]+)\s*threads", part_lower)
                if match:
                    fields.append(
                        _field_from_value(
                            key="cpu.threads_logical",
                            label="Threads",
                            value=match.group(1),
                            unit=None,
                            source_name=self.source_name,
                            source_url="",
                            source_tier=self.source_tier,
                        )
                    )
                continue

            # Clock speed (e.g., "4.2 GHz" or "2520 MHz")
            if "ghz" in part_lower or "mhz" in part_lower:
                match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(ghz|mhz)", part_lower)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2).upper()
                    # Convert GHz to MHz
                    if "ghz" in part_lower:
                        value = int(value * 1000)
                        unit = "MHz"
                    fields.append(
                        _field_from_value(
                            key="cpu.base_clock_mhz",
                            label="Clock",
                            value=str(int(value)),
                            unit=unit,
                            source_name=self.source_name,
                            source_url="",
                            source_tier=self.source_tier,
                        )
                    )
                continue

            # TDP (e.g., "120 W")
            if "w" in part_lower:
                match = re.search(r"([0-9]+)\s*w", part_lower)
                if match:
                    fields.append(
                        _field_from_value(
                            key="cpu.tdp_w",
                            label="TDP",
                            value=match.group(1),
                            unit="W",
                            source_name=self.source_name,
                            source_url="",
                            source_tier=self.source_tier,
                        )
                    )
                continue

        return fields

    def parse_html(self, html: str, url: str) -> List[SpecField]:
        selector = Selector(text=html)
        fields = []

        # Detect CPU vs GPU based on URL and og:description
        # TechPowerUp blocks full HTML, so we use URL pattern and og:description
        is_cpu = "/cpu-specs/" in url or (
            "cores" in html.lower() and "threads" in html.lower()
        )
        is_gpu = "/gpu-specs/" in url or any(
            x in html.lower() for x in ["nvidia", "ad102", "rtx ", "gddr"]
        )

        if is_cpu and not is_gpu:
            # CPU format - extract from og:description since full HTML is blocked
            fields.extend(self._parse_cpu_from_og_description(selector))
        elif is_gpu and not is_cpu:
            # GPU format
            fields.extend(
                parse_og_description_specs(
                    selector, self.source_name, url, self.source_tier
                )
            )
        else:
            # Fallback - try og:description first
            fields.extend(
                parse_og_description_specs(
                    selector, self.source_name, url, self.source_tier
                )
            )

        # Also try traditional extractors as fallback
        fields.extend(
            parse_data_spec_fields(selector, self.source_name, url, self.source_tier)
        )
        if self.label_map:
            fields.extend(
                parse_labeled_fields(
                    selector, self.label_map, self.source_name, url, self.source_tier
                )
            )

        return fields


SPIDERS = {
    "intel_ark_spider": BaseSpecSpider(
        "intel_ark_spider",
        ["intel.com"],
        "Intel ARK",
        SourceTier.OFFICIAL,
        LABEL_MAP_CPU,
    ),
    "amd_cpu_specs_spider": BaseSpecSpider(
        "amd_cpu_specs_spider", ["amd.com"], "AMD", SourceTier.OFFICIAL, LABEL_MAP_CPU
    ),
    "asus_mainboard_spider": BaseSpecSpider(
        "asus_mainboard_spider",
        ["asus.com"],
        "ASUS",
        SourceTier.OFFICIAL,
        LABEL_MAP_MAINBOARD,
    ),
    "msi_mainboard_spider": BaseSpecSpider(
        "msi_mainboard_spider",
        ["msi.com"],
        "MSI",
        SourceTier.OFFICIAL,
        LABEL_MAP_MAINBOARD,
    ),
    "gigabyte_mainboard_spider": BaseSpecSpider(
        "gigabyte_mainboard_spider",
        ["gigabyte.com"],
        "Gigabyte",
        SourceTier.OFFICIAL,
        LABEL_MAP_MAINBOARD,
    ),
    "asrock_mainboard_spider": BaseSpecSpider(
        "asrock_mainboard_spider",
        ["asrock.com"],
        "ASRock",
        SourceTier.OFFICIAL,
        LABEL_MAP_MAINBOARD,
    ),
    "kingston_ram_spider": BaseSpecSpider(
        "kingston_ram_spider",
        ["kingston.com"],
        "Kingston",
        SourceTier.OFFICIAL,
        LABEL_MAP_RAM,
    ),
    "crucial_ram_spider": BaseSpecSpider(
        "crucial_ram_spider",
        ["crucial.com", "micron.com"],
        "Crucial",
        SourceTier.OFFICIAL,
        LABEL_MAP_RAM,
    ),
    "corsair_ram_spider": BaseSpecSpider(
        "corsair_ram_spider",
        ["corsair.com"],
        "Corsair",
        SourceTier.OFFICIAL,
        LABEL_MAP_RAM,
    ),
    "gskill_ram_spider": BaseSpecSpider(
        "gskill_ram_spider",
        ["gskill.com"],
        "G.Skill",
        SourceTier.OFFICIAL,
        LABEL_MAP_RAM,
    ),
    "nvidia_gpu_chip_spider": BaseSpecSpider(
        "nvidia_gpu_chip_spider",
        ["nvidia.com"],
        "NVIDIA",
        SourceTier.OFFICIAL,
        LABEL_MAP_GPU,
    ),
    "amd_gpu_chip_spider": BaseSpecSpider(
        "amd_gpu_chip_spider", ["amd.com"], "AMD", SourceTier.OFFICIAL, LABEL_MAP_GPU
    ),
    "intel_arc_gpu_chip_spider": BaseSpecSpider(
        "intel_arc_gpu_chip_spider",
        ["intel.com"],
        "Intel",
        SourceTier.OFFICIAL,
        LABEL_MAP_GPU,
    ),
    "asus_gpu_aib_spider": BaseSpecSpider(
        "asus_gpu_aib_spider", ["asus.com"], "ASUS", SourceTier.OFFICIAL, LABEL_MAP_GPU
    ),
    "samsung_storage_spider": BaseSpecSpider(
        "samsung_storage_spider",
        ["samsung.com", "semiconductors.samsung.com"],
        "Samsung",
        SourceTier.OFFICIAL,
        LABEL_MAP_DISK,
    ),
    "wdc_storage_spider": BaseSpecSpider(
        "wdc_storage_spider",
        ["wdc.com", "western-digital.com", "sandisk.com"],
        "Western Digital",
        SourceTier.OFFICIAL,
        LABEL_MAP_DISK,
    ),
    "seagate_storage_spider": BaseSpecSpider(
        "seagate_storage_spider",
        ["seagate.com"],
        "Seagate",
        SourceTier.OFFICIAL,
        LABEL_MAP_DISK,
    ),
    # === REFERENCE SPIDERS (Community validated) ===
    # Technical databases - TechPowerUp (specialized spider for og:description format)
    "techpowerup_gpu_spider": TechPowerUpSpider(
        "techpowerup_gpu_spider",
        ["techpowerup.com"],
        "TechPowerUp",
        SourceTier.REFERENCE,
        LABEL_MAP_TECHPOWERUP_GPU,
    ),
    "techpowerup_cpu_spider": TechPowerUpSpider(
        "techpowerup_cpu_spider",
        ["techpowerup.com"],
        "TechPowerUp",
        SourceTier.REFERENCE,
        LABEL_MAP_TECHPOWERUP_CPU,
    ),
    "techpowerup_reference_spider": TechPowerUpSpider(
        "techpowerup_reference_spider",
        ["techpowerup.com"],
        "TechPowerUp",
        SourceTier.REFERENCE,
        LABEL_MAP_REFERENCE,
    ),
    "wikichip_reference_spider": BaseSpecSpider(
        "wikichip_reference_spider",
        ["wikichip.org"],
        "WikiChip",
        SourceTier.REFERENCE,
        LABEL_MAP_REFERENCE,
    ),
    "cpu_world_spider": BaseSpecSpider(
        "cpu_world_spider",
        ["cpu-world.com"],
        "CPU-World",
        SourceTier.REFERENCE,
        LABEL_MAP_CPU,
    ),
    "gpu_specs_spider": BaseSpecSpider(
        "gpu_specs_spider",
        ["gpu-specs.com"],
        "GPU-Specs",
        SourceTier.REFERENCE,
        LABEL_MAP_GPU,
    ),
    # PassMark benchmark sites
    "passmark_cpu_spider": BaseSpecSpider(
        "passmark_cpu_spider",
        ["cpubenchmark.net"],
        "PassMark CPU",
        SourceTier.REFERENCE,
        LABEL_MAP_PASSMARK,
    ),
    "passmark_gpu_spider": BaseSpecSpider(
        "passmark_gpu_spider",
        ["videocardbenchmark.net"],
        "PassMark GPU",
        SourceTier.REFERENCE,
        LABEL_MAP_PASSMARK,
    ),
    "passmark_ram_spider": BaseSpecSpider(
        "passmark_ram_spider",
        ["memorybenchmark.net"],
        "PassMark RAM",
        SourceTier.REFERENCE,
        LABEL_MAP_PASSMARK,
    ),
    "passmark_disk_spider": BaseSpecSpider(
        "passmark_disk_spider",
        ["harddrivebenchmark.net"],
        "PassMark Disk",
        SourceTier.REFERENCE,
        LABEL_MAP_PASSMARK,
    ),
    # Community benchmarks
    "userbenchmark_spider": BaseSpecSpider(
        "userbenchmark_spider",
        ["userbenchmark.com"],
        "UserBenchmark",
        SourceTier.REFERENCE,
        LABEL_MAP_USERBENCHMARK,
    ),
    # Technical reviews
    "tomshardware_spider": BaseSpecSpider(
        "tomshardware_spider",
        ["tomshardware.com"],
        "Tom's Hardware",
        SourceTier.REFERENCE,
        LABEL_MAP_REFERENCE,
    ),
    "anandtech_spider": BaseSpecSpider(
        "anandtech_spider",
        ["anandtech.com"],
        "AnandTech",
        SourceTier.REFERENCE,
        LABEL_MAP_REFERENCE,
    ),
    "notebookcheck_spider": BaseSpecSpider(
        "notebookcheck_spider",
        ["notebookcheck.net"],
        "NotebookCheck",
        SourceTier.REFERENCE,
        LABEL_MAP_NOTEBOOKCHECK,
    ),
    # Component databases / retailers
    "pcpartpicker_spider": BaseSpecSpider(
        "pcpartpicker_spider",
        ["pcpartpicker.com"],
        "PCPartPicker",
        SourceTier.REFERENCE,
        LABEL_MAP_PCPARTPICKER,
    ),
    "newegg_spider": BaseSpecSpider(
        "newegg_spider",
        ["newegg.com"],
        "Newegg",
        SourceTier.REFERENCE,
        LABEL_MAP_PCPARTPICKER,
    ),
    # Aggregators
    "pangoly_spider": BaseSpecSpider(
        "pangoly_spider",
        ["pangoly.com"],
        "Pangoly",
        SourceTier.REFERENCE,
        LABEL_MAP_PCPARTPICKER,
    ),
    "nanoreviews_spider": BaseSpecSpider(
        "nanoreviews_spider",
        ["nanoreviews.net"],
        "NanoReviews",
        SourceTier.REFERENCE,
        LABEL_MAP_REFERENCE,
    ),
    # Specialized retailer spiders for RAM, Disk, Motherboard
    "pcpartpicker_ram_spider": BaseSpecSpider(
        "pcpartpicker_ram_spider",
        ["pcpartpicker.com"],
        "PCPartPicker RAM",
        SourceTier.REFERENCE,
        LABEL_MAP_PCPARTPICKER_RAM,
    ),
    "pcpartpicker_disk_spider": BaseSpecSpider(
        "pcpartpicker_disk_spider",
        ["pcpartpicker.com"],
        "PCPartPicker Disk",
        SourceTier.REFERENCE,
        LABEL_MAP_PCPARTPICKER_DISK,
    ),
    "pcpartpicker_mainboard_spider": BaseSpecSpider(
        "pcpartpicker_mainboard_spider",
        ["pcpartpicker.com"],
        "PCPartPicker Motherboard",
        SourceTier.REFERENCE,
        LABEL_MAP_PCPARTPICKER_MAINBOARD,
    ),
    "newegg_ram_spider": BaseSpecSpider(
        "newegg_ram_spider",
        ["newegg.com"],
        "Newegg RAM",
        SourceTier.REFERENCE,
        LABEL_MAP_NEWEGG_RAM,
    ),
    "newegg_disk_spider": BaseSpecSpider(
        "newegg_disk_spider",
        ["newegg.com"],
        "Newegg Disk",
        SourceTier.REFERENCE,
        LABEL_MAP_NEWEGG_DISK,
    ),
    "newegg_mainboard_spider": BaseSpecSpider(
        "newegg_mainboard_spider",
        ["newegg.com"],
        "Newegg Motherboard",
        SourceTier.REFERENCE,
        LABEL_MAP_NEWEGG_MAINBOARD,
    ),
}
