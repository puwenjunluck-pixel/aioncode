"""aioncode install — Install aioncode binary to system PATH."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path

from aioncode import __version__
from aioncode.utils.console import (
    banner,
    confirm,
    error,
    header,
    info,
    muted,
    success,
    warning,
)
from aioncode.utils.platform import (
    IS_WINDOWS,
    get_install_dir,
    is_admin,
    request_elevation,
)


def _get_current_executable() -> Path:
    """Get the path of the currently running aioncode binary."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable)
    # Running from source — return the script path
    return Path(sys.argv[0]).resolve()


def _install_binary(install_dir: Path) -> Path:
    """Copy the aioncode binary to the install directory."""
    src = _get_current_executable()
    binary_name = "aioncode.exe" if IS_WINDOWS else "aioncode"
    dst = install_dir / binary_name

    install_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

    # Make executable on Unix
    if not IS_WINDOWS:
        dst.chmod(dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    return dst


def _add_to_path_windows(install_dir: Path) -> bool:
    """Add install_dir to the user PATH on Windows."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment",
            0,
            winreg.KEY_READ | winreg.KEY_WRITE,
        )
        try:
            current_path, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current_path = ""

        dir_str = str(install_dir)
        if dir_str.lower() not in current_path.lower():
            new_path = f"{current_path};{dir_str}" if current_path else dir_str
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            # Notify the system of the change
            import ctypes
            HWND_BROADCAST = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageW(  # type: ignore[attr-defined]
                HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            )
            return True
        winreg.CloseKey(key)
        return False  # Already in PATH
    except (ImportError, OSError):
        return False


def _install_shell_completion() -> list[str]:
    """Install shell completion scripts. Returns list of actions taken."""
    actions: list[str] = []

    if IS_WINDOWS:
        return actions  # No shell completion on Windows for now

    home = Path.home()

    # Bash completion
    bash_comp_dir = home / ".local" / "share" / "bash-completion" / "completions"
    bash_comp_dir.mkdir(parents=True, exist_ok=True)
    bash_script = bash_comp_dir / "aioncode"
    bash_script.write_text(
        '_aioncode() {\n'
        '  local commands="install init upgrade uninstall doctor version dashboard clean"\n'
        '  COMPREPLY=($(compgen -W "$commands" -- "${COMP_WORDS[COMP_CWORD]}"))\n'
        '}\n'
        'complete -F _aioncode aioncode\n',
        encoding="utf-8",
    )
    actions.append(f"bash: {bash_script}")

    # Zsh completion
    zsh_comp_dir = home / ".zfunc"
    zsh_comp_dir.mkdir(parents=True, exist_ok=True)
    zsh_script = zsh_comp_dir / "_aioncode"
    zsh_script.write_text(
        '#compdef aioncode\n'
        '_aioncode() {\n'
        '  local commands=(\n'
        '    "install:Install aioncode to system PATH"\n'
        '    "init:Initialize .aion/ in current directory"\n'
        '    "upgrade:Upgrade to the latest version"\n'
        '    "uninstall:Remove aioncode from system"\n'
        '    "doctor:Run environment diagnostics"\n'
        '    "version:Show version and bootstrap status"\n'
        '    "dashboard:Start the web UI"\n'
        '    "clean:Clean up temporary files"\n'
        '  )\n'
        '  _describe "command" commands\n'
        '}\n'
        '_aioncode "$@"\n',
        encoding="utf-8",
    )
    actions.append(f"zsh: {zsh_script}")

    return actions


def run_install(args: argparse.Namespace) -> None:
    """CLI entry point for `aioncode install`."""
    banner("AionCode Install", f"v{__version__}")

    # Check if running from source (not frozen)
    if not getattr(sys, "frozen", False):
        info("Running from source — install from a packaged binary for global installation.")
        info("For development, use: pip install -e .")
        return

    install_dir = get_install_dir()
    binary_name = "aioncode.exe" if IS_WINDOWS else "aioncode"
    target = install_dir / binary_name

    # Check if already installed
    if target.exists():
        info(f"aioncode already installed at: {target}")
        if not confirm("Overwrite existing installation?"):
            return

    header("Installing Binary")

    # Check permissions
    needs_elevation = not os.access(install_dir.parent, os.W_OK) if install_dir.parent.exists() else False
    if needs_elevation and not is_admin():
        warning(f"Need elevated permissions to write to {install_dir}")
        if request_elevation():
            return  # Re-launched with elevation
        error("Cannot install without elevated permissions")
        raise SystemExit(1)

    # Install
    installed_path = _install_binary(install_dir)
    success(f"Binary installed: {installed_path}")

    # Add to PATH on Windows
    if IS_WINDOWS:
        if _add_to_path_windows(install_dir):
            success(f"Added {install_dir} to user PATH")
            warning("Restart your terminal for PATH changes to take effect")
        else:
            muted("Already in PATH")

    # Shell completion
    header("Shell Completion")
    completion_actions = _install_shell_completion()
    if completion_actions:
        for action in completion_actions:
            success(action)
    else:
        muted("No shell completion installed")

    # Summary
    header("Installation Complete")
    success(f"aioncode v{__version__} installed to {installed_path}")
    info("Run `aioncode --help` to get started")
    if not IS_WINDOWS:
        # Check if install_dir is in PATH
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        if str(install_dir) not in path_dirs:
            warning(f"Note: {install_dir} may not be in your PATH")
            info(f"Add to your shell profile: export PATH=\"{install_dir}:$PATH\"")
