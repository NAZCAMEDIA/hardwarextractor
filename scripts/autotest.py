#!/usr/bin/env python3
"""Auto-test script for HardwareXtractor optimization loop.

This script:
1. Tests a list of components not in catalog
2. Records results (success/failure/partial)
3. Generates a report
"""
from __future__ import annotations

import sys
import json
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime

sys.path.insert(0, '.')

from hardwarextractor.classifier.heuristic import classify_component
from hardwarextractor.resolver.resolver import resolve_component
from hardwarextractor.models.schemas import ComponentType


@dataclass
class TestResult:
    """Result of a single component test."""
    component: str
    expected_type: str
    classified_type: str
    classification_confidence: float
    resolved: bool
    candidates_count: int
    best_match: Optional[str]
    best_score: float
    status: str  # SUCCESS, PARTIAL, FAIL
    notes: str


TEST_COMPONENTS = {
    "CPU": [
        "Intel Core i5-14400F",
        "AMD Ryzen 5 7600",
        "Intel Core i9-13900KS",
        "AMD Ryzen 7 5700X3D",
        "Intel Core i7-14700KF",
        "AMD Ryzen 9 9950X",
        "Intel Core Ultra 9 285K",
        "AMD Ryzen 5 5600GT",
        "Intel Core i3-14100",
        "AMD Ryzen 7 8700G",
    ],
    "RAM": [
        "F5-6400J3239G16GX2-TZ5RK",
        "CMK64GX5M2B5200C40",
        "KF560C36BBK2-64",
        "CT2K32G52C42S5",
        "F4-3600C16D-32GTZN",
        "AD5U480032G-DT",
        "BL2K16G32C16U4B",
        "PVS532G480C8K",
        "TF13D432G3200HC16FDC01",
        "FLARE5-6000C32-32GX",
    ],
    "GPU": [
        "RTX 4070 Ti Super",
        "RX 7800 XT",
        "RTX 4060 Ti 16GB",
        "RX 7700 XT",
        "RTX 4080 Super",
        "Intel Arc A750",
        "RTX 4090 D",
        "RX 7600 XT",
        "GeForce RTX 3060 12GB",
        "Radeon RX 6650 XT",
    ],
    "MAINBOARD": [
        "ASUS ROG Maximus Z790 Hero",
        "MSI MEG Z790 ACE",
        "Gigabyte B650E AORUS Master",
        "ASRock X670E Taichi",
        "ASUS TUF Gaming B760M-Plus WiFi",
        "MSI MPG B650 Carbon WiFi",
        "Gigabyte Z790 AORUS Elite AX",
        "ASRock B650 LiveMixer",
        "ASUS ProArt Z790 Creator WiFi",
        "MSI MAG X670E Tomahawk WiFi",
    ],
    "DISK": [
        "MZ-V9E2T0BW",
        "WDS400T3X0E",
        "CT2000P5PSSD8",
        "SFYRD4TK",
        "KSF51280G4X",
        "ALEG-920-2TCS",
        "GP-AG70S2TB",
        "CSSD-F2000GBMP600",
        "7KPNG2TB",
        "DRAM1B2TAV770S",
    ],
}


