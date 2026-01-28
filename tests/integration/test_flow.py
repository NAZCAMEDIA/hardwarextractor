from __future__ import annotations

from pathlib import Path

from hardwarextractor.app.orchestrator import Orchestrator
from hardwarextractor.cache.sqlite_cache import SQLiteCache
from hardwarextractor.export.csv_exporter import export_ficha_csv
from hardwarextractor.scrape.spiders import SPIDERS
from hardwarextractor.data.catalog import load_field_catalog

FIXTURE_BASE = Path(__file__).resolve().parent.parent / "spiders" / "fixtures"


def fixture_scrape(spider_name: str, url: str, cache=None, **kwargs):
    fixture_path = FIXTURE_BASE / spider_name / "sample.html"
    html = fixture_path.read_text(encoding="utf-8")
    spider = SPIDERS[spider_name]
    return spider.parse_html(html, url)


def test_end_to_end_flow(tmp_path: Path):
    cache = SQLiteCache(tmp_path / "cache.sqlite")
    orchestrator = Orchestrator(cache=cache, scrape_fn=fixture_scrape)

    inputs = [
        "Intel Core i7-12700K BX8071512700K",
        "Kingston KF432C16BB/16 DDR4",
        "Samsung 970 EVO Plus MZ-V7S1T0 SSD",
        "ASUS ROG STRIX B550-F GAMING",
        "NVIDIA GeForce RTX 4070",
    ]

    for value in inputs:
        events = orchestrator.process_input(value)
        assert events
        if events[-1].status == "NEEDS_USER_SELECTION":
            events = orchestrator.select_candidate(0)
        assert events[-1].ficha_update is not None

    ficha = events[-1].ficha_update
    output = export_ficha_csv(ficha, tmp_path / "ficha.csv")
    content = output.read_text(encoding="utf-8")
    assert "section,field,value" in content

    catalog = load_field_catalog()
    assert len(ficha.fields_by_template) == len(catalog)
