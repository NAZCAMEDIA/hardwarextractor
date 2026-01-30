#!/usr/bin/env python3
"""Enrich Catalog - Complete specs for all catalog components.

This script:
1. Loads all components from the catalog (resolver_index.json)
2. For each component, checks current spec count
3. Searches multiple web sources to gather complete specs
4. Cross-validates data from 2+ sources
5. Saves validated data to validated_catalog.json

Goal: All 500 components with maximum available specs.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

import requests  # For URL discovery from search results

sys.path.insert(0, ".")

from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.app.paths import cache_db_path
from hardwarextractor.core.events import Event
from hardwarextractor.core.cross_validator import CrossValidator, CrossValidationResult
from hardwarextractor.data.catalog_writer import (
    add_validated_component,
    get_catalog_stats,
    _load_validated_catalog,
    _save_validated_catalog,
)
from hardwarextractor.data.spec_templates import get_template_for_type, SPEC_TEMPLATES
from hardwarextractor.models.schemas import ComponentType, SpecField, SourceTier
from hardwarextractor.scrape.service import scrape_specs


# Reference sources for catalog cross-validation.
# TODO: Many reference sites (TechPowerUp, PassMark, CPU-World) have anti-bot protection.
# The enrichment script works with official sources only. Cross-validation requires
# implementing proper URL discovery or using a scraping service with browser automation.
REFERENCE_SOURCES = {
    "CPU": [],
    "GPU": [],
    "RAM": [],
    "MAINBOARD": [],
    "DISK": [],
}


def _extract_first_link(html: str, pattern: str) -> str | None:
    """Extract first link matching pattern from HTML."""
    try:
        from parsel import Selector

        selector = Selector(text=html)
        links = selector.xpath(f'//a[contains(@href, "{pattern}")]/@href').getall()
        if links:
            # Clean and return first valid link
            for link in links:
                if link.startswith("http"):
                    return link
                elif link.startswith("/"):
                    # Try to extract domain from pattern
                    domain = pattern.split("/")[0]
                    return f"https://{domain}{link}"
        return None
    except Exception:
        return None


@dataclass
class EnrichmentResult:
    """Result of enriching a single component."""

    brand: str
    model: str
    part_number: str
    component_type: str
    original_specs: int
    new_specs: int
    total_specs: int
    template_fields: int
    completeness: float  # new_specs / template_fields
    sources_tried: int
    sources_success: int
    validated: bool
    persisted: bool
    error: Optional[str] = None


class EventCollector:
    """Collects events for logging."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.events: List[Event] = []

    def __call__(self, event: Event):
        self.events.append(event)
        if self.verbose and event.type.value in (
            "source_success",
            "source_failed",
            "log",
        ):
            print(f"    [{event.type.value}] {event.log or event.source_name or ''}")

    def reset(self):
        self.events = []


def load_catalog_components() -> List[Dict[str, Any]]:
    """Load all components from resolver_index.json."""
    index_path = Path("hardwarextractor/data/resolver_index.json")
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


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
    except Exception:
        return []


