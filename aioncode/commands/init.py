"""aioncode init — Initialize .aion/ project intelligence in a directory."""

from __future__ import annotations

import argparse
from pathlib import Path

from aioncode.core.project import InitProfile
from aioncode.utils.console import (
    banner,
    choose_one,
    confirm,
    error,
    header,
    info,
    install_report,
    muted,
    success,
    toggle_select,
    warning,
)


def _ask_project_profile() -> InitProfile:
    """Interactive project setup: ask platform, project type, role, select commands."""
    import shutil

    from aioncode.core.profiles import (
        ALL_COMMANDS,
        CORE_COMMANDS,
        PLATFORMS,
        get_recommended,
    )

    header("Project Setup")

    # 0. Platform detection + selection
    detected = [n for n, cfg in PLATFORMS.items() if shutil.which(cfg.cli_binary)]
    platform_labels = [cfg.label for cfg in PLATFORMS.values()]
    platform_keys = list(PLATFORMS.keys())
    default_plat = platform_keys.index(detected[0]) + 1 if detected else 1
    if detected:
        info(f"检测到：{', '.join(PLATFORMS[d].label for d in detected)}")
    else:
        warning("未检测到 Claude Code 或 Antigravity CLI（仍可手动选择）")
    plat_idx = choose_one("目标平台：", platform_labels, default=default_plat)
    platform = platform_keys[plat_idx - 1]

    # 1. Project type
    project_types = [
        "前端项目（React/Vue/小程序等）",
        "后端项目（API/服务/数据处理）",
        "全栈项目（前后端一体）",
        "Monorepo（多包仓库）",
    ]
    type_keys = ["frontend", "backend", "fullstack", "monorepo"]
    type_idx = choose_one("项目类型：", project_types, default=3)
    project_type = type_keys[type_idx - 1]

    # 2. Role
    roles = ["设计师（原型 & UI 为主）", "前端开发", "后端开发", "测试 / QA", "全栈开发"]
    role_keys = ["designer", "frontend", "backend", "tester", "fullstack"]
    role_idx = choose_one("你的角色：", roles, default=5)
    role = role_keys[role_idx - 1]

    # 3. Command selection
    recommended = get_recommended(role)
    items: list[tuple[str, str, bool]] = []
    for cmd in ALL_COMMANDS:
        selected = cmd.name in recommended or cmd.name in CORE_COMMANDS
        items.append((cmd.name, cmd.label, selected))

    header("Command Selection")
    total_rec = sum(1 for _, _, s in items if s)
    info(f"推荐安装 {total_rec}/{len(ALL_COMMANDS)} 个命令：\n")
    selections = toggle_select(items)

    # Core commands are always selected
    selected_commands: list[str] = []
    for i, cmd in enumerate(ALL_COMMANDS):
        if cmd.name in CORE_COMMANDS or selections[i]:
            selected_commands.append(cmd.name)

    return InitProfile(
        project_type=project_type,
        role=role,
        selected_commands=selected_commands,
        platform=platform,
    )


def _ask_upgrade_commands(existing_commands: list[str]) -> list[str] | None:
    """During upgrade, ask about newly available commands not yet installed."""
    from aioncode.core.profiles import ALL_COMMANDS, CORE_COMMANDS

    existing_set = set(existing_commands)
    all_names = {c.name for c in ALL_COMMANDS}
    new_commands = [c for c in ALL_COMMANDS if c.name not in existing_set and c.name in all_names]

    if not new_commands:
        return None

    header("New Commands Available")
    info(f"发现 {len(new_commands)} 个新命令：\n")
    items = [(c.name, c.label, c.name in CORE_COMMANDS) for c in new_commands]
    selections = toggle_select(items)

    added: list[str] = []
    for i, cmd in enumerate(new_commands):
        if cmd.name in CORE_COMMANDS or selections[i]:
            added.append(cmd.name)

    return added if added else None


