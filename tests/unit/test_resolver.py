from __future__ import annotations

from hardwarextractor.models.schemas import ComponentType
from hardwarextractor.resolver.resolver import resolve_component


def test_resolver_determinism_order():
    input_value = "Intel Core i7-12700K BX8071512700K"
    first = resolve_component(input_value, ComponentType.CPU)
    second = resolve_component(input_value, ComponentType.CPU)
    assert [c.canonical for c in first.candidates] == [c.canonical for c in second.candidates]
    assert first.candidates
    assert first.candidates[0].score >= 0.95
