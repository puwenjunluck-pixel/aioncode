# /project:aion-audit — 安全+性能审计

Project-wide static audit for security vulnerabilities and performance anti-patterns.

$ARGUMENTS — Options: `--focus security` (security only), `--focus perf` (performance only), `--ignore {pattern}` (skip files matching pattern). Default: full audit (both dimensions).

## Role

You are a **security engineer and performance analyst** who audits entire codebases, not just recent changes. You scan methodically, cite every finding with file:line evidence, and never report false positives without marking them. You track improvement trends across audits.

> ⚠️ **CRITICAL**: This is a project-level audit, NOT a change-level review. Scan the full codebase, not just diffs. For change-level review, use /project:aion-review instead.

## Steps

### Step 0: Context Loading
1. Read all files in `.aion/rules/` — load existing security/perf rules as baseline expectations
2. Read `.aion/specs/_product.md` — understand the product's tech stack, module architecture, and known constraints
3. Check `.aion/audits/` — if previous audit reports exist, read the most recent one for baseline comparison (Step 4)
4. Parse `$ARGUMENTS`:
   - `--focus security`: skip performance dimension entirely
   - `--focus perf`: skip security dimension entirely
   - `--ignore {pattern}`: add pattern to exclusion list (cumulative, can specify multiple times)
5. **Default exclusions** (always skipped unless explicitly included):
   - `node_modules/`, `vendor/`, `__pycache__/`, `.git/`, `dist/`, `build/`
   - Files matching `.aion/rules/style.md` exemptions (e.g., `embedded.py` — auto-generated)

### Step 1: Project Scan

Scan the entire codebase file by file. For each source file (`.py`, `.js`, `.ts`, `.go`, `.java`, `.rs`, etc.):

1. Read the COMPLETE file
2. Check for `# audit:ignore` line-level markers — skip those lines
3. Run checks from applicable dimensions (both, or `--focus` filtered)

#### 1a. Security Dimension

**S1 — Dependency Vulnerabilities**:
- Read `requirements.txt` / `pyproject.toml` / `package.json` / `Cargo.toml` / `go.mod`
- Flag packages with known CVEs (check version patterns against common vulnerable versions)
- Flag unpinned dependencies (`>=` without upper bound, `*` versions)
- Severity: critical (known CVE) / medium (unpinned)

**S2 — Hardcoded Secrets**:
- Regex scan for: API keys (`sk-`, `ak-`, `AKIA`), tokens (`ghp_`, `gho_`, `Bearer `), passwords (`password\s*=\s*["']`), private keys (`-----BEGIN.*PRIVATE KEY`)
- Check `.env` files if tracked by git (`git ls-files` includes `.env*`)
- Severity: critical

**S3 — Injection Patterns**:
- SQL: string concatenation/f-string in query construction (not parameterized)
- Command: `subprocess` / `os.system` / `exec` with user-controlled input
- XSS: unescaped user input in HTML templates / `innerHTML` assignment
- Path traversal: user input in `open()` / `Path()` without sanitization
- Severity: critical (SQL/command injection) / high (XSS/path traversal)

**S4 — Auth & Access Control**:
- API endpoints without authentication middleware/decorator
- Hardcoded role checks (`if user == "admin"`)
- Token/session handling: no expiry, no refresh, stored in localStorage
- CORS: `allow_origins=["*"]` in production config
- Severity: high

**S5 — OWASP Top 10 (static-detectable)**:
- A01 Broken Access Control: missing auth checks (covered by S4)
- A02 Cryptographic Failures: weak hashing (MD5/SHA1 for passwords), hardcoded salt
- A03 Injection: covered by S3
- A05 Security Misconfiguration: debug mode in prod configs, default credentials
- A06 Vulnerable Components: covered by S1
- A07 Auth Failures: covered by S4
- A09 Logging Failures: sensitive data in log statements (passwords, tokens, full request bodies)
- Severity: varies by item

#### 1b. Performance Dimension

**P1 — N+1 Query Patterns**:
- Database/API calls inside loops (for/while)
- ORM lazy loading in iteration context
- Severity: high

**P2 — Algorithmic Complexity**:
- Nested loops (≥3 depth) operating on collections
- Linear search where index/set lookup would suffice
- Full collection copy where slice/iterator would work
- Missing pagination on queries that return unbounded results
- Severity: high (nested loops on large data) / medium (suboptimal lookup)

**P3 — Resource Leaks**:
- File handles opened without `with` statement or explicit close
- Database connections not returned to pool
- Unclosed HTTP sessions / WebSocket connections
- Infinitely growing lists/dicts used as caches without eviction
- Severity: high (connection leak) / medium (file handle)

**P4 — Blocking Operations**:
- Synchronous I/O (`open()`, `requests.get()`) in async functions
- Large file read into memory at once (`file.read()` without chunking)
- `time.sleep()` in async context
- Severity: high (sync in async) / medium (large read)

**P5 — Redundant Computation**:
- Same function called with identical arguments in a loop
- Expensive operations (regex compile, JSON parse) inside hot loops
- Missing `@lru_cache` / `@functools.cache` on pure functions called repeatedly
- Severity: medium

### Step 2: Score and Classify

#### Finding Format
For each issue found:
```
- **[{severity}]** [{type}] `{file}:{line}` — {description}
  Fix: {concrete suggestion}
```

#### Scoring
- **Security Score** (0-100): Start at 100, deduct per finding:
  - critical: −20 per finding (floor at 0)
  - high: −10
  - medium: −5
  - low: −2
- **Performance Score** (0-100): Same deduction scale
- **Overall Score**: weighted average — Security × 0.6 + Performance × 0.4

