#!/usr/bin/env bash
# AionCode Monitor Hook — Collects Claude Code events for Mission Control
#
# Called by Claude Code hooks (PreToolUse, PostToolUse, SubagentStart, etc.)
# Reads JSON event data from stdin, adds timestamp, appends to events.jsonl
# Must complete in <5 seconds to avoid blocking Claude Code.

set -euo pipefail

# Monitor directory lives alongside .aion/ in project root
PROJECT_DIR="$(pwd)"
MONITOR_DIR="${PROJECT_DIR}/.aion/monitor"
EVENTS_FILE="${MONITOR_DIR}/events.jsonl"

# Ensure monitor directory exists
mkdir -p "${MONITOR_DIR}"

# Read full stdin JSON (Claude Code pipes event data here)
INPUT=$(cat)

# Skip empty input
if [ -z "${INPUT}" ]; then
  exit 0
fi

# Add ISO 8601 UTC timestamp and append as single JSONL line
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "{\"ts\":\"${TIMESTAMP}\",\"data\":${INPUT}}" >> "${EVENTS_FILE}"
