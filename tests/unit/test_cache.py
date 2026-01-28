from __future__ import annotations

from pathlib import Path

from hardwarextractor.cache.sqlite_cache import SQLiteCache


def test_cache_roundtrip(tmp_path: Path):
    cache = SQLiteCache(tmp_path / "cache.sqlite", ttl_seconds=60)
    cache.set_input("fp", {"value": 123})
    assert cache.get_input("fp") == {"value": 123}

    cache.set_specs("spec", {"specs": [{"key": "cpu.cores_physical"}]})
    assert cache.get_specs("spec") == {"specs": [{"key": "cpu.cores_physical"}]}
