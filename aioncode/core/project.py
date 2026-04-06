"""Core project operations — shared by CLI and Web.

This module contains pure business logic with no console output
or interactive prompts. CLI and Web layers wrap these functions
with their own presentation.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Directories to scaffold (always create if missing)
SCAFFOLD_DIRS = [
    "refs",
    "prototypes",
    "specs",
    "plans",
    "reviews",
    "contracts",
    "monitor",
    "tests",
    "tests/reports",
    "tests/perf",
    "tests/ui",
    "bugs",
]

# Source code file extensions for project type detection
SOURCE_EXTENSIONS = {
    ".ts",
    ".js",
    ".py",
    ".go",
    ".java",
    ".vue",
    ".tsx",
    ".jsx",
    ".rb",
    ".rs",
    ".kt",
    ".swift",
    ".cs",
    ".cpp",
    ".c",
    ".php",
}

# Existing doc patterns to suggest importing
DOC_PATTERNS = [
    "docs/architecture.md",
    "docs/ARCHITECTURE.md",
    "ARCHITECTURE.md",
    "docs/api.md",
    "docs/API.md",
    "DESIGN.md",
    "docs/design.md",
]

# .gitignore entries AionCode needs
GITIGNORE_ENTRIES = [
    ".aion/monitor/events.jsonl",
    ".aion/sessions.jsonl",
]


@dataclass
class ProjectInfo:
    """Detected project characteristics."""

    is_new: bool = True
    has_aion: bool = False
    has_claude_dir: bool = False
    has_claude_md: bool = False
    has_git: bool = False
    installed_version: str = "0.0"
    source_count: int = 0
    existing_docs: list[str] = field(default_factory=list)


@dataclass
class InitResult:
    """Result of project initialization."""

    ok: bool = True
    message: str = ""
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    project: ProjectInfo = field(default_factory=ProjectInfo)
    source_version: str = "0.0"


def _get_templates_dir() -> Path:
    """Locate the bundled templates directory."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base / "templates"
    return Path(__file__).parent.parent / "internal" / "templates"


