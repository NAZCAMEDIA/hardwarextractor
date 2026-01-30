#!/usr/bin/env python3
"""Ralph Wiggum Loop - Real auto-optimization using HardwareXtractor pipeline.

This script implements the Ralph Wiggum pattern using the real orchestrator:
1. Test components not in catalog
2. Uses full pipeline: classify -> resolve -> web search -> scrape
3. Validates extracted data
4. Iterates until 100% success or max iterations

Promise: All 50 components must have valid specs from official or web sources.
"""
from __future__ import annotations

import sys
import json
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

sys.path.insert(0, '.')

from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.app.paths import cache_db_path
from hardwarextractor.core.events import Event


# 50 components NOT in the catalog - testing web search capability
TEST_COMPONENTS = {
    "CPU": [
        "Intel Core i5-14600KF",
        "AMD Ryzen 5 9600X",
        "Intel Core i9-14900KS",
        "AMD Ryzen 7 9700X",
        "Intel Core Ultra 7 265K",
        "AMD Ryzen 9 7900X3D",
        "Intel Core i7-13700F",
        "AMD Ryzen 5 8600G",
        "Intel Core i5-13400",
        "AMD Ryzen 9 7945HX",
    ],
    "RAM": [
        "CMK32GX5M2B6400C32",
        "F5-6400J3239G16GX2-TZ5NR",
        "KF564C32BBK2-32",
        "CT2K16G56C46U5",
        "F5-6000U3636E16GX2-RS5K",
        "AD5U560016G-DT",
        "CMW32GX5M2A4800C40",
        "PVB532G600C3K",
        "TLZGD564G6400HC32DC01",
        "KF548C38BBK2-32",
    ],
    "GPU": [
        "GeForce RTX 5090",
        "Radeon RX 9070 XT",
        "GeForce RTX 4070 Super",
        "Radeon RX 7900 GRE",
        "Intel Arc B580",
        "GeForce RTX 3070 Ti",
        "Radeon RX 6800",
        "GeForce RTX 4060",
        "Intel Arc A580",
        "Radeon RX 7600",
    ],
    "MAINBOARD": [
        "ASUS ROG Strix Z890-E Gaming",
        "MSI MEG Z890 ACE",
        "Gigabyte B850 AORUS Elite",
        "ASRock X870E Taichi Lite",
        "ASUS TUF Gaming B650-Plus WiFi",
        "MSI MAG B850 Tomahawk WiFi",
        "Gigabyte X870 AORUS Elite WiFi7",
        "ASRock B850M Pro RS",
        "ASUS ROG Crosshair X870E Hero",
        "MSI PRO B850-P WiFi",
    ],
    "DISK": [
        "Samsung 990 EVO Plus 2TB",
        "WD Black SN850X 4TB",
        "Crucial T705 2TB",
        "Seagate FireCuda 540 2TB",
        "Kingston KC3000 4TB",
        "SK Hynix Platinum P41 2TB",
        "Corsair MP700 PRO 2TB",
        "Sabrent Rocket 5 2TB",
        "ADATA Legend 970 2TB",
        "Gigabyte AORUS Gen5 12000 2TB",
    ],
}


# Minimum required specs per component type for SUCCESS
# Note: brand and model can be inferred from part number
MIN_REQUIRED_SPECS = {
    "CPU": ["brand", "model"],
    "RAM": ["brand", "model"],  # ram.type is nice-to-have
    "GPU": ["brand", "model"],
    "MAINBOARD": ["brand", "model"],
    "DISK": ["brand", "model"],
}


@dataclass
class TestResult:
    """Result of testing a single component."""
    component: str
    expected_type: str
    classified_type: str
    classification_confidence: float
    source: str  # "catalog", "web_search", "catalog_fallback", "failed"
    source_url: str
    specs_count: int
    key_specs: Dict[str, Any]
    status: str  # "SUCCESS", "PARTIAL", "FAIL"
    notes: str
    iteration: int = 1


class EventCollector:
    """Collects events from orchestrator for analysis."""

    def __init__(self):
        self.events: List[Event] = []
        self.source_used: str = "unknown"
        self.source_url: str = ""
        self.specs_count: int = 0

    def __call__(self, event: Event):
        self.events.append(event)
        # Event.type is EventType enum, use .value for string comparison
        if event.type.value == "source_success":
            self.source_used = event.source_name or "unknown"
            self.specs_count = event.data.get("specs_count", 0) if event.data else 0
        if event.type.value == "source_trying":
            self.source_url = event.data.get("url", "") if event.data else ""

    def reset(self):
        self.events = []
        self.source_used = "unknown"
        self.source_url = ""
        self.specs_count = 0


