from __future__ import annotations

from hardwarextractor.scrape.extractors import _extract_numeric_with_unit


def test_extract_numeric_with_commas():
    value, unit = _extract_numeric_with_unit("1,024 GB")
    assert value == 1024
    assert unit == "GB"


def test_extract_numeric_with_voltage():
    value, unit = _extract_numeric_with_unit("1.35V")
    assert value == 1.35
    assert unit == "V"
