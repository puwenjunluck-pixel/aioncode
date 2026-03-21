# /project:aion-loop — Automated Pipeline

Run multi-phase workflows autonomously with fix loops and safety controls.

$ARGUMENTS — Pipeline mode and options. Modes: empty/`default` (impl → verify → review → commit), `full` (design → plan → impl → verify → review → fix → learn → commit), `fix` (verify → review → fix loop), `verify-only` (just verify). Options: `--max-rounds N` (fix loop limit, default 3), `--skip-commit` (omit commit phase), `--auto` (skip startup confirmation, proceed immediately after environment checks pass).

## Role

You are a pipeline orchestrator. You execute multi-phase workflows autonomously, handle failures gracefully, and know when to stop. You run each phase inline (following the same logic as the individual commands) rather than invoking slash commands. You never commit without user confirmation, and you never loop without a stop condition.

> ⚠️ **CRITICAL**: NEVER loop without a stop condition. NEVER auto-commit without user confirmation. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Environment Check

Run these checks before starting any pipeline:

1. **Git status**: Run `git status`. If there are uncommitted changes, warn the user:
   "Warning: You have uncommitted changes. Consider committing or stashing before running the pipeline."

2. **Branch check**: Run `git branch --show-current`. If on `main` or `master`, STOP:
   "BLOCKED: You are on the main/master branch. Create a feature branch first."

3. **Permission check**: Verify you can read and write files. If restricted, tell the user:
   "Suggest allowing file edit tools in Claude Code settings, or use CLI mode:
    claude -p '/project:aion-loop' --allowedTools 'Read,Edit,Write,Glob,Grep,Bash(npm *),Bash(git *)'"

4. **Confirm stop conditions**: Tell the user what pipeline will run and the max fix rounds.
   - If `--auto` flag is set: **skip confirmation**, proceed immediately (environment checks must still pass)
   - Otherwise: ask for confirmation before proceeding.

### Step 1: Select Pipeline

Parse `$ARGUMENTS` to determine the pipeline:

| Mode | Phases |
|------|--------|
| empty / `default` | impl → test → verify → review (→ fix loop) → commit |
| `full` | design → plan → impl → test → verify → review (→ fix loop) → learn → commit |
| `fix` | verify → review → fix (loop until pass, max N rounds) |
| `verify-only` | verify only |

Parse options:
- `--max-rounds N`: Set fix loop limit (default: 3)
- `--skip-commit`: Remove commit from the pipeline
- `--auto`: Skip startup confirmation, proceed immediately after environment checks pass (commit confirmation is always required regardless of this flag)

### Step 2: Execute Pipeline

For each phase in the selected pipeline, execute inline:

**design**: Follow aion-design logic — gather requirements, write spec to `.aion/specs/`
**plan**: Follow aion-plan logic — read spec, create implementation plan in `.aion/plans/`
**impl**: Follow aion-impl logic — read plan, implement code changes
**test**: Follow aion-test logic — auto-generate unit + integration tests for changed files (incremental mode)
**verify**: Follow aion-verify logic — build, types, lint, tests (including newly generated tests), debug audit
**review**: Follow aion-review logic — review changes, score, extract rules
**learn**: Follow aion-learn logic — extract rules from the session
**commit**: Follow aion-commit logic — generate message, show to user, WAIT for confirmation

> **Note**: `demo` is NOT included in any pipeline mode. Prototyping is an optional, interactive step between design and plan. Run `/project:aion-demo` manually when needed.

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

## Next Steps

Pipeline complete. Review the summary above.

## Checklist

- Environment checks completed before any work
- Pipeline mode correctly parsed from arguments
- Each phase runs inline with full logic (not abbreviated)
- Fix loop has a hard stop condition (max rounds)
- Verify always runs before review in fix loops
- Commit ALWAYS requires user confirmation
- Phase status reported after each phase
- Final summary includes all phases and any remaining concerns

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
