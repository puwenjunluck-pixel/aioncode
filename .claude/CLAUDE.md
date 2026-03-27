<!-- AIONCODE:START -->
# AionCode — Project Intelligence

## Rules (MANDATORY)
NEVER write or edit any code file without first reading ALL rules in `.aion/rules/`. This is non-negotiable.

## Context
ALWAYS check `.aion/` for project context before starting work: changelog, specs, plans, contracts, refs, prototypes, checklists, team.yml, bugs/, sessions.jsonl.

## Commands
Run `/project:aion-help` for full command list. Key workflow commands:
scan | design | plan | fix | qa | loop | review | commit | save | help

## Workflow (MANDATORY)
NEVER skip the workflow. For ANY task involving code changes, follow the appropriate flow:

New feature:  design → plan → 实现 → review → commit
Existing code: scan → design → 实现 → review → commit
Bug fix:       /project:aion-fix {BUG-ID} → review → commit

Key rules:
- For tasks involving 3+ file changes, ALWAYS run `/project:aion-design` first and get user approval before implementing. Use `/project:aion-plan` only to revise an existing plan.
- NEVER commit without running `/project:aion-review` first. commit requires review approval.
- When a task can be broken into independent subtasks, use the Agent tool to parallelize work with subagents.

<!-- AIONCODE:END -->

## Project Notes
- 本项目是 AionCode 自身（dogfooding）— NEVER 同步 commands/ → .claude/commands/
- 公司：成都奕贝科技
- Dashboard dev 模式：`python3.11 -c "from aioncode.internal.dashboard.app import create_app; import uvicorn; uvicorn.run(create_app(dev=True), host='127.0.0.1', port=19200)"`
- E2E 测试定义：`.aion/tests/e2e/*.md`（Given/When/Then 格式，AI 多源自动生成）
- Playwright MCP 仅限 `aion-qa` 和 `aion-scan --url` 模式（见 pitfalls 规则）
- 产品设计文档：`.aion/specs/_product.md`（全局产品全景，design/plan/scan 自动维护）
- `--file` 参数：aion-design / aion-scan 支持导入 .docx/.pdf/.pptx 外部文档
- Bug 报告：`.aion/bugs/`（由 aion-qa 生成，aion-fix 按角色消费）
- `--auto` 参数：loop/fix/qa/review/commit 支持（commit 确认永不跳过）
