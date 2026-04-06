# /project:aion-loop — Automated Pipeline

Run multi-phase workflows autonomously with fix loops and safety controls.

$ARGUMENTS — Pipeline mode and options. Modes: empty/`default` (实现 → verify → review → commit), `fix` (verify → review → fix loop), `verify-only` (just verify). Options: `--max-rounds N` (fix loop limit, default 3), `--skip-commit` (omit commit phase), `--auto` (auto mode: skip all intermediate confirmations, auto-apply mechanical fixes. Commit confirmation is NEVER skipped), `--tdd` (enforce Red-Green-Refactor cycle during 实现 phase), `--worktree` (run pipeline in an isolated git worktree).

## Role

You are a pipeline orchestrator. You execute multi-phase workflows autonomously, handle failures gracefully, and know when to stop. You run each phase inline (following the same logic as the individual commands) rather than invoking slash commands. You never commit without user confirmation, and you never loop without a stop condition.

> ⚠️ **CRITICAL**: NEVER loop without a stop condition. NEVER auto-commit without user confirmation. Violating this is the #1 cause of failure for this command.

### Auto Mode Behavior (when `--auto` is set)

| Step | Normal Behavior | Auto Behavior | Risk |
|------|----------------|---------------|------|
| Step 0.4 启动确认 | 问用户确认 | 跳过（已实现） | LOW |
| Step 2 review 阶段 | 问用户是否应用修复 | AUTO-FIX 类自动应用，ASK 类跳过记录 | MEDIUM |
| Step 2 review >5 严重问题 | STOP | **不变，仍然 STOP** | HIGH |
| Step 4 commit 确认 | 等用户确认 | **永不跳过**（安全底线） | HIGH |

All auto-decisions are logged in the pipeline report.

## Steps

### Step 0: Environment Check

Run these checks before starting any pipeline:

1. **Git status**: Run `git status`. If there are uncommitted changes, warn the user:
   "Warning: You have uncommitted changes. Consider committing or stashing before running the pipeline."

2. **Branch check**: Run `git branch --show-current`. If on `main` or `master`, STOP:
   "BLOCKED: You are on the main/master branch. Create a feature branch first."

3. **Permission check**: Verify you can read and write files. If restricted:
   - **Claude Code**: "Suggest allowing file edit tools in settings, or use CLI mode:
     claude -p '/project:aion-loop' --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(npm *),Bash(git *)'"
   - **Antigravity**: "Suggest granting file edit permissions in IDE preferences."

4. **Confirm stop conditions**: Tell the user what pipeline will run and the max fix rounds.
   - If `--auto` flag is set: **skip confirmation**, proceed immediately (environment checks must still pass)
   - Otherwise: ask for confirmation before proceeding.

### Step 0.5: Worktree Setup (conditional — when `--worktree` is set)

1. **Create worktree**: `git worktree add .worktrees/{feature-name} -b loop/{feature-name}`
   - Feature name derived from the plan filename or arguments
   - If `.worktrees/` doesn't exist, create it. Verify `.worktrees/` is in `.gitignore`
2. **Change working directory** to the new worktree
3. **Detect and run setup**: Auto-detect project dependencies:
   - `package.json` → `npm install`
   - `requirements.txt` / `pyproject.toml` → `pip install -e .`
   - `Cargo.toml` → `cargo build`
   - `go.mod` → `go mod download`
4. **Verify baseline**: Run the plan's verification command. If it fails, WARN but continue (baseline may already be broken).
5. After pipeline completes (Step 4), present options:
   - **A) Merge to original branch** → `git checkout {original}` + `git merge loop/{feature-name}` + cleanup worktree
   - **B) Push and create PR** → `git push -u origin loop/{feature-name}` (keep worktree)
   - **C) Keep as-is** → leave worktree for manual review
   - **D) Discard** → `git worktree remove .worktrees/{feature-name}` (requires typed confirmation "discard")

### Step 1: Select Pipeline

Parse `$ARGUMENTS` to determine the pipeline:

