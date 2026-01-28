from __future__ import annotations

import hashlib
import re


def normalize_input(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^a-z0-9\-\. ]", "", normalized)
    return normalized.strip()


def fingerprint(value: str) -> str:
    normalized = normalize_input(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
