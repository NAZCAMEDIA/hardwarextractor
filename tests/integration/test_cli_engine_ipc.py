from __future__ import annotations

import json
import subprocess
import sys


def test_cli_engine_ipc_analyze():
    proc = subprocess.Popen(
        [sys.executable, "-m", "hardwarextractor.cli_engine"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        proc.stdin.write(json.dumps({"command": "analyze_component", "payload": {"input": "Intel Core i7-12700K"}}) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline().strip()
        assert line
        msg = json.loads(line)
        assert msg["type"] in {"status", "log", "candidates", "result", "ficha_update"}
    finally:
        proc.kill()
