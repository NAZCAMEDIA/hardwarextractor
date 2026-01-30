#!/usr/bin/env python3
"""Catalog enrichment using working sources only.
Strategy: Use official sources that work, skip broken sources.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict

sys.path.insert(0, ".")

from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.app.paths import cache_db_path
from hardwarextractor.models.schemas import ComponentType, SpecField
from hardwarextractor.scrape.service import SPIDERS, scrape_specs
from hardwarextractor.data.catalog_writer import (
    add_validated_component,
    get_catalog_stats,
)


@dataclass
class EnrichmentResult:
    brand: str
    model: str
    part_number: str
    component_type: str
    specs_found: int
    persisted: bool
    error: Optional[str] = None


# Spiders that are broken and should be excluded
BROKEN_SPIDERS = {
    "amd_cpu_specs_spider",  # AMD site restructured - needs new spider
    "amd_gpu_chip_spider",  # AMD site restructured - needs new spider
    "newegg_ram_spider",  # Anti-bot protection
    "newegg_disk_spider",  # Anti-bot protection
    "newegg_mainboard_spider",  # Anti-bot protection
    "pcpartpicker_ram_spider",  # Anti-bot protection
    "pcpartpicker_disk_spider",  # Anti-bot protection
    "pcpartpicker_mainboard_spider",  # Anti-bot protection
}


def scrape_component(component: Dict[str, Any], cache: SQLiteCache) -> List[SpecField]:
    """Scrape a component using its official source."""
    url = component.get("source_url", "")
    spider_name = component.get("spider_name", "")

    if not url or not spider_name:
        return []

    if spider_name in BROKEN_SPIDERS:
        return []

    if spider_name not in SPIDERS:
        return []

    try:
        specs = scrape_specs(
            spider_name,
            url,
            cache=cache,
            enable_tier2=True,
            retries=1,
        )
        return specs or []
    except Exception as e:
        print(f"  Error: {e}")
        return []


def enrich_component(component: Dict[str, Any], cache: SQLiteCache) -> EnrichmentResult:
    """Enrich a single component."""
    brand = component.get("brand", "")
    model = component.get("model", "")
    part_number = component.get("part_number", "")
    comp_type = component.get("component_type", "GENERAL")

    try:
        component_type = ComponentType(comp_type)
    except ValueError:
        component_type = ComponentType.GENERAL

    # Scrape from official source
    specs = scrape_component(component, cache)

    # Minimum threshold for persistence
    min_specs = 5 if comp_type in ("CPU", "GPU") else 3

    # Persist if we have enough specs
    persisted = False
    if len(specs) >= min_specs:
        from hardwarextractor.core.cross_validator import (
            CrossValidationResult,
            ValidatedSpec,
        )

        validated_specs = [
            ValidatedSpec(
                key=s.key,
                value=s.value,
                sources=[component.get("source_name", "official")],
                confidence=s.confidence,
                unit=s.unit,
            )
            for s in specs
            if s.key  # Only specs with a key
        ]

        if len(validated_specs) >= min_specs:
            cv_result = CrossValidationResult(
                component_input=f"{brand} {model}",
                component_type=component_type,
                validated_specs=validated_specs,
                all_source_results=[],
                consensus_reached=True,
                should_persist=True,
            )
            persisted = add_validated_component(cv_result, brand, model, part_number)

    return EnrichmentResult(
        brand=brand,
        model=model,
        part_number=part_number,
        component_type=comp_type,
        specs_found=len(specs),
        persisted=persisted,
    )


def load_catalog() -> List[Dict[str, Any]]:
    """Load the catalog, excluding broken spiders."""
    path = Path("hardwarextractor/data/enrichment_index.json")
    with open(path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Filter out broken spiders
    filtered = [c for c in catalog if c.get("spider_name") not in BROKEN_SPIDERS]
    excluded = len(catalog) - len(filtered)

    print(
        f"Loaded {len(catalog)} components, filtered to {len(filtered)} (excluded {excluded} with broken spiders)"
    )
    return filtered


def run_enrichment(max_components: Optional[int] = None) -> Dict[str, Any]:
    """Run enrichment using working sources only."""
    print("=" * 70)
    print("CATALOG ENRICHMENT - Working Sources Only")
    print("=" * 70)

    catalog = load_catalog()
    if max_components:
        catalog = catalog[:max_components]

    print(f"Processing {len(catalog)} components")
    print("=" * 70)

    cache = SQLiteCache(cache_db_path())
    results: List[EnrichmentResult] = []
    by_type: Dict[str, List[EnrichmentResult]] = defaultdict(list)

    start_time = datetime.now()

    for i, component in enumerate(catalog, 1):
        brand = component.get("brand", "?")
        model = component.get("model", "?")
        comp_type = component.get("component_type", "?")

        print(f"\n[{i}/{len(catalog)}] {comp_type}: {brand} {model}", end=" ")
        sys.stdout.flush()

        try:
            result = enrich_component(component, cache)
            results.append(result)
            by_type[comp_type].append(result)

            status = "✓" if result.persisted else "○"
            print(f"{status} specs={result.specs_found}")

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            results.append(
                EnrichmentResult(
                    brand=brand,
                    model=model,
                    part_number=component.get("part_number", ""),
                    component_type=comp_type,
                    specs_found=0,
                    persisted=False,
                    error=str(e),
                )
            )

        # Progress update
        if i % 50 == 0 and i > 0:
            elapsed = (datetime.now() - start_time).seconds
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(catalog) - i) / rate if rate > 0 else 0
            print(
                f"\n--- Progress: {i}/{len(catalog)} ({i / len(catalog) * 100:.0f}%) | ETA: {remaining / 60:.1f} min ---"
            )

    elapsed = (datetime.now() - start_time).seconds

    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "components_processed": len(results),
        "summary": {
            "with_specs": sum(1 for r in results if r.specs_found > 0),
            "persisted": sum(1 for r in results if r.persisted),
            "errors": sum(1 for r in results if r.error),
            "avg_specs": sum(r.specs_found for r in results) / len(results)
            if results
            else 0,
        },
        "by_type": {},
    }

    for comp_type, type_results in by_type.items():
        report["by_type"][comp_type] = {
            "count": len(type_results),
            "with_specs": sum(1 for r in type_results if r.specs_found > 0),
            "persisted": sum(1 for r in type_results if r.persisted),
            "avg_specs": sum(r.specs_found for r in type_results) / len(type_results)
            if type_results
            else 0,
        }

    # Print final report
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(f"Time: {elapsed // 60}m {elapsed % 60}s")
    print(f"Components: {len(results)}")
    print(f"With specs: {report['summary']['with_specs']}")
    print(f"Persisted: {report['summary']['persisted']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Avg specs: {report['summary']['avg_specs']:.1f}")

    print("\n--- By Type ---")
    for comp_type, stats in report["by_type"].items():
        print(
            f"  {comp_type}: {stats['with_specs']}/{stats['count']} with specs, {stats['persisted']} persisted, {stats['avg_specs']:.1f} avg specs"
        )

    catalog_stats = get_catalog_stats()
    print("\n--- Validated Catalog ---")
    print(f"Total entries: {catalog_stats['metadata'].get('total_entries', 0)}")

    # Save report
    with open("enrichment_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to enrichment_report.json")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Catalog enrichment")
    parser.add_argument("--max", type=int, help="Max components to process")
    args = parser.parse_args()
    run_enrichment(max_components=args.max)
