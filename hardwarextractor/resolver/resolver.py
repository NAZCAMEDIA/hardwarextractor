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
    # IMPORTANTE: Patrones específicos (RTX, RX, Arc) van ANTES del patrón genérico
    # para evitar que "RTX 3090" extraiga solo "3090" en vez de "rtx3090"
    patterns = [
        r'\bi[3579]-?([0-9]{4,5}[kfxu]?)\b',  # Intel: i7-12700K
        r'\b(rtx\s*[0-9]{4}(?:\s*ti)?)\b',  # RTX 4090, RTX 3090 Ti
        r'\b(rx\s*[0-9]{4}(?:\s*xt)?)\b',  # RX 7800, RX 7800 XT
        r'\b(arc\s*a[0-9]{3})\b',  # Arc A770
        r'\b([0-9]{4}[xg]?)\b',  # AMD Ryzen: 5900X, fallback genérico
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return match.group(1).replace(' ', '')
    return None


def _looks_like_part_number(text: str) -> bool:
    """Detecta si el input parece ser un código de referencia (part number).

    Part numbers típicos: CMK32GX5M2B5600C36, F5-6000J3038F16GX2-TZ5RK, KF556C40BBK2-32
    Características: alfanuméricos, pueden tener guiones, sin espacios significativos.
    """
    import re
    # Eliminar espacios y verificar si es mayormente alfanumérico con guiones
    clean = text.replace(" ", "").replace("-", "")
    if len(clean) < 8:
        return False
    # Debe tener mezcla de letras y números
    has_letters = any(c.isalpha() for c in clean)
    has_numbers = any(c.isdigit() for c in clean)
    # No debe tener muchas palabras separadas (eso sería un nombre de producto)
    word_count = len(text.split())
    return has_letters and has_numbers and word_count <= 2


def resolve_component(input_raw: str, component_type: ComponentType) -> ResolveResult:
    """Resuelve un componente a candidatos del catálogo.

    Usa matching exacto, por tokens, y fuzzy matching como fallback.
    Prioriza match exacto de part_number cuando el input parece ser un código.
    """
    url_result = resolve_from_url(input_raw, component_type)
    if url_result:
        return url_result

    normalized = normalize_input(input_raw)
    input_model_number = _extract_model_number(normalized)
    is_part_number_search = _looks_like_part_number(input_raw)

    # Fase 1: Buscar match EXACTO de part_number (prioridad máxima)
    if is_part_number_search:
        for candidate in catalog_by_type(component_type):
            pn = normalize_input(candidate.canonical.get("part_number", ""))
            if pn and pn == normalized:
                # Match exacto 100% - retornar inmediatamente
                candidate.score = 1.0
                return ResolveResult(exact=True, candidates=[candidate])

    candidates: List[ResolveCandidate] = []

    for candidate in catalog_by_type(component_type):
        model = normalize_input(candidate.canonical.get("model", ""))
        pn = normalize_input(candidate.canonical.get("part_number", ""))
        brand = normalize_input(candidate.canonical.get("brand", ""))
        candidate_model_number = _extract_model_number(model)

        # Match exacto por part_number contenido
        if pn and pn in normalized:
            candidate.score = 0.98
            candidates.append(candidate)
            continue

        # Match inverso: input contenido en part_number
        if pn and normalized in pn:
            candidate.score = 0.97
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

        # Para búsquedas de part_number, usar fuzzy matching más estricto
        if is_part_number_search and pn:
            similarity = fuzzy_match_score(pn, normalized)
            if similarity > 0.90:  # Más estricto para part numbers
                candidate.score = similarity * 0.94
                candidates.append(candidate)
                continue
        elif not is_part_number_search:
            # Fuzzy match por modelo (similarity > 0.75)
            if model:
                similarity = fuzzy_match_score(model, normalized)
                if similarity > 0.75:
                    candidate.score = similarity * 0.92
                    candidates.append(candidate)
                    continue

            # Fuzzy match por part_number (similarity > 0.8)
            if pn:
                similarity = fuzzy_match_score(pn, normalized)
                if similarity > 0.8:
                    candidate.score = similarity * 0.88
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

    # Para búsquedas de part_number, si hay un candidato con score muy alto, priorizar
    if is_part_number_search and candidates:
        top_score = candidates[0].score
        if top_score >= 0.90:
            # Filtrar solo los que están cerca del top
            candidates = [c for c in candidates if c.score >= top_score - 0.05]

    # Limitar a 5 candidatos máximo
    candidates = candidates[:5]

    # Determinar si es match exacto
    exact = False
    if candidates and len(candidates) == 1 and candidates[0].score >= 0.95:
        exact = True

    return ResolveResult(exact=exact, candidates=candidates)
