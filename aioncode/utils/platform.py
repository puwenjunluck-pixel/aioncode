"""Cross-platform utilities: paths, permissions, encoding, system info."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------

IS_WINDOWS = sys.platform == "win32"
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")

PLATFORM_NAME = "windows" if IS_WINDOWS else ("macos" if IS_MACOS else "linux")


def get_system_info() -> dict[str, str]:
    """Return a dict of system information for diagnostics."""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "arch": platform.machine(),
        "python": platform.python_version(),
        "platform": PLATFORM_NAME,
    }


# ---------------------------------------------------------------------------
# Architecture detection (for binary downloads)
# ---------------------------------------------------------------------------

def get_platform_tag() -> str:
    """Return a platform-architecture tag for GitHub Releases binary matching.

    Examples: 'macos-arm64', 'macos-x64', 'linux-x64', 'windows-x64'
    """
    machine = platform.machine().lower()
    match machine:
        case "arm64" | "aarch64":
            arch = "arm64"
        case "x86_64" | "amd64":
            arch = "x64"
        case _:
            arch = machine
    return f"{PLATFORM_NAME}-{arch}"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def resolve_path(path: str | Path) -> Path:
    """Resolve a path, handling Windows long paths transparently."""
    p = Path(path).resolve()
    if IS_WINDOWS and len(str(p)) > 240:
        # Enable long path prefix on Windows
        s = str(p)
        if not s.startswith("\\\\?\\"):
            p = Path(f"\\\\?\\{s}")
    return p


def get_config_dir() -> Path:
    """Return the global AionCode config directory (XDG-aware)."""
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "AionCode"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "aioncode"
    return Path.home() / ".config" / "aioncode"


def get_data_dir() -> Path:
    """Return the global AionCode data directory (XDG-aware)."""
    if IS_WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "AionCode" / "data"
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg) / "aioncode"
    return Path.home() / ".local" / "share" / "aioncode"


def get_install_dir() -> Path:
    """Return the directory where the aioncode binary should be installed."""
    if IS_WINDOWS:
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "AionCode"
    # Prefer /usr/local/bin if writable, else ~/.local/bin
    usr_local = Path("/usr/local/bin")
    if usr_local.exists() and os.access(usr_local, os.W_OK):
        return usr_local
    local_bin = Path.home() / ".local" / "bin"
    local_bin.mkdir(parents=True, exist_ok=True)
    return local_bin


# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------

def is_admin() -> bool:
    """Check if the current process has admin/root privileges."""
    if IS_WINDOWS:
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            return False
    return os.geteuid() == 0


def request_elevation(argv: list[str] | None = None) -> bool:
    """Request privilege elevation. Returns True if re-launched elevated.

    On Windows: triggers UAC prompt via ShellExecuteW.
    On Unix: prints a message suggesting sudo.
    """
    if is_admin():
        return False

    if IS_WINDOWS:
        try:
            import ctypes
            exe = sys.executable
            params = " ".join(argv or sys.argv)
            ret = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
                None, "runas", exe, params, None, 1,
            )
            return ret > 32  # ShellExecute returns > 32 on success
        except (AttributeError, OSError):
            return False
    else:
        # On Unix, we don't auto-elevate; we inform the user
        print("This operation requires elevated privileges.")
        print(f"Please re-run with: sudo {' '.join(sys.argv)}")
        return False


# ---------------------------------------------------------------------------
# Encoding
# ---------------------------------------------------------------------------

def ensure_utf8() -> None:
    """Force UTF-8 encoding for the entire process."""
    os.environ.setdefault("PYTHONUTF8", "1")
    if IS_WINDOWS:
        # Also set console code page on Windows
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # type: ignore[attr-defined]
            ctypes.windll.kernel32.SetConsoleCP(65001)  # type: ignore[attr-defined]
        except (AttributeError, OSError):
            pass
    # Reconfigure stdout/stderr
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
            except (OSError, AttributeError):
                pass


def open_utf8(path: str | Path, mode: str = "r", **kwargs):
    """Open a file with UTF-8 encoding enforced."""
    if "b" not in mode and "encoding" not in kwargs:
        kwargs["encoding"] = "utf-8"
    return open(path, mode, **kwargs)


# ---------------------------------------------------------------------------
# Windows long path support
# ---------------------------------------------------------------------------

def check_long_path_support() -> bool:
    """Check if Windows long path support is enabled."""
    if not IS_WINDOWS:
        return True  # Not applicable on Unix
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\FileSystem",
        )
        value, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
        winreg.CloseKey(key)
        return bool(value)
    except (OSError, ImportError):
        return False
