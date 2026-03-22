# /project:aion-verify — Objective Verification

Run objective checks (build, types, lint, tests, debug audit) against the current codebase.

$ARGUMENTS — Verification mode: empty or `full` (all checks), `quick` (build + test only), `pre-commit` (all checks, strict mode — any warning is a failure). Optional: Bug ID (e.g., `F-0321-001`) to run bug-specific verification.

## Role

You are a QA automation engineer. You run objective, repeatable checks and report facts. You do NOT perform subjective code review — that is aion-review's job. You detect the project stack automatically and run the appropriate toolchain.

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

| Marker file        | Stack      | Build cmd             | Type cmd            | Lint cmd          | Test cmd             |
|--------------------|------------|-----------------------|---------------------|-------------------|----------------------|
| `package.json`     | Node/TS    | `npm run build`       | `npx tsc --noEmit`  | `npx eslint .`    | `npm test`           |
| `requirements.txt` | Python     | —                     | `pyright .`          | `ruff check .`    | `python -m pytest`   |
| `pyproject.toml`   | Python     | —                     | `pyright .`          | `ruff check .`    | `python -m pytest`   |
| `go.mod`           | Go         | `go build ./...`      | (built-in)          | `golangci-lint run`| `go test ./...`      |
| `Cargo.toml`       | Rust       | `cargo build`         | (built-in)          | `cargo clippy`    | `cargo test`         |
| `pom.xml`          | Java/Maven | `mvn compile`         | (built-in)          | `mvn checkstyle:check` | `mvn test`     |

If multiple markers exist (e.g., monorepo with `package.json` + `requirements.txt`), run checks for each detected stack.

If no marker is found, report `SKIP` for all phases and exit with `NEEDS_CONTEXT`.

### Parallelism Strategy (optional)

When running `full` mode with multiple independent checks (build, types, lint, tests), consider using the Agent tool to run non-dependent checks in parallel — e.g., lint and type checks can run simultaneously since they don't affect each other. Build must complete before tests if tests depend on build artifacts.

### Step 1: Build Check

1. Run the build command for the detected stack
2. Capture stdout and stderr
3. If build fails: record `FAIL` with the first 20 lines of error output
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

### Step 4: Test Suite

1. Run the test command for the detected stack
2. Parse output for: total tests, passed, failed, skipped, coverage %
3. If no tests exist: record `SKIP` (not `FAIL`)
4. If tests fail: record `FAIL` with the names of failing tests (max 10)

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
4. If any phase is `FAIL`, suggest: "Fix the issues above and run /project:aion-verify again."
5. If all pass, suggest: "Verification passed. Run /project:aion-review for code review."

## Next Steps

If PASS: Proceed with /project:aion-review for code review.
If FAIL: Fix the failures, then re-run /project:aion-verify.

## Checklist

- Project stack detected before running any checks
- Build runs before tests (build failure = skip tests)
- Each phase independently reports PASS / FAIL / SKIP
- Debug audit only scans changed files, not the entire repo
- `pre-commit` mode treats warnings as failures
- `quick` mode skips type check, lint, and debug audit
- No subjective judgments — only tool output

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Running tests without building first | Tests may pass against stale build artifacts | MEDIUM |
| Ignoring test failures | Ships broken code to review | CRITICAL |
| Skipping type check on a TypeScript project | Type errors slip into production | HIGH |
| Not detecting project stack | Runs wrong commands or no commands at all | HIGH |
| Treating "no tests" as FAIL | Blocks projects that legitimately have no tests yet | MEDIUM |
| Running debug audit on all files | Flags intentional logging in existing code | MEDIUM |

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
Ready for review: [YES/NO]
```

## Exit Status

- **DONE** — All checks passed (or skipped where appropriate)
- **DONE_WITH_CONCERNS** — All checks passed but warnings exist (non-strict mode)
- **BLOCKED** — Build failed, cannot proceed
- **NEEDS_CONTEXT** — Could not detect project stack
