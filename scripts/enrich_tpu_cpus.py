#!/usr/bin/env python3
"""Enrich TechPowerUp CPU data from saved links."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, ".")

from hardwarextractor.models.schemas import ComponentType
from hardwarextractor.data.catalog_writer import (
    _load_validated_catalog,
    _save_validated_catalog,
)

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def extract_cpu_specs_from_html(html: str) -> dict[str, Any]:
    """Extract CPU specs from blocked HTML using og:description."""
    from parsel import Selector

    sel = Selector(text=html)

    specs = {}

    # Get og:description
    og_desc = sel.css('meta[property="og:description"]::attr(content)').get()
    if og_desc:
        parts = [p.strip() for p in og_desc.split(",")]

        for part in parts:
            part_lower = part.lower()

            # Codename
            if part == parts[0]:
                specs["cpu.codename"] = part

            # Cores
            if "cores" in part_lower and "threads" not in part_lower:
                match = re.search(r"(\d+)\s*cores", part_lower)
                if match:
                    specs["cpu.cores_physical"] = int(match.group(1))

            # Threads
            if "threads" in part_lower:
                match = re.search(r"(\d+)\s*threads", part_lower)
                if match:
                    specs["cpu.threads_logical"] = int(match.group(1))

            # Clock
            if "ghz" in part_lower or "mhz" in part_lower:
                match = re.search(r"([\d.]+)\s*(ghz|mhz)", part_lower)
                if match:
                    value = float(match.group(1))
                    unit = match.group(2).upper()
                    if "ghz" in part_lower:
                        value = int(value * 1000)
                        unit = "MHz"
                    specs["cpu.base_clock_mhz"] = value
                    specs["cpu.base_clock_mhz_unit"] = unit

            # TDP
            if "w" in part_lower and re.search(r"\d+\s*w", part_lower):
                match = re.search(r"(\d+)\s*w", part_lower)
                if match:
                    specs["cpu.tdp_w"] = int(match.group(1))

    return specs


def enrich_from_tpu_links():
    """Enrich catalog with TechPowerUp CPU data."""
    print("=" * 70)
    print("TECHPOWERUP CPU ENRICHMENT")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    # Load links
    links_file = Path("scripts/tpu_cpu_links.txt")
    if not links_file.exists():
        print("[W] No links file found. Run get_tpu_links.py first.")
        return

    with open(links_file) as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(urls)} CPU links")
    print()

    catalog = _load_validated_catalog()
    added = 0
    updated = 0
    failed = 0

    # Process each URL
    for i, url in enumerate(urls):
        full_url = f"https://www.techpowerup.com{url}"

        # Check if already in catalog
        model = (
            url.split("/")[-1]
            .replace(".c0000", "")
            .replace(".c", " ")
            .replace("-", " ")
            .title()
        )

        print(f"[{i + 1}/{len(urls)}] {model}...", end=" ")

        # Skip if already exists with good specs
        existing = None
        for cpu in catalog.get("CPU", []):
            if (
                cpu.get("model", "").lower() in model.lower()
                or model.lower() in cpu.get("model", "").lower()
            ):
                existing = cpu
                break

        if existing and len(existing.get("specs", {})) >= 10:
            print("skipped (already has specs)")
            continue

        try:
            resp = requests.get(
                full_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}
            )
            if resp.status_code != 200:
                print(f"HTTP {resp.status_code}")
                failed += 1
                continue

            specs = extract_cpu_specs_from_html(resp.text)

            if not specs:
                print("no specs extracted")
                failed += 1
                continue

            # Determine brand from URL
            brand = "AMD" if "ryzen" in url or "epyc" in url else "Intel"
            if "core-ultra" in url:
                brand = "Intel"

            # Add or update catalog
            if existing:
                # Merge specs
                for key, value in specs.items():
                    if key not in existing.get("specs", {}):
                        existing["specs"][key] = {
                            "value": value,
                            "unit": None,
                            "sources": ["TechPowerUp"],
                            "confidence": 0.5,
                        }
                updated += 1
                print("updated")
            else:
                catalog["CPU"].append(
                    {
                        "brand": brand,
                        "model": model,
                        "part_number": "",
                        "validated": True,
                        "validation_sources": ["TechPowerUp"],
                        "validation_date": datetime.now().isoformat(),
                        "confidence": 0.5,
                        "specs": {
                            k: {
                                "value": v,
                                "unit": None,
                                "sources": ["TechPowerUp"],
                                "confidence": 0.5,
                            }
                            for k, v in specs.items()
                        },
                    }
                )
                added += 1
                print("added")

        except Exception as e:
            print(f"error: {str(e)[:30]}")
            failed += 1

    # Save catalog
    catalog["_metadata"]["total_entries"] = sum(
        len(items) for key, items in catalog.items() if key != "_metadata"
    )
    catalog["_metadata"]["last_updated"] = datetime.now().isoformat()
    _save_validated_catalog(catalog)

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Added: {added}")
    print(f"Updated: {updated}")
    print(f"Failed: {failed}")
    print(f"Total catalog: {catalog['_metadata']['total_entries']} entries")


if __name__ == "__main__":
    if not REQUESTS_AVAILABLE:
        print("[W] requests not installed")
    else:
        enrich_from_tpu_links()
