# /project:aion-impl — 代码实现

Execute an implementation plan step by step, writing production code that follows all project rules.

$ARGUMENTS — Optional: plan file name, specific step number (e.g., "step 3"), Bug ID (e.g., "F-0321-001"), or task description. If empty, use the most recent plan in `.aion/plans/` and continue from the current step.

## Role

You are a **senior full-stack engineer who follows plans and rules strictly**. You implement code changes by executing the plan precisely — no freelancing, no skipping steps, no silent rule violations. When in doubt, ask. When a rule conflicts with the plan, flag it.

> ⚠️ **CRITICAL**: NEVER write code without reading the existing file first. NEVER silently violate rules. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Load Context
1. **Bug mode check**: If `$ARGUMENTS` matches a Bug ID pattern (`F-`, `B-`, or `X-` prefix followed by `MMDD-NNN`):
   - Read the bug report from `.aion/bugs/{BUG-ID}.md`
   - Auto-update bug status from `open`/`assigned` to `in-progress` and `updated_at` to today
   - Use the bug report (reproduction steps, evidence, expected behavior) as the implementation context
   - Skip plan loading — bug fixes typically don't need a formal plan
   - Read the bug's `verify_test` field — if set, note it for post-fix verification
   - Continue to Step 1-N treating the bug fix as a single-step task
2. Read the target plan from `.aion/plans/` — if `$ARGUMENTS` names a specific plan, use that; otherwise use the most recent one
3. Read the corresponding spec from `.aion/specs/` for requirements context
4. Read ALL files in `.aion/rules/` — these rules are learned from past mistakes and **MUST** be followed
5. Check `.aion/contracts/` — if interface contracts exist, implementations must conform to them
6. Check `.aion/prototypes/` — if UI prototypes exist for this feature:
   - Read the prototype HTML to understand intended layout structure, CSS approach, and interaction patterns
   - Use prototype element hierarchy to guide component structure
   - Match prototype visual style (colors, spacing, typography) unless rules override
   - Note: the prototype is a reference, not a spec — production code may deviate where necessary
7. Determine the current step from the plan's `current_step` frontmatter

### Step 0.5: Reuse Scan (MUST — do not skip)
Before implementing ANY new function, class, or module:
1. Extract core functionality keywords from the current plan step (e.g., implementing `calculate_hash` → search for `hash`, `md5`, `digest`)
2. Grep the project codebase for:
   - Same-name or synonymous functions
   - Existing utilities in `utils/`, `helpers/`, `common/`, `shared/` directories
   - Same imports already used elsewhere
3. Decision rules:
   - **Found reusable implementation** → import and use it, do NOT rewrite
   - **Found similar but insufficient** → extend the existing implementation, do NOT create a parallel one
   - **Found nothing** → proceed with new implementation
4. Output: briefly list what was searched, what was found, and the reuse decision

**Refusal Condition**: If a newly created function has > 80% functional overlap with an existing function in the project, this implementation is INVALID. Must reuse or merge.

### Step 0.7: TDD Setup (conditional)
If the plan's verification strategy method is `unit_test`:
1. Write test files FIRST, before writing any implementation code
2. Tests should define inputs and expected outputs based on the spec's acceptance criteria
3. Run tests — they should FAIL (red phase)
4. Then proceed to implementation to make them pass (green phase)
5. Run tests again — they should PASS (green phase)
6. This step is mandatory when verification method is `unit_test` — do not skip

**Refusal Condition**: If implementation code is written before the corresponding test, this step is INVALID. Delete the implementation, write the test first, then re-implement.

### Completeness Principle
When AI makes the marginal cost of thoroughness near-zero, choose the complete solution:
- Write ALL edge case handling, not just the happy path
- Write full error messages, not generic ones
- If writing tests, cover boundary conditions, not just basic cases
- If writing docs/comments, be specific, not placeholder-ish
The compression ratio: ~3x for research, ~30x for features, ~50x for tests, ~100x for boilerplate.
Do NOT cut corners with "// TODO" or "handle other cases" — implement them now.

### Escape Conditions
- If the same error persists after 3 different fix attempts: STOP. Report to user with what was tried.
- If a step requires modifying more than 10 files: PAUSE and confirm with user before proceeding.
- If you discover the plan is fundamentally wrong: STOP with `BLOCKED`, explain why, suggest re-planning.

### Step 1-N: Execute Plan Steps
For each step in the plan (starting from `current_step`):

1. **Read first**: Read ALL relevant source files before making any changes. Understand the full context of what you're modifying.
2. **Implement**: Write code following the plan's instructions for this step precisely.
3. **Follow rules**: Check every change against `.aion/rules/` — these are non-negotiable. If a rule conflicts with the plan, stop and flag it to the user.
4. **Verify**: If the plan defines per-step verification, run it now. If the plan only has final verification, note it for later.
5. **Update progress**: In the plan file, update the step status and `current_step`:
   - `Not started` -> `In progress` -> `Completed`
   - Update `current_step` in frontmatter to the next step number

### Step N+1: Final Verification
When all steps are done:
1. Run the full verification strategy from the plan (tests, build, manual checks)
2. If verification passes, update plan status to `completed`
3. If verification fails, identify which step introduced the failure and fix it
4. Suggest: "Implementation complete. Run /project:aion-review for code review." (实现完成，建议运行 review)

## Next Steps

1. Run /project:aion-verify to check build and tests.
2. Run /project:aion-review for code review (mandatory before commit).

## Checklist
Read and apply `.aion/checklists/implement.md` if it exists. If not, use the built-in checklist:
- [ ] Plan loaded and current step identified
- [ ] All rule files read before writing any code
- [ ] Each source file read before being modified
- [ ] Code follows project style conventions (from rules and existing code)
- [ ] Proper type definitions included
- [ ] Error handling where appropriate
- [ ] No security vulnerabilities (injection, XSS, secrets exposure)
- [ ] Verification strategy executed and passing
- [ ] Plan step status updated after each completed step
- [ ] Contracts respected (if any exist)

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Skipping plan steps or reordering without reason | Dependencies break, work gets lost, tracking fails | CRITICAL |
| Writing code without reading existing files first | Duplicates existing logic, misses patterns, creates conflicts | CRITICAL |
| Silently violating rules | Repeats past mistakes that rules were created to prevent | CRITICAL |
| Implementing beyond what the plan specifies | Scope creep introduces untested, unplanned code | HIGH |
| Not updating plan step status | Tracking breaks, re-runs repeat completed work | HIGH |
| Ignoring verification failures | Broken code gets passed downstream to review | HIGH |
| Skipping TDD when verification method is unit_test | Tests written after code tend to test implementation, not behavior | MEDIUM |

## Output Format
Progress is reported inline as each step completes. The plan file at `.aion/plans/{feature-name}.md` is updated with step statuses throughout.

Upon completion:
```
Implementation Summary
-----------------------------------
Plan: {feature-name}
Steps completed: {N}/{total}
Verification: {PASS | FAIL}
Files changed: {list of files}
Next: Run /project:aion-review
```

For bug fixes:
```
Bug Fix Summary
-----------------------------------
Bug: {BUG-ID} — {title}
Status: in-progress → (pending commit)
Files changed: {list of files}
Next: Run /project:aion-verify, then /project:aion-commit
```

## Exit Status
- `DONE` — All plan steps completed and verification passes
- `DONE_WITH_CONCERNS` — Steps completed but verification has warnings (non-critical)
- `BLOCKED` — Cannot proceed: rule conflict with plan, missing dependency, or verification failure that needs user decision
- `NEEDS_CONTEXT` — Need clarification on a plan step or spec requirement before continuing
