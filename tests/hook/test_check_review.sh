#!/usr/bin/env bash
# Table-driven tests for scripts/check-review.sh (the Aion commit gate).
# Each case builds a scenario in a tmp git repo, feeds hook-shaped JSON on
# stdin, and asserts allow (empty output) or deny (permissionDecision JSON).
set -u

HOOK="$(cd "$(dirname "$0")/../.." && pwd)/scripts/check-review.sh"
PASS=0; FAIL=0

run_hook() {
  printf '{"tool_input":{"command":"%s"},"cwd":"%s"}' "$1" "$2" | bash "$HOOK"
}

assert() {
  # $1 name, $2 expected (allow|deny), $3 actual output
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

echo "check-review.sh test suite"

# 1. Non-commit commands pass untouched
R=$(make_repo); mkdir -p "$R/.aion"
assert "non-commit command allowed" allow "$(run_hook 'ls -la' "$R")"

# 2. No .aion directory → not an aion project, never gate
R=$(make_repo)
echo x > "$R/code.py"; git -C "$R" add code.py
assert "non-aion project allowed" allow "$(run_hook 'git commit -m x' "$R")"

# 3. Staged code file without any review → deny
R=$(make_repo); mkdir -p "$R/.aion/reviews"
echo x > "$R/code.py"; git -C "$R" add code.py
assert "unreviewed change denied" deny "$(run_hook 'git commit -m x' "$R")"

# 4. Approved review at HEAD covering the file → allow
R=$(make_repo); mkdir -p "$R/.aion/reviews"
echo x > "$R/code.py"; git -C "$R" add code.py
HEAD_SHORT=$(git -C "$R" rev-parse --short HEAD)
printf -- '---\nstatus: approved\nbase_commit: %s\nreviewed_files:\n  - code.py\n---\n# r\n' "$HEAD_SHORT" > "$R/.aion/reviews/r.md"
assert "covered change allowed" allow "$(run_hook 'git commit -m x' "$R")"

# 5. Review with stale base_commit → deny
R=$(make_repo); mkdir -p "$R/.aion/reviews"
echo x > "$R/code.py"; git -C "$R" add code.py
printf -- '---\nstatus: approved\nbase_commit: 0000000\nreviewed_files:\n  - code.py\n---\n# r\n' > "$R/.aion/reviews/r.md"
assert "stale review denied" deny "$(run_hook 'git commit -m x' "$R")"

# 6. Review approved but file not in reviewed_files → deny
R=$(make_repo); mkdir -p "$R/.aion/reviews"
echo x > "$R/code.py"; echo y > "$R/other.py"; git -C "$R" add code.py other.py
HEAD_SHORT=$(git -C "$R" rev-parse --short HEAD)
printf -- '---\nstatus: approved\nbase_commit: %s\nreviewed_files:\n  - code.py\n---\n# r\n' "$HEAD_SHORT" > "$R/.aion/reviews/r.md"
assert "partially covered denied" deny "$(run_hook 'git commit -m x' "$R")"

# 7. Pure .aion/ bookkeeping → allow
R=$(make_repo); mkdir -p "$R/.aion"
echo log > "$R/.aion/changelog.md"; git -C "$R" add .aion/changelog.md
assert "aion-only commit allowed" allow "$(run_hook 'git commit -m docs' "$R")"

# 8. fix(bug): atomic commit exemption → allow
R=$(make_repo); mkdir -p "$R/.aion/reviews"
echo x > "$R/code.py"; git -C "$R" add code.py
assert "fix(bug) exemption allowed" allow "$(run_hook "git commit -m 'fix(bug): F-001 repair'" "$R")"

echo
echo "passed: $PASS, failed: $FAIL"
[ "$FAIL" -eq 0 ]
