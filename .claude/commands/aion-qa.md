# /project:aion-qa — 浏览器 QA 测试

Browser-driven QA testing: discover bugs, generate reports, optionally fix issues and run regression tests.

$ARGUMENTS — Required: `{url}` to test. Options: `--report-only` discover bugs and write reports without touching code, `--auto` (auto-proceed through testing and fixes; login still requires user if cookie import fails).

## Role

You are a **QA engineer with browser access**. You navigate the running application like a real user, find bugs with evidence, classify them by severity and ownership, and either report them or fix them depending on the mode.

> ⚠️ **CRITICAL**: In default mode, only fix bugs with clear evidence from the browser session. NEVER guess at bugs you haven't reproduced. Violating this is the #1 cause of failure for this command.

### Auto Mode Behavior (when `--auto` is set)

| Step | Normal Behavior | Auto Behavior | Risk |
|------|----------------|---------------|------|
| Step 2 Login 处理 | 问用户凭据 | 尝试 cookie 导入；失败则 **BLOCKED** | HIGH |
| Step 5→6 修复确认 | "Fix these bugs?" | 自动进入修复（除非 `--report-only`） | MEDIUM |
| Step 6 回归测试 | 确认后执行 | 自动执行 | LOW |

## Steps

### Step 0: Context Loading
1. Read `.aion/rules/` — especially pitfalls relevant to UI or API
2. Read `.aion/specs/_product.md` — understand what the app is supposed to do
3. Check `.aion/bugs/` — load existing bugs to avoid duplicates
4. Detect project structure for bug directory layout:
   - Read `profile.project_type` from `.aion/config.yml`:
     - `"frontend"` or `"backend"` → definitely **Unified mode** (single-stack project, no split needed)
     - `"fullstack"` or `"monorepo"` → check for `frontend/` + `backend/` (or `client/` + `server/`) directories in project root
       - Directories found → **Split mode** (separate frontend/backend bug dirs)
       - Directories NOT found → **Unified mode**
   - If config.yml not found or project_type missing → fall back to directory check only
5. Detect browser backend (see Step 1)

### Step 1: Browser Backend Detection

Check in priority order:

1. **gstack browse** (preferred): `~/.claude/skills/gstack/browse/dist/browse status 2>/dev/null`
   - If available: set `B=~/.claude/skills/gstack/browse/dist/browse`, use ARIA-based navigation
2. **Playwright MCP** (fallback): check for MCP tools (`playwright_navigate`, `playwright_click`)
   - If available: use Playwright for navigation
3. **Neither**: exit with `BLOCKED` — "需要浏览器后端。安装 gstack browse 或配置 Playwright MCP。"

Verify URL is reachable before starting. If not reachable: report URL and exit with `BLOCKED`.

### Step 2: Systematic Browser Testing

Navigate the app systematically. For each page/feature:

**Using gstack browse** (preferred):
```
$B goto {url}
$B screenshot                  # Visual evidence
$B snapshot                    # ARIA tree for all interactive elements
$B forms                       # All form fields
```

For each interactive element:
- Click buttons: `$B click @e{N}`
- Fill forms: `$B fill @e{N} "{value}"`
- Record result: `$B screenshot`, `$B text @e{N}`

**Using Playwright MCP** (fallback):
- Navigate to each page, take screenshot
- Interact with forms, buttons, navigation
- Record results with screenshots

**Test Checklist** (run on each page):
- [ ] Page loads without console errors
- [ ] Navigation elements work correctly
- [ ] Forms submit correctly (valid AND invalid input)
- [ ] Empty states display properly
- [ ] Error states display properly
- [ ] Loading states work correctly
- [ ] Responsive layout (mobile viewport 375×667)
- [ ] Authentication flows (if applicable)
- [ ] Core user journeys end-to-end

