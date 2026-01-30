"""Auto-updater for HardwareXtractor.

Checks PyPI for new versions and auto-updates on CLI startup.
"""

from __future__ import annotations

import subprocess
import sys
from typing import Optional, Tuple

import requests

from hardwarextractor._version import __version__


PYPI_URL = "https://pypi.org/pypi/hardwarextractor/json"
TIMEOUT = 3  # seconds


def parse_version(version: str) -> Tuple[int, ...]:
    """Parse version string into tuple for comparison."""
    try:
        return tuple(int(x) for x in version.split("."))
    except (ValueError, AttributeError):
        return (0, 0, 0)


def get_latest_version() -> Optional[str]:
    """Fetch latest version from PyPI.

    Returns:
        Latest version string or None if fetch fails.
    """
    try:
        response = requests.get(PYPI_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            return data.get("info", {}).get("version")
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current."""
    return parse_version(latest) > parse_version(current)


def get_installer() -> str:
    """Detect if running under pipx or pip."""
    # Check if running in a pipx venv
    venv_path = sys.prefix.lower()
    if "pipx" in venv_path:
        return "pipx"
    return "pip"


def do_update(installer: str) -> bool:
    """Perform the update.

    Args:
        installer: 'pipx' or 'pip'

    Returns:
        True if update succeeded.
    """
    try:
        if installer == "pipx":
            result = subprocess.run(
                ["pipx", "upgrade", "hardwarextractor"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        else:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "hardwarextractor"],
                capture_output=True,
                text=True,
                timeout=60,
            )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_and_update(silent: bool = False) -> Optional[str]:
    """Check for updates and auto-update if available.

    Args:
        silent: If True, don't print messages.

    Returns:
        New version string if updated, None otherwise.
    """
    latest = get_latest_version()

    if not latest:
        return None

    if not is_newer_version(latest, __version__):
        return None

    # New version available
    if not silent:
        print(f"  Nueva versión disponible: v{latest} (actual: v{__version__})")
        print("  Actualizando...")

    installer = get_installer()
    success = do_update(installer)

    if success:
        if not silent:
            print(f"  Actualizado a v{latest}. Reinicia para usar la nueva versión.")
        return latest
    else:
        if not silent:
            print(f"  No se pudo actualizar. Ejecuta: {installer} upgrade hardwarextractor")
        return None
