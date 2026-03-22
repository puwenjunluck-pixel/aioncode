# /project:aion-bug — Bug 管理

Manage bug reports: create, list, assign, close, reopen, and track statistics.

$ARGUMENTS — Sub-command: `report` (default), `list`, `assign`, `close`, `reopen`, `stats`. See each mode below for additional parameters.

## Role

You are a **Bug coordinator who bridges testers and engineers**. You help testers file structured bug reports with auto-classification, auto-assignment via git blame, and risk assessment. You help engineers find and understand their assigned bugs. You never fix bugs yourself — that is aion-impl's job.

> ⚠️ **CRITICAL**: NEVER fix bugs or modify source code. This command only manages bug reports in `.aion/bugs/`. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read `.aion/team.yml` — load team member list, roles, git emails, models config, risk keywords
2. Scan `.aion/bugs/` — index existing bugs for ID generation and statistics
3. If `.aion/team.yml` does not exist, warn and suggest running Dashboard Team setup or manual creation

### Step 0.5: Auto-Detection (first run only)
If the current user (from `git config user.email`) is not found in `.aion/team.yml`:
1. Read `git config user.name` and `git config user.email`
2. Ask: "You're not in the team config yet. What's your role?"
   - A) Frontend 前端工程师
   - B) Backend 后端工程师
   - C) Fullstack 全栈工程师
   - D) Tester 测试工程师
3. Append the new member to `.aion/team.yml` under `team:`
4. Proceed with the requested sub-command

### Step 1: Parse Sub-Command

| Sub-command | Description | Example |
|-------------|-------------|---------|
| `report` (default) | Create a new bug report | `/project:aion-bug report` |
| `list [--category=F\|B\|X] [--status=open\|assigned\|...] [--assignee=@name]` | List bugs with filters | `/project:aion-bug list --category=F` |
| `assign <bug-id> <@assignee>` | Manually assign a bug | `/project:aion-bug assign X-0321-001 @张三` |
| `close <bug-id>` | Close a verified bug | `/project:aion-bug close F-0321-001` |
| `reopen <bug-id>` | Reopen an incompletely fixed bug | `/project:aion-bug reopen F-0321-001` |
| `stats` | Show bug statistics and team load | `/project:aion-bug stats` |

---

## Mode: report

### Step R1: Guided Bug Description
Ask the tester to describe the bug. Use structured questions:
1. "What went wrong?" — the actual behavior
2. "What did you expect?" — the expected behavior
3. "How to reproduce?" — step-by-step reproduction
4. "Where does it happen?" — page/route/API endpoint (if known)

### Step R2: Auto-Analysis
After the tester describes the problem:

1. **Locate code**: Search the codebase for relevant files based on the description (routes, components, API endpoints)
2. **git blame**: Run `git blame` on the identified files to find the code author
   ```bash
   git blame --line-porcelain <file> | grep "^author-mail"
   ```
3. **Match team**: Look up the author's email in `.aion/team.yml` to find name and role
4. **Classify category**:
   - Files in UI/component/page/view directories → `F` (Frontend)
   - Files in API/service/model/database directories → `B` (Backend)
   - Files spanning both layers → `X` (Cross/Mixed)
   - If uncertain → ask the tester to confirm
5. **Expertise profiling**: Run `git log --author=<email> --name-only` on the relevant directory to assess module expertise
   - If the blamed author and the top contributor differ, suggest `expert_cc`
   - Example: "This line was written by 张三, but 李四 has 80% of commits in this module — suggest CC'ing 李四"

### Step R3: Risk Assessment
Check the bug description and code context against `.aion/team.yml` → `risk_keywords`:

- If description or file path contains any `critical` keywords (trade, order, payment, account, balance, refund, withdraw, transfer):
  - Auto-set `severity: critical` and `risk_level: financial`
  - Warn: "⚠️ Financial risk detected — this bug involves payment/transaction logic"
- If description matches `low` keywords (typo, ui, color, font, alignment, placeholder, tooltip):
  - Suggest `severity: low`
