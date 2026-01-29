from __future__ import annotations

from typing import List

from hardwarextractor.models.schemas import ComponentType, ResolveCandidate, ResolveResult
from hardwarextractor.normalize.input import normalize_input
from hardwarextractor.resolver.catalog import catalog_by_type
from hardwarextractor.resolver.url_resolver import resolve_from_url


def resolve_component(input_raw: str, component_type: ComponentType) -> ResolveResult:
    url_result = resolve_from_url(input_raw, component_type)
    if url_result:
        return url_result
    normalized = normalize_input(input_raw)
    candidates: List[ResolveCandidate] = []
    for candidate in catalog_by_type(component_type):
        model = normalize_input(candidate.canonical.get("model", ""))
        pn = normalize_input(candidate.canonical.get("part_number", ""))
        brand = normalize_input(candidate.canonical.get("brand", ""))
        if pn and pn in normalized:
            candidates.append(candidate)
            continue
        if model and model in normalized:
            candidates.append(candidate)
            continue
        # Fallback: brand match + any significant token (>3 chars) from input found in model
        # e.g., input="corsair vengeance" matches model="vengeance lpx 3200" because "vengeance" is in model
        if brand and brand in normalized and model and any(
            token for token in normalized.split() if token in model and len(token) > 3
        ):
            candidates.append(candidate)

    candidates = sorted(candidates, key=lambda c: (-c.score, c.canonical.get("model", "")))

    exact = False
    if candidates and candidates[0].score >= 0.95 and len(candidates) == 1:
        exact = True

    return ResolveResult(exact=exact, candidates=candidates)
