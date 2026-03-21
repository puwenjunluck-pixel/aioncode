<!-- AIONCODE:START -->
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
<!-- AIONCODE:END -->

<!-- AIONCODE:LEARNED -->
## Learned Project Context
<!-- Items below are auto-extracted by /aion-save. Edit freely. -->
- 本项目是 AionCode 自身（dogfooding），源码在 commands/ 和 templates/，安装副本在 .claude/commands/ (saved 2026-03-21)
- dashboard.py 是零外部依赖的单文件 Web UI（纯 Python stdlib），禁止引入第三方库 (saved 2026-03-21)
- 命令文件是纯 Markdown，不包含可执行代码，由 Claude Code 解释执行 (saved 2026-03-21)
- install.sh 使用 CLAUDE.md markers 合并策略，永不覆盖用户内容 (saved 2026-03-21)
- 用户偏好中文沟通，回答要简洁直接，设计讨论时喜欢先分析再实现 (saved 2026-03-21)
<!-- AIONCODE:START -->
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
<!-- AIONCODE:END -->

<!-- AIONCODE:LEARNED -->
## Learned Project Context
<!-- Items below are auto-extracted by /aion-save. Edit freely. -->
- 本项目是 AionCode 自身（dogfooding），源码在 commands/ 和 templates/，安装副本在 .claude/commands/ (saved 2026-03-21)
- dashboard.py 是零外部依赖的单文件 Web UI（纯 Python stdlib），禁止引入第三方库 (saved 2026-03-21)
- 命令文件是纯 Markdown，不包含可执行代码，由 Claude Code 解释执行 (saved 2026-03-21)
- install.sh 使用 CLAUDE.md markers 合并策略，永不覆盖用户内容 (saved 2026-03-21)
- 用户偏好中文沟通，回答要简洁直接，设计讨论时喜欢先分析再实现 (saved 2026-03-21)
<!-- AIONCODE:START -->
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
<!-- AIONCODE:END -->

<!-- AIONCODE:LEARNED -->
## Learned Project Context
<!-- Items below are auto-extracted by /aion-save. Edit freely. -->
- 本项目是 AionCode 自身（dogfooding），源码在 commands/ 和 templates/，安装副本在 .claude/commands/ (saved 2026-03-21)
- dashboard.py 是零外部依赖的单文件 Web UI（纯 Python stdlib），禁止引入第三方库 (saved 2026-03-21)
- 命令文件是纯 Markdown，不包含可执行代码，由 Claude Code 解释执行 (saved 2026-03-21)
- install.sh 使用 CLAUDE.md markers 合并策略，永不覆盖用户内容 (saved 2026-03-21)
- 用户偏好中文沟通，回答要简洁直接，设计讨论时喜欢先分析再实现 (saved 2026-03-21)
- 当前版本 v0.3，命令数量 18 个，Write Protocol 已启用 (saved 2026-03-21)
- .aion/bin/ 是工具目录（dashboard.py, uninstall.sh），安装/升级时无条件覆盖 (saved 2026-03-21)
- Write Protocol 四类文件：Accumulative / Versioned / Regenerable / Unique-by-ID (saved 2026-03-21)
- templates/ → .aion/ 单向数据流，禁止反向同步（dogfooding 陷阱）(saved 2026-03-21)
