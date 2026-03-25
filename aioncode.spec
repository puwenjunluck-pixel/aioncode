# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building aioncode single-file binary."""

import os
import ssl
from pathlib import Path

block_cipher = None

# Paths
ROOT = Path(SPECPATH)
PACKAGE = ROOT / "aioncode"
TEMPLATES = PACKAGE / "internal" / "templates"
COMMANDS = ROOT / "commands"

# SSL certificates for HTTPS requests (urllib)
try:
    import certifi
    SSL_CERT_FILE = certifi.where()
except ImportError:
    SSL_CERT_FILE = ssl.get_default_verify_paths().cafile

a = Analysis(
    [str(PACKAGE / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        # Bundle templates for init command
        (str(TEMPLATES), "templates"),
        # Bundle command markdown files
        (str(COMMANDS), "commands"),
        # SSL certificates for HTTPS (GitHub API)
        (SSL_CERT_FILE, "certifi"),
    ],
    hiddenimports=[
        # CLI commands
        "aioncode.commands.init",
        "aioncode.commands.install",
        "aioncode.commands.uninstall",
        "aioncode.commands.upgrade",
        "aioncode.commands.dashboard",
        "aioncode.commands.doctor",
        "aioncode.commands.version",
        "aioncode.commands.clean",
        # Core
        "aioncode.core",
        "aioncode.core.project",
        # Dashboard (FastAPI)
        "aioncode.internal.dashboard",
        "aioncode.internal.dashboard.app",
        "aioncode.internal.dashboard.config",
        "aioncode.internal.dashboard.routers",
        "aioncode.internal.dashboard.routers.projects",
        "aioncode.internal.dashboard.routers.files",
        "aioncode.internal.dashboard.routers.monitor",
        "aioncode.internal.dashboard.routers.bugs",
        "aioncode.internal.dashboard.routers.team",
        "aioncode.internal.dashboard.routers.commands",
        "aioncode.internal.dashboard.routers.browse",
        "aioncode.internal.dashboard.routers.logs",
        "aioncode.internal.dashboard.services",
        "aioncode.internal.dashboard.services.project_registry",
        "aioncode.internal.dashboard.services.stats",
        "aioncode.internal.dashboard.services.file_ops",
        "aioncode.internal.dashboard.services.monitor",
        "aioncode.internal.dashboard.services.bugs",
        "aioncode.internal.dashboard.services.team",
        "aioncode.internal.dashboard.services.encoding",
        "aioncode.internal.dashboard.models",
        "aioncode.internal.dashboard.frontend",
        "aioncode.internal.dashboard.frontend.embedded",
        # FastAPI / uvicorn dependencies
        "fastapi",
        "starlette",
        "starlette.responses",
        "starlette.middleware",
        "starlette.middleware.cors",
        "pydantic",
        "uvicorn",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.loops",
        "uvicorn.loops.asyncio",
        "h11",
        "anyio",
        "anyio._backends",
        "anyio._backends._asyncio",
        "sniffio",
        "click",
        "httptools",
        "certifi",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
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
