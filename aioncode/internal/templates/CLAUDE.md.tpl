# AionCode — Project Intelligence

## Rules (MANDATORY)
NEVER write or edit any code file without first reading ALL rules in `.aion/rules/`. This is non-negotiable.

## Context
ALWAYS check `.aion/` for project context before starting work: changelog, specs, plans, contracts, refs, prototypes, checklists, team.yml, bugs/, sessions.jsonl.

## Commands
Run `/project:aion-help` for full command list. Key workflow commands:
scan | think | design | demo | plan | impl | test | verify | review | commit | save | bug | crosscheck | upgrade | loop

## Workflow (MANDATORY)
NEVER skip the workflow. For ANY task involving code changes, follow the appropriate flow:

New feature:  think → design → (demo) → impl → (test) → verify → review → commit
Existing code: scan → impl/design → verify → review → commit
Bug fix:       bug report → impl {BUG-ID} → verify → review → commit

Key rules:
- For tasks involving 3+ file changes, ALWAYS run `/project:aion-design` first and get user approval before implementing. Use `/project:aion-plan` only to revise an existing plan.
- NEVER commit without running `/project:aion-review` first. commit requires review approval.
- When a task can be broken into independent subtasks, use the Agent tool to parallelize work with subagents.
- review includes auto-learning via `/project:aion-learn`.