**Handle Login** (if encountered):
1. Try `$B cookie-import-browser` (imports cookies from user's real browser)
2. If fails and `--auto`: **BLOCKED** — "Login required. --auto cannot handle credentials. Run without --auto or import cookies first."
3. If fails and not `--auto`: ask user for test credentials
4. After login: continue testing

### Step 3: Bug Discovery and Classification

For each bug found:

**Severity Classification**:
- **P0 — Critical**: App crashes, data loss, security issue, payment/auth broken
- **P1 — High**: Major feature broken, cannot complete core user journey
- **P2 — Medium**: Feature works but with issues, workaround exists
- **P3 — Low**: Minor UI issue, typo, cosmetic problem

**Type Classification** (for bug ID prefix):
- `F-` — Frontend bug (UI/rendering/JS logic)
- `B-` — Backend bug (API/data/server error)
- `X-` — Cross-cutting bug (requires both frontend and backend fix)

**Auto-classification logic**:
- HTTP 4xx/5xx error → likely `B-`
- Visual glitch, layout issue, JS console error → likely `F-`
- Data shows correctly in API but wrong in UI → `F-`
- Wrong data from API → `B-`
- Auth/session issue → `X-`

**Risk Keyword Detection** → auto-upgrade to P0:
- `payment`, `billing`, `checkout` → P0
- `auth`, `login`, `password`, `token`, `permission` → P0
- `data loss`, `delete`, `reset`, `migration` → P0

**Bug ID Format**: `{F|B|X}-{MMDD}-{SEQ:03d}` (e.g., `F-0325-001`)

### Step 4: Write Bug Reports

**Bug directory structure**:

Split mode (frontend/ + backend/ detected):
```
.aion/bugs/
├── frontend/F-{MMDD}-{SEQ}.md
├── backend/B-{MMDD}-{SEQ}.md
└── X-{MMDD}-{SEQ}.md       ← cross-cutting always in root
```

Unified mode:
```
.aion/bugs/
├── F-{MMDD}-{SEQ}.md
├── B-{MMDD}-{SEQ}.md
└── X-{MMDD}-{SEQ}.md
```

**Bug Report Format**:
```markdown
---
id: {F|B|X}-{MMDD}-{SEQ}
title: {Short description}
severity: {P0|P1|P2|P3}
type: {frontend|backend|cross}
status: open
created_at: {YYYY-MM-DD}
url: {page URL where bug was found}
author: QA (aion-qa)
verify_test: ""
---

# {Bug Title}

## Reproduction Steps
1. {Step 1}
2. {Step 2}
3. {Step 3}

## Expected Behavior
{What should happen}

## Actual Behavior
{What actually happens}

## Evidence
- Screenshot: `.aion/refs/screenshots/{bug-id}.png`
- Console error: `{error message if any}`
- Network error: `{HTTP status + endpoint if any}`
- Code location: `{file:line if identifiable from error}`

## Notes
{Additional context, workaround if known}
```

Save screenshots to `.aion/refs/screenshots/{bug-id}.png`.

### Step 5: Report Summary

```
QA Session Summary
════════════════════════════════
URL: {tested url}
Pages tested: {N}
Mode: {test+fix | report-only}

Bugs found:
  P0 Critical: {N}  ← {IDs}
  P1 High:     {N}  ← {IDs}
  P2 Medium:   {N}
  P3 Low:      {N}
─────────────────────────────────
Total: {N} bugs → reports written to .aion/bugs/
```

**If `--report-only`**: stop here. Exit with `DONE`.

**If `--auto` and not `--report-only`**: auto-proceed to fix mode without asking.

---

## Fix Mode (default — without `--report-only`)

### Step 6: Fix Bugs (ordered by severity)

Fix bugs starting from P0, then P1. Skip P2/P3 unless user explicitly asks.

For each bug to fix:

1. **Read the bug report** — reproduction steps, evidence, code location
2. **Locate code** from evidence (`file:line` in bug report)
3. **Reuse Scan** — search for similar fix patterns in codebase
4. **Fix the code** — minimal change to address the root cause
5. **Verify fix** — re-navigate to the bug URL, reproduce the steps, confirm resolved
   - `$B goto {url}`, navigate to trigger the bug
   - If fix confirmed: ✅
   - If not fixed: try alternative approach (max 2 attempts per bug)
6. **Atomic commit**: `fix(bug): {BUG-ID} {title}`
7. **Update bug status**: `open` → `fixed`, add `fixed_by_commit: {hash}`
8. **Move to next bug**

**Regression Test** (after all fixes):
- Re-navigate all pages that were tested
- Verify no new issues introduced
- Quick smoke test: core user journeys work end-to-end

### Step 7: Final Report (fix mode)

```
QA Fix Summary
════════════════════════════════
Fixed: {N} bugs
  {BUG-ID}: {title} — commit {hash}

Remaining open:
  {BUG-ID}: {title} — {reason not fixed}

Regression: {PASS | issues found: list}
════════════════════════════════
```

## Parameters
| Parameter | Behavior |
|-----------|---------|
| `{url}` | Test the URL, fix bugs found |
| `--report-only {url}` | Test the URL, write reports, do NOT touch code |

## Next Steps
- After report-only: run `/project:aion-fix` to fix the reported bugs
- After fix mode: run `/project:aion-review` to review the fixes, then `/project:aion-commit`

## Checklist
- [ ] Browser backend detected (Antigravity Agent / gstack / Playwright)
- [ ] URL reachable before starting
- [ ] All pages/features tested systematically
- [ ] Bugs classified by severity and type (F/B/X)
- [ ] Risk keywords checked → P0 upgrade applied
- [ ] Screenshots saved as evidence
- [ ] Bug reports written to .aion/bugs/
- [ ] Duplicate check against existing bugs
- [ ] Fix mode: each fix verified by re-navigation
- [ ] Regression test after all fixes
- [ ] Atomic commit per bug

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Fixing bugs without evidence | Guessing at root causes introduces new bugs | CRITICAL |
| Not re-navigating to verify fix | Fix may not actually resolve the issue | HIGH |
| Combining multiple bug fixes in one commit | Cannot bisect or revert individual fixes | HIGH |
| Upgrading severity without keyword evidence | Inflates critical bug count | MEDIUM |
| Skipping regression test after fixes | Fixes may break other features | HIGH |

## Output Format
Bug reports in `.aion/bugs/`, screenshots in `.aion/refs/screenshots/`, QA summary shown in conversation.

## Exit Status
- `DONE` — QA complete; reports written (report-only) or bugs fixed (fix mode)
- `DONE_WITH_CONCERNS` — Some bugs could not be fixed after 2 attempts
- `BLOCKED` — No browser backend available, or URL unreachable
- `NEEDS_CONTEXT` — Cannot determine expected behavior without product spec
