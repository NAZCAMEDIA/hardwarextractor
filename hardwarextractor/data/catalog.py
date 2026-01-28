from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(__file__).resolve().parent


def load_field_catalog() -> List[Dict[str, str]]:
    path = DATA_DIR / "field_catalog.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
