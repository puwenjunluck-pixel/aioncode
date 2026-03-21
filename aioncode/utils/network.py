"""Network utilities: GitHub Releases API, downloads."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from aioncode import __version__
from aioncode.utils.platform import get_platform_tag

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_REPO = "puwenjunluck-pixel/aioncode"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"
USER_AGENT = f"aioncode/{__version__}"


# ---------------------------------------------------------------------------
# GitHub API helpers (using stdlib urllib to avoid requests at import time)
# ---------------------------------------------------------------------------


def _github_get(endpoint: str, timeout: int = 10) -> Any:
    """Make a GET request to the GitHub API."""
    url = f"{GITHUB_API}/{endpoint}"
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": USER_AGENT,
        },
    )
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Release queries
# ---------------------------------------------------------------------------


class ReleaseInfo:
    """Information about a GitHub release."""

    __slots__ = ("tag", "version", "url", "assets", "published_at")

    def __init__(self, data: dict[str, Any]) -> None:
        self.tag: str = data.get("tag_name", "")
        self.version: str = self.tag.lstrip("v")
        self.url: str = data.get("html_url", "")
        self.published_at: str = data.get("published_at", "")
        self.assets: dict[str, str] = {}
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            download_url = asset.get("browser_download_url", "")
            if name and download_url:
                self.assets[name] = download_url

    def get_binary_url(self) -> str | None:
        """Find the download URL for the current platform's binary."""
        tag = get_platform_tag()
        for name, url in self.assets.items():
            if tag in name:
                return url
        return None


def get_latest_release() -> ReleaseInfo | None:
    """Fetch the latest release info from GitHub."""
    try:
        data = _github_get("releases/latest")
        return ReleaseInfo(data)
    except (URLError, OSError, json.JSONDecodeError, KeyError):
        return None


def check_for_update() -> tuple[bool, str | None]:
    """Check if a newer version is available.

    Returns:
        (has_update, latest_version) tuple.
    """
    release = get_latest_release()
    if release is None:
        return False, None

    from packaging.version import Version

    try:
        current = Version(__version__)
        latest = Version(release.version)
        return latest > current, release.version
    except Exception:
        # Fallback: simple string comparison
        return release.version != __version__, release.version


def is_github_reachable(timeout: int = 5) -> bool:
    """Quick check if GitHub API is reachable."""
    try:
        req = Request(
            "https://api.github.com",
            headers={"User-Agent": USER_AGENT},
        )
        with urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (URLError, OSError):
        return False


# ---------------------------------------------------------------------------
# Download with progress
# ---------------------------------------------------------------------------


def download_file(
    url: str,
    dest: Path | None = None,
    progress_callback: Any | None = None,
    timeout: int = 60,
) -> Path:
    """Download a file from URL.

    Args:
        url: Download URL.
        dest: Destination path. If None, uses a temp file.
        progress_callback: Callable(bytes_downloaded, total_bytes) for progress updates.
        timeout: Request timeout in seconds.

    Returns:
        Path to the downloaded file.

    Raises:
        URLError: On download failure.
    """
    req = Request(url, headers={"User-Agent": USER_AGENT})

    with urlopen(req, timeout=timeout) as resp:
        total = int(resp.headers.get("Content-Length", 0))

        if dest is None:
            suffix = Path(url.split("/")[-1]).suffix or ".bin"
            fd, tmp_path = tempfile.mkstemp(suffix=suffix, prefix="aioncode-")
            dest = Path(tmp_path)
        else:
            fd = None

        try:
            downloaded = 0
            chunk_size = 8192
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        progress_callback(downloaded, total)
        finally:
            if fd is not None:
                import os

                os.close(fd)

    return dest
