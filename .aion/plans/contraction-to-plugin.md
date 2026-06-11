---
status: completed
created_at: 2026-06-12
spec: contraction-to-plugin.md
version: 1
previous_version: null
change_reason: null
author: waynepo
scope: full
current_step: 0
total_steps: 12
---

# Plan: 收缩为插件形态（P1-P4 + 优化循环）

**Goal:** 把 AionCode 重构为名为 `aion` 的 Claude Code 插件（9 skills + commit 门禁 hook），删除机制层，达到对标领先插件的内容质量。

**Architecture:** 同仓库重构。`skills/` 为新产品源（每 skill 一目录：SKILL.md + references/），`hooks/` + `scripts/` 实现机械门禁，旧 Python/Dashboard 一次性删除（archive/v0.7-cli 已封存）。

**Tech Stack:** Markdown skills + bash hook + `claude plugin validate`。

**Spec:** `.aion/specs/contraction-to-plugin.md` (v2)

---

## Tasks

### Task 1 — 插件骨架
- [ ] `.claude-plugin/plugin.json`（name: aion, version: 0.8.0, MIT）
- [ ] `.claude-plugin/marketplace.json`（self-host 入口，source: 当前仓库）
- Verify: `claude plugin validate .` 通过

### Task 2 — think 垂直切片（手工，作为其余 skills 的范本）
- [ ] `skills/think/SKILL.md`：蒸馏 commands/aion-think.md。砍：PLATFORM:antigravity 块、Dashboard 协作段（已归档）、product-design-layer.md 死引用（结构内联至 Phase 10.1）。改：`/project:aion-plan` → `/aion:plan`；spec-template 引用 → `references/spec-template.md`（自包含）+ 宿主 `.claude/rules/` 种子双轨
- [ ] `skills/think/references/spec-template.md` + `references/write-protocol.md`
- Verify: `grep -n "PLATFORM:\|/project:\|product-design-layer" skills/think/` 为 0；`claude plugin validate .` 通过

### Task 3 — 其余 8 skills 并行蒸馏（subagents，think 为范本）
- [ ] plan（修自相矛盾：统一 bite-sized 格式、删「立即执行」、修 Step 3.8 残句）/ review（吸收 audit 为 `--deep`；frontmatter 增 reviewed_files+base_commit；修学习飞轮出口：stale 清理改为 review 内置步骤）/ commit（门禁说明指向 hook；删 Tier 残留；补 fix/qa atomic 豁免）/ fix / qa / scan（蒸馏：砍与原生 /init 重叠部分）/ save（薄壳：工件落盘）/ init（新写：创建 .aion/ + 写宿主 .claude/rules/ 种子）
- 统一约束：Iron Law 编号全套与 metacognition.md 对齐；无 aion-help/aion-loop/aion-audit/PLATFORM 残留
- Verify: 全目录 grep 断言 + validate 通过

### Task 4 — 门禁 hook
- [ ] `hooks/hooks.json`（PreToolUse, matcher Bash）+ `scripts/check-review.sh`
- 放行条件：无 .aion/ 目录｜staged 全在 .aion/ 下｜commit msg 以 fix(bug): 开头｜存在 review: base_commit==HEAD 且 staged ⊆ reviewed_files。否则 deny + 指引
- [ ] `tests/hook/test_check_review.sh` 表驱动（tmp git repo：阻断/放行×4 类）
- Verify: `bash tests/hook/test_check_review.sh` 全过

### Task 5 — 机制层删除（一次提交）
- [ ] 删 aioncode/ tests/(Python) pyproject.toml aioncode.spec install.sh uninstall.sh commands/ docs/(旧) .github/workflows/release.yml aioncode.egg-info
- [ ] ci.yml 重写：hook 测试 + plugin validate
- Verify: `git ls-files | grep -c '\.py$'` 仅剩 0（.aion/hooks 的 py 除外）；新 CI 脚本本地可跑

### Task 6 — P4 文档
- [ ] README 重写（中文为主+EN TL;DR；≥2 条 pitfalls 真实规则；安装=2 步 plugin 命令）/ MIGRATION.md / CHANGELOG.md / LICENSE 确认
- Verify: README 内命令与 skills/ 实际一致（grep 校验）

### Task 7 — 对标优化循环（直到达标）
- [ ] 基准：读本机 superpowers 插件源（~/.claude/plugins/cache），多 agent 对抗评审：纪律深度 / 指令可执行性 / token 成本 / 独有能力四维
- [ ] 达标线：四维无 high 差距 + 独有能力（机械门禁 hook、可审计飞轮、工件闭环、中文深度）成立 + validate/e2e 全绿
- [ ] 未达标 → 修差距 → 重评（循环）
- Verify: 末轮评审报告 0 项 high

### 提交纪律
每 task 一次 commit，review 文件含 reviewed_files+base_commit（自食 hook 门禁）。不 push（用户保留）。