def run_single_test(
    orchestrator: Orchestrator,
    collector: EventCollector,
    component: str,
    expected_type: str,
    iteration: int = 1,
) -> TestResult:
    """Run a single component test using full orchestrator pipeline."""

    collector.reset()

    # Run orchestrator
    events = orchestrator.process_input(component)

    # Check if we need to auto-select a candidate
    for event in events:
        if event.status == "NEEDS_USER_SELECTION" and event.candidates:
            # Auto-select the first (best) candidate
            more_events = orchestrator.select_candidate(0)
            events.extend(more_events)
            break

    # Analyze results
    classified_type = "GENERAL"
    confidence = 0.0
    source = "failed"
    source_url = collector.source_url
    specs_count = 0
    key_specs = {}
    status = "FAIL"
    notes = ""

    # Extract classification from events
    for event in events:
        if event.status == "CLASSIFY_COMPONENT":
            # Parse from log
            if "Classified as" in event.log:
                parts = event.log.split("Classified as ")[1]
                classified_type = parts.split(" ")[0]
                if "confidence:" in parts:
                    conf_str = parts.split("confidence: ")[1].rstrip("%)")
                    try:
                        confidence = float(conf_str.replace("%", "")) / 100
                    except ValueError:
                        pass

        if event.status == "WEB_SEARCH":
            source = "web_search"

        if event.status == "WEB_SEARCH_COMPLETE":
            source = "web_search"

        if event.component_result:
            component_result = event.component_result
            source_url = component_result.source_url
            specs_count = len(component_result.specs)

            # Determine source from tier
            tier = component_result.source_tier.value
            if tier == "OFFICIAL":
                source = "official"
            elif tier == "REFERENCE":
                source = "web_search"
            elif tier == "CATALOG":
                source = "catalog_fallback"

            # Extract brand/model from canonical first
            if component_result.canonical:
                if "brand" in component_result.canonical:
                    key_specs["brand"] = component_result.canonical["brand"]
                if "model" in component_result.canonical:
                    key_specs["model"] = component_result.canonical["model"]

            # Extract additional specs
            for spec in component_result.specs:
                key_specs[spec.key] = spec.value

    # Validate: check if we have minimum required specs
    required = MIN_REQUIRED_SPECS.get(expected_type, ["brand", "model"])
    missing = [r for r in required if r not in key_specs]

    classification_correct = classified_type == expected_type

    if specs_count > 0 and not missing:
        status = "SUCCESS"
        notes = f"Datos completos desde {source} ({specs_count} specs)"
    elif specs_count > 0:
        status = "PARTIAL"
        notes = f"Datos parciales desde {source}, faltan: {', '.join(missing)}"
    elif not classification_correct:
        status = "FAIL"
        notes = f"Clasificacion incorrecta: {classified_type} (esperado {expected_type})"
    else:
        status = "FAIL"
        notes = "Sin datos encontrados"

    return TestResult(
        component=component,
        expected_type=expected_type,
        classified_type=classified_type,
        classification_confidence=confidence,
        source=source,
        source_url=source_url,
        specs_count=specs_count,
        key_specs=key_specs,
        status=status,
        notes=notes,
        iteration=iteration,
    )


def run_ralph_loop(max_iterations: int = 3, verbose: bool = True) -> Dict:
    """Run the Ralph Wiggum optimization loop.

    Continues until 100% success or max iterations reached.
    """
    print("=" * 70)
    print("RALPH WIGGUM LOOP - HARDWAREXTRACTOR AUTO-OPTIMIZATION")
    print("=" * 70)
    total_components = sum(len(v) for v in TEST_COMPONENTS.values())
    print(f"Testing {total_components} components")
    print(f"Max iterations: {max_iterations}")
    print("Promise: 100% components with valid specs")
    print("=" * 70)

    # Initialize
    cache = SQLiteCache(cache_db_path())
    collector = EventCollector()
    orchestrator = Orchestrator(cache=cache, event_callback=collector)

    all_results: List[TestResult] = []
    iteration = 1

    while iteration <= max_iterations:
        print(f"\n{'='*70}")
        print(f"ITERATION {iteration}")
        print("=" * 70)

        iteration_results = []

        for comp_type, components in TEST_COMPONENTS.items():
            print(f"\n--- {comp_type} ({len(components)} components) ---")

            for component in components:
                result = run_single_test(
                    orchestrator, collector, component, comp_type, iteration
                )
                iteration_results.append(result)

                if verbose:
                    status_icon = {"SUCCESS": "✓", "PARTIAL": "◐", "FAIL": "✗"}[result.status]
                    print(f"{status_icon} {component}")
                    print(f"    Tipo: {result.classified_type} ({result.classification_confidence:.0%})")
                    print(f"    Fuente: {result.source}")
                    if result.key_specs:
                        brand = result.key_specs.get("brand", "?")
                        model = result.key_specs.get("model", "?")
                        print(f"    Datos: {brand} {model}")
                    print(f"    Estado: {result.status} - {result.notes}")

                # Brief pause to avoid rate limiting
                time.sleep(0.5)

        # Calculate success rate
        success_count = sum(1 for r in iteration_results if r.status == "SUCCESS")
        partial_count = sum(1 for r in iteration_results if r.status == "PARTIAL")
        fail_count = sum(1 for r in iteration_results if r.status == "FAIL")
        total = len(iteration_results)
        success_rate = success_count / total * 100

        print(f"\n--- Iteration {iteration} Summary ---")
        print(f"SUCCESS: {success_count}/{total} ({success_rate:.1f}%)")
        print(f"PARTIAL: {partial_count}/{total}")
        print(f"FAIL: {fail_count}/{total}")

        all_results = iteration_results

        # Check promise: 100% success
        if success_rate >= 100.0:
            print(f"\n{'='*70}")
            print("PROMISE FULFILLED! 100% success rate achieved!")
            print("=" * 70)
            break

        # Show failures for debugging
        failed = [r for r in iteration_results if r.status == "FAIL"]
        if failed and verbose:
            print(f"\nFailed components ({len(failed)}):")
            for f in failed[:5]:
                print(f"  - {f.component}: {f.notes}")

        iteration += 1

        if iteration <= max_iterations:
            print(f"\nContinuing to iteration {iteration}...")
            time.sleep(2)

    # Generate final report
    return generate_report(all_results, iteration)


