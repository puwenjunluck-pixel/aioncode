# AionCode — Project Intelligence

## Rules (MANDATORY)
NEVER write or edit any code file without first reading ALL rules in `.aion/rules/`. This is non-negotiable.

**`.aion/rules/metacognition.md` 是元规则** — 元认知 / 反合理化 / Verification Gate / Iron Laws。
每次动作前生效,不是只在某个命令内。

## Context
ALWAYS check `.aion/` for project context before starting work: changelog, specs, plans, contracts, refs, prototypes, checklists, team.yml, bugs/, sessions.jsonl.

## Commands
Run `/project:aion-help` for full command list. Key workflow commands:
scan | think | plan | fix | qa | loop | review | commit | save | help

## Workflow (MANDATORY)
NEVER skip the workflow. For ANY task involving code changes, follow the appropriate flow:

New feature:  think → plan(主动建议) → 实现 → review → commit
Existing code: scan → think → plan(主动建议) → 实现 → review → commit
Bug fix:       /project:aion-fix {BUG-ID} → review → commit

Key rules:
- For tasks involving **3+ file changes**, ALWAYS run `/project:aion-think` first and get user approval (Phase 9 gate) before implementing. `aion-think` 完成后会**主动建议**进入 plan 阶段,**不需要用户显式触发** `/project:aion-plan`。
- `/project:aion-plan` 命令保留,仅用于**修改已有 plan**。主路径初次生成由 aion-think Phase 10 衔接。
- NEVER commit without running `/project:aion-review` first. commit requires review approval + Verification Gate 通过(Iron Law 2: evidence before claims)。
- When a task can be broken into independent subtasks, use the Agent tool to parallelize work with subagents.
- bug fix 强烈建议启用 `--deep`(4-phase 根因分析),除非 bug 极度明确。
