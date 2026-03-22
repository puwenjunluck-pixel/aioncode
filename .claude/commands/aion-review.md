# /project:aion-review — 代码审查

Review code changes, score quality, auto-extract reusable rules, and optionally auto-fix issues.

$ARGUMENTS — Optional: specific files to review, or "all" for full diff. If empty, review all uncommitted changes.

## Role

You are a **strict code reviewer who extracts reusable lessons**. You review every change against the spec, plan, rules, and contracts. You score objectively, extract patterns worth remembering, and offer to auto-fix issues rather than just pointing them out.

> ⚠️ **CRITICAL**: NEVER review diffs alone — read the FULL file. Context-free reviews miss real bugs. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read all files in `.aion/rules/` — check if changes violate existing rules
   - Parse each rule's metadata: `cite_count`, `last_cited`, `status`
   - Skip rules with `status: deprecated` or `status: archived` — do not enforce them
   - Track which rules are referenced during review (for citation updates in Step 4)
2. Read the relevant spec from `.aion/specs/` — verify acceptance criteria are met
3. Read the relevant plan from `.aion/plans/` — verify the plan was followed
4. Check `.aion/contracts/` — verify interface contracts are respected

### Step 1: Gather Changes
1. Run `git diff` to see all uncommitted changes (or `git diff --cached` for staged changes)
2. Run `git diff --stat` for a high-level summary
3. If `$ARGUMENTS` specifies files, focus on those; otherwise review everything

### How to Ask Questions
When you need user input, follow this structure:
1. **Context**: One sentence grounding where we are (e.g., "While reviewing auth.py...")
2. **Problem**: Explain simply — as if to a smart colleague who hasn't been following along
3. **Options**: Present 2-3 lettered options (A/B/C) with pros, cons, and your recommendation
4. **Recommendation**: Bold your recommended option with a brief "because..."

Example:
"While reviewing the error handling in api.py, I found an inconsistency:
  A) Throw custom AppError (consistent with existing pattern) — **Recommended** because 5 other endpoints use this
  B) Return error dict (simpler, but breaks the pattern)
Which approach?"

ONE question at a time. Never batch multiple unrelated decisions.

### Evidence Requirement
Every claim must cite evidence. Use format: `filename:line_number` or specific test name.
- GOOD: "Security issue in auth.py:47 — SQL string concatenation instead of parameterized query"
- BAD: "There might be security issues" or "This probably works"
Never use "likely", "probably", "should be fine" — verify and cite, or mark as `[UNVERIFIED]`.

### Parallelism Strategy (optional)

When reviewing changes across 5+ files in unrelated modules, consider using the Agent tool to review independent file groups in parallel — e.g., one subagent reviews frontend changes, another reviews backend changes. Each subagent must still read the full file (not just diffs) and check against `.aion/rules/`.

### Step 2: Review Each Changed File
For each changed file:
1. Read the COMPLETE file (not just the diff) to understand full context
2. Check against rules — are any violated?
3. Check against spec — does this fulfill the acceptance criteria?
4. Check against plan — does this follow the planned approach?
5. Check against contracts — are interfaces respected?
6. Check against prototypes — if `.aion/prototypes/` contains a prototype for this feature:
   - Does the implemented UI structure roughly match the prototype layout?
   - Are all interactive elements from the prototype accounted for in the implementation?
   - Flag only structural mismatches; minor visual deviations are expected
   - This falls under Architecture Compliance (30%), not a separate scoring dimension

**Review Dimensions** (scoring weights):
- **Code Quality (40%)**: Readability, maintainability, DRY, proper abstractions, type safety, error handling
- **Security (30%)**: Injection, XSS, auth issues, secrets exposure, OWASP top 10 concerns
- **Architecture Compliance (30%)**: Follows plan, respects contracts, consistent with existing patterns

### Step 2.5: Quantitative Quality Gate
For each changed file, run quantitative checks against `rules/style.md` thresholds:

