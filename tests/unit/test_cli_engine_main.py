from __future__ import annotations

import io
import json
import sys

from hardwarextractor.cli_engine import main


def test_cli_engine_main_handles_unknown_and_error(monkeypatch, capsys):
    lines = [
        "\n",
        "{bad json}\n",
        json.dumps({"command": "unknown"}) + "\n",
        json.dumps({"command": "select_candidate", "payload": {"index": "bad"}}) + "\n",
    ]
    monkeypatch.setattr(sys, "stdin", io.StringIO("".join(lines)))
    main()
    out = capsys.readouterr().out
    assert "error" in out.lower()