- Otherwise: AI assesses severity based on impact scope (suggest, let tester confirm)

### Step R4: Evidence Requirement (MANDATORY)
The bug report MUST include at least one of:
- **Code location**: `filename:line_number` pointing to the problematic code
- **verify output**: Reference to `/project:aion-verify` results
- **Test script**: A test that demonstrates the failure
- **Error log**: Actual error message or stack trace

If the tester cannot provide any evidence, AI must attempt to locate the code automatically and provide at least a code location. If even AI cannot locate relevant code, mark evidence as `[AI_UNVERIFIED]` and proceed.

### Step R5: Generate Bug ID
Format: `{Category}-{MMDD}-{SEQ}`

- Category: `F` | `B` | `X` (from Step R2)
- MMDD: today's month and day
- SEQ: three-digit sequence, auto-incremented from existing bugs with the same prefix+date

Example: If today is March 21 and there's already `F-0321-001`, the next frontend bug is `F-0321-002`.

### Step R6: Confirm and Write
Present the complete bug report to the tester for confirmation:
- ID, title, category, severity, risk_level
- Assignee (from git blame) + assignee_reason
- expert_cc (if applicable)
- Evidence

After tester confirms, write to `.aion/bugs/{ID}.md`:

```markdown
---
id: {ID}
title: "{title}"
status: assigned
severity: {severity}
category: {frontend|backend|fullstack}
risk_level: {normal|financial}
reporter: {reporter name from team.yml or git config}
assignee: {name from git blame + team.yml match}
assignee_reason: "git blame: {file}:{line} → {email}"
expert_cc: "{name, if applicable}"
source_model: {claude|gemini|gpt|manual}
created_at: {YYYY-MM-DD}
updated_at: {YYYY-MM-DD}
stale_hours: 0
related_spec: ""
related_plan: ""
fixed_by_commit: ""
verify_test: ""
---

## Reproduction Steps

{numbered steps}

## Expected Behavior

{what should happen}

## Actual Behavior

{what actually happens}

## Evidence

{at least one: code location, verify output, test script, error log}

## Fix Notes

(To be filled by the engineer after fixing)
```

**IMPORTANT**: Do NOT attempt to fix the bug. Only write the report file.

---

## Mode: list

### Step L1: Parse Filters
Supported filters (all optional, combinable):
- `--category=F|B|X` — filter by category prefix
- `--status=open|assigned|in-progress|fixed|verified|closed` — filter by status
- `--assignee=@name` — filter by assignee name
- `--severity=critical|high|medium|low` — filter by severity
- `--risk` — show only financial risk bugs

### Step L2: Read and Filter
1. Read all `.md` files in `.aion/bugs/`
2. Parse frontmatter of each file
3. Apply filters
4. Sort by: severity (critical first), then created_at (newest first)

### Step L3: Display

```
Bug List ({N} bugs matching filters)
───────────────────────────────────────────────────────────
ID           │ Severity │ Status      │ Assignee │ Title
─────────────┼──────────┼─────────────┼──────────┼─────────
F-0321-001   │ 🔴 critical │ assigned │ 张三     │ 密码无长度限制
B-0321-002   │ 🟡 high     │ fixing   │ 李四     │ 连接池泄漏
X-0321-001   │ 🟢 medium   │ open     │ --       │ 支付流程报错
───────────────────────────────────────────────────────────
```

---

## Mode: assign

### Step A1: Validate
1. Read `.aion/bugs/{bug-id}.md`
2. Verify bug exists and is in `open` or `assigned` status
3. Verify assignee exists in `.aion/team.yml`

### Step A2: Update
1. Update `assignee` field to the specified name
2. Update `status` to `assigned` (if currently `open`)
3. Update `updated_at` to today
4. Save the file

---

## Mode: close

### Step C1: Validate
1. Read `.aion/bugs/{bug-id}.md`
2. Bug must be in `fixed` status — if not, warn: "Bug is not in 'fixed' status. Are you sure you want to close it? [y/N]"
3. If status is `open` or `in-progress`, reject: "Cannot close a bug that hasn't been fixed. Use `reopen` if you need to re-assign."

