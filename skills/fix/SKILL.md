---
name: fix
description: Bug 修复 — 按角色消费 .aion/bugs/ 报告，4-phase 根因分析，红→绿验证，原子提交。Use when fixing bug reports in .aion/bugs/ (e.g. after /aion:qa), when the user reports a bug or asks to 修复/排查/debug something, or with a specific BUG-ID. Not for new features or refactoring.
---

# /aion:fix — Bug 修复

Fix bugs from `.aion/bugs/` reports（或用户口述的 bug）。按角色过滤，系统化定位根因，红→绿验证，每个 bug 一个原子提交。

**Arguments**: 可选 bug ID（如 `F-0325-001`）只修指定 bug。Flags: `-f` 仅前端 / `-b` 仅后端 / `--auto`（跳过 triage 确认，按优先级修完，自动提交每个 fix）/ `--deep`（4-phase 根因分析）。为空时修当前角色匹配的全部 open bug。

## Iron Laws（不可协商 — 见宿主 `.aion/rules/metacognition.md`）

```
1. NO FIX WITHOUT ROOT CAUSE — 修任何 bug 之前，MUST 完成根因调查
2. ONE BUG ONE COMMIT — 原子提交，绝不 batch 多个 bug 到一个 commit
3. VERIFY BEFORE CLAIM — 声称"修好"之前，MUST 本轮跑过原始复现用例看到通过
4. 3+ FIXES FAIL → QUESTION ARCHITECTURE — 同一 bug 失败 3 次 = 架构问题，停下来讨论
```

> 💡 **强烈建议默认启用 `--deep`** — 即使 bug 看起来简单。simple bug 有 simple 根因，走流程 2 分钟；跳过的代价是症状式修复 → bug 换个形式回归。只有 bug **极度明确**（已知 typo、已知空指针）且无疑义时才省略。

## Role

你是一个 **focused bug fixer**：读报告 → 定位精确代码 → 最小修复 → 红→绿验证 → 原子提交。修 bug 时不顺手重构 — one bug, one commit。

> ⚠️ **CRITICAL**: Fix the bug as described. 不扩 scope，不重构无关代码。违反这条是本命令失败的第一原因。

## 提交与门禁的关系（先读懂再动手）

「每个 bug 立即提交」与「commit 前必须 review」**不矛盾**，分工如下：

1. **修复中**：每修完一个 bug 立即原子提交，提交信息**必须严格以 `fix(bug):` 开头**，格式 `fix(bug): {BUG-ID} {一句话}`。这个前缀是 commit 门禁 hook 的**官方豁免** — 没有它，提交会被门禁拦下（门禁默认要求先过 `/aion:review`）。
2. **整批修完后**：**仍建议**跑 `/aion:review` 对本修复批次做**事后审查**。这是质量动作，不是门禁前置 — 豁免让你能原子提交，事后 review 保证批次质量并触发 auto-learn。

## Steps

### Step 0: Role & Scope + Bug 加载

Read `.aion/config.yml` → `profile.role` + `profile.project_type`。

**Project type → bug 目录模式**：`frontend`/`backend` → Unified（bug 全在 `.aion/bugs/` 根）；`fullstack`/`monorepo` → 项目根存在 `frontend/` + `backend/` 目录则 Split，否则 Unified。

```
Role → Bug scope:
  designer / tester → STOP: "该角色不修 bug。用 /aion:qa --report-only 生成报告。"
  frontend  → bugs/frontend/*.md + 根目录 F-*.md
  backend   → bugs/backend/*.md + 根目录 B-*.md
  fullstack → bugs/ 全部
```

**Argument overrides**：`-f` 仅前端 / `-b` 仅后端 / `{BUG-ID}` 无视角色直接修该 bug。

Glob `.aion/bugs/**/*.md` 按 scope 过滤，只加载 `status: open`。

**优雅降级（口述模式）**：`.aion/bugs/` 不存在或没有 open bug 时 —
- 用户在对话中描述了 bug → 把口述当作 bug report，直接进 Step 2 走 4-phase 流程（此时无 verify_test，**必须自己构造复现用例**，见 2e）
- 没有任何 bug 输入 → "没有符合条件的待修 bug。" 退出 `DONE`

### Step 1: Bug Triage

列出将修的 bug（按 P0→P1→P2→P3 排序，含 ID / 级别 / 标题），问："开始修复？[Y/n]"
`--auto`：跳过确认直接开始，全部按优先级修；非 auto 且 >3 个 bug 时，问用户只修高优先级还是全修。

### Step 2: For Each Bug（按优先级）

#### 2a. Read Bug Report
读完整报告，提取：复现步骤 / expected / actual / evidence（file:line）/ verify_test。口述模式：向用户确认这五项中缺失的关键项。

#### 2b. Locate Code
1. evidence 有 `file:line` → 直接读该处
2. 有 console error / HTTP endpoint → grep 错误串或路由
3. 只有 UI 症状 → 搜处理该 UI 的组件/函数

**Never start fixing without locating the exact code first.**

#### 2c. Reuse Scan
动手前搜代码库中相似 pattern / 同类 bug 的既有修法 — 防止同一根因在多处被不同方式各修一遍。

#### 2c.5 Root Cause Analysis（`--deep` 时，4-phase）

**Phase 1 复现** — 收集证据，不猜。
- 读完整错误信息/stack trace；沿调用链（caller → callee）trace 代码路径复现
- `git log` 查受影响文件的近期改动 — 是最近的 commit 引入的吗？
- 列出全部假设："I assume X because Y"；跨多模块调查时，用 Agent tool 并行 subagent

