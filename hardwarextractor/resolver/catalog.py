from __future__ import annotations

from typing import Dict, List

from hardwarextractor.models.schemas import ComponentType, ResolveCandidate
from hardwarextractor.data.resolver_catalog import group_by_component_type


def catalog_by_type(component_type: ComponentType) -> List[ResolveCandidate]:
    grouped = group_by_component_type()
    return grouped.get(component_type.value, [])
