from __future__ import annotations

from hardwarextractor.utils.allowlist import classify_tier, is_allowlisted


def test_allowlist_official():
    assert is_allowlisted("https://www.intel.com/product")
    assert classify_tier("https://www.intel.com/product") == "OFFICIAL"


def test_allowlist_reference():
    assert is_allowlisted("https://www.techpowerup.com/gpu")
    assert classify_tier("https://www.techpowerup.com/gpu") == "REFERENCE"


def test_allowlist_blocked():
    assert not is_allowlisted("https://example.com")
