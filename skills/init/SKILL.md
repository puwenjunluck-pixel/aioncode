---
name: init
description: 初始化/升级 Aion 工作流层 — 创建 .aion/ 工件层、安装元认知规则到宿主 .claude/rules/、用标记合并工作流段落进 CLAUDE.md。Use when the user 首次在项目使用 aion、asks to 安装工作流/初始化/"set up aion"，或其他 aion 命令发现 .aion/ 不存在时。幂等：重复运行 = 升级，绝不覆盖用户自有内容。
---

# /aion:init — 初始化 / 升级 Aion 工作流层

在宿主项目安装 Aion 的三层资产。重复运行是**升级**，不是重装 — 逐项检查，能 skip 就 skip，有差异就问。

| # | 安装目标 | 位置 | 内容来源 |
|---|---|---|---|
| 1 | 工件层 | `.aion/` | 本 skill 内联 + `references/rule-headers.md` |
| 2 | 元认知规则 | `.claude/rules/metacognition.md` | `references/metacognition.md` |
| 3 | 工作流段落 | `.claude/CLAUDE.md`（`AION:START/END` 标记对内） | `references/claude-md-section.md` |

> ⚠️ **CRITICAL**: NEVER 覆盖用户已有的 CLAUDE.md 内容。只动 `<!-- AION:START -->` / `<!-- AION:END -->` 标记之间的部分，无标记则追加到末尾。
> ⚠️ **CRITICAL**: 任何已存在且内容不同的文件，NEVER 静默覆盖 — 展示 diff 摘要并询问。

## TodoWrite 驱动

启动时用 TodoWrite 建立 5 个 phase 的 todo（按下方标题），每进入一个标 in_progress，完成标 completed。

---

## Phase 1 — 检测现状（只读，不写任何文件）

逐项检查以下条目，分类为 **新装** / **相同（skip）** / **不同（diff + 询问）**：

1. **git 仓库检测**：`git rev-parse --git-dir` 失败 → 非 git 仓库。引导用户先 `git init`，并如实说明「门禁 hook 在非 git 目录不生效」；用户选择不建仓也可继续安装其余资产，但摘要中必须标注此限制
2. `.aion/` 各子目录与 `.aion/changelog.md`
3. `.aion/rules/pitfalls.md` / `style.md` / `perf.md`（读 frontmatter 的 `rule_count`）
4. `.claude/rules/metacognition.md` — 与 `references/metacognition.md` 逐字节比对
5. `.claude/CLAUDE.md` — 是否存在；是否已有 `AION:START/END` 标记对；标记间内容是否与 `references/claude-md-section.md` 一致
6. **根目录 `./CLAUDE.md` 检测**：存在时询问用户将 Aion 工作流段合并进根目录 `./CLAUDE.md` 还是 `.claude/CLAUDE.md`（Phase 4 按用户选择的目标执行）— **绝不静默造出第二份**

输出一张**安装计划表**（条目 / 当前状态 / 将执行的动作），再进入 Phase 2。
若发现标记残缺（只有 START 没有 END，或顺序颠倒）→ 不要猜测边界，展示上下文问用户如何处理，未决前跳过条目 3。

## Phase 2 — 创建 .aion/ 工件层

1. `mkdir -p .aion/{rules,specs,plans,reviews,bugs,refs,prototypes,contracts,tests/e2e}`
2. `.aion/changelog.md` 不存在时创建：

   ```markdown
   # Changelog

   <!-- Aion auto-appends entries here. -->
   ```

3. `.aion/rules/` 写入 `pitfalls.md` / `style.md` / `perf.md` 初始头部 — 模板见 `references/rule-headers.md`，`{TODAY}` 替换为当天日期。
   **已存在的规则文件永不覆盖**（`rule_count > 0` 是项目长期沉淀的资产），直接 skip 并在摘要中标注。

## Phase 3 — 安装元认知规则

将 `references/metacognition.md` 完整内容写入宿主 `.claude/rules/metacognition.md`（先 `mkdir -p .claude/rules`）。这是原生 rules 目录，每会话自动加载。

- 不存在 → 直接写入
- 已存在且内容相同 → skip 并报告
- 已存在且内容不同 → 展示 diff 摘要（变更的 section 标题 + 增删行数），问用户：
  - (a) **更新** — 覆盖为新版（推荐，纪律层随插件升级）
  - (b) **保留** — 不动现有文件（用户可能有本地定制）
  - (c) **跳过** — 本次不处理，下次 init 再问

