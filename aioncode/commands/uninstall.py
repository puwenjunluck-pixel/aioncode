"""aioncode uninstall — Remove aioncode from system and/or project."""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from aioncode import __version__
from aioncode.utils.console import (
    banner,
    console,
    error,
    header,
    info,
    muted,
    success,
    warning,
)
from aioncode.utils.integrity import strip_claude_md_markers
from aioncode.utils.platform import IS_WINDOWS, get_install_dir, open_utf8


def _scan_project(target: Path) -> dict:
    """Scan a project directory for AionCode artifacts to remove."""
    plan: dict = {
        "commands": [],
        "claude_md_action": "skip",
        "hooks_action": "skip",
        "settings_action": "skip",
    }

    # Commands — dynamic scan for aion-*.md
    cmd_dir = target / ".claude" / "commands"
    if cmd_dir.is_dir():
        plan["commands"] = sorted(cmd_dir.glob("aion-*.md"))

    # CLAUDE.md — check for markers
    claude_md = target / ".claude" / "CLAUDE.md"
    if claude_md.is_file():
        content = claude_md.read_text(encoding="utf-8")
        from aioncode.utils.integrity import MARKER_START, MARKER_END
        if MARKER_START in content:
            # Check if there's user content outside markers
            before = content.split(MARKER_START)[0].strip()
            after_parts = content.split(MARKER_END)
            after = after_parts[-1].strip() if len(after_parts) > 1 else ""
            if before or after:
                plan["claude_md_action"] = "strip_markers"
            else:
                plan["claude_md_action"] = "remove"
        # No markers → skip

    # Hooks and settings
    if (target / ".claude" / "hooks.json").is_file():
        plan["hooks_action"] = "backup_remove"
    if (target / ".claude" / "settings.local.json").is_file():
        plan["settings_action"] = "backup_remove"

    return plan


def _uninstall_project(target: Path, *, dry_run: bool = False) -> None:
    """Remove AionCode from a project directory."""
    plan = _scan_project(target)

    # --- Show plan ---
    header("Uninstall Plan")
    info(f"Commands:      {len(plan['commands'])} aion-*.md files")

    match plan["claude_md_action"]:
        case "strip_markers":
            info("CLAUDE.md:     strip AionCode section (user content preserved)")
        case "remove":
            info("CLAUDE.md:     remove (no user content outside markers)")
        case "skip":
            muted("CLAUDE.md:     skip (no AionCode markers found)")

    match plan["hooks_action"]:
        case "backup_remove":
            info("hooks.json:    backup + remove")
        case "skip":
            muted("hooks.json:    not found")

    match plan["settings_action"]:
        case "backup_remove":
            info("settings.json: backup + remove")
        case "skip":
            muted("settings.json: not found")

    info(".aion/:        preserved (not touched)")
    print()

    if dry_run:
        header("Dry Run Complete")
        muted("No changes made. Run without --dry-run to execute.")
        return

    # --- Confirm ---
    try:
        answer = console.input("Type 'aioncode' to confirm uninstall: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        info("Cancelled.")
        return

    if answer != "aioncode":
        info(f"Cancelled. (Expected 'aioncode', got '{answer}')")
        return

    print()

    # --- Execute ---
    header("Removing")
    removed = 0
    backed_up = 0

    # Commands
    for cmd_file in plan["commands"]:
        cmd_file.unlink()
        success(f"Removed: .claude/commands/{cmd_file.name}")
        removed += 1

    # CLAUDE.md
    claude_md = target / ".claude" / "CLAUDE.md"
    match plan["claude_md_action"]:
        case "strip_markers":
            content = claude_md.read_text(encoding="utf-8")
            cleaned, _ = strip_claude_md_markers(content)
            claude_md.write_text(cleaned, encoding="utf-8")
            success("CLAUDE.md: AionCode section stripped, user content preserved")
        case "remove":
            claude_md.unlink()
            success("CLAUDE.md: removed")
            removed += 1
        case "skip":
            muted("CLAUDE.md: skipped")

    # Backup and remove hooks/settings
    backup_dir = None
    if plan["hooks_action"] == "backup_remove" or plan["settings_action"] == "backup_remove":
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_dir = target / ".claude" / f".aioncode-backup-{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

    hooks_file = target / ".claude" / "hooks.json"
    if plan["hooks_action"] == "backup_remove" and backup_dir:
        shutil.copy2(hooks_file, backup_dir / "hooks.json")
        hooks_file.unlink()
        success("hooks.json: backed up + removed")
        removed += 1
        backed_up += 1

    settings_file = target / ".claude" / "settings.local.json"
    if plan["settings_action"] == "backup_remove" and backup_dir:
        shutil.copy2(settings_file, backup_dir / "settings.local.json")
        settings_file.unlink()
        success("settings.json: backed up + removed")
        removed += 1
        backed_up += 1

    # --- Report ---
    print()
    header("Uninstall Complete")
    info(f"Removed:   {removed} items")
    info(f"Backed up: {backed_up} items")
    info(".aion/:    preserved")

    if backup_dir:
        print()
        info(f"Backups saved to: {backup_dir}")
        muted(f"  To restore: cp {backup_dir}/* {target}/.claude/")

    print()
    muted("Note: .aion/ directory was preserved — your rules and docs are still there.")
    muted(f"      To remove everything: rm -rf {target / '.aion'}")


def _uninstall_global() -> None:
    """Remove aioncode binary from system PATH."""
    install_dir = get_install_dir()
    binary_name = "aioncode.exe" if IS_WINDOWS else "aioncode"
    binary_path = install_dir / binary_name

    if not binary_path.exists():
        info("aioncode binary not found in system PATH")
        return

    header("Global Uninstall")
    info(f"Binary: {binary_path}")

    try:
        answer = console.input("Type 'aioncode' to confirm global uninstall: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        info("Cancelled.")
        return

    if answer != "aioncode":
        info("Cancelled.")
        return

    binary_path.unlink()
    success(f"Removed: {binary_path}")

    # Remove shell completion
    home = Path.home()
    for comp_file in [
        home / ".local" / "share" / "bash-completion" / "completions" / "aioncode",
        home / ".zfunc" / "_aioncode",
    ]:
        if comp_file.exists():
            comp_file.unlink()
            success(f"Removed: {comp_file}")


def run_uninstall(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode uninstall`."""
    banner("AionCode Uninstall", f"v{__version__}")

    # Project-level uninstall (current directory)
    cwd = Path.cwd()
    if (cwd / ".aion").is_dir() or (cwd / ".claude" / "commands").is_dir():
        _uninstall_project(cwd, dry_run=getattr(args, "dry_run", False))
    else:
        # Global uninstall
        _uninstall_global()