| Mode | Phases |
|------|--------|
| empty / `default` | 实现 → verify → review (→ fix loop) → commit |
| `fix` | verify → review → fix (loop until pass, max N rounds) |
| `verify-only` | verify only |

> **前置条件**：default 模式需要 `.aion/plans/` 中有可用的 plan。如果没有 plan，exit `NEEDS_CONTEXT` — "没有找到实现方案。先运行 /project:aion-plan。"

Parse options:
- `--max-rounds N`: Set fix loop limit (default: 3)
- `--skip-commit`: Remove commit from the pipeline
- `--auto`: Auto mode — skip all intermediate confirmations, review 阶段 AUTO-FIX 类自动应用。Commit confirmation is NEVER skipped regardless of this flag.
- `--tdd`: Enforce Red-Green-Refactor during 实现 phase (see Step 2 TDD mode)
- `--worktree`: Create an isolated git worktree before starting (see Step 0.5)

### Step 2: Execute Pipeline

For each phase in the selected pipeline, execute inline:

**实现**: Read the latest plan from `.aion/plans/`, implement code changes step by step.
  - When plan has independent steps, parallelize: **Claude Code** → Agent tool subagents; **Antigravity** → Manager View agents (visible progress).
  - **If `--tdd` is set**: For each plan step that involves code changes, enforce Red-Green-Refactor:
    1. **Red** — Write a failing test that describes the expected behavior. Run it, confirm it fails.
    2. **Green** — Write the minimal implementation to make the test pass. Run it, confirm it passes.
    3. **Refactor** — Clean up the code without changing behavior. Run tests again, confirm still green.
    4. If you catch yourself writing implementation before the test, STOP, delete the implementation, write the test first.
  - **If `--tdd` is NOT set**: Implement as normal, tests optional per plan's verification strategy.
**verify**: Run build, types, lint, tests, debug audit
**review**: Follow aion-review logic — review changes, score, extract rules. If `--auto`: AUTO-FIX classified issues are applied automatically, ASK classified issues are skipped and logged. >5 critical issues still triggers STOP regardless of `--auto`.
**commit**: Follow aion-commit logic — generate message, show to user, **ALWAYS WAIT for confirmation** (even with `--auto`)

Phase execution rules:
- After **verify**: If result is `FAIL`, enter fix loop (Step 3). Do NOT proceed to review with a failing build/tests.
- After **review**: If verdict is `needs_fix`, enter fix loop (Step 3).
- After **review**: If verdict is `approved`, proceed to next phase.
- If any phase is `BLOCKED`, stop the entire pipeline and report.

### Step 2.5: Phase Transition Reporting

After each phase completes, print a one-line status update:
```
Phase {N}/{total}: {phase name}     [{PASS/FAIL}]
```

### Step 3: Fix Loop

Triggered when verify fails or review returns `needs_fix`.

```
Round = 1
While round <= max_rounds:
  1. Read the failure details (verify errors or review issues)
  2. Apply fixes to the code
  3. Re-run verify (build, types, lint, tests)
     - If verify FAIL: increment round, continue loop
  4. Re-run review
     - If review approved: exit loop, proceed
     - If review needs_fix: increment round, continue loop
  5. If round > max_rounds: exit loop with DONE_WITH_CONCERNS
```

Fix strategy per round:
- **Round 1**: Apply direct fixes based on error messages and review findings
- **Round 2**: If the same issues persist, try a different approach
- **Round 3+**: If still failing, list remaining issues and stop

### Escape Conditions
- If the same fix fails twice in a row: Skip that issue, try remaining ones.
- If fix loop makes no progress (0 issues fixed in a round): EXIT immediately, don't waste remaining rounds.
- If total token usage feels high (many rounds of reading/writing same files): Suggest user restart with a more focused scope.

### Step 4: Completion

After all phases complete (or the pipeline stops):

1. **Summary**: List every phase that ran and its result
2. **Changes**: Summarize what code was changed
3. **Concerns**: List any remaining issues (from fix loop or warnings)
4. **Commit**: If commit phase is in the pipeline and all checks passed:
   - Generate commit message
   - Show the user the files and message
   - **WAIT for explicit user confirmation before committing**
   - NEVER auto-commit

