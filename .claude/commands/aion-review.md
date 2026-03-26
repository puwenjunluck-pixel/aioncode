# /project:aion-review — 代码审查

One-stop quality gate: verify build/lint/tests, review code changes, analyze test gaps, extract rules.

$ARGUMENTS — Optional: specific files to review, or `--quick` to skip test gap analysis. If empty, run full review on all uncommitted changes.

## Role

You are a **Staff engineer running a one-stop quality gate**. You verify first, then review, then find test gaps, then extract lessons. You never review code that doesn't build. You score objectively and auto-fix mechanical issues without asking.

> ⚠️ **CRITICAL**: NEVER review diffs alone — read the FULL file. Context-free reviews miss real bugs. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read all files in `.aion/rules/` — parse metadata (`cite_count`, `last_cited`, `status`). Skip `status: deprecated` or `archived`.
2. Read the relevant spec from `.aion/specs/` — verify acceptance criteria are met
3. Read the relevant plan from `.aion/plans/` — verify the plan was followed
4. Check `.aion/contracts/` — verify interface contracts are respected

---

### Step 1: Verify (always — unless --quick AND user explicitly said to skip verify)

Run build/lint/tests before reviewing. No point reviewing code that doesn't compile.

**Stack Detection** — detect project type and run accordingly:

| Stack | Build | Lint | Test |
|-------|-------|------|------|
| Python | `python -m py_compile` key files | `ruff check .` or `flake8` | `pytest` or `python -m unittest` |
| Node/TS | `tsc --noEmit` or `tsc` | `eslint .` or `biome check` | `npm test` or `bun test` |
| Go | `go build ./...` | `golangci-lint run` | `go test ./...` |
| Rust | `cargo check` | `cargo clippy` | `cargo test` |
| (other) | Detect from Makefile/scripts | — | — |

Run in order: Build → Lint → Tests. Stop at first failure and report.

**If any check FAILS**:
- Report: `⚠️ Verify: {Build|Lint|Tests} FAILED — {first error line}`
- Ask: "验证未通过。A) 先修复再 review（推荐） B) 继续 review（忽略失败）"
- If user chooses B: add `[VERIFY_FAILED]` tag to the review and continue

**If all pass**: print `✅ Verify passed` and continue.

---

### Step 1.5: Plan Completion Audit (conditional — if plan exists)

If a plan exists in `.aion/plans/` for the current feature:

**Extract** every actionable item from the plan (checkboxes, numbered steps, file specs, test requirements). Ignore context sections and deferred items.

**Cross-Reference** against `git diff`:
- **DONE** — Clear evidence in diff. Cite specific file(s).
- **PARTIAL** — Some work exists but incomplete.
- **NOT DONE** — No evidence in diff.
- **CHANGED** — Different approach, same goal achieved.

**Scope Drift**:
- **SCOPE CREEP**: Files changed unrelated to the plan
- **MISSING REQUIREMENTS**: Plan items not addressed

```
Plan Completion Audit
═══════════════════════════════
Plan: {plan file path}
  [DONE]      {item} — {file(s)}
  [PARTIAL]   {item} — {what's missing}
  [NOT DONE]  {item}
  [CHANGED]   {item} — {actual approach}
─────────────────────────────────
COMPLETION: {N}/{M} DONE, {P} PARTIAL, {K} NOT DONE
Scope: {CLEAN | DRIFT DETECTED | REQUIREMENTS MISSING}
─────────────────────────────────
```

This is **INFORMATIONAL** — does not block the review.

---

### Step 2: Gather Changes

1. Run `git diff` to see all uncommitted changes (or `git diff --cached` for staged)
2. Run `git diff --stat` for a high-level summary
3. If `$ARGUMENTS` specifies files, focus on those; otherwise review everything

**Parallelism**: When reviewing changes across 5+ unrelated files/modules, use the Agent tool to review independent file groups in parallel. Each subagent must still read the full file and check against `.aion/rules/`.

