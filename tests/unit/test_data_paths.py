"""Tests for data directory path resolution."""

from __future__ import annotations

import pytest
from pathlib import Path


def test_catalog_data_dir_exists():
    """DATA_DIR in catalog.py should point to existing directory."""
    from hardwarextractor.data.catalog import DATA_DIR

    assert DATA_DIR.exists()
    assert DATA_DIR.is_dir()


def test_resolver_catalog_data_dir_exists():
    """DATA_DIR in resolver_catalog.py should point to existing directory."""
    from hardwarextractor.data.resolver_catalog import DATA_DIR

    assert DATA_DIR.exists()
    assert DATA_DIR.is_dir()


def test_field_catalog_json_exists():
    """field_catalog.json should exist in DATA_DIR."""
    from hardwarextractor.data.catalog import DATA_DIR

    path = DATA_DIR / "field_catalog.json"
    assert path.exists()


def test_resolver_index_json_exists():
    """resolver_index.json should exist in DATA_DIR."""
    from hardwarextractor.data.resolver_catalog import DATA_DIR

    path = DATA_DIR / "resolver_index.json"
    assert path.exists()


def test_load_field_catalog():
    """load_field_catalog() should return list of dicts."""
    from hardwarextractor.data.catalog import load_field_catalog

    catalog = load_field_catalog()
    assert isinstance(catalog, list)
    assert len(catalog) > 0
    assert isinstance(catalog[0], dict)


def test_load_resolver_index():
    """load_resolver_index() should return list of ResolveCandidate."""
    from hardwarextractor.data.resolver_catalog import load_resolver_index
    from hardwarextractor.models.schemas import ResolveCandidate

    candidates = load_resolver_index()
    assert isinstance(candidates, list)
    assert len(candidates) > 0
    assert isinstance(candidates[0], ResolveCandidate)


def test_cache_db_path():
    """cache_db_path() should return valid path."""
    from hardwarextractor.app.paths import cache_db_path

    path = cache_db_path()
    assert isinstance(path, Path)
    assert path.name == "cache.sqlite"
    # Parent directory should exist or be creatable
    assert path.parent.exists()
