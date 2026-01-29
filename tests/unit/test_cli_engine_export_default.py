from __future__ import annotations

import os
from pathlib import Path

from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.cli_engine import EngineSession
from hardwarextractor.scrape.spiders import SPIDERS

FIXTURE_BASE = Path(__file__).resolve().parent.parent / "spiders" / "fixtures"


def fixture_scrape(spider_name: str, url: str, cache=None, **kwargs):
    html = (FIXTURE_BASE / spider_name / "sample.html").read_text(encoding="utf-8")
    return SPIDERS[spider_name].parse_html(html, url)


def test_export_default_path(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cache = SQLiteCache(tmp_path / "cache.sqlite")
    orchestrator = Orchestrator(cache=cache, scrape_fn=fixture_scrape)
    session = EngineSession(orchestrator=orchestrator, cache=cache)
    session.analyze_component("Intel Core i7-12700K")
    session.select_candidate(0)
    session.add_to_ficha()
    session.export_ficha("md")
    files = list(tmp_path.glob("hxtractor_export_*.md"))
    assert files
