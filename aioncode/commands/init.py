"""aioncode init — Initialize .aion/ project intelligence in a directory."""

from __future__ import annotations

import argparse
from pathlib import Path

from aioncode.utils.console import (
    banner,
    confirm,
    error,
    header,
    info,
    install_report,
    muted,
    success,
    warning,
)


def _init_project(target: Path, *, upgrade: bool = False) -> None:
    """Execute project initialization with rich CLI output."""
    from aioncode.core.project import (
        _check_gitignore,
        detect_project,
        get_source_version,
        init_project,
    )

    target = target.resolve()
    source_version = get_source_version()
    project = detect_project(target)

    banner(
        f"AionCode {'Upgrade' if upgrade else 'Init'} v{source_version}",
        f"Target: {target}",
    )

    # --- Environment checks ---
    header("Environment Check")
    if not target.is_dir():
        error(f"Target directory does not exist: {target}")
        raise SystemExit(1)
    success("Target directory exists")

    import os
    import shutil

    if not os.access(target, os.W_OK):
        error("No write permission to target directory")
        raise SystemExit(1)
    success("Write permission OK")

    if shutil.which("claude"):
        success("Claude Code CLI available")
    else:
        warning("Claude Code CLI not found — all /project:aion-* commands require Claude Code")
        warning("  Install: https://claude.ai/download")

    if shutil.which("git"):
        success("Git available")
    else:
        warning("Git not found (collaboration features won't work)")

    if project.has_git:
        success("Git repository initialized")
    else:
        warning("Not a Git repository (.aion/ won't sync with team)")

    # --- Project detection ---
    header("Project Detection")

    if project.has_aion:
        info(f"AionCode already installed (v{project.installed_version})")
        if project.installed_version != source_version:
            info(f"  Update available: v{project.installed_version} → v{source_version}")
        else:
            muted("  Already up to date")
    else:
        info("AionCode not installed — fresh init")

    if project.source_count > 0:
        info(f"Existing codebase detected (~{project.source_count} source files)")

    if project.existing_docs:
        info(f"Existing docs found: {', '.join(project.existing_docs)}")
        muted("  Consider importing to .aion/refs/ after init")

    # --- Check gitignore interactively ---
    gitignore_path = target / ".gitignore"
    missing_entries = _check_gitignore(gitignore_path)
    update_gitignore = False
    if missing_entries:
        warning(f".gitignore missing: {', '.join(missing_entries)}")
        update_gitignore = confirm("Add missing entries to .gitignore?", default=True)
    else:
        success(".gitignore already configured")

    # --- Execute core init ---
    result = init_project(
        target,
        upgrade=upgrade,
        update_gitignore=update_gitignore,
    )

    if not result.ok:
        error(result.message)
        raise SystemExit(1)

    # --- Report ---
    header("Installation Report")
    install_report(
        title="File Operations",
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        warnings=result.warnings if result.warnings else None,
    )

    # --- Suggestions ---
    print()
    header("Next Steps")
    info("1. Open Claude Code in your project")
    info("2. Run: /project:aion-status")
    if project.is_new:
        info("3. Start with: /project:aion-design")
    else:
        info("3. Start with: /project:aion-scan")

    if project.existing_docs:
        print()
        info("Import existing docs:")
        for doc in project.existing_docs:
            muted(f"  cp {doc} .aion/refs/")

    print()
    info("Dashboard: aioncode dashboard")
    muted("  → http://localhost:19200")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def run_init(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode init`."""
    target = Path(args.target).resolve()

    if not target.is_dir():
        error(f"Directory does not exist: {target}")
        raise SystemExit(1)

    # Detect if this is an upgrade (already has .aion/)
    upgrade = (target / ".aion").is_dir()

    _init_project(target, upgrade=upgrade)
