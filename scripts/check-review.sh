#!/usr/bin/env bash
# Aion commit gate — PreToolUse hook on Bash tool calls.
# Blocks `git commit` unless approved reviews in .aion/reviews/ (frontmatter:
# status/base_commit/reviewed_files) jointly cover the files being committed.
# Exemptions: non-aion projects, .aion/-only commits, merge-in-progress,
# commit messages starting with "fix(bug): ".
# Fail-open on parse failure; fail-closed on coverage doubt.
set -u

INPUT=$(cat)

extract_field() {
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
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$1"
  exit 0
}

CMD=$(extract_field '.tool_input.command')
CWD=$(extract_field '.cwd')
# Whitespace variants (double space, tabs) must not slip past the matcher.
CMD_NORM=$(printf '%s' "$CMD" | tr '\t' ' ' | tr -s ' ')

# Gate `git [global-opts] commit`; everything else passes untouched.
printf '%s' "$CMD_NORM" | grep -qE '(^|[;&|(] ?)git(( -[Cc] [^ ]+)|( --?[a-zA-Z][a-zA-Z-]*(=[^ ]+)?))* commit( |$)' || exit 0

[ -n "$CWD" ] && cd "$CWD" 2>/dev/null
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
[ -d .aion ] || exit 0

# Merge in progress: the commit concludes a merge, not new work.
[ -f "$(git rev-parse --git-path MERGE_HEAD 2>/dev/null)" ] && exit 0

# Exemption: atomic bugfix commits. Anchored to the start of the -m payload —
# "fix(bug):" appearing elsewhere in a message must NOT unlock the gate.
if printf '%s' "$CMD_NORM" | grep -qE -- '(-m|--message)[ =]?["'"'"']?fix\(bug\): '; then
  exit 0
fi

changed=$(git diff --cached --name-only)
# `git commit -a` (incl. bundled forms like -am/-va) also commits unstaged
# tracked changes; fold them in so they can't dodge coverage.
if printf '%s' "$CMD_NORM" | grep -qE -- '( --all( |$)| -[a-zA-Z]*a[a-zA-Z]*( |$))'; then
  changed=$(printf '%s\n%s' "$changed" "$(git diff --name-only)")
fi
changed=$(printf '%s' "$changed" | sed '/^$/d' | sort -u)
[ -z "$changed" ] && exit 0

non_aion=$(printf '%s\n' "$changed" | grep -v '^\.aion/' || true)
[ -z "$non_aion" ] && exit 0

head_full=$(git rev-parse HEAD 2>/dev/null)
head_short=$(git rev-parse --short HEAD 2>/dev/null)

# Union of reviewed_files across approved reviews whose base_commit == HEAD.
# Tolerates CRLF, quoted values, inline [a, b] lists, and any list indent.
covered=""
for review in .aion/reviews/*.md; do
  [ -f "$review" ] || continue
  fm=$(tr -d '\r' < "$review" | awk '/^---$/{n++; next} n==1{print} n>=2{exit}')
  printf '%s\n' "$fm" | grep -qE '^status: *"?approved"? *$' || continue
  base=$(printf '%s\n' "$fm" | sed -n 's/^base_commit: *//p' | tr -d '"'"'" | head -1)
  [ "$base" = "$head_full" ] || [ "$base" = "$head_short" ] || continue
  inline=$(printf '%s\n' "$fm" | sed -n 's/^reviewed_files: *\[\(.*\)\].*/\1/p')
  if [ -n "$inline" ]; then
    files=$(printf '%s' "$inline" | tr ',' '\n' | sed 's/^ *//;s/ *$//;s/^["'"'"']//;s/["'"'"']$//')
  else
    files=$(printf '%s\n' "$fm" | awk '/^reviewed_files:/{f=1; next} f && /^[ \t]*- /{sub(/^[ \t]*- */,""); print; next} f{exit}' | tr -d '"'"'")
  fi
  covered=$(printf '%s\n%s' "$covered" "$files")
done
covered=$(printf '%s' "$covered" | sed '/^$/d' | sort -u)

uncovered=$(comm -23 <(printf '%s\n' "$non_aion") <(printf '%s\n' "$covered") | head -5)
if [ -n "$uncovered" ]; then
  files_list=$(printf '%s' "$uncovered" | tr '\n' ' ')
  deny "Aion 门禁：以下改动未被 approved review 覆盖（reviewed_files 并集，且 base_commit 须等于当前 HEAD）：${files_list}。请运行 /aion:review。常见原因：刚提交过一次，HEAD 已前移，旧 review 失效——重跑 /aion:review 即可。"
fi
exit 0
