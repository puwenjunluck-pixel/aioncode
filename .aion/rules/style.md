---
category: style
rule_count: 2
last_updated: 2026-03-21
---

# Style — Project code conventions

<!-- Rules are auto-extracted by /aion-learn and /aion-review.
Format:
- **{Title}** ({source}, {date}) [cite_count: {N}, last_cited: {date}]
  {1-2 sentence description with a concrete example from this project}

Each rule entry tracks:
  - cite_count: how many times this rule was referenced during reviews/learns
  - last_cited: the last date this rule was referenced
  - status: active | deprecated | archived (default: active)
Rules with no citations in 60+ days are flagged as "stale" by aion-status.
-->

- **dashboard.py 零外部依赖** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21]
  `dashboard.py` 只使用 Python 标准库（`http.server`, `json`, `pathlib`, `subprocess` 等）。需要 YAML 解析时用 `read_team_config()` 手写状态机，需要 HTTP 路由时用 `startswith()` 匹配。添加新功能前确认 stdlib 有替代方案。

- **命令文件结构规范** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21]
  18 个 `commands/aion-*.md` 命令文件遵循统一结构：Header → `$ARGUMENTS` → Role → `⚠️ CRITICAL` 断言 → Steps（Step 0 = 上下文加载）→ Next Steps → Checklist → Anti-Patterns 表 → Output Format → Exit Status。新命令必须遵循此结构。
