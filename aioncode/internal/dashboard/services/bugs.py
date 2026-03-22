"""Bug management — list, filter, statistics."""

from __future__ import annotations

from pathlib import Path

from aioncode.internal.dashboard.config import BUGS_DIR


def _parse_bug_frontmatter(filepath: Path) -> dict:
    """Parse YAML-like frontmatter from a bug markdown file."""
    content = filepath.read_text(encoding="utf-8")
    meta: dict[str, str] = {"file": filepath.name, "id": filepath.stem}

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        meta["title"] = filepath.stem
        meta["body"] = content
        return meta

    in_frontmatter = True
    body_lines: list[str] = []
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---" and in_frontmatter:
            in_frontmatter = False
            body_lines = lines[i + 1 :]
            break
        if in_frontmatter and ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()

    meta["body"] = "\n".join(body_lines).strip()
    if "title" not in meta:
        meta["title"] = filepath.stem
    return meta


def list_bugs(project_path: str, filters: dict | None = None) -> list[dict]:
    """List bugs from .aion/bugs/ with optional filters.

    Filters: status, assignee, severity, category.
    """
    bugs_dir = Path(project_path) / BUGS_DIR
    if not bugs_dir.is_dir():
        return []

    bugs = []
    for f in sorted(bugs_dir.iterdir()):
        if not f.is_file() or f.suffix != ".md":
            continue
        bug = _parse_bug_frontmatter(f)
        if filters:
            match = True
            for key, val in filters.items():
                if key in bug and bug[key] != val:
                    match = False
                    break
            if not match:
                continue
        bugs.append(bug)
    return bugs


def get_bug_stats(project_path: str) -> dict:
    """Compute bug statistics."""
    bugs = list_bugs(project_path)
    if not bugs:
        return {"total": 0, "by_status": {}, "by_severity": {}, "by_category": {}}

    by_status: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_category: dict[str, int] = {}
    assignee_load: dict[str, int] = {}
    financial_risk = 0

    for bug in bugs:
        status = bug.get("status", "open")
        by_status[status] = by_status.get(status, 0) + 1

        severity = bug.get("severity", "medium")
        by_severity[severity] = by_severity.get(severity, 0) + 1

        category = bug.get("category", "general")
        by_category[category] = by_category.get(category, 0) + 1

        assignee = bug.get("assignee", "unassigned")
        if status not in ("closed", "verified"):
            assignee_load[assignee] = assignee_load.get(assignee, 0) + 1

        risk = bug.get("risk_level", "")
        if risk == "financial":
            financial_risk += 1

    return {
        "total": len(bugs),
        "by_status": by_status,
        "by_severity": by_severity,
        "by_category": by_category,
        "assignee_load": assignee_load,
        "financial_risk": financial_risk,
    }