**Phase 2 根因** — 找到 work 的对照再下结论。
- 找代码库中**正常工作**的相似路径，diff 出差异；判断 systemic vs isolated（同 pattern 在别处也有吗？）
- 形成**单个**可检验假设："bug 发生是因为 {X} 当 {Y}"，设计最小实验验证 — 被推翻则带新证据回 Phase 1，**不要盲试下一个 fix**

**Phase 3 修复** — 带着确信下手。
- 先写复现 bug 的 failing test（fix 前必须 fail）
- 应用最小 fix

**Phase 4 回归验证** — 红→绿闭环（见 2e）+ 检查 Phase 2 发现的同 pattern 位置是否需要同步修。

**Escalation**：同一 bug 修 3 次失败 → STOP，质疑架构，带证据汇报用户，建议进 `/aion:think` 讨论，不要第 4 次。

#### 2d. Fix Code
最小变更直击根因：只修报告描述的问题；不重构无关代码；不顺手加 feature；编辑前读完整文件。

#### 2e. Verify Test — 红→绿证据（Iron Law 3）

按 metacognition 的 **Verification Before Claim**：IDENTIFY → RUN → READ → VERIFY → ONLY THEN claim。每个 fix 必须留下红→绿证据，**没有红→绿就没有"修好"**：

1. 先跑原始复现用例，看到**失败**（red）— 在 fix 之前
2. 应用 fix
3. 再跑，看到**通过**（green）。可选加强：临时 revert fix 确认又失败 → restore → 再次通过，证明 fix 真的起作用

- 报告有 `verify_test` → 跑它，**必须 100% 通过**才能标 fixed
- 没有 `verify_test`（含口述模式）→ 自己构造最小复现用例走红→绿，并跑相关测试套件
- 失败 → fix 不完整，换思路（最多 2 次）；仍失败 → 跳过该 bug 修下一个，最终报 `BLOCKED`

不跑 red→green 的"测试"可能是空 assertion，**没证明力**。

#### 2f. Atomic Commit（门禁豁免路径）
```
git add {仅本 bug 改动的文件}
git commit -m "fix(bug): {BUG-ID} {一句话}"
```
提交信息**严格以 `fix(bug):` 开头**（门禁 hook 官方豁免，见上文「提交与门禁的关系」）。One commit per bug，绝不 batch。口述模式无 BUG-ID 时用 `fix(bug): {模块} {一句话}`。`--auto`：自动 stage + commit，Step 3 汇总审计。

#### 2g. Update Bug Status
```yaml
status: fixed
fixed_by_commit: {short hash}
updated_at: {YYYY-MM-DD}
```
（口述模式无报告文件，跳过。）然后进入下一个 bug。

### Step 3: Summary

```
Bug Fix Summary
Fixed:   {N} — {BUG-ID}: {title} — commit {hash}（红→绿证据：{verify_test}）
Skipped: {N} — {BUG-ID}: {原因 — BLOCKED / 延期 / 不在角色 scope}
Total commits: {N}
```

## Next Steps
整批修完后**建议**跑 `/aion:review` 对修复批次做事后审查（质量动作，非门禁前置 — 原子提交已通过 `fix(bug):` 前缀豁免完成）。

## Checklist
- [ ] Role + scope 从 config.yml 确定（或口述模式优雅降级）
- [ ] 每个 bug：先定位精确代码再动手；Reuse Scan 做了；`--deep` 时 4-phase 完成
- [ ] 每个 bug：红→绿验证有证据（verify_test 或自构用例）
- [ ] 每个 bug：原子提交（信息严格以 `fix(bug):` 开头）+ status 更新为 fixed
- [ ] 无无关代码改动，无顺手加的 feature
- [ ] 整批后建议了 `/aion:review` 事后审查

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 没定位到精确代码就开修 | 靠猜 → 错误 fix 或新 bug | CRITICAL |
| 多个 bug batch 进一个 commit | 无法单独 revert | HIGH |
| 提交信息不以 `fix(bug):` 开头 | 失去门禁豁免被 hook 拦截，或变相绕过门禁 | HIGH |
| 跳过 verify_test / 红→绿 | bug 可能换个形式还活着 | HIGH |
| 修 bug 顺手重构 | scope 扩张，引入新风险 | HIGH |
| 不走根因分析就猜 fix | 症状式修复掩盖底层问题，bug 回归 | HIGH |
| 同一 bug 第 4 次硬试 | 3 次失败 = 架构问题，该升级讨论而非坚持 | MEDIUM |
| 无 `-f`/`-b` 却绕过角色限制 | designer/tester 误改代码 | MEDIUM |

### Rationalization Prevention

以下念头 = STOP，你在合理化（见宿主 `.aion/rules/metacognition.md`）：

| 借口 | 真相 |
|---|---|
| "bug 很简单，不用 --deep" | 简单 bug 有简单根因，流程 2 分钟。只有极度明确才豁免。 |
| "改完了，应该修好了" | Should ≠ does。跑红→绿，看完整输出。 |
| "测试上次跑过了" | 上一轮 ≠ 本轮。Iron Law 3：本轮跑。 |
| "顺手把旁边代码也理一下" | 那是另一个 commit 的事。One bug one commit。 |
| "有 fix(bug): 豁免，证据可以省了" | 豁免只免门禁前置，不免红→绿证据。 |
| "再试一次肯定行"（第 4 次） | 3 次失败 = 架构信号。停，升级讨论。 |

## Exit Status
- `DONE` — 所有符合条件的 bug 已修复（含红→绿证据）
- `DONE_WITH_CONCERNS` — 部分 bug 未修（blocked / 延期）
- `BLOCKED` — 角色不允许修 bug，或 2 次尝试后 verify 仍失败
- `NEEDS_CONTEXT` — bug 报告信息不足以定位问题
