<!-- AION:START -->
# Aion — Workflow Intelligence

## Rules (MANDATORY)
NEVER write or edit any code file without first reading ALL rules in `.claude/rules/` and `.aion/rules/`. This is non-negotiable.

`.claude/rules/metacognition.md` 是元规则 — 元认知 / 反合理化 / Verification Gate / Iron Laws。每次动作前生效,不是只在某个命令内。

## Context
ALWAYS check `.aion/` for project context before starting work: changelog, specs, plans, reviews, bugs/, refs, prototypes, contracts, tests/e2e.

## Workflow (MANDATORY)
NEVER skip the workflow. For ANY task involving code changes:

新功能:        /aion:think → plan(主动衔接) → 实现 → /aion:review → /aion:commit
接手已有项目:  /aion:scan 起步,再进入上面的流程
Bug 修复:      /aion:fix {BUG-ID} → /aion:review → /aion:commit

Key rules:
- 3+ 文件改动,ALWAYS 先跑 /aion:think 并获得用户批准(Phase 9 gate)再实现。think 完成后**主动衔接** plan,不需要显式触发 /aion:plan。
- NEVER commit without /aion:review first — 提交门禁 hook 强制执行:review 批准 + Verification Gate(Iron Law 2: evidence before claims)通过才放行。

## Commands
| 命令 | 用途 |
|---|---|
| /aion:init | 初始化/升级 Aion 工作流层(幂等) |
| /aion:scan | 项目扫描与冷启动 |
| /aion:think | 讨论·碰撞·思考·目标对齐,产出 spec |
| /aion:plan | 修改已有实现计划 |
| /aion:fix | Bug 根因分析与修复 |
| /aion:qa | 浏览器 QA 测试 |
| /aion:review | 代码审查 + 规则自动沉淀 |
| /aion:commit | 安全提交(门禁) |
| /aion:save | 上下文保存 |
<!-- AION:END -->
