from __future__ import annotations

from difflib import SequenceMatcher
from typing import List, Optional

from hardwarextractor.models.schemas import ComponentType, ResolveCandidate, ResolveResult
from hardwarextractor.normalize.input import normalize_input
from hardwarextractor.resolver.catalog import catalog_by_type
from hardwarextractor.resolver.url_resolver import resolve_from_url


def fuzzy_match_score(s1: str, s2: str) -> float:
    """Calcula similitud entre dos strings usando SequenceMatcher.

    Returns:
        float entre 0.0 y 1.0 indicando similitud
    """
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def _extract_model_number(text: str) -> Optional[str]:
    """Extrae el número de modelo principal de un texto.

    Ej: 'Core i7-12700K' -> '12700k', 'Ryzen 9 5900X' -> '5900x'
    """
    import re
    # Buscar patrones de modelo numérico
    patterns = [
        r'\bi[3579]-?([0-9]{4,5}[kfxu]?)\b',  # Intel: i7-12700K
        r'\b([0-9]{4}[xg]?)\b',  # AMD Ryzen: 5900X, GPU: 4090
        r'\b(rtx\s*[0-9]{4})\b',  # RTX 4090
        r'\b(rx\s*[0-9]{4})\b',  # RX 7800
        r'\b(arc\s*a[0-9]{3})\b',  # Arc A770
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1).replace(' ', '')
    return None


def resolve_component(input_raw: str, component_type: ComponentType) -> ResolveResult:
    """Resuelve un componente a candidatos del catálogo.

    Usa matching exacto, por tokens, y fuzzy matching como fallback.
    """
    url_result = resolve_from_url(input_raw, component_type)
    if url_result:
        return url_result

    normalized = normalize_input(input_raw)
    input_model_number = _extract_model_number(normalized)
    candidates: List[ResolveCandidate] = []

    for candidate in catalog_by_type(component_type):
        model = normalize_input(candidate.canonical.get("model", ""))
        pn = normalize_input(candidate.canonical.get("part_number", ""))
        brand = normalize_input(candidate.canonical.get("brand", ""))
        candidate_model_number = _extract_model_number(model)

        # Match exacto por part_number (máxima prioridad)
        if pn and pn in normalized:
            candidate.score = 0.98
            candidates.append(candidate)
            continue

        # Match exacto por modelo completo
        if model and model in normalized:
            candidate.score = 0.96
            candidates.append(candidate)
            continue

        # Match exacto por número de modelo extraído
        if input_model_number and candidate_model_number:
            if input_model_number == candidate_model_number:
                candidate.score = 0.95
                candidates.append(candidate)
                continue

        # Fuzzy match por modelo (similarity > 0.75)
        if model:
            similarity = fuzzy_match_score(model, normalized)
            if similarity > 0.75:
                candidate.score = similarity * 0.92  # Max 0.92
                candidates.append(candidate)
                continue

        # Fuzzy match por part_number (similarity > 0.8)
        if pn:
            similarity = fuzzy_match_score(pn, normalized)
            if similarity > 0.8:
                candidate.score = similarity * 0.88  # Max 0.88
                candidates.append(candidate)
                continue

        # Match por marca + tokens significativos
        if brand and brand in normalized:
            tokens_in_model = [
                t for t in normalized.split()
                if t in model and len(t) > 3
            ]
            if tokens_in_model:
                candidate.score = 0.55 + (len(tokens_in_model) * 0.1)
                candidates.append(candidate)

    # Ordenar por score descendente
    candidates = sorted(candidates, key=lambda c: -c.score)

    # Filtrar candidatos con score muy bajo
    candidates = [c for c in candidates if c.score > 0.5]

    # Limitar a 5 candidatos máximo
    candidates = candidates[:5]

    # Determinar si es match exacto
    exact = False
    if candidates and len(candidates) == 1 and candidates[0].score >= 0.95:
        exact = True

    return ResolveResult(exact=exact, candidates=candidates)
