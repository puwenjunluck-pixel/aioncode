"""Team configuration — read/write team.yml (custom YAML parser)."""

from __future__ import annotations

from pathlib import Path

from aioncode.internal.dashboard.config import TEAM_FILE


def read_team_config(project_path: str) -> dict:
    """Read and parse team.yml (no external YAML dependency).

    Parses sections: team, models, risk_keywords.
    """
    team_path = Path(project_path) / TEAM_FILE
    if not team_path.exists():
        return {"team": [], "models": {}, "risk_keywords": {}}

    content = team_path.read_text(encoding="utf-8")
    config: dict = {"team": [], "models": {}, "risk_keywords": {}}
    current_section: str | None = None
    current_member: dict | None = None

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Section headers
        if stripped == "team:" or stripped == "team: []":
            current_section = "team"
            current_member = None
            continue
        if stripped.startswith("models:"):
            current_section = "models"
            current_member = None
            continue
        if stripped.startswith("risk_keywords:"):
            current_section = "risk_keywords"
            current_member = None
            continue

        if current_section == "team":
            if stripped.startswith("- name:"):
                if current_member:
                    config["team"].append(current_member)
                current_member = {"name": stripped[len("- name:") :].strip().strip('"')}
            elif current_member and ":" in stripped:
                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"')
                if val.startswith("[") and val.endswith("]"):
                    val = [v.strip().strip('"') for v in val[1:-1].split(",") if v.strip()]
                current_member[key] = val

        elif current_section == "models":
            if stripped.startswith("- ") and ":" in stripped[2:]:
                # Skip list items like "- provider: anthropic"
                continue
            if ":" in stripped:
                key, _, val = stripped.partition(":")
                config["models"][key.strip()] = val.strip().strip('"')

        elif current_section == "risk_keywords" and ":" in stripped:
            if stripped.startswith("- "):
                stripped = stripped[2:]
            key, _, val = stripped.partition(":")
            config["risk_keywords"][key.strip()] = val.strip().strip('"')

    # Don't forget last member
    if current_member:
        config["team"].append(current_member)

    return config


def write_team_config(project_path: str, config: dict) -> dict:
    """Write team.yml (no external YAML dependency).

    Returns:
        dict with 'ok' and 'message' keys.
    """
    team_path = Path(project_path) / TEAM_FILE
    lines: list[str] = ["# Team Configuration", ""]

    # Team section
    team = config.get("team", [])
    if team:
        lines.append("team:")
        for member in team:
            lines.append(f'  - name: "{member.get("name", "")}"')
            for key, val in member.items():
                if key == "name":
                    continue
                if isinstance(val, list):
                    val_str = ", ".join(f'"{v}"' for v in val)
                    lines.append(f"    {key}: [{val_str}]")
                else:
                    lines.append(f'    {key}: "{val}"')
    else:
        lines.append("team: []")

    lines.append("")

    # Models section
    models = config.get("models", {})
    lines.append("models:")
    if models:
        for key, val in models.items():
            lines.append(f'  {key}: "{val}"')
    lines.append("")

    # Risk keywords section
    risk = config.get("risk_keywords", {})
    lines.append("risk_keywords:")
    if risk:
        for key, val in risk.items():
            lines.append(f"  {key}: {val}")
    lines.append("")

    try:
        team_path.parent.mkdir(parents=True, exist_ok=True)
        team_path.write_text("\n".join(lines), encoding="utf-8")
        return {"ok": True, "message": "Team configuration saved"}
    except OSError as e:
        return {"ok": False, "message": str(e)}


def is_admin(request=None) -> bool:  # noqa: ARG001
    """Check admin privileges. Phase 1: always True (local deployment)."""
    return True
