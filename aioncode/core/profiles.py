"""Command profiles — role-based command recommendations and profile persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandInfo:
    """Metadata for a single AionCode command."""

    name: str
    label: str
    core: bool = False  # True = always installed, cannot deselect


ALL_COMMANDS: list[CommandInfo] = [
    CommandInfo("aion-help", "帮助与引导", core=True),
    CommandInfo("aion-status", "项目状态", core=True),
    CommandInfo("aion-scan", "项目扫描"),
    CommandInfo("aion-think", "假设挑战"),
    CommandInfo("aion-design", "需求设计"),
    CommandInfo("aion-plan", "修订方案"),
    CommandInfo("aion-demo", "UI 原型"),
    CommandInfo("aion-impl", "代码实现"),
    CommandInfo("aion-test", "测试生成"),
    CommandInfo("aion-verify", "质量验证"),
    CommandInfo("aion-review", "代码审查", core=True),
    CommandInfo("aion-commit", "安全提交", core=True),
    CommandInfo("aion-bug", "Bug 管理"),
    CommandInfo("aion-learn", "规则学习", core=True),
    CommandInfo("aion-save", "上下文保存"),
    CommandInfo("aion-crosscheck", "交叉验证"),
    CommandInfo("aion-loop", "自动流水线"),
    CommandInfo("aion-upgrade", "版本升级"),
]

CORE_COMMANDS: frozenset[str] = frozenset(c.name for c in ALL_COMMANDS if c.core)

# Role presets — which non-core commands are recommended per role.
_SHARED = {"aion-scan", "aion-save"}

ROLE_PRESETS: dict[str, frozenset[str]] = {
    "designer": _SHARED | {"aion-design", "aion-demo"},
    "frontend": _SHARED | {
        "aion-think", "aion-design", "aion-demo",
        "aion-impl", "aion-verify", "aion-bug",
    },
    "backend": _SHARED | {
        "aion-think", "aion-design",
        "aion-impl", "aion-test", "aion-verify", "aion-bug",
    },
    "tester": _SHARED | {"aion-test", "aion-verify", "aion-bug"},
    "fullstack": _SHARED | {
        "aion-think", "aion-design", "aion-plan", "aion-demo",
        "aion-impl", "aion-test", "aion-verify", "aion-bug",
    },
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
    config_path: Path, project_type: str, role: str, commands: list[str],
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
    lines.append("")
    lines.append("commands:")
    lines.append("  installed:")
    for cmd in sorted(commands):
        lines.append(f"    - {cmd}")
    lines.append("")
    config_path.write_text("\n".join(lines), encoding="utf-8")
