from __future__ import annotations

from parsel import Selector

from hardwarextractor.scrape.jsonld import extract_jsonld_pairs


def test_extract_jsonld_pairs():
    html = """
    <script type="application/ld+json">
    {
      "@type": "Product",
      "additionalProperty": [
        {"name": "Base Clock", "value": "3600"},
        {"name": "Cores", "value": "8"}
      ]
    }
    </script>
    """
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert ("Base Clock", "3600") in pairs
