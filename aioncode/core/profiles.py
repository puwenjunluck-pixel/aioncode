"""Command profiles — role-based command recommendations, platform config, and profile persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlatformConfig:
    """Platform-specific paths and conventions."""

    name: str
    label: str
    cmd_dir: str
    instructions_file: str
    instructions_tpl: str
    cmd_prefix: str
    cli_binary: str
    global_dir_name: str = ".claude"  # relative to $HOME
    skills_dir: str = "skills"  # relative to global_dir
    has_hooks: bool = True
    has_settings: bool = True

    @property
    def global_dir(self) -> Path:
        return Path.home() / self.global_dir_name


PLATFORMS: dict[str, PlatformConfig] = {
    "claude": PlatformConfig(
        name="claude",
        label="Claude Code",
        cmd_dir=".claude/commands",
        instructions_file=".claude/CLAUDE.md",
        instructions_tpl="CLAUDE.md.tpl",
        cmd_prefix="/project:",
        cli_binary="claude",
    ),
    "antigravity": PlatformConfig(
        name="antigravity",
        label="Google Antigravity",
        cmd_dir=".agent/workflows",
        instructions_file="GEMINI.md",
        instructions_tpl="GEMINI.md.tpl",
        cmd_prefix="/",
        cli_binary="antigravity",
        global_dir_name=".gemini",
        skills_dir="antigravity/skills",
        has_hooks=False,
        has_settings=False,
    ),
}

DEFAULT_PLATFORM = "claude"


@dataclass(frozen=True)
class CommandInfo:
    """Metadata for a single AionCode command."""

    name: str
    label: str
    core: bool = False  # True = always installed, cannot deselect


ALL_COMMANDS: list[CommandInfo] = [
    CommandInfo("aion-help", "帮助与引导", core=True),
    CommandInfo("aion-scan", "项目扫描"),
    CommandInfo("aion-think", "讨论 · 碰撞 · 思考"),
    CommandInfo("aion-plan", "实现规划"),
    CommandInfo("aion-review", "代码审查", core=True),
    CommandInfo("aion-qa", "浏览器 QA 测试"),
    CommandInfo("aion-fix", "Bug 修复"),
    CommandInfo("aion-commit", "安全提交", core=True),
    CommandInfo("aion-loop", "自动流水线"),
    CommandInfo("aion-save", "上下文保存"),
    CommandInfo("aion-audit", "安全+性能审计"),
]

CORE_COMMANDS: frozenset[str] = frozenset(c.name for c in ALL_COMMANDS if c.core)

# Role presets — which non-core commands are recommended per role.
_SHARED = {"aion-scan", "aion-save"}

ROLE_PRESETS: dict[str, frozenset[str]] = {
    "designer": _SHARED | {"aion-think"},
    "frontend": _SHARED | {"aion-think", "aion-qa", "aion-fix"},
    "backend": _SHARED | {"aion-think", "aion-plan", "aion-qa", "aion-fix", "aion-audit"},
    "tester": _SHARED | {"aion-qa", "aion-fix"},
    "fullstack": _SHARED | {"aion-think", "aion-plan", "aion-qa", "aion-fix", "aion-loop", "aion-audit"},
}


def get_recommended(role: str) -> set[str]:
    """Return recommended command names for a given role."""
    preset = ROLE_PRESETS.get(role, ROLE_PRESETS["fullstack"])
    return set(CORE_COMMANDS) | set(preset)


def read_profile(config_path: Path) -> dict[str, str | list[str]] | None:
    """Read profile and installed commands from config.yml."""
    if not config_path.is_file():
        return None
    text = config_path.read_text(encoding="utf-8")
    result: dict[str, str | list[str]] = {}
    in_commands = False
    installed: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("project_type:"):
            result["project_type"] = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("platform:") and line.startswith("  "):
            result["platform"] = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped.startswith("role:") and "profile" not in line:
            # Only capture role under profile section (indented)
            if line.startswith("  "):
                result["role"] = stripped.split(":", 1)[1].strip().strip('"')
        elif stripped == "installed:":
            in_commands = True
        elif in_commands and stripped.startswith("- "):
            installed.append(stripped[2:].strip())
        elif in_commands and not stripped.startswith("-") and stripped:
            in_commands = False
    if installed:
        result["commands"] = installed
    return result if result.get("project_type") else None


def write_profile(
    config_path: Path,
    project_type: str,
    role: str,
    commands: list[str],
    platform: str = DEFAULT_PLATFORM,
) -> None:
    """Append or update profile + commands section in config.yml."""
    lines: list[str] = []
    if config_path.is_file():
        text = config_path.read_text(encoding="utf-8")
        # Remove existing profile/commands sections
        skip = False
        for line in text.splitlines():
            stripped = line.strip()
            if stripped in ("profile:", "commands:"):
                skip = True
                continue
            if skip and (line.startswith("  ") or line.startswith("    ")):
                continue
            skip = False
            lines.append(line)
        # Remove trailing blank lines
        while lines and not lines[-1].strip():
            lines.pop()

    lines.append("")
    lines.append("profile:")
    lines.append(f'  project_type: "{project_type}"')
    lines.append(f'  role: "{role}"')
    lines.append(f'  platform: "{platform}"')
    lines.append("")
    lines.append("commands:")
    lines.append("  installed:")
    for cmd in sorted(commands):
        lines.append(f"    - {cmd}")
    lines.append("")
    config_path.write_text("\n".join(lines), encoding="utf-8")