def _init_project(target: Path, *, upgrade: bool = False, install_all: bool = False) -> None:
    """Execute project initialization with rich CLI output."""
    from aioncode.core.project import (
        _check_gitignore,
        detect_project,
        get_source_version,
        init_project,
    )

    target = target.resolve()
    source_version = get_source_version()
    project = detect_project(target)

    banner(
        f"AionCode {'Upgrade' if upgrade else 'Init'} v{source_version}",
        f"Target: {target}",
    )

    # --- Environment checks ---
    header("Environment Check")
    if not target.is_dir():
        error(f"Target directory does not exist: {target}")
        raise SystemExit(1)
    success("Target directory exists")

    import os
    import shutil

    if not os.access(target, os.W_OK):
        error("No write permission to target directory")
        raise SystemExit(1)
    success("Write permission OK")

    if shutil.which("claude"):
        success("Claude Code CLI available")
    else:
        warning("Claude Code CLI not found — all /project:aion-* commands require Claude Code")
        warning("  Install: https://claude.ai/download")

    if shutil.which("git"):
        success("Git available")
    else:
        warning("Git not found (collaboration features won't work)")

    if project.has_git:
        success("Git repository initialized")
    else:
        warning("Not a Git repository (.aion/ won't sync with team)")

    # --- Project detection ---
    header("Project Detection")

    if project.has_aion:
        info(f"AionCode already installed (v{project.installed_version})")
        if project.installed_version != source_version:
            info(f"  Update available: v{project.installed_version} → v{source_version}")
        else:
            muted("  Already up to date")
    else:
        info("AionCode not installed — fresh init")

    if project.source_count > 0:
        info(f"Existing codebase detected (~{project.source_count} source files)")

    if project.existing_docs:
        info(f"Existing docs found: {', '.join(project.existing_docs)}")
        muted("  Consider importing to .aion/refs/ after init")

    # --- Project Setup (interactive profile) ---
    profile: InitProfile | None = None
    if install_all:
        muted("--all: installing all commands")
    elif upgrade and project.has_aion:
        # Upgrade: check for new commands
        from aioncode.core.profiles import ALL_COMMANDS, read_profile

        existing_profile = read_profile(target / ".aion" / "config.yml")
        if existing_profile and "commands" in existing_profile:
            existing_cmds = existing_profile["commands"]
            if not isinstance(existing_cmds, list):
                existing_cmds = []
            # Filter out stale commands no longer in source
            valid_names = {c.name for c in ALL_COMMANDS}
            stale = [c for c in existing_cmds if c not in valid_names]
            existing_cmds = [c for c in existing_cmds if c in valid_names]
            if stale:
                info(f"清理 {len(stale)} 个已删除命令: {', '.join(stale)}")
            added = _ask_upgrade_commands(existing_cmds)
            # Always construct profile from existing config to preserve platform
            profile = InitProfile(
                project_type=str(existing_profile.get("project_type", "fullstack")),
                role=str(existing_profile.get("role", "fullstack")),
                selected_commands=existing_cmds + (added or []),
                platform=str(existing_profile.get("platform", "claude")),
            )
            if added:
                success(f"新增 {len(added)} 个命令")
            elif not stale:
                info("无新命令可添加")
        else:
            # No profile saved — ask full setup
            profile = _ask_project_profile()
    else:
        # Fresh init — full interactive setup
        profile = _ask_project_profile()

    # --- Check gitignore interactively ---
    gitignore_path = target / ".gitignore"
    missing_entries = _check_gitignore(gitignore_path)
    update_gitignore = False
    if missing_entries:
        warning(f".gitignore missing: {', '.join(missing_entries)}")
        update_gitignore = confirm("Add missing entries to .gitignore?", default=True)
    else:
        success(".gitignore already configured")

    # --- Execute core init ---
    result = init_project(
        target,
        upgrade=upgrade,
        update_gitignore=update_gitignore,
        profile=profile,
    )

    if not result.ok:
        error(result.message)
        raise SystemExit(1)

    # --- Report ---
    header("Installation Report")
    install_report(
        title="File Operations",
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
        warnings=result.warnings if result.warnings else None,
    )

    # --- Suggestions ---
    from aioncode.core.profiles import DEFAULT_PLATFORM, PLATFORMS

    platform_name = profile.platform if profile else DEFAULT_PLATFORM
    platform_cfg = PLATFORMS.get(platform_name, PLATFORMS[DEFAULT_PLATFORM])
    prefix = platform_cfg.cmd_prefix

    print()
    header("Next Steps")
    info(f"1. Open {platform_cfg.label} in your project")
    info(f"2. Run: {prefix}aion-help")
    if project.is_new:
        info(f"3. Start with: {prefix}aion-design")
    else:
        info(f"3. Start with: {prefix}aion-scan")

    if project.existing_docs:
        print()
        info("Import existing docs:")
        for doc in project.existing_docs:
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
    install_all = getattr(args, "all", False)

    _init_project(target, upgrade=upgrade, install_all=install_all)
