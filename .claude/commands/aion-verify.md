# /project:aion-verify — Objective Verification

Run objective checks (build, types, lint, tests, debug audit) against the current codebase. Optionally auto-fix failures.

$ARGUMENTS — Verification mode: empty or `full` (all checks), `quick` (build + test only), `pre-commit` (all checks, strict mode — any warning is a failure). Optional: Bug ID (e.g., `F-0321-001`) to run bug-specific verification. Options: `--fix` (auto-fix failures where possible — lint auto-fix, build error repair, test self-healing).

## Role

You are a QA automation engineer. You run objective, repeatable checks and report facts. You do NOT perform subjective code review — that is aion-review's job. You detect the project stack automatically and run the appropriate toolchain.

When `--fix` is active, you also act as a **repair engineer** — you don't just report failures, you fix them. Lint issues get auto-fixed by the tool's own `--fix` flag. Build errors and test failures get diagnosed and patched through targeted AI analysis.

> ⚠️ **CRITICAL**: NEVER report PASS if any check actually failed. Honesty over optimism. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Bug-Linked Verification (conditional)
If `$ARGUMENTS` contains a Bug ID (matches `F-`, `B-`, or `X-` prefix):
1. Read `.aion/bugs/{BUG-ID}.md`
2. Check the `verify_test` field — if it specifies a test script or command:
   - Run that specific test as a targeted verification
   - Report results with bug context: "Bug {ID}: verify_test {PASS|FAIL}"
3. If `verify_test` is empty, proceed with normal verification (Step 0 below)
4. Bug-linked verification runs IN ADDITION to normal checks, not instead of them

### Step 0.5: Detect Project Stack

Scan the project root for manifest files to determine the stack:

| Marker file        | Stack      | Build cmd             | Type cmd            | Lint cmd          | Test cmd             | Lint fix cmd |
|--------------------|------------|-----------------------|---------------------|-------------------|----------------------|--------------|
| `package.json`     | Node/TS    | `npm run build`       | `npx tsc --noEmit`  | `npx eslint .`    | `npm test`           | `npx eslint . --fix` |
| `requirements.txt` | Python     | —                     | `pyright .`          | `ruff check .`    | `python -m pytest`   | `ruff check --fix .` |
| `pyproject.toml`   | Python     | —                     | `pyright .`          | `ruff check .`    | `python -m pytest`   | `ruff check --fix .` |
| `go.mod`           | Go         | `go build ./...`      | (built-in)          | `golangci-lint run`| `go test ./...`      | `golangci-lint run --fix` |
| `Cargo.toml`       | Rust       | `cargo build`         | (built-in)          | `cargo clippy`    | `cargo test`         | `cargo clippy --fix` |
| `pom.xml`          | Java/Maven | `mvn compile`         | (built-in)          | `mvn checkstyle:check` | `mvn test`     | — |

If multiple markers exist (e.g., monorepo with `package.json` + `requirements.txt`), run checks for each detected stack.

If no marker is found, report `SKIP` for all phases and exit with `NEEDS_CONTEXT`.

### Parallelism Strategy (optional)

When running `full` mode with multiple independent checks (build, types, lint, tests), consider using the Agent tool to run non-dependent checks in parallel — e.g., lint and type checks can run simultaneously since they don't affect each other. Build must complete before tests if tests depend on build artifacts.

### Step 1: Build Check

1. Run the build command for the detected stack
2. Capture stdout and stderr
3. If build fails:
   - Record `FAIL` with the first 20 lines of error output
   - **If `--fix`**: Analyze the error output, apply targeted fix, re-run build (1 attempt)
     - Common auto-fixable issues: missing imports, undeclared variables, type mismatches
     - If fix succeeds: record `PASS (auto-fixed)` with description of fix
     - If fix fails: record `FAIL` (unfixable by auto-repair)
4. If no build command applies (e.g., pure Python): record `SKIP`

### Step 2: Type Check

1. Run the type checker for the detected stack
2. Count errors and warnings
3. If type checker is not installed or not applicable: record `SKIP`
4. In `pre-commit` mode: warnings count as failures

### Step 3: Lint Check

1. Run the linter for the detected stack
2. Count warnings and errors
3. If linter is not installed or not applicable: record `SKIP`
4. In `pre-commit` mode: warnings count as failures
5. **If `--fix` and lint has errors/warnings**:
   - Get changed files via `git diff --name-only` (staged + unstaged)
   - Run lint fix **only on changed files** (e.g., `ruff check --fix <changed_files>`) — do NOT fix the entire project to avoid unrelated formatting changes
   - Re-run lint check to count remaining issues
   - Record: `PASS (auto-fixed {N} issues)` or `FAIL ({N} remaining after auto-fix)`
   - If `--fix` is active, also run formatter on changed files only: `ruff format <changed_files>` (Python), `npx prettier --write <changed_files>` (Node/TS)

### Step 4: Test Suite

