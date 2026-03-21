"""aioncode doctor — Run environment diagnostics."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from aioncode import __version__
from aioncode.utils.console import banner, header, status_table, info, muted
from aioncode.utils.platform import (
    IS_WINDOWS,
    check_long_path_support,
    get_system_info,
)


def _check_project(target: Path) -> list[tuple[str, bool, str]]:
    """Run project-level diagnostics."""
    checks: list[tuple[str, bool, str]] = []

    # .aion/ exists
    aion_dir = target / ".aion"
    has_aion = aion_dir.is_dir()
    checks.append((".aion/ directory", has_aion, str(aion_dir) if has_aion else "Not found"))

    if not has_aion:
        checks.append(("Project initialized", False, "Run: aioncode init"))
        return checks

    # config.yml
    config = aion_dir / "config.yml"
    checks.append(("config.yml", config.is_file(), "Version config"))

    # Write protocol
    wp = aion_dir / "refs" / "write-protocol.md"
    checks.append(("Write Protocol", wp.is_file(), str(wp.relative_to(target)) if wp.is_file() else "Missing"))

    # Rules
    rules_dir = aion_dir / "rules"
    rule_files = list(rules_dir.glob("*.md")) if rules_dir.is_dir() else []
    checks.append(("Rules", len(rule_files) > 0, f"{len(rule_files)} rule files"))

    # Checklists
    cl_dir = aion_dir / "checklists"
    cl_files = list(cl_dir.glob("*.md")) if cl_dir.is_dir() else []
    checks.append(("Checklists", len(cl_files) > 0, f"{len(cl_files)} checklist files"))

    # Commands
    cmd_dir = target / ".claude" / "commands"
    cmd_files = list(cmd_dir.glob("aion-*.md")) if cmd_dir.is_dir() else []
    checks.append(("Commands", len(cmd_files) > 0, f"{len(cmd_files)} command files"))

    # CLAUDE.md
    claude_md = target / ".claude" / "CLAUDE.md"
    checks.append(("CLAUDE.md", claude_md.is_file(), "Project instructions"))

    # Hooks
    hooks = target / ".claude" / "hooks.json"
    checks.append(("hooks.json", hooks.is_file(), "Safety hooks"))

    # Spec conflicts (multiple authors on same spec)
    specs_dir = aion_dir / "specs"
    if specs_dir.is_dir():
        spec_files = list(specs_dir.glob("*.md"))
        # Simple check: just report count
        checks.append(("Specs", True, f"{len(spec_files)} spec files"))

    # .gitignore entries
    gitignore = target / ".gitignore"
    if gitignore.is_file():
        content = gitignore.read_text(encoding="utf-8")
        has_events = "events.jsonl" in content
        checks.append((".gitignore", has_events, "events.jsonl excluded" if has_events else "Missing events.jsonl"))
    else:
        checks.append((".gitignore", False, "No .gitignore found"))

    return checks


def run_doctor(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode doctor`."""
    banner("AionCode Doctor", f"v{__version__}")

    # --- System checks ---
    sys_info = get_system_info()
    system_checks: list[tuple[str, bool, str]] = [
        ("Python", True, f"{sys_info['python']}"),
        ("OS", True, f"{sys_info['os']} {sys_info['os_version'][:30]}"),
        ("Architecture", True, sys_info["arch"]),
        ("Git", shutil.which("git") is not None, shutil.which("git") or "Not found"),
    ]

    if IS_WINDOWS:
        long_path = check_long_path_support()
        system_checks.append(("Long paths", long_path, "Enabled" if long_path else "Disabled — may cause issues with deep paths"))

    # GitHub connectivity
    header("Connectivity")
    from aioncode.utils.network import is_github_reachable
    gh_ok = is_github_reachable()
    system_checks.append(("GitHub API", gh_ok, "Reachable" if gh_ok else "Unreachable — upgrade won't work"))

    status_table("System Environment", system_checks)

    # --- Project checks ---
    cwd = Path.cwd()
    if (cwd / ".aion").is_dir():
        project_checks = _check_project(cwd)
        status_table(f"Project: {cwd.name}", project_checks)
    else:
        print()
        muted(f"No .aion/ in current directory ({cwd})")
        info("Run `aioncode init` to initialize a project here")
