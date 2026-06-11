#!/usr/bin/env bash
# Aion safety hook — PreToolUse on Bash; denies destructive command patterns.
# Companion to check-review.sh; same stdin JSON contract, same fail-open rule.
set -u

INPUT=$(cat)

extract_command() {
  if command -v jq >/dev/null 2>&1; then
    printf '%s' "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null
  elif command -v python3 >/dev/null 2>&1; then
    printf '%s' "$INPUT" | python3 -c "
import sys, json
try:
    print(json.load(sys.stdin).get('tool_input', {}).get('command', ''))
except Exception:
    pass" 2>/dev/null
  fi
}

CMD=$(extract_command)
[ -z "$CMD" ] && exit 0

DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "git push --force"
  "git push -f "
  "git reset --hard"
  "git clean -fd"
  "DROP TABLE"
  "DROP DATABASE"
  "> /dev/sd"
  "mkfs\."
  ":(){ :|:& };:"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if printf '%s' "$CMD" | grep -qi "$pattern"; then
    printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Aion 安全 hook：检测到危险命令模式（%s）。确有需要请在 Claude Code 外手动执行。"}}\n' "$pattern"
    exit 0
  fi
done
exit 0
