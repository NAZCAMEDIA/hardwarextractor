from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict


def _get_data_dir() -> Path:
    """Get data directory, compatible with PyInstaller bundles."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return Path(sys._MEIPASS) / "hardwarextractor" / "data"
    else:
        # Running in normal Python environment
        return Path(__file__).resolve().parent


DATA_DIR = _get_data_dir()


def load_field_catalog() -> List[Dict[str, str]]:
    path = DATA_DIR / "field_catalog.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
