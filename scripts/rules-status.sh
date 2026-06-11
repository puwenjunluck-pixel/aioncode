#!/usr/bin/env bash
# Aion rules status — mechanical staleness scan for the learning flywheel.
# Parses .aion/rules/*.md entries ("[cite_count: N, last_cited: YYYY-MM-DD]")
# and lists archive candidates whose last_cited is older than the threshold.
# Consumed by /aion:review Step 4c; never modifies anything itself.
# Usage: rules-status.sh [--days N] [--today YYYY-MM-DD] [rules_dir]
set -u

DAYS=60
TODAY=""
DIR=".aion/rules"
while [ $# -gt 0 ]; do
  case "$1" in
    --days) DAYS=$2; shift 2 ;;
    --today) TODAY=$2; shift 2 ;;
    *) DIR=$1; shift ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "rules-status: python3 不可用，跳过机械扫描（请人工检查 last_cited 日期）"
  exit 0
fi

python3 - "$DIR" "$DAYS" "$TODAY" << 'EOF'
import datetime as dt
import pathlib
import re
import sys

rules_dir, days, today_s = pathlib.Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
today = dt.date.fromisoformat(today_s) if today_s else dt.date.today()
entry_re = re.compile(
    r"^- \*\*(?P<title>.+?)\*\*.*?\[cite_count: *(?P<count>\d+), *"
    r"last_cited: *(?P<cited>\d{4}-\d{2}-\d{2})(?P<rest>[^\]]*)\]"
)

stale, active, archived = [], 0, 0
for path in sorted(rules_dir.glob("*.md")) if rules_dir.is_dir() else []:
    for line in path.read_text(encoding="utf-8").splitlines():
        m = entry_re.match(line)
        if not m:
            continue
        if "archived" in (m.group("rest") or "") or "status: archived" in line:
            archived += 1
            continue
        age = (today - dt.date.fromisoformat(m.group("cited"))).days
        if age > days:
            stale.append((path.name, m.group("title"), m.group("cited"), age))
        else:
            active += 1

print(f"rules-status: active={active} archived={archived} stale_candidates={len(stale)} (threshold: {days}d)")
for name, title, cited, age in stale:
    print(f"  STALE [{name}] {title} — last_cited {cited} ({age}d ago)")
if stale:
    print("建议：在 review Step 4c 中逐条向用户确认是否标记 status: archived（NEVER 自动删除正文）")
EOF