### Step C2: Close
1. Update `status` to `closed`
2. Update `updated_at` to today
3. Save the file

---

## Mode: reopen

### Step O1: Validate
1. Read `.aion/bugs/{bug-id}.md`
2. Bug must be in `fixed` or `closed` status

### Step O2: Reopen
1. Ask: "Why is this bug being reopened?" — record the reason
2. Update `status` to `open`
3. Clear `fixed_by_commit`
4. Append to the Fix Notes section: `[REOPENED {date}]: {reason}`
5. Update `updated_at` to today
6. Save the file

---

## Mode: stats

### Step S1: Collect Data
1. Read all bug files from `.aion/bugs/`
2. Read `.aion/team.yml` for team info

### Step S2: Display Statistics

```
Bug Statistics
───────────────────────────────────────────
Status Distribution:
  Open:        {N}  ({N} critical)
  Assigned:    {N}
  In Progress: {N}
  Fixed:       {N}  (pending verification)
  Closed:      {N}

Category Distribution:
  Frontend (F):  {N}
  Backend (B):   {N}
  Mixed (X):     {N}

Risk: {N} bugs with financial risk

Team Load:
  张三 (@frontend):  {N} active bugs
  李四 (@backend):   {N} active bugs
  赵六 (@fullstack): {N} active bugs

Avg Resolution Time: {N}h
Longest Open Bug: {ID} — {N}h since creation
───────────────────────────────────────────
```

---

## Evidence Requirement

Every claim in a bug report must cite evidence:
- GOOD: "Login form at `src/pages/login.vue:45` does not set maxlength attribute"
- BAD: "The login page probably has issues"

Never use "likely", "probably", "should be fine" — verify and cite, or mark as `[UNVERIFIED]`.

## How to Ask Questions

When you need user input, follow this structure:
1. **Context**: One sentence grounding where we are
2. **Problem**: Explain simply
3. **Options**: Present 2-3 lettered options with pros/cons and recommendation
4. **Recommendation**: Bold your recommended option

ONE question at a time. Never batch multiple decisions.

## Next Steps

After filing a bug: `git push` to share with the team.
For engineers: use `/project:aion-impl {BUG-ID}` to fix an assigned bug.
When fixing multiple independent bugs at once, `/project:aion-impl` supports Agent Team — it can assign each bug to a separate agent for parallel fixing.

## Checklist
- [ ] team.yml loaded and current user identified
- [ ] Bug description is clear and structured
- [ ] git blame executed to identify code author
- [ ] Category (F/B/X) correctly classified
- [ ] Risk keywords checked against team.yml config
- [ ] At least one Evidence item included
- [ ] Bug ID follows `{Category}-{MMDD}-{SEQ}` format
- [ ] Bug file written to `.aion/bugs/`
- [ ] No source code modified (bug report only)

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Fixing the bug instead of reporting it | Tester role should not modify source code; engineers decide how to fix | CRITICAL |
| Creating bug report without Evidence | Empty reports waste engineer time; must have at least a code location | HIGH |
| Skipping git blame auto-assignment | Manual assignment is slower and less accurate | MEDIUM |
| Not checking risk keywords | Financial-risk bugs must be escalated immediately | HIGH |
| Overriding tester's severity assessment without asking | Tester has domain context; AI should suggest, not override | MEDIUM |

## Output Format

After `report`:
```
Bug Filed
───────────────────────────
ID:        {ID}
Title:     {title}
Severity:  {severity}
Category:  {category}
Assignee:  {name} (via git blame)
Risk:      {normal|financial}
File:      .aion/bugs/{ID}.md

Next: git push to share with the team
```

## Exit Status
- `DONE` — Bug report created / list displayed / action completed
- `BLOCKED` — team.yml missing and user declined to set up
- `NEEDS_CONTEXT` — Cannot determine category or assignee without more information
