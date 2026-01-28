#!/usr/bin/env bash
set -euo pipefail

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -e .

pyinstaller packaging/pyinstaller.spec --clean