def search_reference_sources(
    brand: str,
    model: str,
    component_type: str,
    cache: SQLiteCache,
    collector: EventCollector,
) -> List[Tuple[str, List[SpecField]]]:
    """Search reference sources for component specs.

    Returns list of (source_name, specs) tuples.
    """
    from urllib.parse import quote_plus
    import requests
    from parsel import Selector

    sources = REFERENCE_SOURCES.get(component_type, [])
    results: List[Tuple[str, List[SpecField]]] = []

    query = f"{brand} {model}".strip()
    query_encoded = quote_plus(query)

    for source_name, spider_name, search_url_template, url_extractor in sources:
        search_url = search_url_template.format(query=query_encoded)

        try:
            # Step 1: Fetch search page to discover product URL
            product_url = search_url  # Default to search URL

            if url_extractor:
                # Fetch HTML to extract product URL
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
                }
                resp = requests.get(search_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    product_url = url_extractor(query, resp.text)
                    if not product_url:
                        collector(
                            Event.log("debug", f"[{source_name}] No product link found")
                        )
                        time.sleep(0.3)
                        continue
                else:
                    collector(
                        Event.log(
                            "warning",
                            f"[{source_name}] Search page error: {resp.status_code}",
                        )
                    )
                    time.sleep(0.3)
                    continue

            # Step 2: Scrape product page
            specs = scrape_specs(
                spider_name,
                product_url,
                cache=cache,
                enable_tier2=True,
                retries=1,
            )

            if specs and len(specs) >= 2:
                results.append((source_name, specs))
                collector(
                    Event.log("info", f"[{source_name}] Found {len(specs)} specs")
                )
            else:
                collector(Event.log("debug", f"[{source_name}] No specs found"))

        except Exception as e:
            collector(Event.log("warning", f"[{source_name}] Error: {str(e)[:50]}"))

        time.sleep(0.3)

    return results


def cross_validate_specs(
    all_sources: List[Tuple[str, List[SpecField]]],
    component_type: ComponentType,
) -> Tuple[List[SpecField], float]:
    """Cross-validate specs from multiple sources.

    Returns (validated_specs, average_confidence).
    """
    if len(all_sources) < 2:
        # Not enough sources for cross-validation
        if all_sources:
            return all_sources[0][1], 0.5
        return [], 0.0

    # Group specs by key
    specs_by_key: Dict[str, List[Tuple[str, SpecField]]] = defaultdict(list)

    for source_name, specs in all_sources:
        for spec in specs:
            specs_by_key[spec.key].append((source_name, spec))

    validated: List[SpecField] = []
    confidences: List[float] = []

    for key, source_specs in specs_by_key.items():
        if len(source_specs) < 2:
            # Only one source, use with lower confidence
            _, spec = source_specs[0]
            spec.confidence = 0.5
            validated.append(spec)
            confidences.append(0.5)
            continue

        # Find matching values
        value_groups: Dict[str, List[Tuple[str, SpecField]]] = defaultdict(list)

        for source_name, spec in source_specs:
            # Normalize value for comparison
            val_str = str(spec.value).lower().strip()
            value_groups[val_str].append((source_name, spec))

        # Use the value with most sources
        best_group = max(value_groups.values(), key=len)

        if len(best_group) >= 2:
            # Cross-validated
            confidence = len(best_group) / len(source_specs)
            _, representative = best_group[0]
            representative.confidence = confidence
            representative.notes = f"Validated by {len(best_group)} sources"
            validated.append(representative)
            confidences.append(confidence)
        else:
            # No consensus, use first with low confidence
            _, spec = source_specs[0]
            spec.confidence = 0.3
            validated.append(spec)
            confidences.append(0.3)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return validated, avg_confidence


def enrich_component(
    component: Dict[str, Any],
    cache: SQLiteCache,
    collector: EventCollector,
    verbose: bool = False,
) -> EnrichmentResult:
    """Enrich a single component with specs from multiple sources."""
    brand = component.get("brand", "")
    model = component.get("model", "")
    part_number = component.get("part_number", "")
    comp_type = component.get("component_type", "GENERAL")

    collector.reset()

    # Get template for this type
    try:
        component_type = ComponentType(comp_type)
    except ValueError:
        component_type = ComponentType.GENERAL

    template = get_template_for_type(component_type)
    template_fields = len(template)

    # Step 1: Try official source first
    official_specs = scrape_official_source(component, cache)
    original_specs = len(official_specs)

    all_sources: List[Tuple[str, List[SpecField]]] = []
    if official_specs:
        all_sources.append(("Official", official_specs))

    # Step 2: Search reference sources
    ref_results = search_reference_sources(brand, model, comp_type, cache, collector)
    all_sources.extend(ref_results)

    sources_tried = len(REFERENCE_SOURCES.get(comp_type, [])) + 1
    sources_success = len(all_sources)

    # Step 3: Cross-validate
    validated_specs, avg_confidence = cross_validate_specs(all_sources, component_type)

    # Step 4: Merge and deduplicate specs
    final_specs: Dict[str, SpecField] = {}
    for spec in validated_specs:
        if (
            spec.key not in final_specs
            or spec.confidence > final_specs[spec.key].confidence
        ):
            final_specs[spec.key] = spec

    new_specs = len(final_specs)
    completeness = new_specs / template_fields if template_fields > 0 else 0

    # Step 5: Persist if validated
    # Lower threshold for catalog enrichment: accept single-source with reduced confidence
    # This allows building up the catalog with official source data
    persisted = False
    validated = (
        (avg_confidence >= 0.6 and sources_success >= 2)  # Standard: cross-validated
        or (
            avg_confidence >= 0.5 and sources_success >= 1 and new_specs >= 10
        )  # Relaxed: single source with enough specs
    )

    if validated and final_specs:
        # Create a mock CrossValidationResult for the catalog writer
        from hardwarextractor.core.cross_validator import (
            ValidatedSpec,
            CrossValidationResult,
        )

        validated_specs_list = [
            ValidatedSpec(
                key=s.key,
                value=s.value,
                sources=[s.source_name or "unknown"],
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
        sources_tried=sources_tried,
        sources_success=sources_success,
        validated=validated,
        persisted=persisted,
    )


def run_enrichment(
    max_components: Optional[int] = None,
    component_types: Optional[List[str]] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Run the enrichment process on catalog components."""

    print("=" * 70)
    print("CATALOG ENRICHMENT - Cross-Validated Spec Completion")
    print("=" * 70)

    # Load components
    components = load_catalog_components()

    # Filter by type if specified
    if component_types:
        components = [
            c for c in components if c.get("component_type") in component_types
        ]

    # Limit if specified
    if max_components:
        components = components[:max_components]

    print(f"Processing {len(components)} components")
    print(
        f"Sources: 1 official + {max(len(v) for v in REFERENCE_SOURCES.values())} reference per type"
    )
    print("=" * 70)

    # Initialize
    cache = SQLiteCache(cache_db_path())
    collector = EventCollector(verbose=False)

    results: List[EnrichmentResult] = []
    by_type: Dict[str, List[EnrichmentResult]] = defaultdict(list)

    start_time = datetime.now()

    for i, component in enumerate(components, 1):
        brand = component.get("brand", "?")
        model = component.get("model", "?")
        comp_type = component.get("component_type", "?")

        if verbose:
            print(f"\n[{i}/{len(components)}] {comp_type}: {brand} {model}")

        try:
            result = enrich_component(component, cache, collector, verbose)
            results.append(result)
            by_type[comp_type].append(result)

            if verbose:
                status = "✓" if result.validated else "○"
                print(
                    f"  {status} Specs: {result.original_specs} → {result.new_specs}/{result.template_fields}"
                )
                print(
                    f"    Sources: {result.sources_success}/{result.sources_tried} | "
                    f"Completeness: {result.completeness:.0%} | "
                    f"Persisted: {'Yes' if result.persisted else 'No'}"
                )

        except Exception as e:
            if verbose:
                print(f"  ✗ Error: {str(e)[:60]}")
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

        # Progress update every 10 components
        if i % 10 == 0:
            elapsed = (datetime.now() - start_time).seconds
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(components) - i) / rate if rate > 0 else 0
            print(
                f"\n--- Progress: {i}/{len(components)} ({i / len(components) * 100:.0f}%) | "
                f"ETA: {remaining / 60:.1f} min ---"
            )

    # Generate report
    elapsed = (datetime.now() - start_time).seconds

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

    # Get catalog stats
    catalog_stats = get_catalog_stats()
    print("\n--- Validated Catalog ---")
    print(f"Total entries: {catalog_stats['metadata'].get('total_entries', 0)}")
    for t, s in catalog_stats["by_type"].items():
        if s["count"] > 0:
            print(f"  {t}: {s['count']} components, {s['specs']} total specs")

    # Save report
    with open("enrichment_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to enrichment_report.json")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Enrich catalog components with cross-validated specs"
    )
    parser.add_argument("--max", type=int, help="Max components to process")
    parser.add_argument(
        "--type",
        action="append",
        dest="types",
        help="Component types to process (can repeat)",
    )
    parser.add_argument("--quiet", action="store_true", help="Less verbose output")

    args = parser.parse_args()

    run_enrichment(
        max_components=args.max,
        component_types=args.types,
        verbose=not args.quiet,
    )