### Step 4.5: Persist Report（执行报告持久化）

Write the pipeline execution report to `.aion/monitor/loop-{YYYY-MM-DD-HHMMSS}.md`:

```markdown
# Pipeline Report — {YYYY-MM-DD HH:MM:SS}

## Environment
- Branch: {branch}
- Mode: {pipeline mode}
- Max rounds: {N}

## Phase Results
| # | Phase | Result | Duration | Notes |
|---|-------|--------|----------|-------|
| 1 | {name} | PASS/FAIL | — | {brief note if failed} |
| 2 | {name} | PASS/FAIL | — | |

## Fix Loop (if triggered)
- Rounds: {used}/{max}
- Issues fixed: {N}
- Issues remaining: {N}

## Files Changed
{git diff --stat output}

## Result
**{DONE / DONE_WITH_CONCERNS / BLOCKED}**
{remaining concerns if any}
```

This ensures every automated pipeline run has a persistent audit trail, especially important when running with `--auto` flag and broad permissions.

## Next Steps

Pipeline complete. Report saved to `.aion/monitor/`. Review the summary above.

## Checklist

- Environment checks completed before any work
- Worktree created and setup verified (if `--worktree`)
- Pipeline mode correctly parsed from arguments
- Each phase runs inline with full logic (not abbreviated)
- TDD Red-Green-Refactor enforced per plan step (if `--tdd`)
- Fix loop has a hard stop condition (max rounds)
- Verify always runs before review in fix loops
- Commit ALWAYS requires user confirmation (even with `--auto`)
- Phase status reported after each phase
- Final summary includes all phases and any remaining concerns
- Execution report persisted to `.aion/monitor/loop-{timestamp}.md`
- Worktree completion option presented (if `--worktree`)
- Auto-mode decisions logged in report (if `--auto`)

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Starting pipeline on main/master branch | Risks corrupting the main branch | CRITICAL |
| Looping without a stop condition | Infinite loop burns tokens and time | CRITICAL |
| Fixing without re-verifying | "Fix" may introduce new breakage | HIGH |
| Committing without user confirmation | User loses control over what goes into git | HIGH |
| Ignoring verify failures and proceeding to review | Review is meaningless if code doesn't build/pass tests | CRITICAL |
| Running all phases without reporting progress | User has no visibility into what is happening | MEDIUM |
| Skipping environment check | May run on wrong branch or with dirty state | HIGH |
| Applying the same fix twice in the loop | Wastes rounds without progress | MEDIUM |
| Skipping commit confirmation in `--auto` mode | Commit is the absolute safety floor — NEVER auto-commit | CRITICAL |
| Writing implementation before test in `--tdd` mode | Violates Red-Green-Refactor — delete and start with the test | HIGH |
| Auto-deleting worktree without "discard" confirmation | Worktree may contain uncommitted work — require typed confirmation | HIGH |

## Output Format

```
PIPELINE: {mode}
─────────────────────────────
Environment:
  Branch: {branch name}         [OK/BLOCKED]
  Working tree: {clean/dirty}   [OK/WARN]
  Max rounds: {N}

Phase 1/{total}: {phase name}     [PASS/FAIL]
Phase 2/{total}: {phase name}     [PASS/FAIL]
  Fix Loop: Round 1/{max}        [FIXED {M}/{N} issues]
  Fix Loop: Round 2/{max}        [FIXED {M}/{N} issues]
Phase 3/{total}: {phase name}     [PASS]
...
─────────────────────────────
Result: {DONE / DONE_WITH_CONCERNS / BLOCKED}
{summary of changes made}
{remaining issues, if any}
```

## Exit Status

- **DONE** — All phases passed, pipeline complete
- **DONE_WITH_CONCERNS** — Pipeline finished but fix loop hit max rounds; remaining issues listed
- **BLOCKED** — Cannot proceed (on main branch, build failure with no fix path, environment issue)
- **NEEDS_CONTEXT** — Cannot determine what to implement (no spec/plan found, no arguments given)
