"""Tests for aioncode.utils.platform — cross-platform utilities."""

from __future__ import annotations

from pathlib import Path

from aioncode.utils.platform import (
    get_platform_tag,
    get_system_info,
    open_utf8,
    resolve_path,
)


class TestGetPlatformTag:
    def test_format(self):
        tag = get_platform_tag()
        parts = tag.split("-")
        assert len(parts) == 2
        assert parts[0] in ("macos", "linux", "windows")
        assert parts[1] in ("arm64", "x64", "x86", "aarch64")

    def test_not_empty(self):
        assert len(get_platform_tag()) > 0


class TestResolvePath:
    def test_returns_absolute(self):
        result = resolve_path(".")
        assert result.is_absolute()

    def test_resolves_relative(self, tmp_path: Path):
        result = resolve_path(tmp_path / "subdir" / ".." / "file.txt")
        assert ".." not in str(result)

    def test_pathlib_type(self):
        result = resolve_path("/tmp")
        assert isinstance(result, Path)


class TestGetSystemInfo:
    def test_has_required_keys(self):
        info = get_system_info()
        for key in ("os", "os_version", "arch", "python", "platform"):
            assert key in info, f"Missing key: {key}"

    def test_values_not_empty(self):
        info = get_system_info()
        for key, value in info.items():
            assert value, f"Empty value for key: {key}"

    def test_platform_matches_tag(self):
        info = get_system_info()
        tag = get_platform_tag()
        assert info["platform"] in tag


class TestOpenUtf8:
    def test_default_encoding(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello", encoding="utf-8")
        with open_utf8(test_file) as f:
            assert f.encoding == "utf-8"
            assert f.read() == "hello"

    def test_chinese_content(self, tmp_path: Path):
        test_file = tmp_path / "test.txt"
        content = "你好世界 AionCode 测试"
        with open_utf8(test_file, "w") as f:
            f.write(content)
        with open_utf8(test_file) as f:
            assert f.read() == content

    def test_binary_mode_no_encoding(self, tmp_path: Path):
        test_file = tmp_path / "test.bin"
        test_file.write_bytes(b"\x00\x01\x02")
        with open_utf8(test_file, "rb") as f:
            assert f.read() == b"\x00\x01\x02"
