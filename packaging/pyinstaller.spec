# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(
    ["/Users/carlosjperez/Documents/GitHub/hardwarextractor/hardwarextractor/__main__.py"],
    pathex=["/Users/carlosjperez/Documents/GitHub/hardwarextractor"],
    binaries=[],
    datas=[("/Users/carlosjperez/Documents/GitHub/hardwarextractor/hardwarextractor/data/field_catalog.json", "hardwarextractor/data")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="HardwareXtractor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon="/Users/carlosjperez/Documents/GitHub/hardwarextractor/icnsFile_0a7782c085eea2ac5e8527e215d70bf9_Open_GPIB.icns",
)

app = BUNDLE(
    exe,
    name="HardwareXtractor.app",
    icon="/Users/carlosjperez/Documents/GitHub/hardwarextractor/icnsFile_0a7782c085eea2ac5e8527e215d70bf9_Open_GPIB.icns",
    bundle_identifier="com.nazcamedia.hardwarextractor",
)
