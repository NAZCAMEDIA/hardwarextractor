#!/usr/bin/env python3
"""Enrich catalog from public datasets and GitHub repositories."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import sys

sys.path.insert(0, ".")

from hardwarextractor.models.schemas import ComponentType
from hardwarextractor.data.catalog_writer import (
    _load_validated_catalog,
    _save_validated_catalog,
)

# Check available libraries
REQUESTS_AVAILABLE = True
PANDAS_AVAILABLE = True
PDFPLUMBER_AVAILABLE = True

try:
    import requests
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pandas as pd
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import pdfplumber
except ImportError:
    PDFPLUMBER_AVAILABLE = False


# ============================================================================
# GITHUB DATASETS
# ============================================================================

GITHUB_DATASETS = [
    # GPU Specs DB (Datacenter + Consumer NVIDIA/AMD)
    {
        "name": "GPU Specs DB",
        "url": "https://raw.githubusercontent.com/gmasse/gpu-specs/main/data/specs.json",
        "component_type": "GPU",
        "format": "gpu_dict",
    },
    # RonnyMuthomi GPUs-Specs (3204 entries, TechPowerUp data)
    {
        "name": "RonnyMuthomi GPUs-Specs",
        "url": "https://raw.githubusercontent.com/RonnyMuthomi/GPUs-Specs/main/gpu_1986-2026.csv",
        "component_type": "GPU",
        "format": "csv",
    },
    # marvic2409 AllCPUs (5210 CPU entries)
    {
        "name": "marvic2409 AllCPUs",
        "url": "https://raw.githubusercontent.com/marvic2409/AllCPUs/main/pretty.json",
        "component_type": "CPU",
        "format": "cpu_list",
    },
    # reox007 RightNow-GPU-Database (2824 GPU entries)
    {
        "name": "reox007 RightNow-GPU-Database",
        "url": "https://raw.githubusercontent.com/reox007/RightNow-GPU-Database/main/data/all-gpus.json",
        "component_type": "GPU",
        "format": "gpu_list",
    },
]


def load_github_dataset(url: str, format: str = "json") -> list[dict]:
    """Load dataset from GitHub."""
    if not REQUESTS_AVAILABLE:
        print("  [W] requests not installed")
        return []

    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            print(f"  [W] HTTP {resp.status_code}")
            return []

        # Handle CSV format
        if format == "csv":
            lines = resp.text.strip().split("\n")
            if len(lines) < 2:
                return []
            header = lines[0].split(",")
            items = []
            for line in lines[1:]:
                values = line.split(",")
                if len(values) >= len(header):
                    item = {}
                    for i, key in enumerate(header[: len(values)]):
                        key = (
                            key.strip()
                            .replace("Top__", "")
                            .replace("Graphics Processor__", "")
                        )
                        val = values[i].strip()
                        if val and val.lower() not in ["", "unknown", "n/a"]:
                            item[key] = val
                    if item.get("Name") and item.get("Brand"):
                        items.append(item)
            return items

        # Handle JSON data
        data = resp.json()

        # Handle GPU specs dict format (gpu name -> specs)
        if format == "gpu_dict" and isinstance(data, dict):
            items = []
            for gpu_name, specs in data.items():
                if gpu_name == "_header":
                    continue
                if isinstance(specs, dict):
                    items.append(
                        {
                            "brand": specs.get("manufacturer", "NVIDIA"),
                            "model": specs.get("name", gpu_name),
                            **specs,
                        }
                    )
            return items

        # Handle CPU list format (marvic2409 AllCPUs)
        if format == "cpu_list" and isinstance(data, list):
            items = []
            for cpu in data:
                if isinstance(cpu, dict):
                    name = cpu.get("name", "")
                    # Extract brand from name
                    brand = "Unknown"
                    if (
                        "Intel" in name
                        or "Core" in name
                        or "Xeon" in name
                        or "Celeron" in name
                        or "Pentium" in name
                    ):
                        brand = "Intel"
                    elif (
                        "AMD" in name
                        or "Ryzen" in name
                        or "EPYC" in name
                        or "Athlon" in name
                        or "Sempron" in name
                    ):
                        brand = "AMD"
                    elif (
                        "Apple" in name or "M1" in name or "M2" in name or "M3" in name
                    ):
                        brand = "Apple"
                    elif "AArch" in name:
                        brand = "ARM"

                    items.append(
                        {
                            "brand": brand,
                            "model": name,
                            "cpumark": cpu.get("cpumark"),
                            "cores": cpu.get("cores"),
                            "threads": cpu.get("thread"),
                            "speed": cpu.get("speed"),
                            "turbo": cpu.get("turbo"),
                            "tdp": cpu.get("tdp"),
                            "socket": cpu.get("socket"),
                            "category": cpu.get("cat"),
                            "date": cpu.get("date"),
                        }
                    )
            return items

        # Handle GPU list format (reox007 RightNow-GPU-Database)
        if format == "gpu_list" and isinstance(data, list):
            items = []
            for gpu in data:
                if isinstance(gpu, dict):
                    name = gpu.get("name", "")
                    # Extract brand from name or fields
                    brand = gpu.get("manufacturer", gpu.get("brand", "Unknown"))
                    if "nvidia" in brand.lower() or "Nvidia" in name:
                        brand = "NVIDIA"
                    elif "amd" in brand.lower() or "AMD" in name or "Radeon" in name:
                        brand = "AMD"
                    elif "intel" in brand.lower() or "Intel" in name:
                        brand = "Intel"

                    items.append(
                        {
                            "brand": brand,
                            "model": name,
                            **gpu,
                        }
                    )
            return items

        return data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"  [W] Error loading {url}: {e}")
        return []


# ============================================================================
# PDF EXTRACTION
# ============================================================================


class DatasheetExtractor:
    """Extract specs from PDF datasheets."""

    def __init__(self):
        self.pdf_lib = "pdfplumber" if PDFPLUMBER_AVAILABLE else None

    def is_available(self) -> bool:
        return self.pdf_lib is not None

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF."""
        if not self.is_available():
            return ""

        with pdfplumber.open(pdf_path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    def parse_specs(self, text: str, comp_type: str) -> dict[str, Any]:
        """Parse hardware specs from text."""
        specs = {}
        text_lower = text.lower()

        # Common patterns
        patterns = {
            "tdp": r"(\d+)\s*w",
            "voltage": r"(\d+\.?\d*)\s*v",
            "temperature": r"(\d+)\s*c",
        }

        # CPU patterns
        if comp_type == "CPU":
            patterns.update(
                {
                    "cores": r"(\d+)\s*core",
                    "threads": r"(\d+)\s*thread",
                    "base_clock": r"(\d+\.?\d*)\s*ghz",
                    "boost_clock": r"(\d+\.?\d*)\s*ghz.*boost",
                    "cache": r"(\d+)\s*(?:mb|kb).*cache",
                    "socket": r"socket[:\s]*([a-z0-9]+)",
                    "process": r"(\d+)\s*nm",
                }
            )

        # GPU patterns
        elif comp_type == "GPU":
            patterns.update(
                {
                    "vram": r"(\d+)\s*(?:gb|mb).*(?:gddr|vram)",
                    "memory_bus": r"(\d+)\s*bit",
                    "cuda_cores": r"(\d+)\s*cuda",
                    "tensor_cores": r"(\d+)\s*tensor",
                    "clock": r"(\d+\.?\d*)\s*(?:mhz|ghz)",
                }
            )

        # RAM patterns
        elif comp_type == "RAM":
            patterns.update(
                {
                    "capacity": r"(\d+)\s*(?:gb|mb)",
                    "speed": r"(\d+)\s*(?:mt/s|mhz)",
                    "latency": r"cl[:\s]*(\d+)",
                }
            )

        for key, pattern in patterns.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                value = match.group(1)
                try:
                    value = float(value)
                    if value == int(value):
                        value = int(value)
                except ValueError:
                    pass
                specs[key] = value

        return specs


# ============================================================================
# SPEC NORMALIZATION
# ============================================================================

SPEC_KEY_MAP = {
    # CPU
    "cores": "cpu.cores_physical",
    "threads": "cpu.threads_logical",
    "base_clock": "cpu.base_clock_mhz",
    "boost_clock": "cpu.boost_clock_mhz",
    "cache": "cpu.cache_total_mb",
    "socket": "cpu.socket",
    "process": "cpu.process_nm",
    "tdp": "cpu.tdp_w",
    # GPU
    "vram": "gpu.vram_gb",
    "memory_bus": "gpu.mem.bus_width_bits",
    "cuda_cores": "gpu.cuda_cores",
    "tensor_cores": "gpu.tensor_cores",
    "clock": "gpu.base_clock_mhz",
    # RAM
    "capacity": "ram.capacity_gb",
    "speed": "ram.speed_mt_s",
    "latency": "ram.cl",
}


def normalize_spec_key(key: str) -> str:
    """Normalize spec key."""
    return SPEC_KEY_MAP.get(key, key)


def normalize_value(value: Any, key: str) -> tuple[Any, Optional[str]]:
    """Normalize value and extract unit."""
    unit = None

    if isinstance(value, (int, float)):
        if "clock" in key:
            unit = "MHz"
            if value > 1000:
                value = value / 1000
                unit = "GHz"
        elif "tdp" in key:
            unit = "W"
        elif "cache" in key:
            unit = "MB"
        elif "process" in key:
            unit = "nm"
        elif "vram" in key or "capacity" in key:
            unit = "GB"
        elif "bus" in key:
            unit = "bit"
        elif "speed" in key:
            unit = "MT/s"

    return value, unit


# ============================================================================
# MAIN ENRICHMENT
# ============================================================================


def enrich_catalog() -> dict:
    """Run enrichment from all sources."""
    print("=" * 70)
    print("ENRICHMENT FROM PUBLIC SOURCES")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    results = {"github": 0, "pdf": 0, "errors": []}
    catalog = _load_validated_catalog()

    # 1. Load GitHub datasets
    print("[1/3] Loading GitHub datasets...")
    for ds in GITHUB_DATASETS:
        print(f"  Processing {ds['name']}...")
        data = load_github_dataset(ds["url"], ds.get("format", "json"))

        if data:
            comp_type = ComponentType(ds["component_type"])
            added = 0

            for item in data[:50]:  # Limit per source
                try:
                    brand = item.get("brand") or item.get("manufacturer") or "Unknown"
                    model = item.get("model") or item.get("name")
                    if not model:
                        continue

                    specs = {}
                    for key, value in item.items():
                        if key in ["brand", "model", "name", "manufacturer"]:
                            continue
                        if not value:
                            continue

                        norm_key = normalize_spec_key(key)
                        norm_value, unit = normalize_value(value, norm_key)

                        if norm_key:
                            specs[norm_key] = {
                                "value": norm_value,
                                "unit": unit,
                                "sources": [ds["name"]],
                                "confidence": 0.6,
                            }

                    # Add to catalog
                    if comp_type.value not in catalog:
                        catalog[comp_type.value] = []

                    exists = any(
                        e.get("model", "").lower() == model.lower()
                        for e in catalog[comp_type.value]
                    )

                    if not exists:
                        catalog[comp_type.value].append(
                            {
                                "brand": brand,
                                "model": model,
                                "part_number": "",
                                "validated": True,
                                "validation_sources": [ds["name"]],
                                "validation_date": datetime.now().isoformat(),
                                "confidence": 0.6,
                                "specs": specs,
                            }
                        )
                        added += 1

                except Exception as e:
                    results["errors"].append(str(e))

            print(f"    Added {added} entries")
            results["github"] += added
        else:
            print(f"    Failed to load")

    # 2. Process PDF datasheets (if directory exists)
    print("\n[2/3] Processing PDF datasheets...")
    datasheet_dir = Path("datasheets")
    if datasheet_dir.exists() and PDFPLUMBER_AVAILABLE:
        extractor = DatasheetExtractor()
        for pdf_file in datasheet_dir.glob("**/*.pdf"):
            try:
                text = extractor.extract_text(str(pdf_file))
                filename = pdf_file.stem.lower()

                if "cpu" in filename or "processor" in filename:
                    comp_type = ComponentType.CPU
                elif "gpu" in filename or "rtx" in filename or "rx " in filename:
                    comp_type = ComponentType.GPU
                elif "ram" in filename or "memory" in filename or "ddr" in filename:
                    comp_type = ComponentType.RAM
                elif "ssd" in filename or "nvme" in filename:
                    comp_type = ComponentType.DISK
                else:
                    continue

                specs = extractor.parse_specs(text, comp_type.value)

                if specs:
                    model = pdf_file.stem.replace("-", " ").replace("_", " ").title()

                    if comp_type.value not in catalog:
                        catalog[comp_type.value] = []

                    catalog[comp_type.value].append(
                        {
                            "brand": "",
                            "model": model,
                            "part_number": "",
                            "validated": True,
                            "validation_sources": ["datasheet"],
                            "validation_date": datetime.now().isoformat(),
                            "confidence": 0.5,
                            "specs": specs,
                        }
                    )
                    results["pdf"] += 1
                    print(f"  Processed: {pdf_file.name}")

            except Exception as e:
                results["errors"].append(str(e))
    else:
        print("  No datasheets directory or pdfplumber not installed")
        print("  Install: pip install pdfplumber")

    # 3. Save catalog
    print("\n[3/3] Saving catalog...")
    catalog["_metadata"]["total_entries"] = sum(
        len(items) for key, items in catalog.items() if key != "_metadata"
    )
    catalog["_metadata"]["last_updated"] = datetime.now().isoformat()
    _save_validated_catalog(catalog)

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"GitHub datasets: {results['github']} entries")
    print(f"PDF datasheets: {results['pdf']} entries")
    print(f"Total catalog: {catalog['_metadata']['total_entries']} entries")

    if results["errors"]:
        print(f"\nErrors: {len(results['errors'])}")

    return results


if __name__ == "__main__":
    enrich_catalog()
