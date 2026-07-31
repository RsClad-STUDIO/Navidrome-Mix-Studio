# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

project_root = Path.cwd()

a = Analysis(
    ["main.py"],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        (
            str(project_root / "resources"),
            "resources",
        ),
        (
            str(project_root / "README.md"),
            ".",
        ),
        (
            str(project_root / "LICENSE"),
            ".",
        ),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Navidrome Mix Studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(
        project_root
        / "resources"
        / "icons"
        / "app.ico"
    ),
    version=str(
        project_root
        / "version_info.txt"
    ),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Navidrome Mix Studio",
)