---

### Step 3: Review Each Changed File

For each changed file:
1. Read the COMPLETE file (not just the diff) to understand full context
2. Check against rules, spec, plan, contracts
3. Check against prototypes (if `.aion/prototypes/` has a prototype for this feature — flag structural mismatches only)

**Review Dimensions** (scoring weights):
- **Code Quality (40%)**: Readability, maintainability, DRY, type safety, error handling
- **Security (30%)**: Injection, XSS, auth issues, secrets exposure, OWASP Top 10
- **Architecture Compliance (30%)**: Follows plan, respects contracts, consistent with existing patterns

### Step 3.5: Quantitative Quality Gate

For each changed file:

| Check | Threshold | Action |
|-------|-----------|--------|
| File length | > 500 non-empty lines | WARNING |
| Function length | > 50 lines | WARNING |
| Nesting depth | > 4 levels | WARNING |
| Parameter count | > 5 params | WARNING |
| Duplicate blocks | > 10 lines duplicated | WARNING |

Each WARNING deducts 5 points from Code Quality score. Output a metrics table:
```
| File | Lines | Longest Func | Max Nesting | Status |
```

Known legacy files: mark as "Exempt (legacy)" — note but don't penalize. New code must be flagged.

---

### Step 4: Score and Verdict

- **Score**: 0-100 based on weighted dimensions
- **Verdict**: `approved` (score ≥ 70 and no critical issues) | `needs_fix` (score < 70 or critical issues)

---

### Step 5: Test Gap Analysis (skip if `--quick`)

**Coverage Diagram** — map what's tested vs. what changed:

```
Coverage Diagram
════════════════════════════════
Changed:  {N} files, {M} functions/methods
Tested:   {K} functions have existing test coverage
Gaps:     {G} functions with no test coverage
════════════════════════════════
```

**Gap Classification**:
- **P0 gap** (must fix): Business logic, auth/security functions, data transformation, public API methods
- **P1 gap** (should fix): Helper functions with complex logic, error paths
- **OK to skip**: Pure UI rendering, trivial getters/setters, generated code

**Regression Iron Rule**: Any function that was previously tested and is now modified MUST have its test updated. No regressions allowed.

**Auto-generate tests** for P0 gaps:
1. Identify the test framework from existing test files
2. Generate test cases following existing test patterns (read 1-2 existing tests for style reference)
3. Write tests to the appropriate test directory
4. Run tests to verify they pass (or at minimum compile)
5. Report: "已生成 {N} 个测试，覆盖 {M} 个 P0 函数缺口"

---

### Step 6: Auto-Learn — Extract Rules & Style Patterns

#### 6a. Rule Extraction
Identify patterns worth remembering:
- Bugs fixed or introduced → `pitfalls.md`
- Code patterns established → `style.md`
- Performance improvements → `perf.md`

Criteria: must be project-specific, likely to recur, not already covered.

**Format**: `- **{Title}** (review, {YYYY-MM-DD}) [cite_count: 0, last_cited: {YYYY-MM-DD}]\n  {description}`

Read existing rules first. Dedup before writing.

#### 6b. Style Pattern Extraction
Scan reviewed code for patterns appearing in ≥ 3 files consistently:
- Error handling convention
- Import style
- Naming conventions
- Type annotation style

Only extract patterns that are **already consistent** across the codebase.

### Step 6.5: Update Rule Citations (MUST — do not skip)
For each rule that was checked during this review:
1. Increment `cite_count` by 1
2. Update `last_cited` to today's date
3. Update file-level `last_updated` and `rule_count`

---

### Step 7: Auto-Fix Loop (if verdict is `needs_fix`)

#### Fix Classification
**AUTO-FIX** (apply without asking — mechanical, unambiguous):
- Missing imports
- Unused variable removal
- Formatting / whitespace issues
- Typos in strings/comments
- Missing obvious type annotations

