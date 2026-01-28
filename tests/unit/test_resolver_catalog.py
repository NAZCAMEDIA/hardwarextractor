from __future__ import annotations

from hardwarextractor.data.resolver_catalog import group_by_component_type, load_resolver_index


def test_resolver_index_loads():
    data = load_resolver_index()
    assert data
    grouped = group_by_component_type()
    assert "CPU" in grouped
