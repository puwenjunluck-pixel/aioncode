"""Skill management — list installed skills and marketplace plugins."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path


def _claude_home() -> Path:
    """Return the Claude home directory (~/.claude)."""
    return Path.home() / ".claude"


def _agents_home() -> Path:
    """Return the agents home directory (~/.agents)."""
    return Path.home() / ".agents"


def _parse_skill_frontmatter(filepath: Path) -> dict:
    """Parse YAML-like frontmatter from a SKILL.md file.

    Returns dict with 'meta' (frontmatter fields) and 'body' (markdown content).
    """
    content = filepath.read_text(encoding="utf-8")
    meta: dict[str, str] = {}
    lines = content.splitlines()

    if not lines or lines[0].strip() != "---":
        return {"meta": meta, "body": content}

    body_lines: list[str] = []
    in_frontmatter = True
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---" and in_frontmatter:
            in_frontmatter = False
            body_lines = lines[i + 1 :]
            break
        if in_frontmatter and ":" in line:
            key, _, val = line.partition(":")
            meta[key.strip()] = val.strip()

    return {"meta": meta, "body": "\n".join(body_lines).strip()}


def _detect_skill_source(skill_dir: Path) -> tuple[str, str]:
    """Detect whether a skill is user-installed, agent-provided, or from a plugin.

    Returns (source_type, source_url).
    """
    agents_skills = _agents_home() / "skills"

    # Check if symlink pointing into ~/.agents/skills/
    if skill_dir.is_symlink():
        try:
            target = skill_dir.resolve()
            if str(target).startswith(str(agents_skills)):
                # Try to get source URL from skill-lock.json
                url = _get_skill_lock_url(skill_dir.name)
                return ("agent", url)
        except OSError:
            pass

    # Check skill-lock.json for agent skills
    url = _get_skill_lock_url(skill_dir.name)
    if url:
        return ("agent", url)

    return ("user", "")


def _get_skill_lock_url(skill_name: str) -> str:
    """Get source URL from ~/.agents/.skill-lock.json."""
    lock_file = _agents_home() / ".skill-lock.json"
    if not lock_file.is_file():
        return ""
    try:
        data = json.loads(lock_file.read_text(encoding="utf-8"))
        skills = data.get("skills", {})
        if skill_name in skills:
            return skills[skill_name].get("source", "")
    except (OSError, json.JSONDecodeError, KeyError):
        pass
    return ""


def list_skills() -> list[dict]:
    """List all installed skills from ~/.claude/skills/.

    Returns a list of skill dicts with name, description, source info, etc.
    """
    skills_dir = _claude_home() / "skills"
    if not skills_dir.is_dir():
        return []

    skills = []
    try:
        for entry in sorted(skills_dir.iterdir()):
            if not entry.is_dir():
                continue
            # Skip broken symlinks
            if entry.is_symlink() and not entry.exists():
                continue

            skill_md = entry / "SKILL.md"
            if not skill_md.is_file():
                continue

            try:
                parsed = _parse_skill_frontmatter(skill_md)
                meta = parsed["meta"]
                source, source_url = _detect_skill_source(entry)

                # Check for supporting directories
                has_scripts = (entry / "scripts").is_dir()
                has_references = (entry / "references").is_dir()
                has_assets = (entry / "assets").is_dir()

                skills.append(
                    {
                        "name": meta.get("name", entry.name),
                        "dir_name": entry.name,
                        "description": meta.get("description", ""),
                        "allowed_tools": meta.get("allowed-tools", ""),
                        "source": source,
                        "source_url": source_url,
                        "is_symlink": entry.is_symlink(),
                        "has_scripts": has_scripts,
                        "has_references": has_references,
                        "has_assets": has_assets,
                    }
                )
            except OSError:
                continue
    except (OSError, PermissionError):
        pass

    return skills


def read_skill(name: str) -> dict:
    """Read a skill's full SKILL.md content and file list.

    Args:
        name: Skill directory name (sanitized to prevent path traversal).

    Returns:
        Dict with ok, name, meta, body, files.
    """
    # Sanitize: remove path separators and dots
    safe_name = re.sub(r"[/\\.]", "", name)
    if not safe_name:
        return {"ok": False, "message": "Invalid skill name"}

    skill_dir = _claude_home() / "skills" / safe_name
    skill_md = skill_dir / "SKILL.md"

    if not skill_md.is_file():
        return {"ok": False, "message": f"Skill not found: {name}"}

    try:
        parsed = _parse_skill_frontmatter(skill_md)

        # Collect all files in the skill directory
        files = []
        try:
            for f in sorted(skill_dir.rglob("*")):
                if f.is_file():
                    files.append(str(f.relative_to(skill_dir)))
        except OSError:
            pass

        return {
            "ok": True,
            "name": safe_name,
            "meta": parsed["meta"],
            "body": parsed["body"],
            "files": files,
        }
    except OSError as e:
        return {"ok": False, "message": str(e)}


def _load_installed_plugin_names() -> set[str]:
    """Load names of installed plugins from installed_plugins.json."""
    installed_file = _claude_home() / "plugins" / "installed_plugins.json"
    if not installed_file.is_file():
        return set()
    try:
        data = json.loads(installed_file.read_text(encoding="utf-8"))
        names: set[str] = set()
        for key in data.get("plugins", {}):
            names.add(key.split("@")[0] if "@" in key else key)
        return names
    except (OSError, json.JSONDecodeError):
        return set()


def _scan_marketplace_dir(market_dir: Path, market_name: str, installed: set[str]) -> list[dict]:
    """Scan a single marketplace directory for plugin metadata."""
    plugins_dir = market_dir / "plugins"
    if not plugins_dir.is_dir():
        return []
    results = []
    try:
        for entry in sorted(plugins_dir.iterdir()):
            if not entry.is_dir():
                continue
            plugin_json = entry / ".claude-plugin" / "plugin.json"
            if not plugin_json.is_file():
                continue
            try:
                pdata = json.loads(plugin_json.read_text(encoding="utf-8"))
                pname = pdata.get("name", entry.name)
                results.append(
                    {
                        "name": pname,
                        "description": pdata.get("description", ""),
                        "author": pdata.get("author", ""),
                        "marketplace": market_name,
                        "installed": pname in installed or entry.name in installed,
                    }
                )
            except (OSError, json.JSONDecodeError):
                continue
    except (OSError, PermissionError):
        pass
    return results


def list_marketplace_plugins() -> list[dict]:
    """List available plugins from known marketplaces.

    Cross-references with installed_plugins.json to mark installed status.
    """
    marketplaces_file = _claude_home() / "plugins" / "known_marketplaces.json"
    if not marketplaces_file.is_file():
        return []
    try:
        marketplaces = json.loads(marketplaces_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    installed = _load_installed_plugin_names()
    plugins: list[dict] = []
    for market_name, market_info in marketplaces.items():
        install_loc = market_info.get("installLocation", "")
        if install_loc:
            plugins.extend(_scan_marketplace_dir(Path(install_loc), market_name, installed))
    return plugins


def delete_skill(name: str) -> dict:
    """Delete an installed skill by removing its directory.

    Args:
        name: Skill directory name (sanitized to prevent path traversal).

    Returns:
        Dict with ok and message.
    """
    safe_name = re.sub(r"[/\\.]", "", name)
    if not safe_name:
        return {"ok": False, "message": "Invalid skill name"}

    skill_dir = _claude_home() / "skills" / safe_name
    if not skill_dir.exists():
        return {"ok": False, "message": f"Skill not found: {name}"}

    try:
        # Handle symlinks: just unlink, don't remove target
        if skill_dir.is_symlink():
            skill_dir.unlink()
        else:
            shutil.rmtree(skill_dir)
        return {"ok": True, "message": f"Skill '{safe_name}' removed"}
    except OSError as e:
        return {"ok": False, "message": str(e)}


def install_plugin(name: str) -> dict:
    """Install a marketplace plugin via claude CLI.

    Args:
        name: Plugin name to install.

    Returns:
        Dict with ok and message.
    """
    safe_name = re.sub(r"[/\\.]", "", name)
    if not safe_name:
        return {"ok": False, "message": "Invalid plugin name"}

    try:
        result = subprocess.run(
            ["claude", "plugin", "add", safe_name, "--yes"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            return {"ok": True, "message": f"Plugin '{safe_name}' installed"}
        return {"ok": False, "message": result.stderr.strip() or result.stdout.strip() or "Install failed"}
    except FileNotFoundError:
        return {"ok": False, "message": "claude CLI not found"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "message": "Install timed out"}
    except OSError as e:
        return {"ok": False, "message": str(e)}
