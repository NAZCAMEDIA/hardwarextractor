from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_TTL_SECONDS = 60 * 60 * 24 * 7


class SQLiteCache:
    def __init__(self, path: str | Path, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.path = Path(path)
        self.ttl_seconds = ttl_seconds
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS input_cache (
                    fingerprint TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS spec_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def _is_fresh(self, created_at: float) -> bool:
        return (time.time() - created_at) < self.ttl_seconds

    def get_input(self, fingerprint: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.path)
        try:
            row = conn.execute(
                "SELECT payload, created_at FROM input_cache WHERE fingerprint = ?",
                (fingerprint,),
            ).fetchone()
            if not row:
                return None
            payload, created_at = row
            if not self._is_fresh(created_at):
                return None
            return json.loads(payload)
        finally:
            conn.close()

    def set_input(self, fingerprint: str, payload: Dict[str, Any]) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "REPLACE INTO input_cache (fingerprint, payload, created_at) VALUES (?, ?, ?)",
                (fingerprint, json.dumps(payload), time.time()),
            )
            conn.commit()
        finally:
            conn.close()

    def get_specs(self, cache_key: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.path)
        try:
            row = conn.execute(
                "SELECT payload, created_at FROM spec_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
            if not row:
                return None
            payload, created_at = row
            if not self._is_fresh(created_at):
                return None
            return json.loads(payload)
        finally:
            conn.close()

    def set_specs(self, cache_key: str, payload: Dict[str, Any]) -> None:
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(
                "REPLACE INTO spec_cache (cache_key, payload, created_at) VALUES (?, ?, ?)",
                (cache_key, json.dumps(payload), time.time()),
            )
            conn.commit()
        finally:
            conn.close()