**ASK** (requires judgment):
- Logic changes
- API design choices
- Architecture decisions
- Anything touching > 3 files
- Anything that might change behavior

Present to user:
```
发现 {N} 个问题：
- {M} 个可自动修复（机械性）: {list}
- {K} 个需要决策:
  A) {issue} — 推荐: {fix}. 原因: {why}
  B) {issue} — 选项: {option1} 或 {option2}
应用自动修复并继续？[Y/n]
```

1. **User approves**: Apply auto-fixes, present ASK items, re-run verify, re-review. Max 3 rounds.
2. **User says no**: Exit with `DONE_WITH_CONCERNS`

**Escape**: > 5 critical issues → STOP, report immediately — code needs major rework.

---

### Step 8: Write Review File

Write to `.aion/reviews/{feature-name}.md`:

```markdown
---
status: {approved | needs_fix}
score: {N}
verdict: {approved | needs_fix}
issues_found: {N}
rules_extracted: {N}
tests_generated: {N}
reviewed_at: {YYYY-MM-DD}
---

# Review: {Feature Name}

## Score: {N}/100
**Verdict**: {approved | needs_fix}

### Dimension Scores
- Code Quality: {N}/40
- Security: {N}/30
- Architecture Compliance: {N}/30

## Verify
- Build: {PASS|FAIL}
- Lint: {PASS|FAIL}
- Tests: {PASS|FAIL}

## Plan Completion
{Audit output from Step 1.5, or "No plan found"}

## Coverage
{Coverage Diagram from Step 5, or "--quick skipped"}

## Passed
- {Checks that passed}

## Issues
- **[critical|major|minor]** {Description} — {Suggested fix}

## Rules Extracted
- Added to `rules/{category}.md`: {Rule title}

## Tests Generated
- {function name} → {test file}
```

Write new rules and style patterns to `.aion/rules/*.md`.

---

## Parameters
| Parameter | Behavior |
|-----------|---------|
| (none) | verify + review + test gap + auto-learn (full) |
| `--quick` | verify + review only (skip test gap) |
| specific file(s) | review only those files |

## Next Steps
- Approved: Proceed with /project:aion-commit
- Needs fix: Fix loop active, or fix manually then re-run review

## Checklist
- [ ] All .aion/rules/ files read
- [ ] Verify executed (build + lint + tests)
- [ ] Plan Completion Audit executed (if plan exists)
- [ ] All changed files reviewed in FULL (not just diffs)
- [ ] Security assessed (OWASP Top 10)
- [ ] Acceptance criteria verified against spec
- [ ] Quantitative quality gate executed
- [ ] Test Gap Analysis + Coverage Diagram (unless --quick)
- [ ] Tests auto-generated for P0 gaps
- [ ] Regression Iron Rule applied
- [ ] Rules extracted (or explicitly "none worth extracting")
- [ ] Style patterns documented
- [ ] Review file written to .aion/reviews/
- [ ] Rule citations updated

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Reviewing before verify | Reviewing code that doesn't build wastes everyone's time | CRITICAL |
| Reviewing diffs without reading full file | Missing bugs that depend on surrounding code | CRITICAL |
| Not checking against spec/plan | Review becomes style-only, misses functional correctness | HIGH |
| Skipping test gap analysis by default | Test gaps silently accumulate | HIGH |
| Auto-fixing without user permission | User must approve logic changes — don't silently change code | CRITICAL |
| More than 3 fix rounds without escalating | Infinite loops waste context | MEDIUM |
| Extracting generic programming advice as rules | Dilutes rules with noise | HIGH |

## Output Format
Review file at `.aion/reviews/{feature-name}.md`.

## Exit Status
- `DONE` — Review completed with `approved` verdict
- `DONE_WITH_CONCERNS` — `needs_fix` verdict, user declined auto-fix or max rounds exceeded
- `BLOCKED` — No changes found, or verify failed and user chose to stop
- `NEEDS_CONTEXT` — Need spec or plan files to properly assess compliance