def run_test(component: str, expected_type: str) -> TestResult:
    """Run a single component test."""
    # Step 1: Classify
    comp_type_enum = ComponentType(expected_type)
    normalized = component.lower()
    classified_type, confidence = classify_component(normalized)

    # Step 2: Resolve (use expected type for resolution)
    resolve_result = resolve_component(component, comp_type_enum)

    # Determine status
    classification_correct = classified_type.value == expected_type
    has_candidates = len(resolve_result.candidates) > 0

    best_match = None
    best_score = 0.0
    if resolve_result.candidates:
        best = resolve_result.candidates[0]
        best_match = best.canonical.get('model', best.canonical.get('part_number', '?'))
        best_score = best.score

    # Status determination
    if classification_correct and has_candidates and best_score >= 0.85:
        status = "SUCCESS"
        notes = f"Clasificación correcta, candidato encontrado ({best_score:.0%})"
    elif classification_correct and has_candidates:
        status = "PARTIAL"
        notes = f"Clasificación correcta, match bajo ({best_score:.0%})"
    elif classification_correct and not has_candidates:
        status = "PARTIAL"
        notes = "Clasificación correcta, sin candidatos en catálogo"
    elif not classification_correct and has_candidates:
        status = "PARTIAL"
        notes = f"Clasificación incorrecta ({classified_type.value}), pero encontró candidato"
    else:
        status = "FAIL"
        notes = f"Clasificación incorrecta ({classified_type.value}), sin candidatos"

    return TestResult(
        component=component,
        expected_type=expected_type,
        classified_type=classified_type.value,
        classification_confidence=confidence,
        resolved=has_candidates,
        candidates_count=len(resolve_result.candidates),
        best_match=best_match,
        best_score=best_score,
        status=status,
        notes=notes,
    )


def run_all_tests() -> List[TestResult]:
    """Run all component tests."""
    results = []

    for comp_type, components in TEST_COMPONENTS.items():
        print(f"\n{'='*60}")
        print(f"Testing {comp_type} ({len(components)} components)")
        print('='*60)

        for component in components:
            result = run_test(component, comp_type)
            results.append(result)

            status_icon = {"SUCCESS": "✓", "PARTIAL": "◐", "FAIL": "✗"}[result.status]
            print(f"{status_icon} {component}")
            print(f"  Clasificado: {result.classified_type} ({result.classification_confidence:.0%})")
            if result.best_match:
                print(f"  Mejor match: {result.best_match} ({result.best_score:.0%})")
            print(f"  Estado: {result.status} - {result.notes}")

    return results


def generate_report(results: List[TestResult]) -> dict:
    """Generate summary report."""
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
            "classification_accuracy": sum(1 for r in type_results if r.classified_type == comp_type) / len(type_results) * 100,
        }

    # Classification accuracy
    correct_classifications = sum(1 for r in results if r.classified_type == r.expected_type)

    return {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total,
            "success": success,
            "partial": partial,
            "fail": fail,
            "success_rate": success / total * 100,
            "partial_or_better_rate": (success + partial) / total * 100,
            "classification_accuracy": correct_classifications / total * 100,
        },
        "by_type": by_type,
        "failures": [asdict(r) for r in results if r.status == "FAIL"],
        "partial": [asdict(r) for r in results if r.status == "PARTIAL"],
    }


def main():
    print("="*60)
    print("HARDWAREXTRACTOR AUTO-TEST")
    print(f"Testing {sum(len(v) for v in TEST_COMPONENTS.values())} components")
    print("="*60)

    results = run_all_tests()
    report = generate_report(results)

    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)

    s = report["summary"]
    print(f"\nTotal tests: {s['total_tests']}")
    print(f"✓ SUCCESS: {s['success']} ({s['success_rate']:.1f}%)")
    print(f"◐ PARTIAL: {s['partial']} ({(s['partial_or_better_rate'] - s['success_rate']):.1f}%)")
    print(f"✗ FAIL: {s['fail']} ({100 - s['partial_or_better_rate']:.1f}%)")
    print(f"\nClasificación correcta: {s['classification_accuracy']:.1f}%")

    print("\nPor tipo de componente:")
    for comp_type, stats in report["by_type"].items():
        print(f"  {comp_type}: {stats['success']}/{stats['total']} success, "
              f"clasificación {stats['classification_accuracy']:.0f}%")

    if report["failures"]:
        print("\nFALLOS:")
        for f in report["failures"]:
            print(f"  - {f['component']}: {f['notes']}")

    # Save report
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("\nReporte guardado en test_report.json")

    return report


if __name__ == "__main__":
    main()
