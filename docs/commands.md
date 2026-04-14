# Command Reference

All commands are invoked as `/project:aion-{name}` in Claude Code (or `/aion-{name}` in Antigravity).

> Full, up-to-date details are always available via `/project:aion-help` inside Claude Code. This document is a summary.

---

## /project:aion-scan

**Purpose**: Cold-start scanning of an existing codebase. Builds initial `.aion/` context (rules, refs, specs).

**Arguments**: Optional scope (path), or `--url <url>` / `--file <path>` to import external docs.

**Examples**:
```
/project:aion-scan                    # Full project
/project:aion-scan src/api            # Specific directory
/project:aion-scan --file docs/PRD.pdf  # Import a PDF
/project:aion-scan --url https://...    # QA / scan a live site
```

---

## /project:aion-think

**Purpose**: Discussion · collision · thinking · goal alignment. 10-phase brainstorming that turns ideas into a structured spec. Main entry point for any non-trivial feature or 3+ file changes.

**Flow**: Phase 0 (quick note) → 1–4 (approach exploration + convergence) → 5 (challenge the chosen path) → 6–9 (spec writing + user approval at Phase 9) → Phase 10 (hands off to `aion-plan` automatically).

**Arguments**: Optional description; `--file` to import docs.

**Examples**:
```
/project:aion-think Add OAuth login
/project:aion-think                   # Interactive mode
/project:aion-think --file spec.docx
```

---

## /project:aion-plan

**Purpose**: Bite-sized implementation plan (2–5 min / step, TDD-oriented). Usually triggered automatically by `aion-think` Phase 10; invoke directly only to modify an existing plan.

**Examples**:
```
/project:aion-plan auth               # Modify plan for auth spec
/project:aion-plan                    # Most recent spec
```

---

## /project:aion-review

**Purpose**: Review uncommitted changes with a Verification Gate (evidence before claims). Scores on quality / security / architecture, auto-extracts reusable rules to `.aion/rules/`, writes a review file to `.aion/reviews/`.

**Arguments**: Optional file list or scope.

**Examples**:
```
/project:aion-review                  # All uncommitted changes
/project:aion-review src/auth/        # Specific directory
```

---

## /project:aion-fix

**Purpose**: Bug fix. Strongly recommend `--deep` (4-phase root-cause analysis) unless the bug is trivial. Consumes `.aion/bugs/{BUG-ID}` when given an ID.

**Examples**:
```
/project:aion-fix F-0414-001          # Fix a specific bug
/project:aion-fix --deep              # Root-cause mode
/project:aion-fix "login fails on Safari"
```

---

## /project:aion-qa

**Purpose**: Browser-based QA testing. Drives a headless browser (gstack `browse` CLI or Playwright MCP fallback) to exercise the app, logs findings as bug reports in `.aion/bugs/`.

**Examples**:
```
/project:aion-qa                      # Interactive QA session
/project:aion-qa --url http://localhost:3000
/project:aion-qa --auto               # Non-interactive mode
```

---

## /project:aion-audit

**Purpose**: Security + performance audit. Looks for OWASP Top 10 class issues, perf regressions, and architectural risk.

**Examples**:
```
/project:aion-audit                   # Full audit
/project:aion-audit src/api/          # Scoped audit
```

---

## /project:aion-loop

**Purpose**: Automated pipeline — run `think → plan → impl → review → commit` end-to-end with minimal user intervention. `--auto` skips non-destructive confirmations; commit still asks before pushing.

---

## /project:aion-commit

**Purpose**: Safe git commit. Requires a passing review and the Verification Gate (Iron Law 2: evidence before claims). Never pushes automatically, never force-resets, never commits secrets.

---

## /project:aion-save

**Purpose**: Save conversation context to `.aion/` before it is lost. Routes to spec / plan / rules / changelog by type. Always appends, never overwrites.

**Examples**:
```
/project:aion-save                    # Save everything relevant
/project:aion-save rules              # Only extract rules
```

---

## /project:aion-help

**Purpose**: List all installed commands, recommended workflows (by scenario), and per-command detail.

**Examples**:
```
/project:aion-help                    # Overview
/project:aion-help think              # Detail for aion-think
/project:aion-help workflow           # Workflow diagrams
```

---

## Recommended Workflows

- **New feature**: `think → plan (auto) → impl → review → commit`
- **Existing code**: `scan → think → plan (auto) → impl → review → commit`
- **Bug fix**: `fix --deep {BUG-ID} → review → commit`
- **QA loop**: `qa → fix → review → commit`
