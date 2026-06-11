#!/usr/bin/env bash
# Aion safety hook — PreToolUse on Bash; denies destructive command patterns.
# Parses per command segment (split on ;|&) and inspects the actual program +
# flags + targets, so flag order/bundling can't dodge it and prose mentioning
# dangerous strings (echo/grep/commit messages) isn't falsely killed.
# This guards against slips, not adversaries. Fail-open on parse failure.
set -uf

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

deny() {
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Aion 安全 hook：检测到危险命令（%s）。确有需要请在 Claude Code 外手动执行。"}}\n' "$1"
  exit 0
}

CMD=$(extract_command)
[ -z "$CMD" ] && exit 0

# Substring checks for patterns with no legitimate prose ambiguity.
case "$CMD" in
  *"mkfs."*|*":(){ :|:& };:"*|*"> /dev/sd"*) deny "磁盘/fork-bomb 模式" ;;
esac

# Per-segment structural checks. deny() prints JSON then exits the pipeline
# subshell; the trailing exit 0 of the script is harmless after that.
printf '%s\n' "$CMD" | tr ';&|' '\n' | while IFS= read -r seg; do
  # shellcheck disable=SC2086
  set -- $seg
  [ $# -eq 0 ] && continue
  # Skip env-var prefixes and sudo/env wrappers to find the real program.
  while [ $# -gt 0 ]; do
    case "$1" in *=*) shift ;; sudo|env) shift ;; *) break ;; esac
  done
  [ $# -eq 0 ] && continue
  prog=$1; shift

  case "$prog" in
    rm)
      has_r=0; has_f=0; bad_target=""
      for tok in "$@"; do
        case "$tok" in
          --recursive) has_r=1 ;;
          --force) has_f=1 ;;
          --*) ;;
          -*[rR]*f*|-*f*[rR]*) has_r=1; has_f=1 ;;
          -*[rR]*) has_r=1 ;;
          -*f*) has_f=1 ;;
          /|/.|"/*") bad_target="/" ;;
          "~"|"~/"|'$HOME'|"$HOME") bad_target="~" ;;
        esac
      done
      if [ "$has_r" = 1 ] && [ "$has_f" = 1 ] && [ -n "$bad_target" ]; then
        deny "rm 递归强制删除根/家目录"
      fi
      ;;
    git)
      # Skip git global options (-C path, -c k=v, --git-dir=...).
      while [ $# -gt 0 ]; do
        case "$1" in
          -C|-c) shift 2 2>/dev/null || break ;;
          --*) shift ;;
          -*) shift ;;
          *) break ;;
        esac
      done
      sub=${1:-}; [ $# -gt 0 ] && shift
      case "$sub" in
        push)
          for tok in "$@"; do
            case "$tok" in
              --force-with-lease*) ;;
              --force) deny "git push 强推" ;;
              --*) ;;
              -*f*) deny "git push 强推" ;;
            esac
          done
          ;;
        reset)
          for tok in "$@"; do
            [ "$tok" = "--hard" ] && deny "git reset --hard"
          done
          ;;
        clean)
          for tok in "$@"; do
            case "$tok" in
              --force) deny "git clean 强制删除" ;;
              --*) ;;
              -*f*) deny "git clean 强制删除" ;;
            esac
          done
          ;;
      esac
      ;;
    mysql|psql|sqlite3|mariadb)
      if printf '%s' "$seg" | grep -qiE 'DROP +(TABLE|DATABASE)'; then
        deny "数据库 DROP 语句"
      fi
      ;;
  esac
done
exit 0
