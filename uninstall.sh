#!/usr/bin/env bash
set -euo pipefail

# DEPRECATED: This script is deprecated in favor of the unified Python CLI.
# Use `aioncode uninstall` instead. See: https://github.com/puwenjunluck-pixel/aioncode
#
# AionCode uninstaller — safely removes AionCode from your project
# Does NOT remove .aion/ (your rules and docs are valuable!)
# Usage: bash uninstall.sh [target-dir]
#        bash uninstall.sh --dry-run [target-dir]

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    shift
fi

TARGET="${1:-.}"
TARGET="$(cd "$TARGET" && pwd)"

MARKER_START="<!-- AIONCODE:START -->"
MARKER_END="<!-- AIONCODE:END -->"

removed=0
backed_up=0
skipped=0

echo "╔══════════════════════════════════════════╗"
echo "║  AionCode Uninstaller                    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Target: $TARGET"
if [ "$DRY_RUN" = true ]; then
    echo "  Mode:   DRY RUN (preview only, no changes)"
fi
echo ""

# =====================================================================
# Step 1: Scan what will be removed
# =====================================================================
echo "── Uninstall Plan ────────────────────────"

# 1a. Commands — dynamic scan for aion-*.md
cmd_dir="$TARGET/.claude/commands"
cmd_list=()
if [ -d "$cmd_dir" ]; then
    while IFS= read -r -d '' f; do
        cmd_list+=("$f")
    done < <(find "$cmd_dir" -maxdepth 1 -name "aion-*.md" -print0 2>/dev/null)
fi
echo "  Commands:       ${#cmd_list[@]} aion-*.md files"

# 1b. CLAUDE.md — check for markers
claude_dst="$TARGET/.claude/CLAUDE.md"
claude_action="skip"
if [ -f "$claude_dst" ]; then
    if grep -q "$MARKER_START" "$claude_dst"; then
        # Check if there's user content outside markers
        before_lines=$(sed -n "1,/$MARKER_START/p" "$claude_dst" | sed '$d' | grep -cv '^$' || true)
        after_lines=$(sed -n "/$MARKER_END/,\$p" "$claude_dst" | sed '1d' | grep -cv '^$' || true)
        if [ "$before_lines" -gt 0 ] || [ "$after_lines" -gt 0 ]; then
            claude_action="strip_markers"
            echo "  CLAUDE.md:      strip AionCode section (user content preserved)"
        else
            claude_action="remove"
            echo "  CLAUDE.md:      remove (no user content outside markers)"
        fi
    else
        claude_action="skip"
        echo "  CLAUDE.md:      skip (no AionCode markers found)"
    fi
else
    echo "  CLAUDE.md:      not found"
fi

# 1c. Hooks and settings — backup before removing
hooks_file="$TARGET/.claude/hooks.json"
settings_file="$TARGET/.claude/settings.local.json"
hooks_action="skip"
settings_action="skip"

if [ -f "$hooks_file" ]; then
    hooks_action="backup_remove"
    echo "  hooks.json:     backup + remove"
else
    echo "  hooks.json:     not found"
fi

if [ -f "$settings_file" ]; then
    settings_action="backup_remove"
    echo "  settings.json:  backup + remove"
else
    echo "  settings.json:  not found"
fi

echo "  .aion/:         preserved (not touched)"
echo ""

# =====================================================================
# Step 2: Confirm (unless --dry-run)
# =====================================================================
if [ "$DRY_RUN" = true ]; then
    echo "── Dry Run Complete ──────────────────────"
    echo "  No changes made. Run without --dry-run to execute."
    exit 0
fi

echo -n "Type 'aioncode' to confirm uninstall: "
read -r confirm
if [ "$confirm" != "aioncode" ]; then
    echo "Cancelled. (Expected 'aioncode', got '$confirm')"
    exit 0
fi
echo ""

# =====================================================================
# Step 3: Execute
# =====================================================================
echo "── Removing ──────────────────────────────"

# 3a. Remove commands (dynamic)
for f in "${cmd_list[@]}"; do
    name=$(basename "$f")
    rm "$f"
    echo "  ✅ Removed: .claude/commands/$name"
    removed=$((removed + 1))
done
echo "  Commands: $removed removed"

# 3b. Handle CLAUDE.md
case "$claude_action" in
    strip_markers)
        # Remove only the AIONCODE:START...AIONCODE:END block, keep the rest
        before=$(sed -n "1,/$MARKER_START/p" "$claude_dst" | sed '$d')
        after=$(sed -n "/$MARKER_END/,\$p" "$claude_dst" | sed '1d')
        {
            echo "$before"
            echo "$after"
        } > "$claude_dst.tmp"
        # Clean up empty lines at the junction
        mv "$claude_dst.tmp" "$claude_dst"
        echo "  ✅ CLAUDE.md: AionCode section stripped, user content preserved"
        ;;
    remove)
        rm "$claude_dst"
        echo "  ✅ CLAUDE.md: removed"
        removed=$((removed + 1))
        ;;
    skip)
        echo "  ⏭️  CLAUDE.md: skipped"
        skipped=$((skipped + 1))
        ;;
esac

# 3c. Backup and remove hooks/settings
backup_dir="$TARGET/.claude/.aioncode-backup-$(date +%Y%m%d%H%M%S)"
need_backup=false
if [ "$hooks_action" = "backup_remove" ] || [ "$settings_action" = "backup_remove" ]; then
    need_backup=true
    mkdir -p "$backup_dir"
fi

if [ "$hooks_action" = "backup_remove" ]; then
    cp "$hooks_file" "$backup_dir/hooks.json"
    rm "$hooks_file"
    echo "  ✅ hooks.json: backed up + removed"
    removed=$((removed + 1))
    backed_up=$((backed_up + 1))
fi

if [ "$settings_action" = "backup_remove" ]; then
    cp "$settings_file" "$backup_dir/settings.local.json"
    rm "$settings_file"
    echo "  ✅ settings.json: backed up + removed"
    removed=$((removed + 1))
    backed_up=$((backed_up + 1))
fi

# =====================================================================
# Step 4: Report
# =====================================================================
echo ""
echo "══════════════════════════════════════════"
echo "  AionCode Uninstall Complete"
echo "══════════════════════════════════════════"
echo ""
echo "  Removed:    $removed items"
echo "  Backed up:  $backed_up items"
echo "  Skipped:    $skipped items"
echo "  .aion/:     preserved"
if [ "$need_backup" = true ]; then
    echo ""
    echo "  Backups saved to:"
    echo "    $backup_dir"
    echo "  To restore: cp $backup_dir/* $TARGET/.claude/"
fi
echo ""
echo "  Note: .aion/ directory was preserved — your rules and docs are still there."
echo "        To remove everything: rm -rf $TARGET/.aion"
