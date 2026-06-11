#!/usr/bin/env bash
# Tests for scripts/safety-check.sh — bypass variants denied, prose allowed.
# Covers the flag-order/bundling bypasses and false positives from the
# 2026-06 red-team review.
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

# ── 正常命令放行 ──
assert "normal command allowed" allow "$(run_hook 'ls -la && git status')"
assert "git commit allowed" allow "$(run_hook 'git commit -m x')"
assert "empty input allowed" allow "$(printf '{}' | bash "$HOOK")"
assert "safe rm in project allowed" allow "$(run_hook 'rm -rf /Users/me/project/node_modules')"
assert "force-with-lease allowed" allow "$(run_hook 'git push --force-with-lease origin main')"

# ── 误杀回归（prose 提到危险串不拦）──
assert "echo prose allowed" allow "$(run_hook "echo 'never run rm -rf /'")"
assert "grep prose allowed" allow "$(run_hook "grep -r 'git reset --hard' .")"
assert "commit message prose allowed" allow "$(run_hook "git commit -m 'doc DROP TABLE caveat'")"

# ── 教科书形态拦截 ──
assert "rm -rf / denied" deny "$(run_hook 'rm -rf /')"
assert "force push denied" deny "$(run_hook 'git push --force origin master')"
assert "git reset --hard denied" deny "$(run_hook 'git reset --hard origin/main')"
assert "git clean -fd denied" deny "$(run_hook 'git clean -fd')"
assert "drop table denied" deny "$(run_hook 'mysql -e DROP TABLE users')"

# ── 红队绕过变体拦截 ──
assert "rm -fr (flag order) denied" deny "$(run_hook 'rm -fr /')"
assert "rm long flags denied" deny "$(run_hook 'rm --recursive --force /')"
assert "rm double-space denied" deny "$(run_hook 'rm  -rf  /')"
assert "rm HOME denied" deny "$(run_hook 'rm -rf $HOME')"
assert "push trailing --force denied" deny "$(run_hook 'git push origin main --force')"
assert "push -f denied" deny "$(run_hook 'git push origin -f')"
assert "git -c prefix reset denied" deny "$(run_hook 'git -c x=y reset --hard')"
assert "clean -df (flag order) denied" deny "$(run_hook 'git clean -df')"
assert "clean split flags denied" deny "$(run_hook 'git clean -f -d')"
assert "piped rm denied" deny "$(run_hook 'echo go | rm -rf /')"

# ── 第二轮红队：程序名形态绕过 ──
assert "abs path /bin/rm denied" deny "$(run_hook '/bin/rm -rf /')"
assert "abs path /usr/bin/git push denied" deny "$(run_hook '/usr/bin/git push origin -f')"
assert "command wrapper rm denied" deny "$(run_hook 'command rm -rf /')"
# xargs 的删除目标来自 stdin（管道），静态分析的固有盲区——
# 硬拦会误杀合法的 find ... | xargs rm。如实记录为放行，不假装拦截。
assert "xargs pipe is known blind spot (allowed)" allow "$(run_hook 'echo / | xargs rm -rf')"
assert "rm -r -f split denied" deny "$(run_hook 'rm -r -f /')"
assert "subshell rm denied" deny "$(run_hook '$(rm -rf /)')"

echo
echo "passed: $PASS, failed: $FAIL"
[ "$FAIL" -eq 0 ]
