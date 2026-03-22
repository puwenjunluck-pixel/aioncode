---
category: style
rule_count: 11
last_updated: 2026-03-22
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

- **分发物必须单文件自包含** (design, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  开发态允许引入成熟第三方库（如 rich, requests），但 PyInstaller 打包后的分发物必须是单文件自包含二进制，用户无需预装 Python 或任何库。`internal/dashboard.py` 保持零外部依赖（历史遗留，v0.5 重构时再统一）。

- **命令文件结构规范** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21]
  18 个 `commands/aion-*.md` 命令文件遵循统一结构：Header → `$ARGUMENTS` → Role → `⚠️ CRITICAL` 断言 → Steps（Step 0 = 上下文加载）→ Next Steps → Checklist → Anti-Patterns 表 → Output Format → Exit Status。新命令必须遵循此结构。

- **单文件行数上限 500 行** (design, 2026-03-22) [cite_count: 1, last_cited: 2026-03-22]
  单个源码文件不得超过 500 行（不含空行和注释）。超过时必须拆分为多个模块。已知豁免：`frontend/embedded.py`（自动生成文件）。

- **单函数行数上限 50 行** (design, 2026-03-22) [cite_count: 1, last_cited: 2026-03-22]
  单个函数/方法不得超过 50 行（逻辑行，不含空行和注释）。超过时必须提取子函数。例：`aioncode/commands/init.py` 的 `_init_project()` 应控制在 50 行以内，复杂逻辑拆分为 `_copy_commands()`、`_scaffold_aion()` 等子函数。

- **嵌套深度上限 4 层** (design, 2026-03-22) [cite_count: 1, last_cited: 2026-03-22]
  if/for/while/try 嵌套不得超过 4 层。使用 early return、guard clause 或提取函数来降低嵌套。

- **参数个数上限 5 个** (design, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  函数参数不得超过 5 个（不含 self/cls）。超过时使用 dataclass 或 TypedDict 封装。例外：`__init__` 方法在必要时可放宽至 7 个。

- **Python: 模块必须有 module docstring** (save, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  每个 .py 文件顶部必须有一行 module docstring 说明用途。例：`"""Bug management — list, filter, statistics."""`

- **Python: 公开函数必须有 docstring** (save, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  所有不以 `_` 开头的函数必须有 docstring（说明 what + returns）。复杂函数加 Args 段。私有函数可选。

- **JavaScript: 文件顶部必须有模块说明** (save, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  每个 .js 文件必须有 `/* ... */` 格式的模块说明注释。

- **JavaScript: 公开函数加一行说明** (save, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  公开函数前加 `/** 一行说明 */`，不需要完整 JSDoc。section 分隔线模式（`// ══════`）保持。

- **注释只解释 why，不解释 what** (save, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  行内注释解释"为什么这样做"，不解释"这段代码在做什么"。不写 TODO/FIXME（用 `.aion/bugs/` 跟踪），不保留注释掉的代码。
