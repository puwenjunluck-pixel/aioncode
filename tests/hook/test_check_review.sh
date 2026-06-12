#!/usr/bin/env bash
# Table-driven tests for scripts/check-review.sh (the Aion commit gate).
# Includes the adversarial bypass cases found in the 2026-06 red-team review.
set -u

HOOK="$(cd "$(dirname "$0")/../.." && pwd)/scripts/check-review.sh"
PASS=0; FAIL=0

run_hook() {
  printf '{"tool_input":{"command":"%s"},"cwd":"%s"}' "$1" "$2" | bash "$HOOK"
}

assert() {
  local verdict="allow"
  case "$3" in *permissionDecision*deny*) verdict="deny";; esac
  if [ "$verdict" = "$2" ]; then
    PASS=$((PASS + 1)); echo "  ✓ $1"
  else
    FAIL=$((FAIL + 1)); echo "  ✗ $1 — expected $2, got $verdict: $3"
  fi
}

make_repo() {
  local dir
  dir=$(mktemp -d)
  git -C "$dir" init -q
  git -C "$dir" -c user.email=t@t -c user.name=t commit -q --allow-empty -m init
  echo "$dir"
}

stage_file() { echo x > "$1/$2"; git -C "$1" add "$2"; }

write_review() {
  # $1 repo, $2 filename, $3 base_commit, $4... reviewed files
  local repo=$1 file=$2 base=$3; shift 3
  mkdir -p "$repo/.aion/reviews"
  { printf -- '---\nstatus: approved\nbase_commit: %s\nreviewed_files:\n' "$base"
    for f in "$@"; do printf '  - %s\n' "$f"; done
    printf -- '---\n# r\n'; } > "$repo/.aion/reviews/$file"
}

echo "check-review.sh test suite"

# ── 执行位（运行时 hooks.json 由 /bin/sh 直接 exec，缺 +x 即 126 拒载 — v0.8.1 事故）──
if [ -x "$HOOK" ]; then
  PASS=$((PASS + 1)); echo "  ✓ hook script has exec bit"
else
  FAIL=$((FAIL + 1)); echo "  ✗ hook script has exec bit — chmod +x $HOOK"
fi

# ── 基础行为 ──
R=$(make_repo); mkdir -p "$R/.aion"
assert "non-commit command allowed" allow "$(run_hook 'ls -la' "$R")"

R=$(make_repo); stage_file "$R" code.py
assert "non-aion project allowed" allow "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
assert "unreviewed change denied" deny "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); stage_file "$R" code.py
write_review "$R" r.md "$(git -C "$R" rev-parse --short HEAD)" code.py
assert "covered change allowed" allow "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); stage_file "$R" code.py
write_review "$R" r.md 0000000 code.py
assert "stale review denied" deny "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); stage_file "$R" code.py; stage_file "$R" other.py
write_review "$R" r.md "$(git -C "$R" rev-parse --short HEAD)" code.py
assert "partially covered denied" deny "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); stage_file "$R" a.py; stage_file "$R" b.py
H=$(git -C "$R" rev-parse --short HEAD)
write_review "$R" r1.md "$H" a.py
write_review "$R" r2.md "$H" b.py
assert "union across reviews allowed" allow "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); mkdir -p "$R/.aion"
echo log > "$R/.aion/changelog.md"; git -C "$R" add .aion/changelog.md
assert "aion-only commit allowed" allow "$(run_hook 'git commit -m docs' "$R")"

R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
assert "fix(bug) exemption allowed" allow "$(run_hook "git commit -m 'fix(bug): F-001 repair'" "$R")"

# ── 红队对抗用例 ──
R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
assert "fix(bug) mid-message denied" deny "$(run_hook "git commit -m 'feat: replace old fix(bug): handler'" "$R")"

R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
assert "double-space variant denied" deny "$(run_hook 'git  commit -m x' "$R")"

R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
assert "git -C variant denied" deny "$(run_hook 'git -C . commit -m x' "$R")"

R=$(make_repo); mkdir -p "$R/.aion/reviews"
echo x > "$R/code.py"; git -C "$R" add code.py
git -C "$R" -c user.email=t@t -c user.name=t commit -qm seed
echo y > "$R/code.py"  # tracked, unstaged
assert "bundled -va flag denied" deny "$(run_hook 'git commit -va -m x' "$R")"

# ── 格式健壮性（fail-closed 误拒修复）──
R=$(make_repo); stage_file "$R" code.py
H=$(git -C "$R" rev-parse --short HEAD); mkdir -p "$R/.aion/reviews"
printf -- '---\r\nstatus: approved\r\nbase_commit: %s\r\nreviewed_files:\r\n  - code.py\r\n---\r\n# r\n' "$H" > "$R/.aion/reviews/r.md"
assert "CRLF review accepted" allow "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); stage_file "$R" code.py
H=$(git -C "$R" rev-parse --short HEAD); mkdir -p "$R/.aion/reviews"
printf -- '---\nstatus: "approved"\nbase_commit: "%s"\nreviewed_files: [code.py]\n---\n# r\n' "$H" > "$R/.aion/reviews/r.md"
assert "quoted + inline list accepted" allow "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); stage_file "$R" code.py
H=$(git -C "$R" rev-parse --short HEAD); mkdir -p "$R/.aion/reviews"
printf -- '---\nstatus: approved\nbase_commit: %s\nreviewed_files:\n- code.py\n---\n# r\n' "$H" > "$R/.aion/reviews/r.md"
assert "zero-indent list accepted" allow "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
touch "$(git -C "$R" rev-parse --git-path MERGE_HEAD | sed "s|^|$R/|")" 2>/dev/null || touch "$R/.git/MERGE_HEAD"
assert "merge in progress allowed" allow "$(run_hook 'git commit -m merge' "$R")"

# ── 第二轮红队：status 前缀伪批准 + -m 紧贴写法 ──
R=$(make_repo); stage_file "$R" code.py
H=$(git -C "$R" rev-parse --short HEAD); mkdir -p "$R/.aion/reviews"
printf -- '---\nstatus: approved-pending\nbase_commit: %s\nreviewed_files:\n  - code.py\n---\n' "$H" > "$R/.aion/reviews/r.md"
assert "approved-pending prefix denied" deny "$(run_hook 'git commit -m x' "$R")"

R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
assert "fix(bug) tight -m quote allowed" allow "$(run_hook "git commit -m'fix(bug): x'" "$R")"
R=$(make_repo); mkdir -p "$R/.aion/reviews"; stage_file "$R" code.py
assert "fix(bug): no-space-after-colon denied" deny "$(run_hook "git commit -m 'fix(bug):x'" "$R")"

echo
echo "passed: $PASS, failed: $FAIL"
[ "$FAIL" -eq 0 ]