def _get_commands_dir() -> Path:
    """Locate the bundled commands directory."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        return base / "commands"
    return Path(__file__).parent.parent.parent / "commands"


def detect_project(target: Path) -> ProjectInfo:
    """Detect project characteristics (pure, no side effects)."""
    info = ProjectInfo()
    aion_dir = target / ".aion"

    if aion_dir.is_dir():
        info.has_aion = True
        info.is_new = False
        config = aion_dir / "config.yml"
        if config.is_file():
            try:
                text = config.read_text(encoding="utf-8")
                for line in text.splitlines():
                    if line.startswith("version:"):
                        v = line.split('"')[1] if '"' in line else line.split(":")[1].strip()
                        info.installed_version = v
                        break
            except (OSError, IndexError):
                pass

    claude_dir = target / ".claude"
    info.has_claude_dir = claude_dir.is_dir()
    info.has_claude_md = (claude_dir / "CLAUDE.md").is_file()
    info.has_git = (target / ".git").is_dir()

    count = 0
    try:
        for p in target.rglob("*"):
            if count >= 500:
                break
            parts = p.parts
            if any(
                part.startswith(".") or part in ("node_modules", "venv", "__pycache__", "dist", "build")
                for part in parts
            ):
                continue
            if p.is_file() and p.suffix in SOURCE_EXTENSIONS:
                count += 1
    except OSError:
        pass
    info.source_count = count
    if count > 0:
        info.is_new = False

    for pattern in DOC_PATTERNS:
        if (target / pattern).is_file():
            info.existing_docs.append(pattern)

    return info


def get_source_version() -> str:
    """Read version from bundled templates."""
    config = _get_templates_dir() / "aion" / "config.yml"
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


@dataclass
class InitProfile:
    """User profile for selective command installation."""

    project_type: str = "fullstack"
    role: str = "fullstack"
    selected_commands: list[str] = field(default_factory=list)
    platform: str = "claude"


def init_project(
    target: Path,
    *,
    upgrade: bool = False,
    update_gitignore: bool = True,
    profile: InitProfile | None = None,
) -> InitResult:
    """Initialize or upgrade .aion/ project intelligence.

    Pure logic — no console output, no interactive prompts.
    CLI and Web layers handle presentation.

    Args:
        target: Project root directory.
        upgrade: If True, update version in config.yml.
        update_gitignore: If True, add missing entries to .gitignore.
        profile: If set, install only selected commands and save profile.

    Returns:
        InitResult with details of what was created/updated/skipped.
    """
    target = target.resolve()
    result = InitResult()

    if not target.is_dir():
        result.ok = False
        result.message = f"Directory not found: {target}"
        return result

    import os

    if not os.access(target, os.W_OK):
        result.ok = False
        result.message = f"No write permission: {target}"
        return result

    templates_dir = _get_templates_dir()
    commands_dir = _get_commands_dir()
    result.source_version = get_source_version()
    result.project = detect_project(target)

    # Resolve platform config
    from aioncode.core.profiles import DEFAULT_PLATFORM, PLATFORMS

    platform_name = profile.platform if profile else DEFAULT_PLATFORM
    platform_cfg = PLATFORMS.get(platform_name, PLATFORMS[DEFAULT_PLATFORM])

    # 1. Copy commands to platform-specific directory (filtered by profile)
    cmd_dst = target / platform_cfg.cmd_dir
    cmd_dst.mkdir(parents=True, exist_ok=True)
    cmd_rel = platform_cfg.cmd_dir  # for result messages
    selected = set(profile.selected_commands) if profile else None
    source_commands = set()
    # Prefix transform: source uses /project: (Claude Code), convert for target platform
    src_prefix = "/project:"
    tgt_prefix = platform_cfg.cmd_prefix
    needs_prefix_transform = src_prefix != tgt_prefix
    if commands_dir.is_dir():
        for f in sorted(commands_dir.glob("*.md")):
            source_commands.add(f.stem)
            if selected is not None and f.stem not in selected:
                result.skipped.append(f"{cmd_rel}/{f.name}")
                continue
            dst = cmd_dst / f.name
            if needs_prefix_transform:
                content = f.read_text(encoding="utf-8")
                content = content.replace(src_prefix, tgt_prefix)
                dst.write_text(content, encoding="utf-8")
            else:
                shutil.copy2(f, dst)
            result.updated.append(f"{cmd_rel}/{f.name}")

    # 1.5. Clean up stale aion-* command files (always based on source truth)
    for existing in sorted(cmd_dst.glob("aion-*.md")):
        if existing.stem not in source_commands:
            existing.unlink()
            result.updated.append(f"{cmd_rel}/{existing.name} (removed)")

    # 2. Scaffold .aion/ (never overwrite existing files)
    aion_src = templates_dir / "aion"
    aion_dst = target / ".aion"
    if aion_src.is_dir():
        for f in sorted(aion_src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(aion_src)
            dst_file = aion_dst / rel
            if not dst_file.exists():
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst_file)
                result.created.append(f".aion/{rel}")
            else:
                result.skipped.append(f".aion/{rel}")

    for d in SCAFFOLD_DIRS:
        dir_path = aion_dst / d
        if not dir_path.is_dir():
            dir_path.mkdir(parents=True, exist_ok=True)

    # 2.5. Install bundled skills (never overwrite)
    _install_bundled_skills(templates_dir, platform_cfg, result)

    # 3. Install hooks & settings (Claude Code only)
    if platform_cfg.has_hooks or platform_cfg.has_settings:
        platform_dir = target / platform_cfg.cmd_dir.split("/")[0]  # .claude or .agent
        platform_dir.mkdir(parents=True, exist_ok=True)

    if platform_cfg.has_hooks:
        hooks_src = templates_dir / "claude-hooks.json"
        hooks_dst = target / ".claude" / "hooks.json"
        if hooks_src.is_file():
            if hooks_dst.is_file():
                result.skipped.append(".claude/hooks.json")
            else:
                hooks_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(hooks_src, hooks_dst)
                result.created.append(".claude/hooks.json")

    if platform_cfg.has_settings:
        settings_src = templates_dir / "claude-settings.json"
        settings_dst = target / ".claude" / "settings.local.json"
        if settings_src.is_file():
            if settings_dst.is_file():
                result.skipped.append(".claude/settings.local.json")
            else:
                settings_dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(settings_src, settings_dst)
                result.created.append(".claude/settings.local.json")

    # 4. Project instructions merge (CLAUDE.md or GEMINI.md)
    instructions_path = target / platform_cfg.instructions_file
    tpl_path = templates_dir / platform_cfg.instructions_tpl
    if tpl_path.is_file():
        from aioncode.utils.integrity import merge_claude_md

        tpl_content = tpl_path.read_text(encoding="utf-8")
        # Apply prefix transform to template content
        if needs_prefix_transform:
            tpl_content = tpl_content.replace(src_prefix, tgt_prefix)
        instructions_path.parent.mkdir(parents=True, exist_ok=True)
        existing = instructions_path.read_text(encoding="utf-8") if instructions_path.is_file() else None
        merge_result = merge_claude_md(existing, tpl_content)
        instructions_path.write_text(merge_result.content, encoding="utf-8")

        if merge_result.action == "created":
            result.created.append(platform_cfg.instructions_file)
        else:
            result.updated.append(platform_cfg.instructions_file)

        for warning in merge_result.warnings:
            result.warnings.append(warning)

    # 5. Update version (upgrade mode)
    if upgrade:
        config_path = aion_dst / "config.yml"
        if config_path.is_file():
            text = config_path.read_text(encoding="utf-8")
            new_lines = []
            updated = False
            for line in text.splitlines():
                if line.startswith("version:"):
                    new_lines.append(f'version: "{result.source_version}"')
                    updated = True
                else:
                    new_lines.append(line)
            if not updated:
                new_lines.append(f'version: "{result.source_version}"')
            config_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # 5.5. Save profile to config.yml
    if profile is not None:
        from aioncode.core.profiles import write_profile

        write_profile(
            aion_dst / "config.yml",
            profile.project_type,
            profile.role,
            profile.selected_commands,
            platform=platform_name,
        )

    # 6. Gitignore update
    if update_gitignore:
        gitignore_path = target / ".gitignore"
        missing = _check_gitignore(gitignore_path)
        if missing:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# AionCode runtime files\n")
                for entry in missing:
                    f.write(f"{entry}\n")

    result.ok = True
    result.message = f"{'Upgraded' if upgrade else 'Initialized'} .aion/ in {target}"
    return result


def _check_gitignore(gitignore_path: Path) -> list[str]:
    """Check which gitignore entries are missing."""
    if gitignore_path.is_file():
        content = gitignore_path.read_text(encoding="utf-8")
        return [e for e in GITIGNORE_ENTRIES if e not in content]
    return list(GITIGNORE_ENTRIES)


def _install_bundled_skills(templates_dir: Path, platform_cfg: object, result: InitResult) -> None:
    """Install bundled skills to platform-specific global skills directory."""
    from aioncode.core.profiles import PlatformConfig

    skills_src = templates_dir / "skills"
    if not skills_src.is_dir():
        return
    if isinstance(platform_cfg, PlatformConfig):
        global_dir = platform_cfg.global_dir
        skills_subdir = platform_cfg.skills_dir
    else:
        global_dir = Path.home() / ".claude"
        skills_subdir = "skills"
    user_skills_dir = global_dir / skills_subdir
    display_prefix = f"~/{global_dir.relative_to(Path.home())}/{skills_subdir}"
    for skill_dir in sorted(skills_src.iterdir()):
        if not skill_dir.is_dir():
            continue
        dst = user_skills_dir / skill_dir.name
        if dst.exists():
            result.skipped.append(f"{display_prefix}/{skill_dir.name}/")
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(skill_dir.rglob("*")):
            if not f.is_file():
                continue
            dst_file = dst / f.relative_to(skill_dir)
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst_file)
        result.created.append(f"{display_prefix}/{skill_dir.name}/")
