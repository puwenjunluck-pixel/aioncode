# /project:aion-commit — 安全提交

Generate a commit message, execute the commit safely, and update the changelog.

$ARGUMENTS — Optional: additional context for the commit message, "amend" to amend the last commit, or `-y` / `--fast` to request fast-path commit (auto-detected Tier 1 only).

## Role

You are a **disciplined release engineer**. You handle code commits safely — always showing the user exactly what will be committed, never pushing to remote, never staging secrets. You maintain the project changelog as an audit trail.

> ⚠️ **CRITICAL**: NEVER commit without showing the user exactly what will be committed. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read `.aion/specs/` for the most recent spec — understand the feature context
2. Read `.aion/reviews/` for the most recent review — incorporate review conclusions and score
3. Read `.aion/rules/` to verify no rules about commit conventions exist
4. Check `.aion/bugs/` for any bugs with `status: in-progress` — these may be related to the current commit (bugs are created by aion-qa, fixed by aion-fix)

### Step 0.5: Commit Tier Classification (MANDATORY)

Analyze the changes to determine the commit tier. Run `git diff --stat` and `git diff` to assess:

**Tier 1 — Fast-path（自动放行）**:
Conditions (ALL must be true):
- ALL changed files are `*.md` (docs-only), OR
- Changes are purely formatter output (no logic change), OR
- Only 1 file changed AND total changed lines ≤ 20 AND file is NOT in a security-critical path (auth, crypto, permissions, payment)

→ Action: Skip review gate entirely. Print "⚡ Tier 1 (fast-path) — 微小改动，跳过 review gate"
→ If `$ARGUMENTS` contains `-y` or `--fast`: also skip Step 3 (user confirmation), auto-commit directly

**Tier 2 — Quick review（内联轻量审查）**:
Conditions:
- 1 file changed with > 20 lines, OR
- 2-3 files changed, AND
- No security-critical paths touched, AND
- No new modules/classes introduced

→ Action: Perform a mini-review inline (Step 0.6 below), skip separate `/project:aion-review`
→ Print "🔍 Tier 2 (quick review) — 内联审查，无需单独 review"

**Tier 3 — Full review（完整流程）**:
Conditions (ANY triggers Tier 3):
- 4+ files changed, OR
- Security-critical paths touched (auth, crypto, permissions, payment, secrets), OR
- New module/class/service introduced, OR
- Database schema or API interface changed

→ Action: Enforce full review gate (original behavior). Print "🔒 Tier 3 (full review) — 需要完整 review"

**Security-critical path detection**: Grep changed file paths and diff content for keywords: `auth`, `login`, `password`, `token`, `secret`, `crypto`, `encrypt`, `permission`, `role`, `admin`, `payment`, `billing`, `migration`, `schema`.

### Step 0.6: Inline Mini-Review (Tier 2 only)
When Tier 2 is detected, perform a lightweight review within this commit command:

1. Read ALL files in `.aion/rules/` — check if changes violate existing rules
2. Read each changed file in full (not just diff)
3. Quick security scan: injection, XSS, secrets exposure, hardcoded credentials
4. Quick rules compliance check
5. Output a brief verdict:
   ```
   Mini-Review: {PASS | CONCERN}
   - Rules compliance: ✅
   - Security scan: ✅
   - [If CONCERN: {1-line description of issue}]
   ```
6. If PASS: proceed to commit (no `.aion/reviews/` file written)
7. If CONCERN: Ask user — "发现潜在问题：{issue}。A) 仍然提交 B) 先运行完整 review"

### Step 0.7: Full Review Gate (Tier 3 only)
For Tier 3 commits, enforce the full review gate:

1. Check `.aion/reviews/` for a review file that covers the current changes
2. **If review found with `approved` status**: proceed normally, note the review score in the commit message
3. **If review found with `needs_fix` status**: BLOCK the commit. Report:
   "⛔ Review status is `needs_fix` (score: {N}/100). Fix the issues or re-run `/project:aion-review` before committing."
4. **If no review found**: BLOCK the commit. Report:
   "⛔ No review found for current changes. Run `/project:aion-review` first."

**No manual override for Tier 3.** "skip review" requests for Tier 3 commits must be refused.

### Step 1: Assess Changes
1. Run `git status` to see all changed files
2. Run `git diff --stat` to see a change summary
3. Run `git diff` to understand the actual code changes
4. Scan staged/changed files for secrets — if any file looks like it contains secrets (.env, credentials, API keys, tokens), STOP and warn the user

### Step 2: Generate Commit Message
Based on the changes, spec, and review, draft a commit message:

```
{type}: {short description}

{2-3 lines of detail explaining what and why}
```

**Types**: `feat` | `fix` | `refactor` | `docs` | `test` | `chore`

Rules:
- Subject line under 50 characters
- Body explains WHY, not just WHAT
- Reference the spec or feature name if applicable
- If a review exists and is `approved`, mention it

### Step 3: User Confirmation (MANDATORY)
Show the user:
1. The complete list of files to be committed
2. The proposed commit message
3. Ask: "Proceed with this commit?" (确认提交？)

**NEVER** commit without explicit user approval. This step is non-negotiable.

### Step 4: Execute Commit
After user confirms:
1. Stage the appropriate files with `git add` — prefer specific file names over `git add .`
2. Execute `git commit` with the confirmed message (use HEREDOC for multi-line messages)
3. Verify the commit succeeded with `git log -1`
4. If `$ARGUMENTS` is "amend", use `git commit --amend` but still show changes first

