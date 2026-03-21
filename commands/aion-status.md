# /project:aion-status — 项目状态总览

Show the current state of AionCode project intelligence, rules, documents, and git activity.

$ARGUMENTS — None. This command takes no arguments.

## Role

You are a **project intelligence reporter**. Scan the `.aion/` directory and git state, then present a concise, structured status report. Do not modify any files.

> ⚠️ **CRITICAL**: NEVER modify any files. Status is strictly read-only. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Check if `.aion/` directory exists in the project root
2. If it does not exist, report that AionCode is not initialized and suggest running install — then exit with `DONE`

### Step 1: Scan Rules
1. Read each file in `.aion/rules/` (`pitfalls.md`, `style.md`, `perf.md`)
2. Count the number of rules in each category
3. Identify the 3 most recently added rules (by date) across all categories
4. If any category exceeds 25 rules, flag it for consolidation

### Step 1.5: Rule Health Report
Parse rule citation metadata and generate a health report:

1. **Stale rules**: Find rules where `last_cited` is more than 60 days ago (or has never been cited). Mark as "stale"
2. **Similar rules**: Scan for rules with high keyword overlap (>80% shared keywords in title+description) across all categories. Flag as "candidates for merge"
3. **Top 5 high-frequency rules**: Sorted by `cite_count` descending — these are your most valuable rules
4. **Bottom 5 low-frequency rules**: Sorted by `cite_count` ascending — candidates for review or deprecation
5. **Deprecated rules**: Count rules with `status: deprecated` or `status: archived`
6. **Backward compatibility**: Rules without citation metadata are treated as `cite_count: 0, last_cited: unknown` and flagged as "needs metadata update"

**Actionable suggestions**:
- For stale rules: "Consider reviewing: {rule title} — not cited in {N} days. Run `/project:aion-learn` to validate or deprecate."
- For similar rules: "Possible merge candidates: '{rule A}' and '{rule B}' — similar content detected."
- For rules without metadata: "Legacy rules without tracking data found. Next `/project:aion-review` or `/project:aion-learn` will auto-update them."

### Step 1.7: Bug Status
Scan `.aion/bugs/` for bug reports:

1. Count bugs by status: open, assigned, in-progress, fixed, verified, closed
2. Count bugs by category: F (frontend), B (backend), X (mixed)
3. Count bugs with `risk_level: financial`
4. Calculate team load: count `status: in-progress` or `status: assigned` bugs per assignee
5. Identify the longest-open bug (highest `stale_hours` or oldest `created_at` with status not closed)
6. If `.aion/team.yml` exists, read team member list for load display

### Step 2: Scan Documents
Check which `.aion/` documents exist and their status:
- `.aion/specs/` — list spec files with their status (from frontmatter)
- `.aion/plans/` — list plan files with step completion progress (e.g., 3/7 steps done)
  - For each plan, check for archived versions (`.v{N}.md` files)
  - Show current version number and count of historical versions
  - If archived versions exist, list them with `change_reason` from frontmatter
- `.aion/reviews/` — list review files with scores and verdicts
- `.aion/contracts/` — list contract files
- `.aion/refs/` — list reference documents
- `.aion/prototypes/` — list prototype directories

### Step 2.5: Tech Debt Summary
Check `.aion/refs/tech-debt.md` if it exists:
1. Count entries by status: `open` vs `closed`
2. Find the newest open entry date
3. Report one line: `Tech Debt: {N} open / {M} closed (newest: {date})`
4. If > 10 open items, add warning: "⚠️ Tech debt accumulating — consider running `aioncode clean` or addressing open items"

### Step 3: Recent Activity
Read the last 3 entries from `.aion/changelog.md` (if it exists).

### Step 4: Git Status
1. Run `git status --short` to show uncommitted changes
2. Run `git log --oneline -5` to show recent commits
3. Run `git branch --show-current` to identify the active branch

## Next Steps

Start a task with /project:aion-design, or check /project:aion-think for ideas.

## Checklist
Read and apply `.aion/checklists/status.md` if it exists. If not, use the built-in checklist:
- [ ] `.aion/` directory existence verified
- [ ] All rule files scanned and counted
- [ ] Rule health report generated (stale, similar, top/bottom cited)
- [ ] All document directories checked
- [ ] Plan version history scanned
- [ ] Changelog recent entries read
- [ ] Git status and log retrieved

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Modifying any files during status check | Status is read-only; side effects break trust | CRITICAL |
| Skipping directories that don't exist without reporting | User needs to know what's missing | MEDIUM |
| Showing raw file contents instead of summaries | Status should be a dashboard, not a dump | MEDIUM |

## Output Format

```
Project Status
-----------------------------------
Rules: {n} pitfalls | {n} style | {n} perf ({n} active, {n} deprecated)
Recent rules:
  - {title} ({category}, {date})
  - {title} ({category}, {date})
  - {title} ({category}, {date})
{if any category > 25: "Warning: {category} has {n} rules — consider consolidation"}

Rule Health:
  Top cited:   {title} (cited {n} times)
  Stale:       {n} rules not cited in 60+ days
  Merge candidates: {n} similar rule pairs detected
  Legacy:      {n} rules without tracking metadata
  {actionable suggestions}

Bugs:
  Open:        {n}  ({n} critical, {n} financial risk)
  In Progress: {n}
  Fixed:       {n}  (pending verification)
  Closed:      {n}
  Team Load:
    {name} (@{role}): {n} active bugs
    ...
  Longest Open: {BUG-ID} — {n}h since creation

Documents:
  specs/      {count} file(s) — {latest status}
  plans/      {count} file(s) — {latest step progress} {version history: vN}
  reviews/    {count} file(s) — {latest score}
  contracts/  {count} file(s)
  refs/       {count} file(s)
  prototypes/ {count} dir(s)
  bugs/       {count} file(s) — {n} open, {n} closed

Plan Versions:
  {plan name}: v{current} ({n} historical versions)
  ...

Recent Activity:
  {last 3 changelog entries, one line each}

Git:
  Branch: {branch}
  {last 5 commits, one line each}
  {uncommitted changes summary}
```

## Exit Status
- `DONE` — Always. Status is a read-only operation that always succeeds.
