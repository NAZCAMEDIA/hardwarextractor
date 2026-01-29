from __future__ import annotations

from hardwarextractor.app import paths


def test_app_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    path = paths.app_data_dir()
    assert path.exists()


def test_cache_and_export_paths():
    assert str(paths.cache_db_path()).endswith("cache.sqlite")
    assert str(paths.export_csv_path()).endswith("ficha.csv")