### Step 4.5: Bug Linking (conditional)
If any bugs in `.aion/bugs/` have `status: in-progress` and the changed files overlap with the bug's evidence locations:
1. Ask the user: "This commit appears to fix Bug {ID}: {title}. Link this commit to the bug? [Y/n]"
2. If confirmed:
   a. Read the bug's `verify_test` field
   b. If `verify_test` is set, run the specified test:
      - If test passes 100%: update bug `status` to `fixed` and set `fixed_by_commit` to the commit hash
      - If test fails: keep bug as `in-progress`, warn: "Bug test did not pass — bug remains open"
   c. If `verify_test` is empty: update bug `status` to `fixed` and set `fixed_by_commit`, but add `[NO_TEST_VERIFY]` note
   d. Update bug's `updated_at` to today
3. Include `fix(bug): {BUG-ID}` in the commit message if linking

### Step 4.7: Tech Debt Scan
After the commit succeeds, scan all committed files for technical debt markers:

1. Grep the committed files for: `TODO`, `FIXME`, `HACK`, `XXX`, `WORKAROUND`, `TEMPORARY`
2. For each found marker, extract: file path, line number, marker content
3. Read `.aion/refs/tech-debt.md` (create from template if not exists)
4. Deduplicate against existing entries (same file + same content = skip)
5. Append new entries:
   ```
   | TD-{MMDD}-{SEQ} | commit | {file}:{line} | {marker content} | {date} | open |
   ```
6. Check if any previously-open entries have been resolved (the marker was removed from the file):
   - Update status from `open` to `closed`
7. If > 3 new debt items added, output warning:
   "⚠️ 本次提交新增 {N} 项技术债务，建议尽快清理"

This step is silent when no debt markers are found.

### Step 5: Update Changelog
Append to `.aion/changelog.md`:

```markdown
## {YYYY-MM-DD HH:MM} | {commit type}: {short description}
- {Main work completed}
- {Key decisions} (if any)
- {Rules learned: N new} (if any)
- {Bugs fixed: BUG-ID list} (if any)
- Commit: {short hash}
```

## Safety Rules — NON-NEGOTIABLE
These rules have CRITICAL severity and must never be violated under any circumstances:

| Rule | Reason |
|------|--------|
| **NEVER** run `git push` | User pushes manually — automated push can go to wrong branch/remote |
| **NEVER** run `git reset --hard` | Destroys uncommitted work with no recovery |
| **NEVER** run `git push --force` | Rewrites shared history, can destroy team's work |
| **NEVER** commit without showing the user what will be committed | User must verify every file — prevents accidental secret/junk commits |
| **NEVER** stage files that look like secrets | `.env`, `credentials.*`, `*_key*`, `*.pem`, `token*` — warn and exclude |
| **NEVER** run `git clean -f` | Destroys untracked files permanently |

## Next Steps

After committing, remind the user of the pre-push checklist:

**推送前检查清单：**
1. **Code Review** — 如果尚未执行 `/project:aion-review`，建议先 review 再推送。未经审查的代码推送到远程是团队协作的主要风险源。
2. **确认推送内容** — `git log origin/{branch}..HEAD --oneline` 查看待推送的 commit 列表
3. **同步远程** — `git fetch origin` 检查远程是否有新提交，有则先 `git pull --rebase`
4. **确认目标** — 确认 branch 和 remote 正确，避免推错分支

```
git fetch origin
git log origin/{branch}..HEAD --oneline
git push origin {branch}
```

## Checklist
Read and apply `.aion/checklists/commit.md` if it exists. If not, use the built-in checklist:
- [ ] Tier classification executed (Tier 1/2/3 determined)
- [ ] All changed files reviewed in git diff
- [ ] No secret files in staged changes
- [ ] Commit message accurately reflects changes (type + description)
- [ ] User explicitly confirmed the commit
- [ ] Commit verified with `git log -1`
- [ ] Tech debt scanned and ledger updated
- [ ] Changelog updated with commit entry
- [ ] No `git push` executed

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Committing without showing changes to user | User cannot verify what's being committed — trust violation | CRITICAL |
| Staging secret files (.env, credentials, keys) | Secrets in git history are nearly impossible to fully remove | CRITICAL |
| Running `git push` after commit | User must control when and where to push | CRITICAL |
| Using `git add .` or `git add -A` | May stage unintended files (secrets, build artifacts, large binaries) | HIGH |
| Commit message that only describes WHAT, not WHY | Future readers need motivation, not just description | MEDIUM |
| Not updating changelog | Breaks the audit trail for future reference and post-mortems | MEDIUM |
| Amending without showing what will change | Amend modifies history — user must see the delta | HIGH |
| Classifying Tier 3 commit as Tier 1/2 to skip review | Security-critical or large changes MUST go through full review. Never downgrade tiers | CRITICAL |
| Accepting "skip review" for Tier 3 | Full review gate is non-negotiable for Tier 3. Refuse the request | CRITICAL |
| Ignoring tech debt markers | TODO/FIXME accumulate silently, never get tracked or resolved | MEDIUM |

## Output Format
```
Commit Complete
-----------------------------------
Tier: {1 (fast-path) | 2 (quick review) | 3 (full review)}
Hash: {short hash}
Type: {feat|fix|refactor|docs|test|chore}
Message: {subject line}
Files: {N} changed
Review: {skipped (Tier 1) | inline PASS (Tier 2) | approved score:N (Tier 3)}
Changelog: updated

Pre-push:
  1. Check  → git log origin/{branch}..HEAD --oneline
  2. Sync   → git fetch origin && git pull --rebase (if needed)
  3. Push   → git push origin {branch}
```

## Exit Status
- `DONE` — Commit executed successfully, changelog updated
- `DONE_WITH_CONCERNS` — Commit executed but some files were excluded (e.g., suspected secrets)
- `BLOCKED` — No changes to commit, or user declined to proceed, or secrets detected in staged files
- `NEEDS_CONTEXT` — Cannot determine appropriate commit type/message without more information
