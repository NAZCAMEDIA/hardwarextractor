# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for HardwareXtractor macOS app bundle."""

import os
import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH)
PROJECT_ROOT = SPEC_DIR.parent

block_cipher = None

# Find Playwright driver (NOT browsers - they're too complex to bundle)
def get_playwright_data():
    """Get Playwright driver path for bundling.

    Note: Browsers (Chromium) are NOT bundled because:
    1. Code signing issues with nested .app bundles
    2. Size (~400MB+)

    The app will use system Chromium from ~/Library/Caches/ms-playwright/
    or prompt user to install if not found.
    """
    playwright_datas = []

    try:
        import playwright
        playwright_path = Path(playwright.__file__).parent
        driver_path = playwright_path / "driver"

        if driver_path.exists():
            # Include entire driver directory
            playwright_datas.append((str(driver_path), "playwright/driver"))
            print(f"[SPEC] Found Playwright driver: {driver_path}")
        else:
            print(f"[SPEC] Playwright driver not found at {driver_path}")

    except ImportError:
        print("[SPEC] Playwright not installed, skipping")

    return playwright_datas

playwright_datas = get_playwright_data()

datas = [
    (str(PROJECT_ROOT / "hardwarextractor" / "data" / "field_catalog.json"), "hardwarextractor/data"),
    (str(PROJECT_ROOT / "hardwarextractor" / "data" / "resolver_index.json"), "hardwarextractor/data"),
]

# Add Playwright driver data
datas.extend(playwright_datas)

hiddenimports = [
    "scrapy", "scrapy.spiders", "scrapy.http",
    "parsel", "parsel.selector",
    "requests", "requests.adapters", "urllib3",
    "hardwarextractor.ui.app", "hardwarextractor.ui.splash",
    "hardwarextractor.app.orchestrator", "hardwarextractor.app.config", "hardwarextractor.app.paths",
    "hardwarextractor.core.events", "hardwarextractor.core.source_chain",
    "hardwarextractor.scrape.service", "hardwarextractor.scrape.engines.base",
    "hardwarextractor.scrape.engines.detector", "hardwarextractor.scrape.engines.requests_engine",
    "hardwarextractor.engine.ficha_manager",
    "hardwarextractor.export.factory", "hardwarextractor.export.csv_exporter",
    "hardwarextractor.cache.sqlite_cache",
    "hardwarextractor.classifier.heuristic",
    "hardwarextractor.resolver.resolver",
    "hardwarextractor.normalize.input",
    "hardwarextractor.validate.validator",
    "hardwarextractor.aggregate.aggregator",
    "hardwarextractor.models.schemas",
    "hardwarextractor.data.catalog", "hardwarextractor.data.resolver_catalog",
    "tkinter", "tkinter.ttk", "tkinter.filedialog", "tkinter.messagebox",
    "openpyxl", "playwright",
]

icon_file = PROJECT_ROOT / "icnsFile_0a7782c085eea2ac5e8527e215d70bf9_Open_GPIB.icns"
if not icon_file.exists():
    icon_file = None
else:
    icon_file = str(icon_file)

a = Analysis(
    [str(PROJECT_ROOT / "hardwarextractor" / "__main__.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas", "scipy", "PIL", "cv2", "torch", "tensorflow"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name="HardwareXtractor",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=True, upx_exclude=[],
    runtime_tmpdir=None, console=False, disable_windowed_traceback=False,
    target_arch=None, codesign_identity=None, entitlements_file=None, icon=icon_file,
)

app = BUNDLE(
    exe,
    name="HardwareXtractor.app",
    icon=icon_file,
    bundle_identifier="com.nazcamedia.hardwarextractor",
    info_plist={
        "CFBundleDisplayName": "HardwareXtractor",
        "CFBundleShortVersionString": "0.2.0",
        "CFBundleVersion": "0.2.0",
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": True,
        "LSMinimumSystemVersion": "10.15",
    },
)
