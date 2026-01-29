from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "HardwareXtractor"


def app_data_dir() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        base = home / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    path = base / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def cache_db_path() -> Path:
    return app_data_dir() / "cache.sqlite"


def export_csv_path() -> Path:
    return app_data_dir() / "ficha.csv"


def log_file_path() -> Path:
    return app_data_dir() / "run.log"
