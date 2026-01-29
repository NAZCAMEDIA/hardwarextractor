from __future__ import annotations

from pathlib import Path

from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.cli_engine import EngineSession, export_ficha_md
from hardwarextractor.scrape.spiders import SPIDERS

FIXTURE_BASE = Path(__file__).resolve().parent.parent / "spiders" / "fixtures"


def fixture_scrape(spider_name: str, url: str, cache=None, **kwargs):
    html = (FIXTURE_BASE / spider_name / "sample.html").read_text(encoding="utf-8")
    return SPIDERS[spider_name].parse_html(html, url)


def test_engine_session_flow(tmp_path: Path):
    cache = SQLiteCache(tmp_path / "cache.sqlite")
    orchestrator = Orchestrator(cache=cache, scrape_fn=fixture_scrape)
    session = EngineSession(orchestrator=orchestrator, cache=cache)

    session.analyze_component("Intel Core i7-12700K")
    session.select_candidate(0)
    session.add_to_ficha()
    assert session.ficha is not None

    out = tmp_path / "ficha.md"
    export_ficha_md(session.ficha, str(out))
    assert out.exists()


def test_engine_export_reset(tmp_path: Path):
    cache = SQLiteCache(tmp_path / "cache.sqlite")
    orchestrator = Orchestrator(cache=cache, scrape_fn=fixture_scrape)
    session = EngineSession(orchestrator=orchestrator, cache=cache)
    session.reset_ficha()
    assert session.ficha is not None
