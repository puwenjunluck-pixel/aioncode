#!/usr/bin/env bash
# Tests for scripts/rules-status.sh — stale detection with injected today.
set -u

SCRIPT="$(cd "$(dirname "$0")/../.." && pwd)/scripts/rules-status.sh"
PASS=0; FAIL=0

assert_contains() {
  if printf '%s' "$3" | grep -q "$2"; then
    PASS=$((PASS + 1)); echo "  ✓ $1"
  else
    FAIL=$((FAIL + 1)); echo "  ✗ $1 — output: $3"
  fi
}

D=$(mktemp -d)
cat > "$D/pitfalls.md" << 'EOF'
---
category: pitfalls
---
- **新鲜规则** (review, 2026-06-01) [cite_count: 2, last_cited: 2026-06-01]
  描述。
- **陈旧规则** (scan, 2026-01-10) [cite_count: 0, last_cited: 2026-01-10]
  描述。
- **已归档规则** (scan, 2026-01-01) [cite_count: 0, last_cited: 2026-01-01, status: archived]
  描述。
EOF

OUT=$(bash "$SCRIPT" --days 60 --today 2026-06-12 "$D")
echo "rules-status.sh test suite"
assert_contains "fresh rule not stale" "active=1" "$OUT"
assert_contains "stale rule detected" "STALE \[pitfalls.md\] 陈旧规则" "$OUT"
assert_contains "archived rule skipped" "archived=1" "$OUT"
assert_contains "summary counts" "stale_candidates=1" "$OUT"

OUT2=$(bash "$SCRIPT" --days 60 --today 2026-06-12 "$D/nonexistent")
assert_contains "missing dir tolerated" "stale_candidates=0" "$OUT2"

echo
echo "passed: $PASS, failed: $FAIL"
[ "$FAIL" -eq 0 ]
