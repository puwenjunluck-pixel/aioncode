# Rule File Headers — `.aion/rules/` 初始模板

`/aion:init` 用本文件为宿主 `.aion/rules/` 创建三个规则文件的初始头部。
写入时将 `{TODAY}` 替换为当天日期（YYYY-MM-DD）。
目标文件已存在 → **永不覆盖**（`rule_count > 0` 意味着项目已有沉淀资产），直接 skip。

## pitfalls.md

```markdown
---
category: pitfalls
rule_count: 0
last_updated: {TODAY}
---

# Pitfalls — Known gotchas and traps

<!-- Rules are auto-extracted by /aion:review (auto-learn runs in every review).
Format:
- **{Title}** ({source}, {date}) [cite_count: {N}, last_cited: {date}]
  {1-2 sentence description with a concrete example from this project}

Each rule entry tracks:
  - cite_count: how many times this rule was referenced during reviews/learns
  - last_cited: the last date this rule was referenced
  - status: active | deprecated | archived (default: active)
Rules with no citations in 60+ days are flagged as "stale" (archive candidates).
-->
```

## style.md

```markdown
---
category: style
rule_count: 0
last_updated: {TODAY}
---

# Style — Project coding conventions

<!-- Rules are auto-extracted by /aion:review (auto-learn runs in every review).
Format:
- **{Title}** ({source}, {date}) [cite_count: {N}, last_cited: {date}]
  {1-2 sentence description with a concrete example from this project}

Each rule entry tracks:
  - cite_count: how many times this rule was referenced during reviews/learns
  - last_cited: the last date this rule was referenced
  - status: active | deprecated | archived (default: active)
Rules with no citations in 60+ days are flagged as "stale" (archive candidates).
-->
```

## perf.md

```markdown
---
category: perf
rule_count: 0
last_updated: {TODAY}
---

# Perf — Performance rules

<!-- Rules are auto-extracted by /aion:review (auto-learn runs in every review).
Format:
- **{Title}** ({source}, {date}) [cite_count: {N}, last_cited: {date}]
  {1-2 sentence description with a concrete example from this project}

Each rule entry tracks:
  - cite_count: how many times this rule was referenced during reviews/learns
  - last_cited: the last date this rule was referenced
  - status: active | deprecated | archived (default: active)
Rules with no citations in 60+ days are flagged as "stale" (archive candidates).
-->
```
