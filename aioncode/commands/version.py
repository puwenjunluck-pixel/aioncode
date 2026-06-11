"""aioncode version — Show version and bootstrap status."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from aioncode import __version__
from aioncode.utils.console import console, info, muted, success, warning
from aioncode.utils.platform import get_platform_tag, get_system_info


def _read_project_version(target: Path) -> str | None:
    """Read the version from a project's .aion/config.yml."""
    config = target / ".aion" / "config.yml"
    if not config.is_file():
        return None
    try:
        text = config.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("version:"):
                return line.split('"')[1] if '"' in line else line.split(":")[1].strip()
    except (OSError, IndexError):
        pass
    return None


def run_version(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode version`."""
    console.print(f"[bold magenta]aioncode[/bold magenta] v{__version__}")

    # Binary info
    if getattr(sys, "frozen", False):
        info(f"Binary: {Path(sys.executable)}")
    else:
        info("Running from source")

    info(f"Platform: {get_platform_tag()}")
    sys_info = get_system_info()
    muted(f"Python {sys_info['python']} | {sys_info['os']} {sys_info['arch']}")

    # Project version
    cwd = Path.cwd()
    project_version = _read_project_version(cwd)
    if project_version:
        info(f"Project: {cwd.name} (v{project_version})")
        if project_version != __version__:
            warning(f"Project template version (v{project_version}) differs from CLI (v{__version__})")
            info("Run `aioncode init` to update project templates")
    else:
        muted("No .aion/ project in current directory")

    # Check for updates (non-blocking)
    try:
        from aioncode.utils.network import get_latest_release

        release = get_latest_release()
        if release and release.version != __version__:
            print()
            success(f"Update available: v{__version__} → v{release.version}")
            info("Run `aioncode upgrade` to update")
    except Exception:
        pass  # Silently skip if network unavailable
