"""Tests for aioncode.utils.integrity — core defense against content corruption."""

from __future__ import annotations

from pathlib import Path

from aioncode.utils.integrity import (
    MARKER_END,
    MARKER_START,
    append_fingerprint,
    compute_fingerprint,
    content_without_fingerprint,
    extract_fingerprint,
    md5_of_bytes,
    md5_of_text,
    merge_claude_md,
    strip_claude_md_markers,
)


class TestMD5:
    def test_empty_string(self):
        assert md5_of_text("") == "d41d8cd98f00b204e9800998ecf8427e"

    def test_known_hash(self):
        assert md5_of_text("hello") == "5d41402abc4b2a76b9719d911017c592"

    def test_bytes_matches_text(self):
        assert md5_of_bytes(b"hello") == md5_of_text("hello")

    def test_utf8_content(self):
        result = md5_of_text("你好世界")
        assert len(result) == 32
        assert result.isalnum()


class TestMergeClaudeMd:
    """merge_claude_md is the first line of defense against content corruption."""

    def test_create_new(self):
        """Scenario: CLAUDE.md doesn't exist yet."""
        result = merge_claude_md(None, "template content")
        assert result.action == "created"
        assert MARKER_START in result.content
        assert MARKER_END in result.content
        assert "template content" in result.content

    def test_merge_with_existing_markers(self):
        """Scenario: CLAUDE.md has markers, replace content between them."""
        existing = f"user header\n{MARKER_START}\nold content\n{MARKER_END}\nuser footer"
        result = merge_claude_md(existing, "new content")
        assert result.action == "merged"
        assert "user header" in result.content
        assert "user footer" in result.content
        assert "new content" in result.content
        assert "old content" not in result.content

    def test_append_without_markers(self):
        """Scenario: CLAUDE.md exists but has no markers."""
        existing = "user content only"
        result = merge_claude_md(existing, "template content")
        assert result.action == "appended"
        assert "user content only" in result.content
        assert MARKER_START in result.content
        assert "template content" in result.content

    def test_preserves_user_content_before_markers(self):
        """User content before markers is preserved (moved after template)."""
        existing = f"# My Project Notes\n\n{MARKER_START}\nold\n{MARKER_END}\n"
        result = merge_claude_md(existing, "new")
        assert "# My Project Notes" in result.content
        # New design: template always comes first
        assert result.content.startswith(MARKER_START)

    def test_preserves_user_content_after_markers(self):
        existing = f"{MARKER_START}\nold\n{MARKER_END}\n\n# My Custom Section"
        result = merge_claude_md(existing, "new")
        assert "# My Custom Section" in result.content

    def test_strips_duplicate_markers(self):
        """Critical: the original bug — 3x duplicated markers get collapsed to 1."""
        existing = (
            f"{MARKER_START}\nt1\n{MARKER_END}\n"
            f"<!-- AIONCODE:LEARNED -->\n## Learned\n- i1\n"
            f"{MARKER_START}\nt2\n{MARKER_END}\n"
            f"<!-- AIONCODE:LEARNED -->\n## Learned\n- i2\n"
        )
        result = merge_claude_md(existing, "clean")
        assert result.content.count(MARKER_START) == 1
        assert result.content.count(MARKER_END) == 1
        assert "LEARNED" not in result.content
        assert "clean" in result.content

    def test_strips_legacy_learned_section(self):
        """LEARNED sections are fully removed."""
        existing = f"{MARKER_START}\ntpl\n{MARKER_END}\n<!-- AIONCODE:LEARNED -->\n## Learned\n- item\n"
        result = merge_claude_md(existing, "new")
        assert "LEARNED" not in result.content
        assert "item" not in result.content

    def test_size_warning(self):
        """Files exceeding 100 lines trigger a warning."""
        big = "\n".join(f"line {i}" for i in range(120))
        result = merge_claude_md(None, big)
        assert len(result.warnings) == 1
        assert "limit" in result.warnings[0]

    def test_no_warning_under_limit(self):
        result = merge_claude_md(None, "short template")
        assert len(result.warnings) == 0

    def test_emoji_in_template(self):
        """Edge case: template contains emoji characters."""
        result = merge_claude_md(None, "🚀 AionCode Setup 🎯")
        assert "🚀" in result.content
        assert "🎯" in result.content

    def test_emoji_in_existing(self):
        """Edge case: existing content contains emoji."""
        existing = f"📝 My Notes\n{MARKER_START}\nold\n{MARKER_END}\n🔥 Footer"
        result = merge_claude_md(existing, "new")
        assert "📝" in result.content
        assert "🔥" in result.content

    def test_special_characters(self):
        """Edge case: content with regex-special characters."""
        template = "path: C:\\Users\\test\\project"
        result = merge_claude_md(None, template)
        assert "C:\\Users\\test\\project" in result.content

    def test_empty_template(self):
        result = merge_claude_md(None, "")
        assert MARKER_START in result.content
        assert MARKER_END in result.content

    def test_multiline_template(self):
        template = "line1\nline2\nline3"
        result = merge_claude_md(None, template)
        assert "line1" in result.content
        assert "line3" in result.content


class TestStripClaudeMdMarkers:
    def test_strip_markers_with_surrounding_content(self):
        content = f"before\n{MARKER_START}\naion stuff\n{MARKER_END}\nafter"
        cleaned, action = strip_claude_md_markers(content)
        assert action == "stripped"
        assert "before" in cleaned
        assert "after" in cleaned
        assert MARKER_START not in cleaned

    def test_remove_entirely(self):
        content = f"{MARKER_START}\naion stuff\n{MARKER_END}"
        cleaned, action = strip_claude_md_markers(content)
        assert action == "removed_entirely"
        assert cleaned == ""

    def test_no_markers(self):
        content = "just regular content"
        cleaned, action = strip_claude_md_markers(content)
        assert action == "no_markers"
        assert cleaned == content


class TestFingerprint:
    def test_compute_is_deterministic(self):
        text = "some content\nmore content\n"
        assert compute_fingerprint(text) == compute_fingerprint(text)

    def test_compute_ignores_existing_fingerprint(self):
        text = "content\n<!-- aion:fingerprint:abc123def456abc123def456abc123de -->\n"
        clean_fp = compute_fingerprint("content\n")
        with_fp = compute_fingerprint(text)
        assert clean_fp == with_fp

    def test_append_fingerprint(self):
        text = "some content\n"
        result = append_fingerprint(text)
        assert "<!-- aion:fingerprint:" in result
        assert "some content" in result

    def test_content_without_fingerprint(self):
        text = "line1\nline2\n<!-- aion:fingerprint:abcdef1234567890abcdef1234567890 -->\n"
        clean = content_without_fingerprint(text)
        assert "line1" in clean
        assert "fingerprint" not in clean

    def test_extract_fingerprint_from_file(self, tmp_path: Path):
        fp_file = tmp_path / "test.md"
        fp_file.write_text(
            "content\n<!-- aion:fingerprint:abcdef1234567890abcdef1234567890 -->\n",
            encoding="utf-8",
        )
        result = extract_fingerprint(fp_file)
        assert result == "abcdef1234567890abcdef1234567890"

    def test_extract_fingerprint_missing(self, tmp_path: Path):
        fp_file = tmp_path / "test.md"
        fp_file.write_text("no fingerprint here\n", encoding="utf-8")
        assert extract_fingerprint(fp_file) is None
