"""aioncode init — Initialize .aion/ project intelligence in a directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from aioncode.utils.console import (
    banner,
    confirm,
    error,
    file_table,
    header,
    info,
    install_report,
    muted,
    success,
    warning,
)
from aioncode.utils.integrity import (
    compare_template,
    merge_claude_md,
)
from aioncode.utils.platform import open_utf8, resolve_path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Directories to scaffold (always create if missing)
SCAFFOLD_DIRS = [
    "refs", "prototypes", "specs", "plans", "reviews", "contracts",
    "monitor", "tests", "tests/reports", "tests/perf", "tests/ui", "bugs",
]

# Source code file extensions for project type detection
SOURCE_EXTENSIONS = {
    ".ts", ".js", ".py", ".go", ".java", ".vue", ".tsx", ".jsx",
    ".rb", ".rs", ".kt", ".swift", ".cs", ".cpp", ".c", ".php",
}

# Existing doc patterns to suggest importing
DOC_PATTERNS = [
    "docs/architecture.md", "docs/ARCHITECTURE.md", "ARCHITECTURE.md",
    "docs/api.md", "docs/API.md", "DESIGN.md", "docs/design.md",
]

# .gitignore entries AionCode needs
GITIGNORE_ENTRIES = [
    ".aion/monitor/events.jsonl",
    ".aion/sessions.jsonl",
]


# ---------------------------------------------------------------------------
# Template resolution
# ---------------------------------------------------------------------------

def _get_templates_dir() -> Path:
    """Locate the bundled templates directory."""
    # In development: aioncode/internal/templates/
    # In PyInstaller bundle: resolved via sys._MEIPASS
    import sys

    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base / "templates"

    # Development mode
    return Path(__file__).parent.parent / "internal" / "templates"


def _get_commands_dir() -> Path:
    """Locate the bundled commands directory (Markdown command files)."""
    import sys

    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base / "commands"

    # Development: commands/ at repo root
    return Path(__file__).parent.parent.parent / "commands"


# ---------------------------------------------------------------------------
# Project detection
# ---------------------------------------------------------------------------

def _detect_project(target: Path) -> dict:
    """Detect project characteristics."""
    result = {
        "is_new": True,
        "has_aion": False,
        "has_claude_dir": False,
        "has_claude_md": False,
        "has_git": False,
        "installed_version": "0.0",
        "source_count": 0,
        "existing_docs": [],
    }

    # Check .aion/
    aion_dir = target / ".aion"
    if aion_dir.is_dir():
        result["has_aion"] = True
        result["is_new"] = False
        # Read installed version
        config = aion_dir / "config.yml"
        if config.is_file():
            try:
                text = config.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if line.startswith("version:"):
                        # Extract version from: version: "0.3"
                        v = line.split('"')[1] if '"' in line else line.split(":")[1].strip()
                        result["installed_version"] = v
                        break
            except (OSError, IndexError):
                pass

    # Check .claude/
    claude_dir = target / ".claude"
    result["has_claude_dir"] = claude_dir.is_dir()
    result["has_claude_md"] = (claude_dir / "CLAUDE.md").is_file()

    # Check .git
    result["has_git"] = (target / ".git").is_dir()

    # Count source files (max depth 2, cap at 500)
    count = 0
    try:
        for p in target.rglob("*"):
            if count >= 500:
                break
            # Skip hidden dirs and common noise
            parts = p.parts
            if any(part.startswith(".") or part in ("node_modules", "venv", "__pycache__", "dist", "build") for part in parts):
                continue
            if p.is_file() and p.suffix in SOURCE_EXTENSIONS:
                count += 1
    except OSError:
        pass
    result["source_count"] = count
    if count > 0:
        result["is_new"] = False

    # Check existing docs
    for pattern in DOC_PATTERNS:
        doc_path = target / pattern
        if doc_path.is_file():
            result["existing_docs"].append(pattern)

    return result


# ---------------------------------------------------------------------------
# Version helpers
# ---------------------------------------------------------------------------

def _get_source_version(templates_dir: Path) -> str:
    """Read version from templates/aion/config.yml."""
    config = templates_dir / "aion" / "config.yml"
    if not config.is_file():
        return "0.0"
    try:
        text = config.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("version:"):
                return line.split('"')[1] if '"' in line else line.split(":")[1].strip()
    except (OSError, IndexError):
        pass
    return "0.0"


# ---------------------------------------------------------------------------
# Core init logic
# ---------------------------------------------------------------------------

def _init_project(target: Path, *, upgrade: bool = False) -> None:
    """Execute project initialization."""
    target = resolve_path(target)
    templates_dir = _get_templates_dir()
    commands_dir = _get_commands_dir()
    source_version = _get_source_version(templates_dir)

    # --- Detection ---
    project = _detect_project(target)

    banner(
        f"AionCode {'Upgrade' if upgrade else 'Init'} v{source_version}",
        f"Target: {target}",
    )

    # --- Environment checks ---
    header("Environment Check")
    checks: list[str] = []

    if not target.is_dir():
        error(f"Target directory does not exist: {target}")
        raise SystemExit(1)
    success("Target directory exists")

    import os
    if not os.access(target, os.W_OK):
        error("No write permission to target directory")
        raise SystemExit(1)
    success("Write permission OK")

    if shutil.which("git"):
        success("Git available")
    else:
        warning("Git not found (collaboration features won't work)")

    if project["has_git"]:
        success("Git repository initialized")
    else:
        warning("Not a Git repository (.aion/ won't sync with team)")

    # --- Project detection ---
    header("Project Detection")

    if project["has_aion"]:
        info(f"AionCode already installed (v{project['installed_version']})")
        if project["installed_version"] != source_version:
            info(f"  Update available: v{project['installed_version']} → v{source_version}")
        else:
            muted("  Already up to date")
    else:
        info("AionCode not installed — fresh init")

    if project["source_count"] > 0:
        info(f"Existing codebase detected (~{project['source_count']} source files)")

    if project["existing_docs"]:
        info(f"Existing docs found: {', '.join(project['existing_docs'])}")
        muted("  Consider importing to .aion/refs/ after init")

    # --- Tracking ---
    created: list[str] = []
    updated: list[str] = []
    skipped: list[str] = []
    warnings_list: list[str] = []

    # --- 1. Copy commands to .claude/commands/ (always overwrite) ---
    header("Installing Commands")
    cmd_dst = target / ".claude" / "commands"
    cmd_dst.mkdir(parents=True, exist_ok=True)

    if commands_dir.is_dir():
        cmd_count = 0
        for f in sorted(commands_dir.glob("*.md")):
            dst = cmd_dst / f.name
            shutil.copy2(f, dst)
            cmd_count += 1
            updated.append(f".claude/commands/{f.name}")
        success(f"{cmd_count} command files installed")
    else:
        warning("Commands directory not found")

    # --- 2. Scaffold .aion/ (never overwrite existing files) ---
    header("Scaffolding .aion/")
    aion_src = templates_dir / "aion"
    aion_dst = target / ".aion"

    if aion_src.is_dir():
        for f in sorted(aion_src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(aion_src)
            dst_file = aion_dst / rel

            if dst_file.exists():
                if upgrade and not dst_file.exists():
                    # Upgrade mode: add missing files
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, dst_file)
                    created.append(f".aion/{rel}")
                else:
                    skipped.append(f".aion/{rel}")
            else:
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst_file)
                created.append(f".aion/{rel}")

    # Create scaffold directories
    dirs_created = 0
    for d in SCAFFOLD_DIRS:
        dir_path = aion_dst / d
        if not dir_path.is_dir():
            dir_path.mkdir(parents=True, exist_ok=True)
            dirs_created += 1

    success(f"Scaffold: {len([c for c in created if c.startswith('.aion/')])} files, {dirs_created} directories")

    # --- 3. Install hooks & settings (only if not existing) ---
    header("Configuration")
    claude_dir = target / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # hooks.json
    hooks_src = templates_dir / "claude-hooks.json"
    hooks_dst = claude_dir / "hooks.json"
    if hooks_src.is_file():
        if hooks_dst.is_file():
            skipped.append(".claude/hooks.json")
            muted("  Hooks: kept existing")
        else:
            shutil.copy2(hooks_src, hooks_dst)
            created.append(".claude/hooks.json")
            success("  Hooks: created")

    # settings.local.json
    settings_src = templates_dir / "claude-settings.json"
    settings_dst = claude_dir / "settings.local.json"
    if settings_src.is_file():
        if settings_dst.is_file():
            skipped.append(".claude/settings.local.json")
            muted("  Settings: kept existing")
        else:
            shutil.copy2(settings_src, settings_dst)
            created.append(".claude/settings.local.json")
            success("  Settings: created")

    # --- 4. CLAUDE.md merge ---
    header("CLAUDE.md")
    claude_md_path = claude_dir / "CLAUDE.md"
    tpl_path = templates_dir / "CLAUDE.md.tpl"

    if tpl_path.is_file():
        tpl_content = tpl_path.read_text(encoding="utf-8")
        existing_content = None
        if claude_md_path.is_file():
            existing_content = claude_md_path.read_text(encoding="utf-8")

        result = merge_claude_md(existing_content, tpl_content)
        claude_md_path.write_text(result.content, encoding="utf-8")

        match result.action:
            case "created":
                created.append(".claude/CLAUDE.md")
                success("CLAUDE.md: created")
            case "merged":
                updated.append(".claude/CLAUDE.md")
                success("CLAUDE.md: merged (user content preserved)")
            case "appended":
                updated.append(".claude/CLAUDE.md")
                success("CLAUDE.md: appended (user content preserved)")

    # --- 5. Update version (upgrade mode) ---
    if upgrade:
        config_path = aion_dst / "config.yml"
        if config_path.is_file():
            text = config_path.read_text(encoding="utf-8")
            new_text = []
            version_updated = False
            for line in text.splitlines():
                if line.startswith("version:"):
                    new_text.append(f'version: "{source_version}"')
                    version_updated = True
                else:
                    new_text.append(line)
            if not version_updated:
                new_text.append(f'version: "{source_version}"')
            config_path.write_text("\n".join(new_text) + "\n", encoding="utf-8")
            success(f"Version updated: → v{source_version}")

    # --- 6. Check .gitignore ---
    header("Gitignore Check")
    gitignore_path = target / ".gitignore"
    missing_entries: list[str] = []

    if gitignore_path.is_file():
        gitignore_content = gitignore_path.read_text(encoding="utf-8")
        for entry in GITIGNORE_ENTRIES:
            if entry not in gitignore_content:
                missing_entries.append(entry)
    else:
        missing_entries = list(GITIGNORE_ENTRIES)

    if missing_entries:
        warning(f".gitignore missing: {', '.join(missing_entries)}")
        if confirm("Add missing entries to .gitignore?", default=True):
            with open_utf8(gitignore_path, "a") as f:
                f.write("\n# AionCode runtime files\n")
                for entry in missing_entries:
                    f.write(f"{entry}\n")
            success("Updated .gitignore")
    else:
        success(".gitignore already configured")

    # --- Report ---
    header("Installation Report")
    install_report(
        title="File Operations",
        created=created,
        updated=updated,
        skipped=skipped,
        warnings=warnings_list if warnings_list else None,
    )

    # --- Suggestions ---
    print()
    header("Next Steps")
    info("1. Open Claude Code in your project")
    info("2. Run: /project:aion-status")
    if project["is_new"]:
        info("3. Start with: /project:aion-design")
    else:
        info("3. Start with: /project:aion-scan")

    if project["existing_docs"]:
        print()
        info("Import existing docs:")
        for doc in project["existing_docs"]:
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
