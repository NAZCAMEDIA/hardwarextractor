from __future__ import annotations

from pathlib import Path

from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.scrape.spiders import SPIDERS

FIXTURE_BASE = Path(__file__).resolve().parent.parent / "spiders" / "fixtures"


def fixture_scrape(spider_name: str, url: str, cache=None, **kwargs):
    html = (FIXTURE_BASE / spider_name / "sample.html").read_text(encoding="utf-8")
    return SPIDERS[spider_name].parse_html(html, url)


def test_orchestrator_candidate_selection(tmp_path: Path):
    orch = Orchestrator(cache=SQLiteCache(tmp_path / "cache.sqlite"), scrape_fn=fixture_scrape)
    events = orch.process_input("ASUS ROG STRIX B550-F GAMING")
    assert events[-1].status in {"NEEDS_USER_SELECTION", "READY_TO_ADD"}
    if events[-1].status == "NEEDS_USER_SELECTION":
        events = orch.select_candidate(0)
    assert events[-1].ficha_update is not None
