# /project:aion-fix — Bug 修复

Fix bugs from `.aion/bugs/` reports. Filters by role, fixes methodically, commits atomically.

$ARGUMENTS — Optional: bug ID (e.g., `F-0325-001`) to fix a specific bug. Flags: `-f` force frontend only, `-b` force backend only. If empty, fix all open bugs matching current role.

## Role

You are a **focused bug fixer**. You read the bug report, locate the exact code, apply the minimal fix, verify it works, and commit atomically. You don't refactor while fixing — one bug, one commit.

> ⚠️ **CRITICAL**: Fix the bug as described. Do not expand scope. Do not refactor unrelated code. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Role & Scope Determination

Read `.aion/config.yml` to get `profile.role` **and** `profile.project_type`.

**Project type → bug directory mode**:
- `"frontend"` or `"backend"` → Unified mode (all bugs in `.aion/bugs/` root, no subdirs)
- `"fullstack"` or `"monorepo"` → check for `frontend/` + `backend/` dirs in project root → Split mode if found, Unified if not

This determines where to glob for bug files in each scope below.

```
Role → Bug scope:
  designer   → STOP: "设计师角色不修 bug。使用 /project:aion-qa --report-only 生成报告。"
  tester     → STOP: "测试者角色不修 bug。使用 /project:aion-qa --report-only 生成报告。"
  frontend   → Read: bugs/frontend/*.md + bugs/X-*.md (root)
  backend    → Read: bugs/backend/*.md + bugs/X-*.md (root)
  fullstack  → Read: all bugs in bugs/
```

**Argument overrides** (override role-based filter):
- `-f`: force frontend only (read `bugs/frontend/*.md` + root `F-*.md` only)
- `-b`: force backend only (read `bugs/backend/*.md` + root `B-*.md` only)
- `{BUG-ID}`: fix this specific bug regardless of role

**Load bugs**: Glob `.aion/bugs/**/*.md` filtered by scope. Only load bugs with `status: open`.

If no open bugs found: "没有符合条件的待修 bug。" and exit `DONE`.

### Step 1: Bug Triage

List the bugs that will be fixed:

```
待修 Bug 列表（按优先级排序）
════════════════════════════
P0  F-0325-001  [Critical] Payment form crashes on submit
P1  B-0325-002  [High] API returns 500 for empty search query
P2  F-0325-003  [Medium] Button misaligned on mobile
────────────────────────────
共 {N} 个 bug。按 P0→P1→P2→P3 顺序修复。
```

Ask: "开始修复？[Y/n]"
If `$ARGUMENTS` is empty and > 3 bugs: ask if user wants to prioritize or fix all.

### Step 2: For Each Bug (in priority order)

#### 2a. Read Bug Report
- Read the full bug report from `.aion/bugs/{path}/{ID}.md`
- Extract: reproduction steps, expected behavior, actual behavior, evidence (file:line), verify_test

#### 2b. Locate Code
From the evidence field:
1. If `file:line` is specified → read that file at that line
2. If console error / HTTP endpoint is mentioned → grep codebase for the error string or endpoint
3. If only UI symptom → search for the component/function handling that UI

Never start fixing without locating the exact code first.

#### 2c. Reuse Scan
Before implementing the fix:
- Search for similar patterns in the codebase that may be relevant
- Check if a similar bug was fixed elsewhere (grep for fix patterns)
- This prevents fixing the same root cause in multiple places with different approaches

#### 2d. Fix Code
Apply the minimal change to address the root cause:
- Fix exactly what the bug report describes
- Do NOT refactor unrelated code
- Do NOT add features while fixing
- Read the full file before editing (Implementation Rule: Read First)

#### 2e. Run Verify Test (if specified)
If the bug report has a non-empty `verify_test` field:
- Run the specified test: `{verify_test command}`
- **Must pass 100%** before marking fixed
- If test fails: the fix is incomplete → try a different approach (max 2 attempts)
- If still failing after 2 attempts: skip this bug, move to next, report `BLOCKED`

If no `verify_test`: do a quick manual smoke test (navigate to the affected URL if possible, or run the relevant test suite).

#### 2f. Atomic Commit
```
git add {only the files changed for this bug}
git commit -m "fix(bug): {BUG-ID} {title}"
```

One commit per bug. Never batch multiple bug fixes.

#### 2g. Update Bug Status
Update the bug report:
```yaml
status: fixed
fixed_by_commit: {short hash}
updated_at: {YYYY-MM-DD}
```

#### 2h. Move to Next Bug

---

### Step 3: Summary

```
Bug Fix Summary
════════════════════════════════
Fixed:   {N} bugs
  {BUG-ID}: {title} — commit {hash}

Skipped: {N} bugs
  {BUG-ID}: {reason — BLOCKED / P2 deferred / not in role scope}

Total commits: {N}
════════════════════════════════
```

## Parameters
| Parameter | Behavior |
|-----------|---------|
| (none) | Fix all open bugs matching current role |
| `-f` | Force: only fix frontend bugs |
| `-b` | Force: only fix backend bugs |
| `{BUG-ID}` | Fix this specific bug only |

## Next Steps
After fixing: run `/project:aion-review` to review the fixes, then `/project:aion-commit`.

Or: use `/project:aion-commit` directly if fixes are straightforward (Tier 1/2 may apply).

## Checklist
- [ ] Role determined from config.yml
- [ ] Bug scope filtered correctly
- [ ] Each bug: code located before fixing
- [ ] Each bug: Reuse Scan performed
- [ ] Each bug: verify_test run (if specified)
- [ ] Each bug: atomic commit with ID in message
- [ ] Each bug: status updated to `fixed`
- [ ] No unrelated code changed
- [ ] No features added during bug fixes

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Fixing without locating the exact code | Guessing causes incorrect fixes or new bugs | CRITICAL |
| Batching multiple bugs in one commit | Cannot revert individual fixes | HIGH |
| Refactoring while fixing | Expands scope, introduces new risk | HIGH |
| Skipping verify_test | Bug may still be broken in a different way | HIGH |
| Role bypass without explicit `-f`/`-b` flag | Designer/tester accidentally modifying code | MEDIUM |
| Fixing > 3 files for a "simple" bug | Scope has exploded — stop and confirm with user | MEDIUM |

## Output Format
Bug status updated in `.aion/bugs/`, atomic commits per fix, summary shown in conversation.

## Exit Status
- `DONE` — All eligible bugs fixed
- `DONE_WITH_CONCERNS` — Some bugs could not be fixed (blocked or deferred)
- `BLOCKED` — Role not allowed to fix bugs, or no browser backend for verification
- `NEEDS_CONTEXT` — Bug report lacks enough information to locate the issue
