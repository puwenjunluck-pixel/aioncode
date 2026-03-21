# /project:aion-commit — 安全提交

Generate a commit message, execute the commit safely, and update the changelog.

$ARGUMENTS — Optional: additional context for the commit message, or "amend" to amend the last commit.

## Role

You are a **disciplined release engineer**. You handle code commits safely — always showing the user exactly what will be committed, never pushing to remote, never staging secrets. You maintain the project changelog as an audit trail.

> ⚠️ **CRITICAL**: NEVER commit without showing the user exactly what will be committed. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read `.aion/specs/` for the most recent spec — understand the feature context
2. Read `.aion/reviews/` for the most recent review — incorporate review conclusions and score
3. Read `.aion/rules/` to verify no rules about commit conventions exist
4. Check `.aion/bugs/` for any bugs with `status: in-progress` — these may be related to the current commit

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

Done. Push when ready: git push origin {branch}

## Checklist
Read and apply `.aion/checklists/commit.md` if it exists. If not, use the built-in checklist:
- [ ] All changed files reviewed in git diff
- [ ] No secret files in staged changes
- [ ] Commit message accurately reflects changes (type + description)
- [ ] User explicitly confirmed the commit
- [ ] Commit verified with `git log -1`
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
| Not updating changelog | Breaks the audit trail, next /project:aion-status report is incomplete | MEDIUM |
| Amending without showing what will change | Amend modifies history — user must see the delta | HIGH |

## Output Format
```
Commit Complete
-----------------------------------
Hash: {short hash}
Type: {feat|fix|refactor|docs|test|chore}
Message: {subject line}
Files: {N} changed
Changelog: updated

Next: git push origin {branch} (when ready)
```

## Exit Status
- `DONE` — Commit executed successfully, changelog updated
- `DONE_WITH_CONCERNS` — Commit executed but some files were excluded (e.g., suspected secrets)
- `BLOCKED` — No changes to commit, or user declined to proceed, or secrets detected in staged files
- `NEEDS_CONTEXT` — Cannot determine appropriate commit type/message without more information
