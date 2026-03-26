<!-- AIONCODE:START -->
# AionCode — Project Intelligence

## Rules (MANDATORY)
NEVER write or edit any code file without first reading ALL rules in `.aion/rules/`. This is non-negotiable.

## Context
ALWAYS check `.aion/` for project context before starting work: changelog, specs, plans, contracts, refs, prototypes, checklists, team.yml, bugs/, sessions.jsonl.

## Implementation Rules (MANDATORY)
- **Reuse Scan**: 写任何新函数/类/模块前，先搜索现有代码。> 80% 重叠则必须复用。
- **Escape**: 同一错误 3 次修不好 → 停止并报告。改动 > 10 文件 → 确认后再继续。
- **Read First**: 改文件前必须先读完整文件。
- **Rules First**: 写代码前必须先读 .aion/rules/。

## Commands
Run `/project:aion-help` for full command list. Core commands:
scan | design | plan | review | fix | qa | commit | save

## Workflow (MANDATORY)
NEVER skip the workflow. For ANY task involving code changes, follow the appropriate flow:

New feature:   design → plan → [用户说 OK → 直接执行] → review → commit
Existing code: scan → design/plan → review → commit
Bug fix:       qa --report-only → fix → review → commit
Quick change:  [直接改] → commit -y  (Tier 1 自动放行)

Key rules:
- For complex tasks (introducing new modules/services, changing API interfaces, touching security-critical code, or large-scope refactors), ALWAYS run `/project:aion-design` first and get user approval before implementing.
- After `/project:aion-plan` and user confirms OK, proceed directly to implementation — no separate impl command needed.
- Commit uses **smart tier classification** (see aion-commit): Tier 1 (fast-path) skips review for trivial changes, Tier 2 (quick review) does inline mini-review, Tier 3 (full review) requires `/project:aion-review`.
- When a task can be broken into independent subtasks, use the Agent tool to parallelize work with subagents.
- review includes auto-learning and test gap analysis in one pass.

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