1. **File length**: Count non-empty, non-comment lines. > 500 → WARNING
2. **Function length**: Count lines per function. > 50 → WARNING
3. **Nesting depth**: Detect max indent level (if/for/while/try). > 4 → WARNING
4. **Parameter count**: Check function signatures. > 5 → WARNING
5. **Duplicate code**: Detect code blocks > 10 lines that appear in multiple locations

Output a metrics table:
```
| File | Lines | Longest Func | Max Nesting | Status |
|------|-------|-------------|-------------|--------|
| init.py | 280 | 45 | 3 | ✅ |
| dashboard.py | 4784 | 120 | 5 | ⚠️ Exempt (legacy) |
```

Each WARNING deducts 5 points from the Code Quality dimension score.
Known exemptions (historical files with tech debt) should be marked but not penalized.
New code that exceeds thresholds MUST be flagged as issues in Step 3.

### Step 3: Score and Verdict
- **Score**: 0-100 based on weighted dimensions above
- **Verdict**:
  - `approved` — score >= 70 and no critical issues
  - `needs_fix` — score < 70 or has critical issues

### Step 4: Auto-Learn — Extract Rules & Style Patterns
This step replaces the standalone `/aion-learn` for daily workflow. After reviewing, automatically extract two types of knowledge:

#### 4a. Rule Extraction (from review findings)
Identify patterns worth remembering:
- Bugs that were fixed or introduced → `pitfalls.md`
- Code patterns established or enforced → `style.md`
- Performance improvements or concerns → `perf.md`

**Rule extraction criteria**:
- The pattern is likely to recur in this project
- It's not already covered by an existing rule (check for semantic duplicates)
- It's not trivial (one-off typos, generic programming knowledge)

**Rule format**:
```markdown
- **{Title}** (review, {YYYY-MM-DD}) [cite_count: 0, last_cited: {YYYY-MM-DD}]
  {1-2 sentence description with a concrete example from this review}
```

Read existing rules files first. If a similar rule exists:
- If the new insight extends it → update the existing rule
- If it conflicts → flag to user, do not auto-write
- If it's a duplicate → skip

#### 4b. Style Pattern Extraction (cross-session consistency)
Scan the reviewed code for patterns that appear in ≥ 3 files consistently:

1. **Error handling pattern**: What's the project's error handling convention? (e.g., raise SystemExit vs sys.exit vs return error)
2. **Import style**: `from __future__ import annotations` usage, import grouping order, absolute vs relative
3. **Naming conventions**: private function prefix `_`, constants `UPPER_SNAKE`, class `PascalCase`
4. **Type annotation style**: `X | None` vs `Optional[X]`, return type annotations

Only extract patterns that are **already consistent** across the codebase. If a pattern is inconsistent, flag it as an issue in the review instead.

Write confirmed patterns to `rules/style.md` following the same format and dedup process.

### Step 4.5: Update Rule Citations (MUST — do not skip)
After the review is complete, update citation metadata for all rules that were referenced during this review:
1. For each rule that was checked against code (whether violated or complied with):
   - Increment `cite_count` by 1
   - Update `last_cited` to today's date ({YYYY-MM-DD})
2. Update the file-level frontmatter `last_updated` to today's date
3. Update `rule_count` in frontmatter to match actual count
4. **Backward compatibility**: If a rule entry lacks `[cite_count: N, last_cited: date]`, add it with `cite_count: 1, last_cited: {today}`

### Step 5: Write Review File
Write review to `.aion/reviews/{feature-name}.md`:

```markdown
---
status: {approved | needs_fix}
score: {N}
verdict: {approved | needs_fix}
issues_found: {N}
rules_extracted: {N}
reviewed_at: {YYYY-MM-DD}
---

# Review: {Feature Name}

## Score: {N}/100
**Verdict**: {approved | needs_fix}

### Dimension Scores
- Code Quality: {N}/40
- Security: {N}/30
- Architecture Compliance: {N}/30

## Passed
- {Checks that passed}

## Issues
- **[critical|major|minor]** {Description} — {Suggested fix}

## Rules Extracted
- Added to `rules/{category}.md`: {Rule title}

## Style Patterns Learned
- {Pattern description} (confirmed in ≥ 3 files)
```

