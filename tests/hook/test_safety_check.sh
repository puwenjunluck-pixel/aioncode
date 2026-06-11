#!/usr/bin/env bash
# Tests for scripts/safety-check.sh — dangerous patterns denied, normal allowed.
set -u

HOOK="$(cd "$(dirname "$0")/../.." && pwd)/scripts/safety-check.sh"
PASS=0; FAIL=0

run_hook() {
  printf '{"tool_input":{"command":"%s"},"cwd":"/tmp"}' "$1" | bash "$HOOK"
}

assert() {
  local verdict="allow"
  case "$3" in *permissionDecision*deny*) verdict="deny";; esac
  if [ "$verdict" = "$2" ]; then
    PASS=$((PASS + 1)); echo "  ✓ $1"
  else
    FAIL=$((FAIL + 1)); echo "  ✗ $1 — expected $2, got $verdict"
  fi
}

echo "safety-check.sh test suite"
assert "normal command allowed" allow "$(run_hook 'ls -la && git status')"
assert "git commit allowed" allow "$(run_hook 'git commit -m x')"
assert "force push denied" deny "$(run_hook 'git push --force origin master')"
assert "rm -rf / denied" deny "$(run_hook 'rm -rf /')"
assert "git reset --hard denied" deny "$(run_hook 'git reset --hard origin/main')"
assert "drop table denied" deny "$(run_hook 'mysql -e DROP TABLE users')"
assert "empty input allowed" allow "$(printf '{}' | bash "$HOOK")"

echo
echo "passed: $PASS, failed: $FAIL"
[ "$FAIL" -eq 0 ]
