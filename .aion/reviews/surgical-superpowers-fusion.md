---
status: approved
score: 93
verdict: approved
issues_found: 0
rules_extracted: 1
reviewed_at: 2026-04-14
review_rounds: 2
---

# Review: Surgical superpowers 融合 (v0.7.6)

## Score: 93/100
**Verdict**: `approved`

### Dimension Scores
- Code Quality: 37/40
- Security: 30/30
- Architecture Compliance: 26/30

## Verification Gate ✅

本次改动跨 doc/config 与 Python/JS 运行时代码。实际执行的验证:

| 验证项 | 命令 | 结果 |
|---|---|---|
| `profiles.py` import + rename 完整性 | `python3.11 -c "from aioncode.core.profiles import ...; assert 'aion-think' in names ..."` | ✓ 11 commands,aion-think 在所有 role preset |
| `init.py` import | `python3.11 -c "from aioncode.commands.init import *"` | ✓ OK |
| `embedded.py` 合规性 | 检查 help 段无 aion-design,aion-think 注入 | ✓ OK |
| Dashboard rebuild | `python3.11 -m aioncode.internal.dashboard.frontend.build_frontend` | ✓ EMBEDDED_HTML 117983 chars |
| PLATFORM 标签配对 | grep count 开闭标签 | ✓ think 6/6, fix 6/6, review 2/2 |
| aion-design live 扫描 | grep 全 live 路径 | ✓ 0 命中(仅 aion-think.md:3 历史演进注释,预期保留) |
| aion-plan Step 编号连续性 | grep heading | ✓ 0→1→2→3→3.5→3.8→4→4.5→5,全用 `###` |

**验证结论**:所有 rename 路径已打穿,无新增 regression。

## Passed (本次全部通过)
- ✅ Iron Laws 注入 metacognition.md / aion-review / aion-fix 三处一致
- ✅ `aion-think.md` 10-phase 结构,TodoWrite 驱动(工具名修正)
- ✅ `aion-plan.md` 触发方式 / bite-sized task / Step 5 heading 层级正确
- ✅ CREDITS.md 归属清晰
- ✅ `.aion/rules/` 模板(metacognition / spec / plan)独立抄录,不依赖 superpowers
- ✅ **Rename 跨层完整性**:profile → init → install.sh → template(.md.tpl + checklist) → command 内部引用 → dashboard UI → build artifact 全链路更新
- ✅ uninstall.sh 采用动态 `find aion-*.md`,对 rename 天然兼容

## Issues
无 blocking。两处 minor 观察,不阻塞 approval:

- **[minor]** `commands/aion-plan.md:225` Output Format 新文案 "referenced from Step 4's Format section" — 准确但稍绕。后续若有其他编辑本文件时顺手合并到 Step 4.5 之后的 Format 段即可。
- **[minor]** `views.js` release log 段保留 "aion-design" 3 处(v0.6.6 / 2026-03-23 两个历史版本)— 是有意的"不篡改历史",但对首次读文档的新用户可能有疑惑。可选在段首加一行 "(命令已于 v0.7.6 重命名为 aion-think,此为发布时原貌)"。**不阻塞**。

## Rules Extracted

### 新增 pitfalls 候选(建议用户拍板)

> **命令 rename 必须跨层扫描七件套** (2026-04-14, from surgical-fusion v0.7.6)
>
> rename 一个 `aion-*` 命令时,grep 需覆盖以下 7 层,少一层就会留残留:
> 1. `commands/aion-*.md` (命令定义 + 内部 `/project:aion-*` 引用)
> 2. `aioncode/core/profiles.py` (CommandInfo + ROLE_PRESETS)
> 3. `aioncode/commands/init.py` (安装时的 hint)
> 4. `aioncode/internal/templates/CLAUDE.md.tpl` + `GEMINI.md.tpl` (给新项目的默认 CLAUDE.md)
> 5. `aioncode/internal/templates/aion/checklists/*.md` (命令对应 checklist)
> 6. `aioncode/internal/dashboard/frontend/static/*.js` + `*.html` → 重跑 `build_frontend.py` 同步 `embedded.py`
> 7. `install.sh` + `.aion/rules/pitfalls.md` 中的命令列表注释
>
> **Verify**: `grep -rn "aion-{旧名}" commands/ aioncode/core/ aioncode/commands/ install.sh aioncode/internal/templates/` 结果为 0 (允许 `commands/aion-{新名}.md` 内部历史演进注释,以及 `views.js` release log 段)。
>
> **原因**:本次 surgical fusion 首轮 review 只查了 `.aion/` 和 `commands/`,漏掉 `profiles.py` 等 6 层,导致"声称完成"但新用户 init 出来仍是旧命令。Iron Law 2 的反面教材。

**建议**:加到 `.aion/rules/pitfalls.md`。用户可运行 `/project:aion-save` 或手动 append。

## Style Patterns Learned
无新增(本次未涉及代码编写)。

---

## 批准结论

**本次 PR 改动建议分 3 个 commit**(细粒度便于回溯):

1. `feat: surgical superpowers fusion — think/plan/review/fix 注入 Iron Laws + Verification Gate + 10-phase`
   - 含:rename aion-design → aion-think,注入 metacognition / spec-template / plan-template,命令文件内部引用统一,CREDITS.md
2. `chore: propagate aion-think rename across install/template/profile layers`
   - 含:profiles.py / init.py / install.sh / CLAUDE.md.tpl / GEMINI.md.tpl / checklists rename / pitfalls rule
3. `chore(dashboard): refresh help + command catalog + rebuild embedded.py`
   - 含:views.js / brainstorm.js / index.html + rebuilt embedded.py

或者按用户偏好一个大 commit 也行(solo master 风格)。

## Next Steps
- `/project:aion-commit` 提交
- 建议 bump 版本 v0.7.6 + 更新 `.aion/changelog.md`