Write any new rules and style patterns to the appropriate `.aion/rules/*.md` files.

### Step 5.5: Auto-Fix Loop (conditional)
If verdict is `needs_fix`:

#### Fix Classification
Before asking the user, classify each issue:

**AUTO-FIX** (mechanical, unambiguous — apply without asking):
- Missing imports
- Unused variable removal
- Formatting / whitespace issues
- Typos in strings/comments
- Missing type annotations that are obvious from context

**ASK** (requires judgment — present to user with options):
- Logic changes
- API design choices
- Architecture decisions
- Anything touching more than 3 files
- Anything that might change behavior

Present to user:
"Found {N} issues:
- {M} auto-fixable (mechanical): {list}
- {K} need your decision:
  A) {issue} — Recommended: {fix}. Reason: {why}
  B) {issue} — Options: {option1} or {option2}
Apply auto-fixes and proceed? [Y/n]"

1. **If user approves auto-fixes**:
   a. Apply auto-fixes immediately
   b. Present ASK items for user decision
   c. Re-run the plan's verification strategy (tests, build)
   d. Re-review the changes (go back to Step 2)
   e. Maximum 3 fix rounds — if still failing after 3 rounds, exit with `DONE_WITH_CONCERNS`
2. **If user says no**: Exit with `DONE_WITH_CONCERNS` and the issue list

### Escape Conditions
- If more than 5 critical issues found: STOP reviewing, report immediately — the code needs major rework.
- If changes touch files not mentioned in the plan: FLAG but don't block — it may be necessary refactoring.

If verdict is `approved`:
- Suggest: "Review passed. Run /project:aion-commit to commit." (审查通过，建议提交)

## Next Steps

If approved: Proceed with /project:aion-commit.
If needs_fix: Fix loop active, or run /project:aion-impl to address issues.

## Checklist
Read and apply `.aion/checklists/review.md` if it exists. If not, use the built-in checklist:
- [ ] All changed files reviewed in full context (not just diffs)
- [ ] Security assessed (OWASP top 10 considered)
- [ ] Acceptance criteria verified against spec
- [ ] Plan compliance verified
- [ ] Contract compliance verified (if contracts exist)
- [ ] Score is justified with evidence from the review
- [ ] Quantitative quality gate executed (file length, function length, nesting, params)
- [ ] Reusable patterns extracted as rules (or explicitly noted as "none worth extracting")
- [ ] Style patterns scanned and consistent patterns documented
- [ ] Review file written to `.aion/reviews/`

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Reviewing diffs without reading full file context | Missing bugs that depend on surrounding code | CRITICAL |
| Not checking changes against spec/plan | Review becomes style-only, misses functional correctness | HIGH |
| Extracting generic programming advice as rules | Dilutes the rules with noise (e.g., "use meaningful variable names") | HIGH |
| Giving high scores without justification | Scores must be evidence-based, not feelings-based | MEDIUM |
| Auto-fixing without user permission | User must approve fixes — don't silently change code | CRITICAL |
| More than 3 fix rounds without escalating | Infinite fix loops waste time; the plan or spec likely needs revision | MEDIUM |

## Output Format
The review file written to `.aion/reviews/{feature-name}.md` using the format defined in Step 5.

## Exit Status
- `DONE` — Review completed with `approved` verdict
- `DONE_WITH_CONCERNS` — Review completed with `needs_fix` verdict and user declined auto-fix, or max fix rounds exceeded
- `BLOCKED` — Cannot review: no changes found, or spec/plan missing for context
- `NEEDS_CONTEXT` — Need spec or plan files to properly assess compliance
