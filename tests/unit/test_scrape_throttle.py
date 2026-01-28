from __future__ import annotations

from hardwarextractor.scrape.service import _throttle


def test_throttle_no_config():
    _throttle("https://www.intel.com/", None)