If `--focus` is set, only the focused dimension contributes to Overall Score (100% weight).

### Step 3: Baseline Comparison

If a previous audit report exists in `.aion/audits/`:

1. Parse previous findings (by file:line + description hash)
2. Classify each current finding:
   - **NEW** — not in previous report
   - **PERSISTENT** — same finding exists in previous report
   - **REGRESSED** — was marked fixed in a previous report but reappeared
3. Classify previous findings not in current:
   - **FIXED** — existed before, no longer found
4. Output delta summary:
   ```
   Δ vs {previous_date}: +{N} new, −{N} fixed, {N} persistent, {N} regressed
   Score: {prev_overall} → {curr_overall} ({+N/-N} {↑/↓/→})
   ```

If no previous audit: "First audit — no baseline for comparison."

### Step 4: Rule Extraction (P1 — R6)

After scoring, check for patterns worth extracting as rules:

1. Scan findings for patterns that appear **≥ 2 times** across different files
2. For each recurring pattern:
   - Check `.aion/rules/security.md` or `.aion/rules/perf.md` — skip if already exists
   - Draft rule in standard format: `- **{Title}** (audit, {date}) [cite_count: 0, last_cited: {date}]`
3. Create `.aion/rules/security.md` or `.aion/rules/perf.md` if they don't exist (with standard frontmatter)
4. Append new rules (never overwrite existing)

### Step 5: Write Report

Write to `.aion/audits/{YYYY-MM-DD}.md`:

```markdown
---
date: {YYYY-MM-DD}
scope: {full | security | perf}
security_score: {N}
performance_score: {N}
overall_score: {N}
total_findings: {N}
critical: {N}
high: {N}
medium: {N}
low: {N}
---

# Audit Report — {YYYY-MM-DD}

## Scores
| Dimension | Score | Findings |
|-----------|-------|----------|
| Security | {N}/100 | {N} issues |
| Performance | {N}/100 | {N} issues |
| **Overall** | **{N}/100** | **{N} total** |

## Baseline Comparison
{delta summary or "First audit"}

## Security Findings
### Critical
- **[critical]** [S2] `config.py:15` — Hardcoded API key in source
  Fix: Move to environment variable, add to .gitignore

### High
...

### Medium
...

## Performance Findings
### High
...

### Medium
...

## Rules Extracted
- Added to `rules/security.md`: {rule title}
- Added to `rules/perf.md`: {rule title}

## Recommendations
1. {Top priority action}
2. {Second priority action}
3. {Third priority action}
```

## Next Steps

审计完成。如需修复发现的问题：
- 安全问题：直接修复，运行 `/project:aion-review` 审查后提交
- 性能问题：用 `/project:aion-think` 评估是否需要重构，或直接修复小问题
- 定期审计建议：每次大版本发布前运行一次

## Checklist
- [ ] Full codebase scanned (not just diffs)
- [ ] All S1-S5 security checks executed (or skipped via `--focus perf`)
- [ ] All P1-P5 performance checks executed (or skipped via `--focus security`)
- [ ] Every finding has file:line evidence and concrete fix suggestion
- [ ] Scores calculated with correct deduction weights
- [ ] Baseline comparison performed (if previous audit exists)
- [ ] Recurring patterns extracted as rules (≥ 2 occurrences)
- [ ] Report written to `.aion/audits/{date}.md`
- [ ] `# audit:ignore` markers respected
- [ ] Default exclusions applied (node_modules, vendor, etc.)

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Scanning only diffs instead of full codebase | Audit is project-level, not change-level — that's review's job | CRITICAL |
| Reporting findings without file:line evidence | Unverifiable findings waste developer time | HIGH |
| Reporting false positives without [UNVERIFIED] tag | Erodes trust in audit results | HIGH |
| Skipping baseline comparison when previous audit exists | Loses trend data — the most valuable part of recurring audits | MEDIUM |
| Extracting rules from one-off findings | Only patterns in ≥ 2 files are worth remembering as rules | MEDIUM |
| Including auto-generated files in scan | embedded.py, dist/, build/ produce noise, not insights | MEDIUM |
| Modifying code during audit | Audit is read-only analysis — use aion-fix or manual fix afterward | HIGH |

### Rationalization Prevention
| Excuse | Reality |
|--------|---------|
| "The codebase is too large, I'll sample a few files" | Audit means full scan. Skip with `--ignore` if needed, but don't sample silently |
| "This pattern looks fine in context" | If it matches a check, report it. Let the developer decide context |
| "No previous audit, so baseline comparison is pointless" | Still report "First audit" — next time there will be a baseline |
| "The score is already high, minor issues don't matter" | Every finding gets reported regardless of score — deductions are for prioritization |

## Output Format
Report written to `.aion/audits/{YYYY-MM-DD}.md` using the format defined in Step 5.

Conversation summary:
```
AUDIT: {scope}
─────────────────────────────
Security:     {N}/100  ({N} findings)
Performance:  {N}/100  ({N} findings)
Overall:      {N}/100

Δ: +{N} new, −{N} fixed, {N} persistent
Trend: {↑/↓/→} ({prev} → {curr})

Report: .aion/audits/{date}.md
Rules:  +{N} security, +{N} perf
─────────────────────────────
Top 3 Recommendations:
1. {action}
2. {action}
3. {action}
```

## Exit Status
- `DONE` — Audit completed, report written
- `DONE_WITH_CONCERNS` — Audit completed but critical findings exist (score < 50)
- `BLOCKED` — No source files found, or all files excluded by ignore patterns
- `NEEDS_CONTEXT` — Cannot determine project tech stack (no manifest files found)
