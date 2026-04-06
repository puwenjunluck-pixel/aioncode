# AionCode — Project Intelligence

## Rules (MANDATORY)
NEVER write or edit any code file without first reading ALL rules in `.aion/rules/`. This is non-negotiable.

## Context
ALWAYS check `.aion/` for project context before starting work: changelog, specs, plans, contracts, refs, prototypes, checklists, team.yml, bugs/, sessions.jsonl.

## Commands
Run `/aion-help` for full command list. Key workflow commands:
scan | design | plan | review | qa | fix | audit | commit | loop | save | help

## Workflow (MANDATORY)
NEVER skip the workflow. For ANY task involving code changes, follow the appropriate flow:

New feature:  design → plan（自动执行）→ review → commit
Existing code: scan → design → plan → review → commit
Bug fix:       /aion-fix {BUG-ID} → review → commit

Key rules:
- For tasks involving 3+ file changes, ALWAYS run `/aion-design` first and get user approval before implementing. Use `/aion-plan` only to revise an existing plan.
- NEVER commit without running `/aion-review` first. commit requires review approval.
- When a task can be broken into independent subtasks, use parallel agents.