def generate_report(results: List[TestResult], iterations: int) -> Dict:
    """Generate final report."""
    total = len(results)
    success = sum(1 for r in results if r.status == "SUCCESS")
    partial = sum(1 for r in results if r.status == "PARTIAL")
    fail = sum(1 for r in results if r.status == "FAIL")

    # By type
    by_type = {}
    for comp_type in TEST_COMPONENTS.keys():
        type_results = [r for r in results if r.expected_type == comp_type]
        by_type[comp_type] = {
            "total": len(type_results),
            "success": sum(1 for r in type_results if r.status == "SUCCESS"),
            "partial": sum(1 for r in type_results if r.status == "PARTIAL"),
            "fail": sum(1 for r in type_results if r.status == "FAIL"),
            "classification_accuracy": sum(
                1 for r in type_results if r.classified_type == comp_type
            ) / len(type_results) * 100,
        }

    # By source
    by_source = {}
    for source in ["official", "web_search", "catalog_fallback", "failed"]:
        source_results = [r for r in results if r.source == source]
        by_source[source] = len(source_results)

    report = {
        "timestamp": datetime.now().isoformat(),
        "iterations": iterations,
        "promise": "100% components with valid specs",
        "promise_met": success == total,
        "summary": {
            "total_tests": total,
            "success": success,
            "partial": partial,
            "fail": fail,
            "success_rate": success / total * 100,
            "classification_accuracy": sum(
                1 for r in results if r.classified_type == r.expected_type
            ) / total * 100,
        },
        "by_type": by_type,
        "by_source": by_source,
        "failures": [asdict(r) for r in results if r.status == "FAIL"],
        "all_results": [asdict(r) for r in results],
    }

    # Print final report
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)

    print(f"\nIterations: {iterations}")
    print(f"Promise: {report['promise']}")
    print(f"Promise met: {'YES' if report['promise_met'] else 'NO'}")

    print(f"\n--- Summary ---")
    print(f"Total tests: {total}")
    print(f"✓ SUCCESS: {success} ({success/total*100:.1f}%)")
    print(f"◐ PARTIAL: {partial} ({partial/total*100:.1f}%)")
    print(f"✗ FAIL: {fail} ({fail/total*100:.1f}%)")
    print(f"Classification accuracy: {report['summary']['classification_accuracy']:.1f}%")

    print(f"\n--- By Source ---")
    for source, count in by_source.items():
        print(f"  {source}: {count}")

    print(f"\n--- By Component Type ---")
    for comp_type, stats in by_type.items():
        print(f"  {comp_type}: {stats['success']}/{stats['total']} success, "
              f"classification {stats['classification_accuracy']:.0f}%")

    if report["failures"]:
        print(f"\n--- Failures ({len(report['failures'])}) ---")
        for f in report["failures"][:10]:
            print(f"  - {f['component']}: {f['notes']}")

    # Save report
    with open("ralph_loop_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport saved to ralph_loop_report.json")

    return report


if __name__ == "__main__":
    report = run_ralph_loop(max_iterations=3, verbose=True)

    # Exit with error code if promise not met
    sys.exit(0 if report["promise_met"] else 1)
