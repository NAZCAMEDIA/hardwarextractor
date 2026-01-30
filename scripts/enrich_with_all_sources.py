#!/usr/bin/env python3
"""Enrich catalog using ALL available reference sources."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.app.paths import cache_db_path
from hardwarextractor.models.schemas import ComponentType, SpecField
from hardwarextractor.scrape.service import SPIDERS, scrape_specs
from hardwarextractor.data.catalog_writer import (
    _load_validated_catalog,
    _save_validated_catalog,
)


BROKEN_SPIDERS = {
    "amd_cpu_specs_spider",
    "amd_gpu_chip_spider",
    "newegg_ram_spider",
    "newegg_disk_spider",
    "newegg_mainboard_spider",
    "pcpartpicker_ram_spider",
    "pcpartpicker_disk_spider",
    "pcpartpicker_mainboard_spider",
    "asus_mainboard_spider",
    "msi_mainboard_spider",
    "gigabyte_mainboard_spider",
    "asrock_mainboard_spider",
    "kingston_ram_spider",
    "corsair_ram_spider",
    "crucial_ram_spider",
    "gskill_ram_spider",
    "samsung_storage_spider",
    "wdc_storage_spider",
    "seagate_storage_spider",
}


def generate_search_urls(
    model: str, brand: str, component_type: str, spider_name: str
) -> list[str]:
    urls = []
    model_clean = model.strip()
    brand_lower = brand.lower()

    if "techpowerup" in spider_name:
        if component_type == "CPU":
            search = f"{brand_lower} {model_clean}".replace(" ", "-").lower()
            urls.append(f"https://www.techpowerup.com/cpu-specs/{search}.c")
        elif component_type == "GPU":
            search = f"{model_clean}".replace(" ", "-").lower()
            urls.append(f"https://www.techpowerup.com/gpu-specs/{search}")

    elif "passmark" in spider_name:
        if component_type == "CPU":
            search = f"{brand} {model}".replace(" ", "+")
            urls.append(f"https://www.cpubenchmark.net/search.php?search={search}")
        elif component_type == "GPU":
            search = f"{model}".replace(" ", "+")
            urls.append(f"https://www.videocardbenchmark.net/gpu.php?gpu={search}")
        elif component_type == "RAM":
            search = f"{brand}+{model}".replace(" ", "+")
            urls.append(f"https://www.memorybenchmark.net/search.php?search={search}")
        elif component_type == "DISK":
            search = f"{brand}+{model}".replace(" ", "+")
            urls.append(
                f"https://www.harddrivebenchmark.net/search.php?search={search}"
            )

    elif "userbenchmark" in spider_name:
        if component_type == "CPU":
            urls.append(
                f"https://cpu.userbenchmark.com/SpeedTest/185226/{brand}-{model}"
            )
        elif component_type == "GPU":
            urls.append(
                f"https://gpu.userbenchmark.com/SpeedTest/182367/{model.replace(' ', '-')}"
            )
        elif component_type == "RAM":
            urls.append(
                f"https://ram.userbenchmark.com/SpeedTest/155321/{brand}-{model}"
            )
        elif component_type == "DISK":
            urls.append(
                f"https://ssd.userbenchmark.com/SpeedTest/158582/{brand}-{model}"
            )

    elif "wikichip" in spider_name and component_type == "CPU":
        search = f"{brand} {model}".replace(" ", "-").lower()
        urls.append(f"https://en.wikichip.org/wiki/{brand}/{search}")

    elif "cpu_world" in spider_name and component_type == "CPU":
        search = f"{brand} {model}".replace(" ", "-").lower()
        urls.append(f"https://www.cpu-world.com/CPUs/Multi_Core/{search}.html")

    elif "gpu_specs" in spider_name and component_type == "GPU":
        search = model.replace(" ", "-").lower()
        urls.append(f"https://www.gpu-specs.org/{search}")

    elif "tomshardware" in spider_name and component_type == "CPU":
        search = f"{brand}-{model}".replace(" ", "-").lower()
        urls.append(f"https://www.tomshardware.com/reviews/{search}")

    elif "anandtech" in spider_name and component_type == "CPU":
        search = f"{brand} {model}".replace(" ", "-").lower()
        urls.append(f"https://www.anandtech.com/show/{search}")

    elif "notebookcheck" in spider_name and component_type == "CPU":
        urls.append(
            f"https://www.notebookcheck.net/{brand}-{model}-Processor.190000.0.0.html"
        )

    return urls


def get_all_spiders_for_type(component_type: ComponentType) -> list[str]:
    spider_map = {
        ComponentType.CPU: [
            "techpowerup_cpu_spider",
            "passmark_cpu_spider",
            "wikichip_reference_spider",
            "cpu_world_spider",
            "userbenchmark_spider",
            "tomshardware_spider",
            "anandtech_spider",
            "notebookcheck_spider",
        ],
        ComponentType.GPU: [
            "techpowerup_gpu_spider",
            "passmark_gpu_spider",
            "gpu_specs_spider",
            "userbenchmark_spider",
        ],
        ComponentType.RAM: ["passmark_ram_spider", "userbenchmark_spider"],
        ComponentType.DISK: ["passmark_disk_spider", "userbenchmark_spider"],
        ComponentType.MAINBOARD: [],
    }

    spiders = []
    for spider_name in spider_map.get(component_type, []):
        if spider_name not in BROKEN_SPIDERS and spider_name in SPIDERS:
            spiders.append(spider_name)
    return spiders


def try_all_spiders_for_component(
    model: str, brand: str, component_type: ComponentType, cache: SQLiteCache
) -> list[SpecField]:
    all_specs = []
    seen_keys = set()

    spiders = get_all_spiders_for_type(component_type)

    for spider_name in spiders:
        search_urls = generate_search_urls(
            model, brand, component_type.value, spider_name
        )

        if not search_urls:
            continue

        for url in search_urls[:2]:
            try:
                specs = scrape_specs(
                    spider_name, url, cache=cache, enable_tier2=True, retries=1
                )
                for spec in specs:
                    if spec.key not in seen_keys:
                        seen_keys.add(spec.key)
                        all_specs.append(spec)
            except Exception:
                continue

    return all_specs


def add_component_to_catalog(
    catalog: dict,
    model: str,
    brand: str,
    component_type: ComponentType,
    specs: list[SpecField],
    source_url: str,
) -> None:
    """Add or update component in catalog."""
    comp_type = component_type.value

    if comp_type not in catalog:
        catalog[comp_type] = []

    # Check for existing entry
    for entry in catalog[comp_type]:
        if (
            entry.get("brand", "").lower() == brand.lower()
            and entry.get("model", "").lower() == model.lower()
        ):
            # Merge specs
            for spec in specs:
                if spec.key not in entry.get("specs", {}):
                    entry["specs"][spec.key] = {
                        "value": spec.value,
                        "unit": spec.unit,
                        "sources": [spec.source_name]
                        if spec.source_name
                        else ["Unknown"],
                        "confidence": spec.confidence,
                    }
            entry["validation_date"] = datetime.now().isoformat()
            return

    # Create new entry
    entry = {
        "brand": brand,
        "model": model,
        "part_number": "",
        "validated": True,
        "validation_sources": list(
            set([spec.source_name for spec in specs if spec.source_name])
        ),
        "validation_date": __import__("datetime").datetime.now().isoformat(),
        "confidence": sum(spec.confidence for spec in specs) / len(specs)
        if specs
        else 0,
        "specs": {
            spec.key: {
                "value": spec.value,
                "unit": spec.unit,
                "sources": [spec.source_name] if spec.source_name else ["Unknown"],
                "confidence": spec.confidence,
            }
            for spec in specs
        },
    }

    catalog[comp_type].append(entry)


def main():
    print("=" * 70)
    print("ENRICHMENT WITH ALL REFERENCE SOURCES")
    print("=" * 70)

    catalog = _load_validated_catalog()
    cache = SQLiteCache(str(cache_db_path("enrichment_all.db")))

    with open("hardwarextractor/data/enrichment_index.json") as f:
        enrichment_index = json.load(f)

    results = {"success": 0, "empty": 0, "total": len(enrichment_index)}

    for i, entry in enumerate(enrichment_index):
        model = entry.get("model", "Unknown")
        brand = entry.get("brand", "")
        component_type_str = entry.get("component_type", "CPU")

        component_type = ComponentType(component_type_str)

        spiders = get_all_spiders_for_type(component_type)
        if not spiders:
            print(
                f"[{i + 1}/{len(enrichment_index)}] {brand} {model} ○ (no working spiders)"
            )
            continue

        specs = try_all_spiders_for_component(model, brand, component_type, cache)

        if specs:
            add_component_to_catalog(
                catalog,
                model,
                brand,
                component_type,
                specs,
                entry.get("source_url", ""),
            )
            print(
                f"[{i + 1}/{len(enrichment_index)}] {brand} {model} ✓ specs={len(specs)}"
            )
            results["success"] += 1
        else:
            print(f"[{i + 1}/{len(enrichment_index)}] {brand} {model} ○ specs=0")
            results["empty"] += 1

    # Save catalog
    _save_validated_catalog(catalog)

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total processed: {results['total']}")
    print(f"With specs: {results['success']}")
    print(f"Empty: {results['empty']}")
    print(f"Success rate: {results['success'] / results['total'] * 100:.1f}%")


if __name__ == "__main__":
    main()
