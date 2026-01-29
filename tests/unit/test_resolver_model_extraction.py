"""Tests for model number extraction in resolver."""

from __future__ import annotations

import pytest


def test_extract_model_number_rtx_no_space():
    """RTX3090 (without space) should extract rtx3090."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    result = _extract_model_number("nvidia rtx3090")
    assert result == "rtx3090"


def test_extract_model_number_rtx_with_space():
    """RTX 3090 (with space) should also extract rtx3090."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    result = _extract_model_number("geforce rtx 3090")
    assert result == "rtx3090"


def test_extract_model_number_rtx_ti():
    """RTX 3090 Ti should extract rtx3090ti."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    result = _extract_model_number("NVIDIA RTX 3090 Ti")
    assert result == "rtx3090ti"


def test_extract_model_number_rtx_4090():
    """RTX 4090 should extract rtx4090."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    result = _extract_model_number("rtx 4090")
    assert result == "rtx4090"


def test_extract_model_number_rx_xt():
    """RX 7800 XT should extract rx7800xt."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    result = _extract_model_number("RX 7800 XT")
    assert result == "rx7800xt"


def test_extract_model_number_ryzen():
    """Ryzen 9 5900X should extract 5900x."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    result = _extract_model_number("Ryzen 9 5900X")
    assert result == "5900x"


def test_extract_model_number_intel():
    """Core i7-12700K should extract 12700k."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    result = _extract_model_number("Core i7-12700K")
    assert result == "12700k"


def test_rtx3090_matches_catalog_rtx_3090():
    """Input 'nvidia rtx3090' should match catalog 'GeForce RTX 3090'."""
    from hardwarextractor.resolver.resolver import _extract_model_number

    input_model = _extract_model_number("nvidia rtx3090")
    catalog_model = _extract_model_number("GeForce RTX 3090")

    assert input_model == catalog_model == "rtx3090"
