"""Team configuration — read/write team.yml + Claude Code settings (custom YAML parser)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from aioncode.internal.dashboard.config import TEAM_FILE

CLAUDE_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
_PROJECT_LOCAL_SETTINGS = ".claude/settings.local.json"


def _read_project_settings(project_path: str) -> dict:
    """Read {project}/.claude/settings.local.json."""
    path = Path(project_path) / _PROJECT_LOCAL_SETTINGS
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def read_team_config(project_path: str) -> dict:
    """Read and parse team.yml (no external YAML dependency).

    Parses sections: team, models, risk_keywords.
    Models are parsed as a list of objects (each with name, provider, etc.).
    """
    team_path = Path(project_path) / TEAM_FILE
    if not team_path.exists():
        return {"team": [], "models": [], "risk_keywords": {}}

    content = team_path.read_text(encoding="utf-8")
    config: dict = {"team": [], "models": [], "risk_keywords": {}}
    current_section: str | None = None
    current_member: dict | None = None
    current_model: dict | None = None

    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Section headers — only match top-level (non-indented) lines
        is_top_level = line == stripped or not line[0].isspace()
        if is_top_level and (stripped == "team:" or stripped == "team: []"):
            current_section = "team"
            current_member = None
            if current_model:
                config["models"].append(current_model)
                current_model = None
            continue
        if is_top_level and stripped.startswith("models:"):
            current_section = "models"
            if current_member:
                config["team"].append(current_member)
                current_member = None
            current_model = None
            continue
        if is_top_level and stripped.startswith("risk_keywords:"):
            current_section = "risk_keywords"
            if current_member:
                config["team"].append(current_member)
                current_member = None
            if current_model:
                config["models"].append(current_model)
                current_model = None
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
            if stripped.startswith("- name:"):
                if current_model:
                    config["models"].append(current_model)
                current_model = {"name": stripped[len("- name:") :].strip().strip('"')}
            elif current_model and ":" in stripped:
                line_content = stripped
                if line_content.startswith("- "):
                    line_content = line_content[2:]
                key, _, val = line_content.partition(":")
                key = key.strip()
                val = val.strip().strip('"')
                if val.startswith("[") and val.endswith("]"):
                    val = [v.strip().strip('"') for v in val[1:-1].split(",") if v.strip()]
                current_model[key] = val

        elif current_section == "risk_keywords" and ":" in stripped:
            if stripped.startswith("- "):
                stripped = stripped[2:]
            key, _, val = stripped.partition(":")
            config["risk_keywords"][key.strip()] = val.strip().strip('"')

    # Flush last items
    if current_member:
        config["team"].append(current_member)
    if current_model:
        config["models"].append(current_model)

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
    models = config.get("models", [])
    if models and isinstance(models, list):
        lines.append("models:")
        for model in models:
            lines.append(f'  - name: "{model.get("name", "")}"')
            for key, val in model.items():
                if key == "name":
                    continue
                if isinstance(val, list):
                    val_str = ", ".join(f'"{v}"' for v in val)
                    lines.append(f"    {key}: [{val_str}]")
                else:
                    lines.append(f'    {key}: "{val}"')
    else:
        lines.append("models: []")

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


def read_claude_settings() -> dict:
    """Read ~/.claude/settings.json."""
    if not CLAUDE_SETTINGS_PATH.exists():
        return {}
    try:
        return json.loads(CLAUDE_SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_claude_settings(data: dict) -> dict:
    """Write ~/.claude/settings.json preserving structure.

    Returns:
        dict with 'ok' and 'message' keys.
    """
    try:
        CLAUDE_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        CLAUDE_SETTINGS_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return {"ok": True, "message": "Claude settings updated"}
    except OSError as e:
        return {"ok": False, "message": str(e)}


def check_env_vars(names: list[str]) -> dict[str, bool]:
    """Check which environment variables are set (without revealing values)."""
    result = {}
    for name in names:
        if isinstance(name, str) and name:
            result[name] = name in os.environ and bool(os.environ[name])
    return result


_THIRD_PARTY_ENV_KEYS = [
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "API_TIMEOUT_MS",
]


def switch_model(project_path: str, provider_name: str, model_name: str, api_key_override: str = "") -> dict:
    """Switch active model by writing to ~/.claude/settings.json (global).

    For official Anthropic: sets model field, clears all custom env vars.
    For custom providers: sets ANTHROPIC_BASE_URL, ANTHROPIC_AUTH_TOKEN, and all model-family
    env vars so Claude Code skips its internal model-name validation.
    api_key_override takes precedence over os.environ lookup.
    Note: CC daemon broadcasts env vars to all sessions, so project-level isolation is not
    achievable at runtime. Global settings is the only effective target.
    """
    settings = read_claude_settings()
    env = settings.get("env", {})

    if provider_name == "__official__":
        settings["model"] = model_name
        # Set to empty instead of removing — running CC can't unset env vars via hot-reload,
        # but treats empty string as falsy (same effect as unset)
        for key in _THIRD_PARTY_ENV_KEYS:
            env[key] = ""
        env.pop("ANTHROPIC_API_KEY", None)
    else:
        config = read_team_config(project_path)
        provider = next((m for m in config.get("models", []) if m.get("name") == provider_name), None)
        if not provider:
            return {"ok": False, "message": f"Provider '{provider_name}' not found"}

        api_key_env_name = provider.get("api_key_env", "")
        api_key = api_key_override or os.environ.get(api_key_env_name, "")
        if not api_key:
            return {"ok": False, "message": f"环境变量 '{api_key_env_name}' 未设置且未提供 API Key"}

        # Clear official model field — third-party uses env vars only
        settings.pop("model", None)
        env["ANTHROPIC_BASE_URL"] = provider.get("endpoint", "")
        env["ANTHROPIC_AUTH_TOKEN"] = api_key
        # Set all model-family vars so CC skips hardcoded model-name validation
        for key in [
            "ANTHROPIC_MODEL",
            "ANTHROPIC_SMALL_FAST_MODEL",
            "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "ANTHROPIC_DEFAULT_OPUS_MODEL",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL",
        ]:
            env[key] = model_name
        env["API_TIMEOUT_MS"] = "3000000"
        env.pop("ANTHROPIC_API_KEY", None)

    settings["env"] = env
    result = write_claude_settings(settings)
    if result["ok"]:
        return {
            "ok": True,
            "active_provider": provider_name,
            "active_model": model_name,
            "message": f"Switched to {provider_name}/{model_name}",
        }
    return result


def get_current_model(project_path: str = "") -> dict:
    """Read current active model — project settings take precedence over global.

    Returns:
        dict with model, base_url, anthropic_model keys.
    """
    proj = _read_project_settings(project_path) if project_path else {}
    proj_env = proj.get("env", {})

    # Project-level overrides global
    if proj_env.get("ANTHROPIC_BASE_URL") or proj.get("model"):
        return {
            "model": proj.get("model", ""),
            "base_url": proj_env.get("ANTHROPIC_BASE_URL", ""),
            "anthropic_model": proj_env.get("ANTHROPIC_MODEL", ""),
        }

    global_settings = read_claude_settings()
    global_env = global_settings.get("env", {})
    return {
        "model": global_settings.get("model", ""),
        "base_url": global_env.get("ANTHROPIC_BASE_URL", ""),
        "anthropic_model": global_env.get("ANTHROPIC_MODEL", ""),
    }


def is_admin(request=None) -> bool:  # noqa: ARG001
    """Check admin privileges. Phase 1: always True (local deployment)."""
    return True
