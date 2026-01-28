from __future__ import annotations

from parsel import Selector

from hardwarextractor.scrape.jsonld import extract_jsonld_pairs


def test_extract_jsonld_graph():
    html = """
    <script type="application/ld+json">
    {
      "@graph": [
        {"@type": "Product", "additionalProperty": [{"name": "Memory Size", "value": "8"}]}
      ]
    }
    </script>
    """
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert ("Memory Size", "8") in pairs
