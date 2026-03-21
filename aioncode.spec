# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building aioncode single-file binary."""

import os
from pathlib import Path

block_cipher = None

# Paths
ROOT = Path(SPECPATH)
PACKAGE = ROOT / "aioncode"
TEMPLATES = PACKAGE / "internal" / "templates"
COMMANDS = ROOT / "commands"

a = Analysis(
    [str(PACKAGE / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundle templates for init command
        (str(TEMPLATES), "templates"),
        # Bundle command markdown files
        (str(COMMANDS), "commands"),
    ],
    hiddenimports=[
        "aioncode.commands.init",
        "aioncode.commands.install",
        "aioncode.commands.uninstall",
        "aioncode.commands.upgrade",
        "aioncode.commands.dashboard",
        "aioncode.commands.doctor",
        "aioncode.commands.version",
        "aioncode.commands.clean",
        "aioncode.internal.dashboard",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary rich sub-modules to reduce size
        "rich.jupyter",
        "rich.pretty",
        # Exclude test frameworks
        "pytest",
        "unittest",
        # Exclude other unnecessary modules
        "tkinter",
        "PIL",
        "numpy",
        "pandas",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
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
    name="aioncode",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
