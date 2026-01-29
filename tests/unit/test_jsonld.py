from __future__ import annotations

from parsel import Selector

from hardwarextractor.scrape.jsonld import extract_jsonld_pairs, _walk_jsonld_items


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


def test_extract_jsonld_with_graph():
    """Test extracting from JSON-LD with @graph structure."""
    html = '''
    <script type="application/ld+json">
    {
        "@graph": [
            {
                "@type": "Product",
                "additionalProperty": [
                    {"name": "speed", "value": "3.5 GHz"}
                ]
            }
        ]
    }
    </script>
    '''
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert len(pairs) == 1
    assert ("speed", "3.5 GHz") in pairs


def test_extract_jsonld_array():
    """Test extracting from JSON-LD array structure."""
    html = '''
    <script type="application/ld+json">
    [
        {
            "@type": "Product",
            "additionalProperty": [
                {"name": "memory", "value": "32GB"}
            ]
        }
    ]
    </script>
    '''
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert len(pairs) == 1
    assert ("memory", "32GB") in pairs


def test_extract_empty_jsonld():
    """Test extracting from empty JSON-LD."""
    html = '<script type="application/ld+json"></script>'
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert len(pairs) == 0


def test_extract_invalid_json():
    """Test handling invalid JSON."""
    html = '<script type="application/ld+json">{invalid json}</script>'
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert len(pairs) == 0


def test_extract_no_jsonld():
    """Test HTML with no JSON-LD scripts."""
    html = '<html><head><title>Test</title></head></html>'
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert len(pairs) == 0


def test_extract_jsonld_missing_name_or_value():
    """Test JSON-LD properties missing name or value."""
    html = '''
    <script type="application/ld+json">
    {
        "@type": "Product",
        "additionalProperty": [
            {"name": "cores"},
            {"value": "16"},
            {"name": "valid", "value": "100"}
        ]
    }
    </script>
    '''
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert len(pairs) == 1
    assert ("valid", "100") in pairs


def test_extract_jsonld_non_dict_item():
    """Test JSON-LD with non-dict items."""
    html = '''
    <script type="application/ld+json">
    {
        "@graph": [
            "not a dict",
            123,
            {
                "additionalProperty": [
                    {"name": "test", "value": "data"}
                ]
            }
        ]
    }
    </script>
    '''
    selector = Selector(text=html)
    pairs = list(extract_jsonld_pairs(selector))
    assert len(pairs) == 1
    assert ("test", "data") in pairs


def test_walk_jsonld_items_dict():
    """Test walking a simple dict."""
    data = {"key": "value"}
    items = list(_walk_jsonld_items(data))
    assert len(items) == 1
    assert items[0] == data


def test_walk_jsonld_items_graph():
    """Test walking dict with @graph."""
    data = {"@graph": [{"id": 1}, {"id": 2}]}
    items = list(_walk_jsonld_items(data))
    assert len(items) == 2


def test_walk_jsonld_items_list():
    """Test walking a list."""
    data = [{"a": 1}, {"b": 2}]
    items = list(_walk_jsonld_items(data))
    assert len(items) == 2


def test_walk_jsonld_items_list_with_non_dict():
    """Test walking list with non-dict items."""
    data = [{"a": 1}, "string", 123, {"b": 2}]
    items = list(_walk_jsonld_items(data))
    assert len(items) == 2
