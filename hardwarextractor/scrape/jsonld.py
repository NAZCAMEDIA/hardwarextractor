from __future__ import annotations

import json
from typing import Dict, Iterable, Tuple

from parsel import Selector


def extract_jsonld_pairs(selector: Selector) -> Iterable[Tuple[str, str]]:
    for node in selector.css('script[type="application/ld+json"]'):
        raw = node.xpath("string()").get(default="").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for item in _walk_jsonld_items(data):
            if not isinstance(item, dict):
                continue
            additional = item.get("additionalProperty") or []
            for prop in additional:
                name = prop.get("name")
                value = prop.get("value")
                if name and value:
                    yield str(name), str(value)


def _walk_jsonld_items(data) -> Iterable[dict]:  # noqa: ANN001
    if isinstance(data, dict):
        if "@graph" in data and isinstance(data["@graph"], list):
            for item in data["@graph"]:
                if isinstance(item, dict):
                    yield item
        else:
            yield data
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yield item
