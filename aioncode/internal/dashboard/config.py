"""Dashboard configuration — ports, paths, constants."""

from __future__ import annotations

import sys
from pathlib import Path

from aioncode import __version__

# --- Server ---
DEFAULT_PORT = 19200
DASHBOARD_VERSION = __version__

# --- AionCode scaffold directories ---
AION_DIRS = [
    "refs",
    "prototypes",
    "specs",
    "plans",
    "reviews",
    "contracts",
    "rules",
    "bugs",
]

# --- CLAUDE.md merge markers ---
MARKER_START = "<!-- AIONCODE:START -->"
MARKER_END = "<!-- AIONCODE:END -->"

# --- Monitor ---
MONITOR_EVENTS_DIR = ".aion/monitor"
MONITOR_EVENTS_FILE = "events.jsonl"

# --- Bug tracking ---
BUGS_DIR = ".aion/bugs"

# --- Team ---
TEAM_FILE = ".aion/team.yml"

# --- Brainstorm ---
BRAINSTORM_DIR = ".aion/brainstorm"
BRAINSTORM_SCREEN_FILE = "screen.json"
BRAINSTORM_EVENTS_FILE = "events.jsonl"

# --- Path resolution for commands/templates ---
_FROZEN = getattr(sys, "frozen", False)


def _resolve_source_paths() -> tuple[Path, Path, Path, Path]:
    """Resolve paths to commands, templates, and CLAUDE.md template.

    Returns:
        (commands_src, templates_src, aion_template_dir, claude_md_tpl)
    """
    if _FROZEN:
        # PyInstaller bundle
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        commands_src = base / "commands"
        templates_src = base / "templates"
    else:
        # Package mode: config.py is at aioncode/internal/dashboard/config.py
        # templates is at aioncode/internal/templates/
        internal_dir = Path(__file__).resolve().parent.parent  # → aioncode/internal/
        tmpl_check = internal_dir / "templates"
        if tmpl_check.exists():
            # Dev / installed package mode
            commands_src = internal_dir.parent.parent / "commands"  # → repo root/commands/
            templates_src = tmpl_check
        else:
            # Fallback standalone
            script_dir = Path(__file__).resolve().parent
            commands_src = script_dir / "commands"
            templates_src = script_dir / "templates"

    aion_template_dir = templates_src / "aion"
    claude_md_tpl = templates_src / "CLAUDE.md.tpl"
    return commands_src, templates_src, aion_template_dir, claude_md_tpl


COMMANDS_SRC, TEMPLATES_SRC, AION_TEMPLATE_DIR, CLAUDE_MD_TPL = _resolve_source_paths()


def resolve_projects_file() -> Path:
    """Determine the projects.json file location.

    Priority: env override > platform-specific data dir > script dir.
    """
    import os

    env_override = os.environ.get("AIONCODE_PROJECTS_FILE")
    if env_override:
        return Path(env_override)

    internal_dir = Path(__file__).resolve().parent.parent  # aioncode/internal/
    if _FROZEN or (internal_dir / "templates").exists():
        # Package/frozen mode: use platform-specific data directory
        if sys.platform == "win32":
            base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            data_dir = base / "AionCode"
        else:
            xdg = os.environ.get("XDG_DATA_HOME", "")
            data_dir = Path(xdg) / "aioncode" if xdg else Path.home() / ".config" / "aioncode"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "projects.json"

    # Standalone mode: beside script
    return Path(__file__).resolve().parent / "projects.json"
