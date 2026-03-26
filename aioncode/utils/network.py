"""Network utilities: GitHub Releases API, downloads."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from aioncode import __version__
from aioncode.utils.platform import get_platform_tag

# ---------------------------------------------------------------------------
# SSL fix for PyInstaller-bundled binary
# ---------------------------------------------------------------------------


def _setup_ssl() -> None:
    """Ensure SSL certificates are found in PyInstaller bundles."""
    if not getattr(sys, "frozen", False):
        return
    bundle_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    cert_file = bundle_dir / "certifi" / "cacert.pem"
    if cert_file.exists():
        os.environ.setdefault("SSL_CERT_FILE", str(cert_file))
        return
    # Fallback: try system CA paths (covers old binaries missing bundled certs)
    for candidate in (
        "/etc/ssl/certs/ca-certificates.crt",  # Debian/Ubuntu
        "/etc/pki/tls/certs/ca-bundle.crt",    # RHEL/CentOS
        "/etc/ssl/ca-bundle.pem",               # openSUSE
        "/usr/local/etc/openssl/cert.pem",      # macOS Homebrew
        "/usr/local/share/ca-certificates/cacert.pem",
    ):
        if Path(candidate).exists():
            os.environ.setdefault("SSL_CERT_FILE", candidate)
            return


_setup_ssl()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GITHUB_REPO = "puwenjunluck-pixel/aioncode"
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}"
USER_AGENT = f"aioncode/{__version__}"


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _get_token() -> str | None:
    """Read GitHub token from GITHUB_TOKEN environment variable."""
    return os.environ.get("GITHUB_TOKEN") or None


def _build_headers(accept: str = "application/vnd.github.v3+json") -> dict[str, str]:
    """Build HTTP headers with optional Authorization."""
    headers: dict[str, str] = {
        "Accept": accept,
        "User-Agent": USER_AGENT,
    }
    token = _get_token()
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


# ---------------------------------------------------------------------------
# GitHub API helpers (using stdlib urllib to avoid requests at import time)
# ---------------------------------------------------------------------------


def _github_get(endpoint: str, timeout: int = 10) -> Any:
    """Make a GET request to the GitHub API."""
    url = f"{GITHUB_API}/{endpoint}"
    req = Request(url, headers=_build_headers())
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Release queries
# ---------------------------------------------------------------------------


class ReleaseInfo:
    """Information about a GitHub release."""

    __slots__ = ("tag", "version", "url", "assets", "api_urls", "published_at")

    def __init__(self, data: dict[str, Any]) -> None:
        self.tag: str = data.get("tag_name", "")
        self.version: str = self.tag.lstrip("v")
        self.url: str = data.get("html_url", "")
        self.published_at: str = data.get("published_at", "")
        self.assets: dict[str, str] = {}
        self.api_urls: dict[str, str] = {}
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            download_url = asset.get("browser_download_url", "")
            api_url = asset.get("url", "")
            if name and download_url:
                self.assets[name] = download_url
            if name and api_url:
                self.api_urls[name] = api_url

    def get_binary_url(self) -> tuple[str, bool, str] | None:
        """Find the download URL for the current platform's binary.

        Returns:
            (url, is_api, asset_name) tuple — is_api=True means use API URL with octet-stream Accept header.
            None if no matching binary found.
        """
        tag = get_platform_tag()
        token = _get_token()
        for name in self.assets:
            if tag in name:
                if token and name in self.api_urls:
                    return self.api_urls[name], True, name
                return self.assets[name], False, name
        return None


def get_latest_release() -> ReleaseInfo | None:
    """Fetch the latest release info from GitHub."""
    try:
        data = _github_get("releases/latest")
        return ReleaseInfo(data)
    except HTTPError as e:
        if e.code in (401, 403):
            raise PermissionError("GitHub API 认证失败，请检查 GITHUB_TOKEN 是否有效") from e
        if e.code == 404 and not _get_token():
            raise PermissionError("无法访问仓库，私有仓库需设置 GITHUB_TOKEN 环境变量") from e
        return None
    except (URLError, OSError, json.JSONDecodeError, KeyError):
        return None


def check_for_update() -> tuple[bool, str | None]:
    """Check if a newer version is available.

    Returns:
        (has_update, latest_version) tuple.
    """
    try:
        release = get_latest_release()
    except PermissionError:
        return False, None
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
    headers: dict[str, str] | None = None,
) -> Path:
    """Download a file from URL.

    Args:
        url: Download URL.
        dest: Destination path. If None, uses a temp file.
        progress_callback: Callable(bytes_downloaded, total_bytes) for progress updates.
        timeout: Request timeout in seconds.
        headers: Additional HTTP headers to include in the request.

    Returns:
        Path to the downloaded file.

    Raises:
        URLError: On download failure.
    """
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = Request(url, headers=req_headers)

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
