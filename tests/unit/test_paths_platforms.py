from __future__ import annotations

import os
import sys
from pathlib import Path

from hardwarextractor.app import paths


def test_app_data_dir_darwin(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "platform", "darwin")
    path = paths.app_data_dir()
    assert path.exists()
    assert "Library/Application Support" in str(path)


def test_app_data_dir_windows(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setattr(sys, "platform", "win32")
    path = paths.app_data_dir()
    assert path.exists()
    assert "Roaming" in str(path)


def test_app_data_dir_linux(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setattr(sys, "platform", "linux")
    path = paths.app_data_dir()
    assert path.exists()
    assert "data" in str(path)
