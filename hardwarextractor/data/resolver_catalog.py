from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from hardwarextractor.models.schemas import ResolveCandidate, SourceTier

DATA_DIR = Path(__file__).resolve().parent


def load_resolver_index() -> List[ResolveCandidate]:
    path = DATA_DIR / "resolver_index.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    candidates: List[ResolveCandidate] = []
    for item in data:
        candidates.append(
            ResolveCandidate(
                canonical={
                    "brand": item["brand"],
                    "model": item["model"],
                    "part_number": item.get("part_number"),
                },
                score=item["score"],
                source_url=item["source_url"],
                source_name=item["source_name"],
                spider_name=item["spider_name"],
                source_tier=SourceTier.CATALOG,
            )
        )
    return candidates


def group_by_component_type() -> Dict[str, List[ResolveCandidate]]:
    data = json.loads((DATA_DIR / "resolver_index.json").read_text(encoding="utf-8"))
    grouped: Dict[str, List[ResolveCandidate]] = {}
    for item in data:
        grouped.setdefault(item["component_type"], []).append(
            ResolveCandidate(
                canonical={
                    "brand": item["brand"],
                    "model": item["model"],
                    "part_number": item.get("part_number"),
                },
                score=item["score"],
                source_url=item["source_url"],
                source_name=item["source_name"],
                spider_name=item["spider_name"],
                source_tier=SourceTier.CATALOG,
            )
        )
    return grouped
