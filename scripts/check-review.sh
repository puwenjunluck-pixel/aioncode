#!/usr/bin/env bash
# Aion commit gate — PreToolUse hook on Bash tool calls.
# Blocks `git commit` unless an approved review in .aion/reviews/ covers the
# staged changes (frontmatter: status/base_commit/reviewed_files), with three
# exemptions: non-aion projects, .aion/-only commits, fix(bug): atomic commits.
# Fail-open by design: parsing failures must never brick the user's commits.
set -u

INPUT=$(cat)

extract_field() {
  # $1: jq path (e.g. .tool_input.command)
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r "$1 // empty" 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$INPUT" | python3 -c "
import sys, json, functools
try:
    data = json.load(sys.stdin)
    keys = [k for k in '$1'.strip('.').split('.') if k]
    print(functools.reduce(lambda d, k: d.get(k, {}), keys[:-1], data).get(keys[-1], ''))
except Exception:
    pass" 2>/dev/null
  fi
}

deny() {
  # JSON decision output; exit 0 lets Claude Code apply the deny.
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}

CMD=$(extract_field '.tool_input.command')
CWD=$(extract_field '.cwd')

# Only gate actual git commit invocations; everything else passes untouched.
case "$CMD" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

[ -n "$CWD" ] && cd "$CWD" 2>/dev/null
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -d .aion ] || exit 0

# Exemption: atomic bugfix commits from /aion:fix and /aion:qa.
case "$CMD" in
  *"fix(bug):"*) exit 0 ;;
esac

changed=$(git diff --cached --name-only)
# `git commit -a` commits modified tracked files that are not yet staged.
case "$CMD" in
  *" -a"*|*" -am"*|*" --all"*) changed=$(printf '%s\n%s' "$changed" "$(git diff --name-only)") ;;
esac
changed=$(printf '%s' "$changed" | sed '/^$/d' | sort -u)
[ -z "$changed" ] && exit 0

# Exemption: pure .aion/ bookkeeping (changelog, rules, reviews themselves).
non_aion=$(printf '%s\n' "$changed" | grep -v '^\.aion/' || true)
[ -z "$non_aion" ] && exit 0

head_full=$(git rev-parse HEAD 2>/dev/null)
head_short=$(git rev-parse --short HEAD 2>/dev/null)

# Union of reviewed_files across approved reviews whose base_commit == HEAD.
covered=""
for review in .aion/reviews/*.md; do
  [ -f "$review" ] || continue
  fm=$(awk '/^---$/{n++; next} n==1{print} n>=2{exit}' "$review")
  printf '%s' "$fm" | grep -q '^status: *approved' || continue
  base=$(printf '%s' "$fm" | sed -n 's/^base_commit: *//p' | tr -d '"' | head -1)
  [ "$base" = "$head_full" ] || [ "$base" = "$head_short" ] || continue
  files=$(printf '%s' "$fm" | awk '/^reviewed_files:/{f=1; next} f && /^  *- /{sub(/^  *- */,""); print; next} f{exit}')
  covered=$(printf '%s\n%s' "$covered" "$files")
done
covered=$(printf '%s' "$covered" | sed '/^$/d' | sort -u)

uncovered=$(comm -23 <(printf '%s\n' "$non_aion") <(printf '%s\n' "$covered") | head -5)
if [ -n "$uncovered" ]; then
  files_list=$(printf '%s' "$uncovered" | tr '\n' ' ')
  deny "Aion 门禁：以下改动没有被任何 approved review 覆盖（base_commit 需等于当前 HEAD）：${files_list}。请先运行 /aion:review；review 文件 frontmatter 需含 reviewed_files 与 base_commit 字段。"
fi
exit 0
