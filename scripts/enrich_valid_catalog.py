#!/usr/bin/env python3
"""Enrich catalog with valid URLs only."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

sys.path.insert(0, ".")

from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.app.paths import cache_db_path
from hardwarextractor.core.events import Event
from hardwarextractor.core.cross_validator import CrossValidator, CrossValidationResult
from hardwarextractor.data.catalog_writer import (
    add_validated_component,
    get_catalog_stats,
)
from hardwarextractor.data.spec_templates import get_template_for_type
from hardwarextractor.models.schemas import (
    ComponentType,
    SpecField,
    SpecStatus,
    SourceTier,
)
from hardwarextractor.scrape.service import scrape_specs


@dataclass
class EnrichmentResult:
    brand: str
    model: str
    part_number: str
    component_type: str
    original_specs: int
    new_specs: int
    total_specs: int
    template_fields: int
    completeness: float
    sources_tried: int
    sources_success: int
    validated: bool
    persisted: bool
    error: Optional[str] = None


class EventCollector:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.events: List[Event] = []

    def __call__(self, event: Event):
        self.events.append(event)

    def reset(self):
        self.events = []


# Spiders known to be broken (site changed or requires JS rendering)
BROKEN_SPIDERS = {
    "amd_cpu_specs_spider",  # AMD site restructured - new URLs needed
    "amd_gpu_chip_spider",  # AMD site restructured - new URLs needed
    "newegg_ram_spider",  # Requires Playwright / anti-bot protection
    "newegg_disk_spider",  # Requires Playwright / anti-bot protection
    "newegg_mainboard_spider",  # Requires Playwright / anti-bot protection
    "pcpartpicker_ram_spider",  # Requires Playwright / anti-bot protection
    "pcpartpicker_disk_spider",  # Requires Playwright / anti-bot protection
    "pcpartpicker_mainboard_spider",  # Requires Playwright / anti-bot protection
}


def load_valid_catalog() -> List[Dict[str, Any]]:
    """Load catalog with valid URLs, excluding broken spiders."""
    path = Path("hardwarextractor/data/enrichment_index.json")
    with open(path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    # Filter out components with broken spiders
    filtered = [c for c in catalog if c.get("spider_name") not in BROKEN_SPIDERS]

    print(
        f"Loaded {len(catalog)} components, filtered to {len(filtered)} (excluded {len(catalog) - len(filtered)} with broken spiders)"
    )
    return filtered


def scrape_official_source(
    component: Dict[str, Any],
    cache: SQLiteCache,
) -> List[SpecField]:
    """Scrape the official source URL for a component."""
    url = component.get("source_url", "")
    spider = component.get("spider_name", "")

    if not url or not spider:
        return []

    try:
        specs = scrape_specs(
            spider,
            url,
            cache=cache,
            enable_tier2=True,
            retries=2,
        )
        return specs or []
    except Exception as e:
        print(f"  Error scraping {url}: {e}")
        return []


def enrich_component(
    component: Dict[str, Any],
    cache: SQLiteCache,
    collector: EventCollector,
) -> EnrichmentResult:
    """Enrich a single component with specs from official source."""
    brand = component.get("brand", "")
    model = component.get("model", "")
    part_number = component.get("part_number", "")
    comp_type = component.get("component_type", "GENERAL")

    collector.reset()

    try:
        component_type = ComponentType(comp_type)
    except ValueError:
        component_type = ComponentType.GENERAL

    template = get_template_for_type(component_type)
    template_fields = len(template)

    # Scrape official source
    official_specs = scrape_official_source(component, cache)
    original_specs = len(official_specs)

    # Create SpecField objects if needed
    specs_list: List[SpecField] = []
    for spec in official_specs:
        if isinstance(spec, dict):
            specs_list.append(
                SpecField(
                    key=spec.get("key", ""),
                    label=spec.get("label", ""),
                    value=spec.get("value"),
                    unit=spec.get("unit"),
                    status=spec.get("status", SpecStatus.EXTRACTED_REFERENCE),
                    source_tier=spec.get("source_tier", SourceTier.CATALOG),
                    source_name=spec.get(
                        "source_name", component.get("source_name", "")
                    ),
                    confidence=spec.get("confidence", 0.9),
                )
            )
        else:
            specs_list.append(spec)

    # Merge specs
    final_specs: Dict[str, SpecField] = {}
    for spec in specs_list:
        if (
            spec.key not in final_specs
            or spec.confidence > final_specs[spec.key].confidence
        ):
            final_specs[spec.key] = spec

    new_specs = len(final_specs)
    completeness = new_specs / template_fields if template_fields > 0 else 0

    # Persist if we have enough specs
    persisted = False
    validated = new_specs >= 5 and completeness >= 0.1

    if validated and final_specs:
        from hardwarextractor.core.cross_validator import ValidatedSpec

        validated_specs_list = [
            ValidatedSpec(
                key=s.key,
                value=s.value,
                sources=[s.source_name or "official"],
                confidence=s.confidence,
                unit=s.unit,
            )
            for s in final_specs.values()
        ]

        cv_result = CrossValidationResult(
            component_input=f"{brand} {model}",
            component_type=component_type,
            validated_specs=validated_specs_list,
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
        original_specs=original_specs,
        new_specs=new_specs,
        total_specs=new_specs,
        template_fields=template_fields,
        completeness=completeness,
        sources_tried=1,
        sources_success=1 if original_specs > 0 else 0,
        validated=validated,
        persisted=persisted,
    )


def run_enrichment(max_components: Optional[int] = None) -> Dict[str, Any]:
    """Run the enrichment process."""
    print("=" * 70)
    print("CATALOG ENRICHMENT - Valid URLs Only")
    print("=" * 70)

    components = load_valid_catalog()
    if max_components:
        components = components[:max_components]

    print(f"Processing {len(components)} components with valid URLs")
    print("=" * 70)

    cache = SQLiteCache(cache_db_path())
    collector = EventCollector()

    results: List[EnrichmentResult] = []
    by_type: Dict[str, List[EnrichmentResult]] = defaultdict(list)

    start_time = datetime.now()

    for i, component in enumerate(components, 1):
        brand = component.get("brand", "?")
        model = component.get("model", "?")
        comp_type = component.get("component_type", "?")

        print(f"\n[{i}/{len(components)}] {comp_type}: {brand} {model}", end=" ... ")
        sys.stdout.flush()

        try:
            result = enrich_component(component, cache, collector)
            results.append(result)
            by_type[comp_type].append(result)

            status = "✓" if result.validated else "○"
            print(
                f"{status} specs={result.new_specs}/{result.template_fields}, persisted={result.persisted}"
            )

        except Exception as e:
            print(f"✗ Error: {str(e)[:50]}")
            results.append(
                EnrichmentResult(
                    brand=brand,
                    model=model,
                    part_number=component.get("part_number", ""),
                    component_type=comp_type,
                    original_specs=0,
                    new_specs=0,
                    total_specs=0,
                    template_fields=0,
                    completeness=0,
                    sources_tried=0,
                    sources_success=0,
                    validated=False,
                    persisted=False,
                    error=str(e),
                )
            )

        # Progress update
        if i % 20 == 0:
            elapsed = (datetime.now() - start_time).seconds
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(components) - i) / rate if rate > 0 else 0
            print(
                f"\n--- Progress: {i}/{len(components)} ({i / len(components) * 100:.0f}%) | ETA: {remaining / 60:.1f} min ---"
            )

    elapsed = (datetime.now() - start_time).seconds

    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "elapsed_seconds": elapsed,
        "components_processed": len(results),
        "summary": {
            "validated": sum(1 for r in results if r.validated),
            "persisted": sum(1 for r in results if r.persisted),
            "errors": sum(1 for r in results if r.error),
            "avg_completeness": sum(r.completeness for r in results) / len(results)
            if results
            else 0,
            "avg_specs": sum(r.new_specs for r in results) / len(results)
            if results
            else 0,
        },
        "by_type": {},
    }

    for comp_type, type_results in by_type.items():
        report["by_type"][comp_type] = {
            "count": len(type_results),
            "validated": sum(1 for r in type_results if r.validated),
            "persisted": sum(1 for r in type_results if r.persisted),
            "avg_specs": sum(r.new_specs for r in type_results) / len(type_results)
            if type_results
            else 0,
            "avg_completeness": sum(r.completeness for r in type_results)
            / len(type_results)
            if type_results
            else 0,
        }

    # Print final report
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    print(f"Time: {elapsed // 60}m {elapsed % 60}s")
    print(f"Components: {len(results)}")
    print(
        f"Validated: {report['summary']['validated']} ({report['summary']['validated'] / len(results) * 100:.1f}%)"
    )
    print(f"Persisted: {report['summary']['persisted']}")
    print(f"Errors: {report['summary']['errors']}")
    print(f"Avg specs: {report['summary']['avg_specs']:.1f}")
    print(f"Avg completeness: {report['summary']['avg_completeness'] * 100:.1f}%")

    print("\n--- By Type ---")
    for comp_type, stats in report["by_type"].items():
        print(
            f"  {comp_type}: {stats['validated']}/{stats['count']} validated, "
            f"{stats['avg_specs']:.1f} specs, {stats['avg_completeness'] * 100:.0f}% complete"
        )

    catalog_stats = get_catalog_stats()
    print("\n--- Validated Catalog ---")
    print(f"Total entries: {catalog_stats['metadata'].get('total_entries', 0)}")

    # Save report
    with open("enrichment_valid_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to enrichment_valid_report.json")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrich catalog with valid URLs")
    parser.add_argument("--max", type=int, help="Max components to process")
    args = parser.parse_args()
    run_enrichment(max_components=args.max)
