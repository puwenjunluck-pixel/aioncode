# /project:aion-fix — Bug 修复

<!-- 本命令 Iron Law + 4-phase debugging 综合 superpowers:systematic-debugging 精髓。
     See .aion/CREDITS.md -->

Fix bugs from `.aion/bugs/` reports. Filters by role, fixes methodically, commits atomically.

$ARGUMENTS — Optional: bug ID (e.g., `F-0325-001`) to fix a specific bug. Flags: `-f` force frontend only, `-b` force backend only, `--auto` (skip triage confirmation, fix all in priority order, auto-commit each fix), `--deep` (root cause analysis mode: 4-phase investigation before fixing). If empty, fix all open bugs matching current role.

## Iron Laws (不可协商 — 见 `.aion/rules/metacognition.md`)

```
1. NO FIX WITHOUT ROOT CAUSE — 修任何 bug 之前,MUST 完成 Phase 1 的根因调查
2. ONE BUG ONE COMMIT — 原子提交,绝不 batch 多个 bug 到一个 commit
3. VERIFY BEFORE CLAIM — 声称"修好"之前,MUST 跑原始复现用例看到它现在通过
4. 3+ FIXES FAIL → QUESTION ARCHITECTURE — 同一 bug 失败 3 次 = 架构问题,停下来讨论,不要第 4 次
```

> 💡 **强烈建议默认启用 `--deep`** — 即使 bug 看起来简单。simple bug 有 simple 根因,走流程 2 分钟,跳过流程的代价是症状式修复→ bug 以另一形式回归。只有当 bug **极度明确**(例如已知 typo、已知空指针)且**无疑义**时,才省略 `--deep`。

## Role

You are a **focused bug fixer**. You read the bug report, locate the exact code, apply the minimal fix, verify it works, and commit atomically. You don't refactor while fixing — one bug, one commit.

> ⚠️ **CRITICAL**: Fix the bug as described. Do not expand scope. Do not refactor unrelated code. Violating this is the #1 cause of failure for this command.

### Auto Mode Behavior (when `--auto` is set)

| Step | Normal Behavior | Auto Behavior | Risk |
|------|----------------|---------------|------|
| Step 1 开始修复确认 | "开始修复？[Y/n]" | 跳过，直接开始 | LOW |
| Step 1 >3 bug 优先级 | 问用户 | 全部修复，P0→P1→P2→P3 | LOW |
| Step 2f atomic commit | 逐个提交 | 自动提交（模板消息 `fix(bug): {ID} {title}`） | MEDIUM |

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
- If `--auto`: skip confirmation, proceed immediately. If > 3 bugs: auto fix all in P0→P1→P2→P3 order.
- Otherwise: if `$ARGUMENTS` is empty and > 3 bugs, ask if user wants to prioritize or fix all.

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

#### 2c.5. Root Cause Analysis (conditional — when `--deep` is set)

When `--deep` flag is present, run four-phase investigation BEFORE attempting any fix:

**Phase 1: Investigation** — Gather evidence, don't guess.
- Read the full error message/stack trace
- Reproduce the bug by tracing the code path (read caller → callee chain)
- If bug is UI-related: use Playwright MCP / gstack browse if available to reproduce
- Check `git log` for recent changes to affected files — did a recent commit introduce this?
- List all assumptions: "I assume X because Y"
- When investigation spans multiple modules, use Agent tool subagents to parallelize

**Phase 2: Pattern Analysis** — Find what works and compare.
- Find a similar feature or code path in the codebase that DOES work correctly
- Diff the working code against the broken code — what's different?
- Check if the bug exists in other similar locations (systemic vs isolated)

**Phase 3: Hypothesis** — One hypothesis at a time.
- Form a single, testable hypothesis: "The bug occurs because {X} when {Y}"
- Design a minimal test to confirm or refute — don't fix yet, just verify the hypothesis
- If refuted: return to Phase 1 with new evidence. Do NOT try another fix blindly.

**Phase 4: Implementation** — Fix with confidence.
- Write a failing test that reproduces the bug (this test must fail before the fix)
- Apply the minimal fix
- Run the test — it must now pass
- Check for the same pattern in other locations (Phase 2 findings)

**Escalation rule**: After 3 failed fix attempts on the same bug, STOP and question the architecture:
- "Is the bug a symptom of a deeper design problem?"
- Report to user with evidence gathered, suggest architectural discussion.

#### 2d. Fix Code
Apply the minimal change to address the root cause:
- Fix exactly what the bug report describes
- Do NOT refactor unrelated code
- Do NOT add features while fixing
- Read the full file before editing (Implementation Rule: Read First)

#### 2e. Run Verify Test (Iron Law 3)

> **NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION** — 声称"修好"之前,必须在本轮跑过原始复现用例看到它通过。

If the bug report has a non-empty `verify_test` field:
- Run the specified test: `{verify_test command}`
- **Must pass 100%** before marking fixed
- If test fails: the fix is incomplete → try a different approach (max 2 attempts)
- If still failing after 2 attempts: skip this bug, move to next, report `BLOCKED`

**红-绿回归验证**(推荐):
1. 先跑原始复现用例看到**失败**(red)
2. 应用 fix
3. 再跑看到**通过**(green)
4. 可选:临时 revert fix,确认用例又失败 → restore fix → 再次通过 — 证明 fix 真的起作用

不跑 red→green 的"测试"可能是空 assertion,**没证明力**。

If no `verify_test`: use gstack/Playwright if available to verify, otherwise run the relevant test suite.

#### 2f. Atomic Commit
```
git add {only the files changed for this bug}
git commit -m "fix(bug): {BUG-ID} {title}"
```

One commit per bug. Never batch multiple bug fixes.
- If `--auto`: auto-stage and auto-commit without pausing. Template message ensures consistency. Full audit in Step 3 summary.

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
- [ ] Each bug: Root Cause Analysis completed (if `--deep`)
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
| Guessing the fix without root cause analysis (`--deep`) | Symptom fixes mask underlying issues; bug recurs in a different form | HIGH |
| Trying a 4th fix on the same bug in `--deep` mode | 3 failures = likely architectural issue. Escalate, don't persist | MEDIUM |

## Output Format
Bug status updated in `.aion/bugs/`, atomic commits per fix, summary shown in conversation.

## Exit Status
- `DONE` — All eligible bugs fixed
- `DONE_WITH_CONCERNS` — Some bugs could not be fixed (blocked or deferred)
- `BLOCKED` — Role not allowed to fix bugs, or no browser backend for verification
- `NEEDS_CONTEXT` — Bug report lacks enough information to locate the issue