NEVER 截断、改写或"精简"规则内容 — 元认知规则是产品核心资产，逐字节写入。

## Phase 4 — 合并 CLAUDE.md 工作流段

以 `references/claude-md-section.md` 的**完整内容**（含首尾标记行）为待合并块；目标文件默认 `.claude/CLAUDE.md`，根目录 `./CLAUDE.md` 存在时按 Phase 1 中用户的选择执行（绝不同时写两份）：

| 宿主状态 | 动作 |
|---|---|
| `.claude/CLAUDE.md` 不存在 | 创建，内容即待合并块 |
| 存在，已有标记对 | 仅替换 `AION:START` 到 `AION:END`（含标记）之间的内容；相同 → skip |
| 存在，无标记 | 整块追加到文件末尾（前面空一行） |

标记外的每一行都是用户的 — **一个字符都不改**。替换前若标记间内容与模板不同，展示 diff 摘要再执行（标记间区域归 Aion 管理，默认更新，但要让用户看到变了什么）。

## Phase 5 — 安装摘要 + 引导

1. 输出摘要表：每个条目 + 最终状态（created / updated / skipped-same / kept-old）
2. 状态声明前**实际验证**：`ls .aion/`、确认三个文件存在（Iron Law 2 — 不报告未发生的动作）
3. 输出引导：

   > 安装完成。下一步：
   > - 新项目从 `/aion:think` 开始 — 把想法收敛为 spec
   > - 接手已有项目先跑 `/aion:scan` — 冷启动扫描
   > - 提交用 `/aion:commit`（门禁 hook 随插件已生效 — 仅在 git 仓库 + `.aion/` 存在时拦截，review 先行）

---

## Checklist

- [ ] Phase 1 安装计划表已输出，分类清楚（含 git 仓库与根目录 `./CLAUDE.md` 检测）
- [ ] Phase 2 目录齐全，已有规则文件未被覆盖
- [ ] Phase 3 metacognition 逐字节写入，差异时三选项询问
- [ ] Phase 4 仅动标记间内容，用户内容零改动
- [ ] Phase 5 摘要基于实际验证（ls / 文件存在性）
- [ ] TodoWrite 全程驱动

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 覆盖用户已有 CLAUDE.md 内容而不用标记合并 | 摧毁用户的项目记忆，信任不可恢复 | CRITICAL |
| 覆盖 `rule_count > 0` 的 `.aion/rules/` 文件 | pitfalls/style/perf 是项目长期学习成果，丢了找不回 | CRITICAL |
| 内容不同时静默覆盖而不展示 diff | 用户的本地定制被无声丢弃 | CRITICAL |
| 削弱/截断/改写 metacognition 规则后再安装 | 元认知规则是产品核心资产，不容稀释 | CRITICAL |
| 跳过 Phase 1 直接开写 | 无法区分新装/升级，幂等性失效 | HIGH |
| 摘要里报告未实际执行/验证的动作 | 违反 Iron Law 2：evidence before claims | HIGH |

### Rationalization Prevention

以下念头 = STOP，你在合理化（见 `references/metacognition.md`，本 skill 正要安装它）：

| 借口 | 真相 |
|--------|---------|
| ".aion/ 已存在，整个 init 跳过吧" | 幂等 ≠ 不做。逐项检查，每项独立决定 skip/update。 |
| "diff 太长，直接覆盖更快" | 那是用户的资产。展示摘要，让用户决定。 |
| "CLAUDE.md 反正要加段落，全文件重写更整洁" | 标记外的每一行都是用户的。只动标记之间。 |
| "用户肯定想要最新版，不用问" | 假设 ≠ 确认。问一下只花一句。 |
| "规则文件头部反正一样，重写一遍没事" | `rule_count > 0` 时正文有沉淀条目，重写 = 清空。 |

## Exit Status

- `DONE` — 全部条目 created / updated / skipped-same
- `DONE_WITH_CONCERNS` — 存在 kept-old 条目（用户保留旧版，与插件版本不一致）
- `BLOCKED` — 写入失败（权限/只读）或标记残缺等待用户决定
