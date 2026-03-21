"""aioncode clean — Clean up temporary files in .aion/."""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from aioncode.utils.console import (
    banner,
    confirm,
    error,
    file_table,
    header,
    info,
    muted,
    success,
)

# Files older than this many days are considered expired
ARCHIVE_MAX_AGE_DAYS = 30

# Max size for events.jsonl before truncation
EVENTS_MAX_SIZE_BYTES = 1_048_576  # 1MB

# Keep this many bytes from the end when truncating
EVENTS_KEEP_BYTES = 204_800  # 200KB

# Temp file patterns to clean
TEMP_PATTERNS = ["tmp_*", "*.bak", "*.tmp", "*.swp"]


def _find_expired_archives(aion_dir: Path) -> list[Path]:
    """Find archived version files older than ARCHIVE_MAX_AGE_DAYS."""
    expired: list[Path] = []
    cutoff = time.time() - (ARCHIVE_MAX_AGE_DAYS * 86400)

    for subdir in ("plans", "specs"):
        target_dir = aion_dir / subdir
        if not target_dir.is_dir():
            continue
        for f in target_dir.glob("*.v[0-9]*.md"):
            if f.stat().st_mtime < cutoff:
                expired.append(f)

    return expired


def _find_oversized_events(aion_dir: Path) -> Path | None:
    """Check if events.jsonl exceeds size limit."""
    events = aion_dir / "monitor" / "events.jsonl"
    if events.is_file() and events.stat().st_size > EVENTS_MAX_SIZE_BYTES:
        return events
    return None


def _find_temp_files(aion_dir: Path) -> list[Path]:
    """Find temporary files matching known patterns."""
    temps: list[Path] = []
    for pattern in TEMP_PATTERNS:
        temps.extend(aion_dir.rglob(pattern))
    return temps


def _truncate_events(events_path: Path) -> int:
    """Truncate events.jsonl, keeping only the last EVENTS_KEEP_BYTES.

    Returns bytes freed.
    """
    original_size = events_path.stat().st_size
    with open(events_path, "rb") as f:
        f.seek(max(0, original_size - EVENTS_KEEP_BYTES))
        # Find the next complete line
        f.readline()  # Skip partial line
        kept_data = f.read()

    events_path.write_bytes(kept_data)
    return original_size - len(kept_data)


def _format_size(size_bytes: int) -> str:
    """Format byte count for display."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1_048_576:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / 1_048_576:.1f} MB"


def run_clean(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode clean`."""
    dry_run = getattr(args, "dry_run", False)
    cwd = Path.cwd()
    aion_dir = cwd / ".aion"

    if not aion_dir.is_dir():
        error("No .aion/ directory found in current directory")
        info("Run `aioncode init` first")
        raise SystemExit(1)

    banner("AionCode Clean", f"Project: {cwd.name}")

    # --- Scan ---
    header("Scanning")
    expired_archives = _find_expired_archives(aion_dir)
    oversized_events = _find_oversized_events(aion_dir)
    temp_files = _find_temp_files(aion_dir)

    # Build summary
    rows: list[tuple[str, str, str]] = []
    total_freed = 0

    for f in expired_archives:
        size = f.stat().st_size
        total_freed += size
        rel = f.relative_to(cwd)
        rows.append((str(rel), "expired archive", _format_size(size)))

    if oversized_events:
        size = oversized_events.stat().st_size
        freed = size - EVENTS_KEEP_BYTES
        total_freed += freed
        rows.append(
            (
                str(oversized_events.relative_to(cwd)),
                "truncate",
                f"{_format_size(size)} → {_format_size(EVENTS_KEEP_BYTES)}",
            )
        )

    for f in temp_files:
        size = f.stat().st_size
        total_freed += size
        rel = f.relative_to(cwd)
        rows.append((str(rel), "temp file", _format_size(size)))

    if not rows:
        success("Nothing to clean — project is tidy!")
        return

    file_table("Files to Clean", rows)
    info(f"Total space to free: {_format_size(total_freed)}")
    print()

    if dry_run:
        muted("Dry run — no changes made")
        return

    if not confirm("Proceed with cleanup?", default=True):
        info("Cancelled.")
        return

    # --- Execute ---
    header("Cleaning")
    cleaned = 0

    for f in expired_archives:
        f.unlink()
        success(f"Removed: {f.relative_to(cwd)}")
        cleaned += 1

    if oversized_events:
        freed = _truncate_events(oversized_events)
        success(f"Truncated events.jsonl (freed {_format_size(freed)})")
        cleaned += 1

    for f in temp_files:
        f.unlink()
        success(f"Removed: {f.relative_to(cwd)}")
        cleaned += 1

    print()
    success(f"Cleaned {cleaned} items, freed {_format_size(total_freed)}")
