#!/usr/bin/env bash
set -euo pipefail

# DEPRECATED: This script is deprecated in favor of the unified Python CLI.
# Use `aioncode init` instead. See: https://github.com/puwenjunluck-pixel/aioncode
#
# AionCode installer — copies commands and scaffolding to your project
# Usage: bash install.sh [target-dir]
#        bash install.sh --check [target-dir]
#        bash install.sh --upgrade [target-dir]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHECK_MODE=false
UPGRADE_MODE=false

# Parse flags
if [[ "${1:-}" == "--check" ]]; then
    CHECK_MODE=true
    shift
elif [[ "${1:-}" == "--upgrade" ]]; then
    UPGRADE_MODE=true
    shift
fi

TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"

# --- Markers for idempotent CLAUDE.md merge ---
MARKER_START="<!-- AIONCODE:START -->"
MARKER_END="<!-- AIONCODE:END -->"

# --- Version helpers ---
get_source_version() {
    grep -m1 '^version:' "$SCRIPT_DIR/templates/aion/config.yml" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/' || echo "0.0"
}

get_installed_version() {
    local cfg="$1/.aion/config.yml"
    if [ -f "$cfg" ]; then
        grep -m1 '^version:' "$cfg" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/' || echo "0.0"
    else
        echo "0.0"
    fi
}

SOURCE_VERSION=$(get_source_version)
INSTALLED_VERSION=$(get_installed_version "$TARGET")

MODE_LABEL="install"
if [ "$CHECK_MODE" = true ]; then
    MODE_LABEL="check"
elif [ "$UPGRADE_MODE" = true ]; then
    MODE_LABEL="upgrade"
fi

# =====================================================================
# Phase 1: Pre-Check (环境检查 + 冲突检测)
# =====================================================================
echo "╔══════════════════════════════════════════╗"
echo "║  AionCode Installer v$SOURCE_VERSION                ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Source:   $SCRIPT_DIR"
echo "  Target:   $TARGET"
echo "  Mode:     $MODE_LABEL"
echo ""

errors=0
warnings=0
upgraded=0
created_files=0
created_dirs=0

# --- Environment checks ---
echo "── Environment Check ──────────────────────"

# Check target directory
if [ ! -d "$TARGET" ]; then
    echo "  ❌ Target directory does not exist"
    exit 1
fi
echo "  ✅ Target directory exists"

# Check write permission
if [ ! -w "$TARGET" ]; then
    echo "  ❌ No write permission to target directory"
    exit 1
fi
echo "  ✅ Write permission OK"

# Check git
if command -v git &>/dev/null; then
    echo "  ✅ Git available ($(git --version | head -c 20))"
else
    echo "  ⚠️  Git not found (collaboration features won't work)"
    warnings=$((warnings + 1))
fi

# Check Python 3
if command -v python3 &>/dev/null; then
    echo "  ✅ Python3 available ($(python3 --version 2>&1 | head -c 15))"
else
    echo "  ⚠️  Python3 not found (Dashboard and hooks won't work)"
    warnings=$((warnings + 1))
fi

# Check git repo
if [ -d "$TARGET/.git" ]; then
    echo "  ✅ Git repository initialized"
else
    echo "  ⚠️  Not a Git repository (.aion/ won't sync with team)"
    warnings=$((warnings + 1))
fi

# --- Project type detection ---
echo ""
echo "── Project Detection ─────────────────────"

IS_NEW_PROJECT=true
HAS_AION=false
HAS_CLAUDE_DIR=false
HAS_CLAUDE_MD=false
EXISTING_DOCS=""

# Check if AionCode already installed
if [ -d "$TARGET/.aion" ]; then
    HAS_AION=true
    IS_NEW_PROJECT=false
    echo "  📦 AionCode already installed (v$INSTALLED_VERSION)"
    if [ "$INSTALLED_VERSION" != "$SOURCE_VERSION" ]; then
        echo "     ↳ Update available: v$INSTALLED_VERSION → v$SOURCE_VERSION"
    else
        echo "     ↳ Already up to date"
    fi
else
    echo "  🆕 AionCode not installed"
fi

# Check existing .claude/
if [ -d "$TARGET/.claude" ]; then
    HAS_CLAUDE_DIR=true
    echo "  📂 .claude/ directory exists"
fi

