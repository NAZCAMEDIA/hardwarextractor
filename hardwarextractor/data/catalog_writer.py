"""Catalog writer for persisting validated web search data.

Writes validated components to the catalog for future lookups.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from hardwarextractor.models.schemas import ComponentType, SpecField
from hardwarextractor.core.cross_validator import CrossValidationResult


# Path to validated catalog file
VALIDATED_CATALOG_PATH = Path(__file__).parent / "validated_catalog.json"


def _load_validated_catalog() -> Dict[str, List[Dict[str, Any]]]:
    """Load existing validated catalog."""
    if not VALIDATED_CATALOG_PATH.exists():
        return {
            "CPU": [],
            "RAM": [],
            "GPU": [],
            "MAINBOARD": [],
            "DISK": [],
            "GENERAL": [],
            "_metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_entries": 0,
            }
        }

    with open(VALIDATED_CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_validated_catalog(catalog: Dict[str, List[Dict[str, Any]]]) -> None:
    """Save validated catalog with backup."""
    # Create backup
    if VALIDATED_CATALOG_PATH.exists():
        backup_path = VALIDATED_CATALOG_PATH.with_suffix(".json.bak")
        shutil.copy(VALIDATED_CATALOG_PATH, backup_path)

    # Update metadata
    if "_metadata" not in catalog:
        catalog["_metadata"] = {}

    catalog["_metadata"]["last_updated"] = datetime.now().isoformat()
    catalog["_metadata"]["total_entries"] = sum(
        len(items) for key, items in catalog.items()
        if key != "_metadata"
    )

    # Save
    with open(VALIDATED_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)


def add_validated_component(
    result: CrossValidationResult,
    brand: str,
    model: str,
    part_number: Optional[str] = None,
) -> bool:
    """Add a validated component to the catalog.

    Args:
        result: CrossValidationResult from cross-validator
        brand: Component brand
        model: Component model
        part_number: Optional part number

    Returns:
        True if added, False if already exists or validation failed
    """
    if not result.should_persist:
        return False

    catalog = _load_validated_catalog()
    comp_type = result.component_type.value

    if comp_type not in catalog:
        catalog[comp_type] = []

    # Check for duplicates
    for entry in catalog[comp_type]:
        if (entry.get("brand", "").lower() == brand.lower() and
            entry.get("model", "").lower() == model.lower()):
            # Update existing entry with new specs
            _merge_specs(entry, result)
            _save_validated_catalog(catalog)
            return True

    # Create new entry
    entry = {
        "brand": brand,
        "model": model,
        "part_number": part_number or result.component_input,
        "validated": True,
        "validation_sources": list(set(
            source for vs in result.validated_specs for source in vs.sources
        )),
        "validation_date": datetime.now().isoformat(),
        "confidence": sum(vs.confidence for vs in result.validated_specs) / len(result.validated_specs) if result.validated_specs else 0,
        "specs": {
            vs.key: {
                "value": vs.value,
                "unit": vs.unit,
                "sources": vs.sources,
                "confidence": vs.confidence,
            }
            for vs in result.validated_specs
        },
    }

    catalog[comp_type].append(entry)
    _save_validated_catalog(catalog)
    return True


def _merge_specs(entry: Dict, result: CrossValidationResult) -> None:
    """Merge new validated specs into existing entry."""
    if "specs" not in entry:
        entry["specs"] = {}

    for vs in result.validated_specs:
        existing = entry["specs"].get(vs.key)

        # Only update if new confidence is higher
        if existing is None or vs.confidence > existing.get("confidence", 0):
            entry["specs"][vs.key] = {
                "value": vs.value,
                "unit": vs.unit,
                "sources": vs.sources,
                "confidence": vs.confidence,
            }

    # Update validation metadata
    entry["validation_date"] = datetime.now().isoformat()
    entry["validation_sources"] = list(set(
        entry.get("validation_sources", []) +
        [s for vs in result.validated_specs for s in vs.sources]
    ))


def get_validated_component(
    component_type: ComponentType,
    query: str,
) -> Optional[Dict[str, Any]]:
    """Search for a validated component.

    Args:
        component_type: Type of component
        query: Search query (brand, model, or part number)

    Returns:
        Entry if found, None otherwise
    """
    catalog = _load_validated_catalog()
    comp_type = component_type.value
    query_lower = query.lower()

    for entry in catalog.get(comp_type, []):
        if (query_lower in entry.get("brand", "").lower() or
            query_lower in entry.get("model", "").lower() or
            query_lower in entry.get("part_number", "").lower()):
            return entry

    return None


def list_validated_components(
    component_type: Optional[ComponentType] = None,
) -> List[Dict[str, Any]]:
    """List all validated components.

    Args:
        component_type: Optional filter by type

    Returns:
        List of validated entries
    """
    catalog = _load_validated_catalog()

    if component_type:
        return catalog.get(component_type.value, [])

    results = []
    for key, items in catalog.items():
        if key != "_metadata":
            results.extend(items)
    return results


def get_catalog_stats() -> Dict[str, Any]:
    """Get statistics about the validated catalog."""
    catalog = _load_validated_catalog()

    stats = {
        "metadata": catalog.get("_metadata", {}),
        "by_type": {},
        "total_specs": 0,
    }

    for comp_type in ["CPU", "RAM", "GPU", "MAINBOARD", "DISK", "GENERAL"]:
        entries = catalog.get(comp_type, [])
        specs_count = sum(len(e.get("specs", {})) for e in entries)

        stats["by_type"][comp_type] = {
            "count": len(entries),
            "specs": specs_count,
        }
        stats["total_specs"] += specs_count

    return stats
