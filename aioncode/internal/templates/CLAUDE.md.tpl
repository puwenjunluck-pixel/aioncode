# AionCode — Project Intelligence

## Rules (MANDATORY)
Before making ANY code changes, read and strictly follow all rules in .aion/rules/:
- .aion/rules/pitfalls.md — Known pitfalls and gotchas
- .aion/rules/style.md — Project code style conventions
- .aion/rules/perf.md — Performance guidelines

## Checklists
Apply relevant checklists from .aion/checklists/ during each workflow phase.

## Session History
Check `.aion/sessions.jsonl` for recent session digests (last 3 entries).
Each entry shows: tools used, files changed, duration, last active file.
Use this to understand what was done previously and continue where left off.

## Team & Bugs
- .aion/team.yml — Team members, roles, AI model configs, risk keywords
- .aion/bugs/ — Bug reports (filed by testers or crosscheck)

## Project Context
Check these files for project context when starting a new task:
- .aion/changelog.md — Work history
- .aion/refs/ — External reference docs (client requirements, API specs)
- .aion/prototypes/ — UI design prototypes (HTML/JS demos)
- .aion/specs/ — Structured requirement specs
- .aion/plans/ — Implementation plans
- .aion/contracts/ — Interface contracts (backend↔frontend)

## Available Commands
/project:aion-scan    — Scan existing project, bootstrap intelligence + checklists
/project:aion-think   — Challenge assumptions before starting
/project:aion-design  — Turn ideas into structured specs
/project:aion-demo    — Generate interactive HTML prototypes (optional)
/project:aion-plan    — Create implementation plans
/project:aion-impl    — Execute plans with rules enforcement
/project:aion-test    — Generate tests, analyze coverage, create perf scripts
/project:aion-verify  — Run build, tests, lint, type checks
/project:aion-review  — Code review with auto-learning + fix loop
/project:aion-learn   — Extract rules from recent work
/project:aion-save    — Save current context to .aion/ docs
/project:aion-commit  — Safe git commit with changelog
/project:aion-status  — Show project intelligence status
/project:aion-bug     — Bug management (report/list/assign/close/reopen/stats)
/project:aion-crosscheck — Cross-model verification (use other AI to find issues)
/project:aion-upgrade — Check and upgrade AionCode to latest version
/project:aion-loop    — Automated pipeline execution
/project:aion-help    — Show commands, workflows, and usage guide

New project: think → design → (demo) → plan → impl → (test) → verify → review → learn → commit
Existing project: scan → (choose intent) → impl/design → verify → review → commit
Bug workflow: tester: bug report → engineer: impl {BUG-ID} → verify → review → commit
Cross-check: crosscheck --model gemini → auto-generates bug reports