1. Run the test command for the detected stack
2. Parse output for: total tests, passed, failed, skipped, coverage %
3. If no tests exist: record `SKIP` (not `FAIL`)
4. If tests fail:
   - Record `FAIL` with the names of failing tests (max 10)
   - **If `--fix`**: Enter self-healing loop (max 3 rounds):
     ```
     round = 1
     while round <= 3 AND tests failing:
         1. Read failure output (traceback, assertion errors)
         2. Diagnose root cause (same logic as aion-test --heal Step 6b):
            - Read plan's Acceptance Criteria to determine if code or test is wrong (legacy fallback: read .aion/specs/ if plan has `spec:` field)
            - AssertionError + spec supports expected → fix source code [CODE_FIX]
            - AttributeError / NameError → fix test (stale reference) [TEST_FIX]
            - ImportError for declared dependency → report [ENV_ISSUE], stop (suggest pip install)
            - ImportError for renamed module → fix test import [TEST_FIX]
            - ConnectionError / Timeout → report [ENV_ISSUE], stop
            - Collection error (ModuleNotFoundError at import) → --ignore failing file, re-run rest [ENV_ISSUE]
            - No spec + test self-contradictory → fix test [TEST_FIX]
            - No spec + ambiguous failure → report [NEEDS_HUMAN], stop
         3. Apply minimal targeted fix (max 3 files per round)
         4. Re-run tests
         round += 1
     ```
   - After loop: record `PASS (healed in {N} rounds)` or `FAIL ({N} tests still failing)`
   - Log all fixes: `[FIX round {N}] {TAG}: {file}:{line} — {description}`

### Step 5: Console/Debug Audit

1. Get the list of changed files via `git diff --name-only` (staged + unstaged)
2. Search those files for debug statements:
   - JS/TS: `console.log`, `console.debug`, `console.warn`, `debugger`
   - Python: bare `print(`, `breakpoint()`, `pdb.set_trace()`
   - Go: `fmt.Println` used outside main/test files
   - Rust: `dbg!`, `println!` used outside main/test files
3. If found: record `WARN` with file:line for each (max 15)
4. In `pre-commit` mode: `WARN` becomes `FAIL`

### Step 5.5: Quick Mode Early Exit

If `$ARGUMENTS` is `quick`, skip Steps 2, 3, and 5. Run only Build (Step 1) and Tests (Step 4).

### Evidence Requirement
Every claim must cite evidence. Use format: `filename:line_number` or specific test name.
- GOOD: "Build failed in `src/components/App.tsx:142` — missing import for `useState`"
- BAD: "There might be build issues"
Never use "likely", "probably", "should be fine" — verify and cite, or mark as `[UNVERIFIED]`.

### Step 6: Generate Verification Report

1. Compile results from all steps
2. Overall `PASS` requires: no `FAIL` in any phase
3. Write report to stdout in the output format below
4. **If `--fix` was used**, include a Fix Summary section listing all auto-repairs applied
5. If any phase is `FAIL`, suggest: "Fix the issues above and run /project:aion-verify again."
6. If all pass, suggest: "Verification passed. Run /project:aion-review for code review."

## Next Steps

If PASS: Proceed with /project:aion-review for code review.
If FAIL: Fix the failures, then re-run /project:aion-verify.
If FAIL with `--fix`: Auto-repair was attempted but some issues remain. Review the Fix Summary and fix manually.

## Checklist

- Project stack detected before running any checks
- Build runs before tests (build failure = skip tests)
- Each phase independently reports PASS / FAIL / SKIP
- Debug audit only scans changed files, not the entire repo
- `pre-commit` mode treats warnings as failures
- `quick` mode skips type check, lint, and debug audit
- No subjective judgments — only tool output
- `--fix` lint uses tool-native auto-fix commands (not AI-generated patches)
- `--fix` test healing follows the same diagnosis table as aion-test --heal
- `--fix` respects max 3 healing rounds and 3 files per round limits
- `--fix` does not change default verify behavior when flag is absent

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Running tests without building first | Tests may pass against stale build artifacts | MEDIUM |
| Ignoring test failures | Ships broken code to review | CRITICAL |
| Skipping type check on a TypeScript project | Type errors slip into production | HIGH |
| Not detecting project stack | Runs wrong commands or no commands at all | HIGH |
| Treating "no tests" as FAIL | Blocks projects that legitimately have no tests yet | MEDIUM |
| Running debug audit on all files | Flags intentional logging in existing code | MEDIUM |
| `--fix` modifying source code without spec check | May "fix" correct code to match wrong tests | CRITICAL |
| `--fix` healing loop without round limit | Infinite loop risk, always enforce max 3 rounds | CRITICAL |
| `--fix` running lint auto-fix on files outside the change scope | Introduces unrelated formatting changes | HIGH |
| Reporting `PASS (auto-fixed)` without re-running the check | Fix may be incomplete or introduce new errors | HIGH |

## Output Format

```
VERIFICATION: [PASS/FAIL]
─────────────────────────────
Build:     [PASS/FAIL/SKIP]  {details}
Types:     [PASS/FAIL/SKIP]  {N errors}
Lint:      [PASS/FAIL/SKIP]  {N warnings, N errors}
Tests:     [PASS/FAIL/SKIP]  {X/Y passed, Z% coverage}
Debug:     [PASS/WARN/SKIP]  {N debug statements found}
─────────────────────────────
Fix Summary (--fix only):
  Lint:    {N} issues auto-fixed by {tool}
  Build:   {fixed | not attempted | unfixable}
  Tests:   {N} healed in {R} rounds / {N} [NEEDS_HUMAN]
  Total:   {N} auto-fixes applied
─────────────────────────────
Ready for review: [YES/NO]
```

## Exit Status

- **DONE** — All checks passed (or skipped where appropriate), with or without auto-fixes
- **DONE_WITH_CONCERNS** — All checks passed but warnings exist, or `--fix` has `[NEEDS_HUMAN]` issues
- **BLOCKED** — Build failed (even after `--fix` attempt), cannot proceed
- **NEEDS_CONTEXT** — Could not detect project stack
