#!/usr/bin/env bash
# AionCode safety hook — blocks dangerous bash commands
# Used as PreToolUse hook for Bash tool

INPUT="$CLAUDE_TOOL_INPUT"

# Extract the command from JSON input
CMD=$(echo "$INPUT" | grep -o '"command":"[^"]*"' | head -1 | sed 's/"command":"//;s/"$//')

# Dangerous patterns
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf ~"
  "rm -rf \."
  "git push --force"
  "git push -f "
  "git reset --hard"
  "git clean -fd"
  "DROP TABLE"
  "DROP DATABASE"
  "truncate "
  "> /dev/sda"
  "mkfs\."
  ":(){ :|:& };:"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$CMD" | grep -qi "$pattern"; then
    echo "BLOCKED: Dangerous command detected — $pattern"
    echo "If you need this, run it manually outside Claude Code."
    exit 2
  fi
done

exit 0
