from __future__ import annotations

import pytest

from hardwarextractor.scrape.service import ScrapeError, _fetch_with_retries


def test_fetch_with_retries_fail_fast(monkeypatch):
    def _boom(*args, **kwargs):  # noqa: ANN001
        raise RuntimeError("fail")

    monkeypatch.setattr("requests.get", _boom)
    with pytest.raises(ScrapeError):
        _fetch_with_retries("https://www.intel.com/", user_agent="UA", retries=0)
