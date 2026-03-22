"""Project statistics computation."""

from __future__ import annotations

import re
from pathlib import Path

from aioncode import __version__


def _count_rules_in_file(filepath: Path) -> int:
    """Count rule entries (lines starting with '- **') in a markdown file."""
    if not filepath.exists():
        return 0
    count = 0
    for line in filepath.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("- **"):
            count += 1
    return count


def _count_files_in_dir(dirpath: Path, extensions: tuple[str, ...] = (".md",)) -> int:
    """Count files with given extensions in a directory."""
    if not dirpath.is_dir():
        return 0
    return sum(1 for f in dirpath.iterdir() if f.is_file() and f.suffix in extensions)


def _last_activity(changelog_path: Path) -> str | None:
    """Extract the latest date from changelog.md."""
    if not changelog_path.exists():
        return None
    content = changelog_path.read_text(encoding="utf-8")
    dates = re.findall(r"## (\d{4}-\d{2}-\d{2})", content)
    return dates[0] if dates else None


def get_project_stats(project_path: str) -> dict:
    """Compute full project statistics."""
    root = Path(project_path)
    aion = root / ".aion"

    if not aion.is_dir():
        return {"ok": False, "message": "No .aion/ directory found"}

    rules_dir = aion / "rules"
    style_count = _count_rules_in_file(rules_dir / "style.md")
    pitfalls_count = _count_rules_in_file(rules_dir / "pitfalls.md")
    perf_count = _count_rules_in_file(rules_dir / "perf.md")

    specs_count = _count_files_in_dir(aion / "specs")
    plans_count = _count_files_in_dir(aion / "plans")
    reviews_count = _count_files_in_dir(aion / "reviews")
    bugs_count = _count_files_in_dir(aion / "bugs")

    last = _last_activity(aion / "changelog.md")

    # Version detection
    version = "unknown"
    version_file = aion / "version"
    if version_file.exists():
        version = version_file.read_text(encoding="utf-8").strip()

    # Command count
    claude_cmds = root / ".claude" / "commands"
    cmd_count = _count_files_in_dir(claude_cmds) if claude_cmds.is_dir() else 0

    return {
        "ok": True,
        "project_name": root.name,
        "project_path": str(root),
        "rules": {
            "style": style_count,
            "pitfalls": pitfalls_count,
            "perf": perf_count,
            "total": style_count + pitfalls_count + perf_count,
        },
        "specs": specs_count,
        "plans": plans_count,
        "reviews": reviews_count,
        "bugs": bugs_count,
        "commands": cmd_count,
        "version": version,
        "last_activity": last,
        "aioncode_version": __version__,
    }
