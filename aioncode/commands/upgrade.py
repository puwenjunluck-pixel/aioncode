"""aioncode upgrade — Update aioncode to the latest version."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import stat
import sys
import tempfile
from pathlib import Path

from aioncode import __version__
from aioncode.utils.console import (
    banner,
    confirm,
    download_progress,
    error,
    header,
    info,
    muted,
    success,
    warning,
)
from aioncode.utils.network import (
    download_file,
    get_latest_release,
)
from aioncode.utils.platform import IS_WINDOWS, get_platform_tag


def _compare_versions(current: str, latest: str) -> int:
    """Compare version strings. Returns -1, 0, or 1."""
    def parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split(".") if x.isdigit())

    c, l = parse(current), parse(latest)
    if c < l:
        return -1
    if c > l:
        return 1
    return 0


def _replace_binary(new_binary: Path, target: Path) -> None:
    """Replace the current binary with the new one.

    On Unix: atomic rename.
    On Windows: rename old → .old, copy new → target, schedule cleanup.
    """
    if IS_WINDOWS:
        old_backup = target.with_suffix(".old")
        try:
            if old_backup.exists():
                old_backup.unlink()
            target.rename(old_backup)
        except OSError:
            pass
        shutil.copy2(new_binary, target)
        # Schedule cleanup of .old file via a batch script
        cleanup_bat = target.parent / "_aioncode_cleanup.bat"
        cleanup_bat.write_text(
            '@echo off\n'
            'timeout /t 2 /nobreak >nul\n'
            f'del /f /q "{old_backup}"\n'
            f'del /f /q "{cleanup_bat}"\n',
            encoding="utf-8",
        )
        os.startfile(str(cleanup_bat))  # type: ignore[attr-defined]
    else:
        # Unix: atomic rename
        new_binary.chmod(
            new_binary.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
        )
        # Use rename for atomicity (same filesystem)
        tmp_in_place = target.with_suffix(".new")
        shutil.copy2(new_binary, tmp_in_place)
        tmp_in_place.chmod(
            tmp_in_place.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH,
        )
        tmp_in_place.rename(target)


def run_upgrade(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode upgrade`."""
    banner("AionCode Upgrade", f"Current: v{__version__}")

    if not getattr(sys, "frozen", False):
        info("Running from source — use `git pull` or `pip install --upgrade` instead.")
        return

    header("Checking for Updates")
    release = get_latest_release()

    if release is None:
        error("Failed to check for updates. Check your internet connection.")
        raise SystemExit(1)

    latest_version = release.version
    cmp = _compare_versions(__version__, latest_version)

    if cmp >= 0:
        success(f"Already up to date (v{__version__})")
        return

    info(f"New version available: v{__version__} → v{latest_version}")
    info(f"Release: {release.url}")

    # Find binary for this platform
    binary_url = release.get_binary_url()
    if binary_url is None:
        tag = get_platform_tag()
        error(f"No binary found for platform: {tag}")
        info("Available assets:")
        for name in release.assets:
            muted(f"  {name}")
        raise SystemExit(1)

    info(f"Binary: {binary_url.split('/')[-1]}")

    if not confirm(f"Upgrade to v{latest_version}?", default=True):
        info("Cancelled.")
        return

    # Download
    header("Downloading")
    with download_progress() as progress:
        task = progress.add_task(f"v{latest_version}", total=None)

        def on_progress(downloaded: int, total: int) -> None:
            if total > 0:
                progress.update(task, total=total, completed=downloaded)

        tmp_path = download_file(binary_url, progress_callback=on_progress)

    # Replace
    header("Installing")
    current_binary = Path(sys.executable)
    try:
        _replace_binary(tmp_path, current_binary)
        success(f"Upgraded: v{__version__} → v{latest_version}")
    except OSError as e:
        error(f"Failed to replace binary: {e}")
        warning(f"Downloaded file saved at: {tmp_path}")
        warning(f"Manually copy it to: {current_binary}")
        raise SystemExit(1)
    finally:
        # Clean up temp file
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass

    info("Restart aioncode to use the new version.")