# Check existing CLAUDE.md
if [ -f "$TARGET/.claude/CLAUDE.md" ]; then
    HAS_CLAUDE_MD=true
    # Check if it has user content outside markers
    if grep -q "$MARKER_START" "$TARGET/.claude/CLAUDE.md" 2>/dev/null; then
        echo "  📄 CLAUDE.md exists (has AionCode markers → will merge)"
    else
        echo "  📄 CLAUDE.md exists (no markers → will add AionCode section)"
    fi
fi

# Check for source code (old project indicator)
file_count=$(find "$TARGET" -maxdepth 2 -type f \( -name "*.ts" -o -name "*.js" -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.vue" -o -name "*.tsx" -o -name "*.jsx" \) 2>/dev/null | head -500 | wc -l | tr -d ' ')
if [ "$file_count" -gt 0 ]; then
    IS_NEW_PROJECT=false
    echo "  📁 Existing codebase detected (~$file_count source files)"
fi

# Check for existing docs that could be imported
for doc in "docs/architecture.md" "docs/ARCHITECTURE.md" "ARCHITECTURE.md" "docs/api.md" "docs/API.md" "DESIGN.md" "docs/design.md"; do
    if [ -f "$TARGET/$doc" ]; then
        EXISTING_DOCS="$EXISTING_DOCS $doc"
    fi
done
if [ -n "$EXISTING_DOCS" ]; then
    echo "  📝 Existing docs found:$EXISTING_DOCS"
    echo "     ↳ Consider importing to .aion/refs/ after install"
fi

# Check .gitignore
echo ""
echo "── Conflict Check ────────────────────────"

gitignore_needs_update=false
if [ -f "$TARGET/.gitignore" ]; then
    if ! grep -q "events.jsonl" "$TARGET/.gitignore" 2>/dev/null; then
        gitignore_needs_update=true
        echo "  ⚠️  .gitignore missing: events.jsonl, sessions.jsonl"
    else
        echo "  ✅ .gitignore already configured"
    fi
else
    gitignore_needs_update=true
    echo "  ⚠️  No .gitignore found"
fi

# Show what will happen
echo ""
echo "── Installation Plan ─────────────────────"
echo "  📁 .claude/commands/   → 18 command files ($([ "$HAS_CLAUDE_DIR" = true ] && echo 'overwrite aion-*' || echo 'create'))"
echo "  📁 .aion/              → project scaffold ($([ "$HAS_AION" = true ] && echo 'skip existing' || echo 'create'))"
echo "  📄 .claude/CLAUDE.md   → $([ "$HAS_CLAUDE_MD" = true ] && echo 'merge (preserve user content)' || echo 'create')"
echo "  📄 .claude/hooks.json  → $([ -f "$TARGET/.claude/hooks.json" ] && echo 'keep existing' || echo 'create')"
echo "  📄 .claude/settings    → $([ -f "$TARGET/.claude/settings.local.json" ] && echo 'keep existing' || echo 'create')"
echo ""

# In check mode, just report and exit
if [ "$CHECK_MODE" = true ]; then
    # Run detailed checks
    cmd_src="$SCRIPT_DIR/commands"
    cmd_dst="$TARGET/.claude/commands"
    echo "── Detailed Check ────────────────────────"
    for f in "$cmd_src"/*.md; do
        name="$(basename "$f")"
        if [ ! -f "$cmd_dst/$name" ]; then
            echo "  MISSING: .claude/commands/$name"
            errors=$((errors + 1))
        elif ! diff -q "$f" "$cmd_dst/$name" > /dev/null 2>&1; then
            echo "  OUTDATED: .claude/commands/$name"
            errors=$((errors + 1))
        fi
    done
    aion_src="$SCRIPT_DIR/templates/aion"
    aion_dst="$TARGET/.aion"
    for f in $(cd "$aion_src" && find . -type f | sed 's|^\./||'); do
        if [ ! -f "$aion_dst/$f" ]; then
            echo "  MISSING: .aion/$f"
            errors=$((errors + 1))
        fi
    done
    for d in refs prototypes specs plans reviews contracts monitor tests tests/reports tests/perf tests/ui bugs; do
        if [ ! -d "$aion_dst/$d" ]; then
            echo "  MISSING: .aion/$d/"
            errors=$((errors + 1))
        fi
    done
    if [ "$INSTALLED_VERSION" != "$SOURCE_VERSION" ]; then
        echo "  VERSION: $INSTALLED_VERSION → $SOURCE_VERSION (needs upgrade)"
        errors=$((errors + 1))
    fi
    echo ""
    if [ "$errors" -gt 0 ]; then
        echo "Check: $errors issue(s) found."
        echo "  Fix: bash install.sh $TARGET"
        echo "  Or:  bash install.sh --upgrade $TARGET"
        exit 1
    else
        echo "All checks passed. ✅"
    fi
    exit 0
fi

# =====================================================================
# Phase 2: Execute Installation
# =====================================================================
echo "── Installing ────────────────────────────"

# --- 1. Copy commands to .claude/commands/ ---
cmd_src="$SCRIPT_DIR/commands"
cmd_dst="$TARGET/.claude/commands"
mkdir -p "$cmd_dst"
cmd_count=0
for f in "$cmd_src"/*.md; do
    name="$(basename "$f")"
    cp "$f" "$cmd_dst/$name"
    cmd_count=$((cmd_count + 1))
done
echo "  Commands: $cmd_count files installed"

# --- 2. Scaffold .aion/ (never overwrite existing files) ---
aion_src="$SCRIPT_DIR/templates/aion"
aion_dst="$TARGET/.aion"

for f in $(cd "$aion_src" && find . -type f | sed 's|^\./||'); do
    dst_file="$aion_dst/$f"
    if [ -f "$dst_file" ]; then
        : # skip silently
    else
        mkdir -p "$(dirname "$dst_file")"
        cp "$aion_src/$f" "$dst_file"
        created_files=$((created_files + 1))
    fi
done

for d in refs prototypes specs plans reviews contracts monitor tests tests/reports tests/perf tests/ui bugs; do
    if [ ! -d "$aion_dst/$d" ]; then
        mkdir -p "$aion_dst/$d"
        created_dirs=$((created_dirs + 1))
    fi
done
echo "  Scaffold: $created_files files, $created_dirs directories created"

# --- 2.5. Upgrade: create new directories and template files ---
if [ "$UPGRADE_MODE" = true ]; then
    for d in refs prototypes specs plans reviews contracts monitor tests tests/reports tests/perf tests/ui bugs; do
        if [ ! -d "$aion_dst/$d" ]; then
            mkdir -p "$aion_dst/$d"
            upgraded=$((upgraded + 1))
        fi
    done
    for f in $(cd "$aion_src" && find . -type f | sed 's|^\./||'); do
        dst_file="$aion_dst/$f"
        if [ ! -f "$dst_file" ]; then
            mkdir -p "$(dirname "$dst_file")"
            cp "$aion_src/$f" "$dst_file"
            upgraded=$((upgraded + 1))
        fi
    done
    # Update version
    if [ -f "$aion_dst/config.yml" ]; then
        if grep -q '^version:' "$aion_dst/config.yml"; then
            sed -i.bak "s/^version: .*/version: \"$SOURCE_VERSION\"/" "$aion_dst/config.yml"
            rm -f "$aion_dst/config.yml.bak"
        else
            echo "version: \"$SOURCE_VERSION\"" >> "$aion_dst/config.yml"
        fi
    fi
    echo "  Upgrade: $upgraded new items, version → $SOURCE_VERSION"
fi

# --- 2.7. Copy tools to .aion/bin/ (always overwrite — these are tools, not user data) ---
bin_dst="$TARGET/.aion/bin"
mkdir -p "$bin_dst"
cp "$SCRIPT_DIR/dashboard.py" "$bin_dst/dashboard.py"
cp "$SCRIPT_DIR/uninstall.sh" "$bin_dst/uninstall.sh"
echo "  Tools: dashboard.py, uninstall.sh → .aion/bin/"

# --- 3. Install hooks config ---
hooks_src="$SCRIPT_DIR/templates/claude-hooks.json"
settings_src="$SCRIPT_DIR/templates/claude-settings.json"
claude_dir="$TARGET/.claude"
mkdir -p "$claude_dir"

hooks_status="skipped"
if [ -f "$hooks_src" ]; then
    if [ -f "$claude_dir/hooks.json" ]; then
        hooks_status="kept existing"
    else
        cp "$hooks_src" "$claude_dir/hooks.json"
        hooks_status="created"
    fi
fi

settings_status="skipped"
if [ -f "$settings_src" ]; then
    if [ -f "$claude_dir/settings.local.json" ]; then
        settings_status="kept existing"
    else
        cp "$settings_src" "$claude_dir/settings.local.json"
        settings_status="created"
    fi
fi
echo "  Hooks: $hooks_status | Settings: $settings_status"

# --- 4. Write .claude/CLAUDE.md (MERGE, not overwrite) ---
claude_dst="$TARGET/.claude/CLAUDE.md"
tpl="$SCRIPT_DIR/templates/CLAUDE.md.tpl"
tpl_content=$(cat "$tpl")

if [ -f "$claude_dst" ]; then
    existing=$(cat "$claude_dst")
    if echo "$existing" | grep -q "$MARKER_START"; then
        # Has markers → replace content between markers
        before=$(echo "$existing" | sed -n "1,/$MARKER_START/p" | sed '$d')
        after=$(echo "$existing" | sed -n "/$MARKER_END/,\$p" | sed '1d')
        {
            echo "$before"
            echo "$MARKER_START"
            echo "$tpl_content"
            echo "$MARKER_END"
            echo "$after"
        } > "$claude_dst"
        echo "  CLAUDE.md: merged (user content preserved)"
    else
        # No markers → append AionCode section with markers
        {
            echo "$existing"
            echo ""
            echo "$MARKER_START"
            echo "$tpl_content"
            echo "$MARKER_END"
        } > "$claude_dst"
        echo "  CLAUDE.md: appended (user content preserved)"
    fi
else
    # New file → wrap in markers
    {
        echo "$MARKER_START"
        echo "$tpl_content"
        echo "$MARKER_END"
    } > "$claude_dst"
    echo "  CLAUDE.md: created"
fi

# =====================================================================
# Phase 3: Installation Report
# =====================================================================
echo ""
echo "══════════════════════════════════════════"
if [ "$UPGRADE_MODE" = true ]; then
    echo "  Upgrade Complete: v$INSTALLED_VERSION → v$SOURCE_VERSION"
else
    echo "  Installation Complete: v$SOURCE_VERSION"
fi
echo "══════════════════════════════════════════"
echo ""
echo "  Installed:"
echo "    Commands:    $cmd_count slash commands"
echo "    Scaffold:    $created_files files, $created_dirs dirs"
echo "    Hooks:       $hooks_status"
echo "    Settings:    $settings_status"
echo "    CLAUDE.md:   $([ "$HAS_CLAUDE_MD" = true ] && echo 'merged' || echo 'created')"
if [ "$UPGRADE_MODE" = true ]; then
    echo "    Upgraded:    $upgraded new items"
fi
echo ""

# Suggestions
suggestions=0
echo "  Suggestions:"
if [ "$gitignore_needs_update" = true ]; then
    suggestions=$((suggestions + 1))
    echo "    $suggestions. Add to .gitignore:"
    echo "       .aion/monitor/events.jsonl"
    echo "       .aion/sessions.jsonl"
fi
if [ -n "$EXISTING_DOCS" ]; then
    suggestions=$((suggestions + 1))
    echo "    $suggestions. Import existing docs to .aion/refs/:"
    for doc in $EXISTING_DOCS; do
        echo "       cp $doc .aion/refs/"
    done
fi
if [ "$IS_NEW_PROJECT" = false ] && [ "$HAS_AION" = false ]; then
    suggestions=$((suggestions + 1))
    echo "    $suggestions. Run /project:aion-scan to bootstrap project intelligence"
fi
if [ "$suggestions" -eq 0 ]; then
    echo "    None — you're all set!"
fi

echo ""
echo "  Next steps:"
echo "    1. Open Claude Code in your project"
echo "    2. Run: /project:aion-status"
if [ "$IS_NEW_PROJECT" = true ]; then
    echo "    3. Start with: /project:aion-think"
else
    echo "    3. Start with: /project:aion-scan"
fi
echo ""
echo "  Dashboard:"
echo "    python3 .aion/bin/dashboard.py"
echo "    → http://localhost:19200"
echo ""
echo "  Uninstall:"
echo "    bash .aion/bin/uninstall.sh"
echo ""
