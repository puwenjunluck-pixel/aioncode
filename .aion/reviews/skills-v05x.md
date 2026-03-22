---
status: approved
score: 73
verdict: approved
issues_found: 8
rules_extracted: 0
reviewed_at: 2026-03-22
---

# Review: Skills 管理视图 + CLAUDE.md 强制化 + 命令并行策略 + aion-save 增强

## Score: 73/100
**Verdict**: approved (with strong recommendations)

### Dimension Scores
- Code Quality: 26/40
- Security: 20/30
- Architecture Compliance: 27/30

## Passed
- Backend service/router 模式与现有 bugs.py/commands.py 一致
- 路径遍历防护：read_skill/delete_skill/install_plugin 均有 regex 消毒
- subprocess 使用列表形式（无 shell 注入）
- Init step 2.5 绝不覆盖已有 skill
- 前端 skill 视图 sidebar+detail 模式与现有视图一致
- CLAUDE.md 强制化措辞合理（NEVER/ALWAYS）
- 命令并行策略用 "consider using" 非强制措辞
- aion-save 新增 git diff 审计和 CLAUDE.md 标记外更新
- CSS 使用现有变量，双主题自动适配
- ruff 0 违规

## Issues (must fix — introduced by this change)
- **[HIGH]** views.js 660行超500行限制 — 提取 skills 相关函数或压缩现有代码
- **[HIGH]** services/skills.py:186 `list_marketplace_plugins` 54行+nesting 5 — 提取 `_load_installed_set()` 和 `_scan_marketplace_dir()`
- **[HIGH]** project.py:248 step 2.5 nesting depth 5 — 提取 `_install_bundled_skills()`
- **[MEDIUM]** views.js:642 卸载失败按钮文案不一致

## Issues (pre-existing — should be tracked as bugs)
- **[HIGH]** app.js:10 `esc()` 缺少引号转义，onclick 属性注入风险
- **[HIGH]** views.js:17 `applyInline()` 允许 `javascript:` URL
- **[HIGH]** app.py:42 CORS `allow_origins=["*"]` 配合 DELETE/POST 端点
- **[MEDIUM]** 0/52 JS 函数无 doc comments（新规则，需逐步补充）

## Quantitative Quality Gate

| File | Lines | Longest Func | Max Nesting | Status |
|------|-------|-------------|-------------|--------|
| services/skills.py | 205 | 54 (list_marketplace_plugins) | 5 | ⚠️ |
| routers/skills.py | 30 | 7 | 1 | ✅ |
| app.py | 63 | 34 | 2 | ✅ |
| project.py | 263 | 133 (init_project) | 5 | ⚠️ pre-existing |
| index.html | 190 | — | — | ✅ |
| app.js | 287 | — | — | ✅ |
| views.js | 660 | — | — | ⚠️ 超限 |
| style.css | 269 | — | — | ✅ |
| views.css | 184 | — | — | ✅ |
| embedded.py | — | — | — | ✅ 豁免(自动生成) |

## Rules Extracted
无新规则提取（本次注释规则已在 save 阶段写入 style.md）

## Style Patterns Learned
无新模式（现有模式已覆盖）
