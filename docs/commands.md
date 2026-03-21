# Command Reference

All commands are invoked as `/project:aion-{name}` in Claude Code.

## /project:aion-design

**Purpose**: Turn ideas into structured requirement specs.

**Arguments**: Optional description of what to build.

**What it does**:
1. Reads `.aion/rules/` to avoid designing around known pitfalls
2. Reads `.aion/refs/` and `.aion/prototypes/` for external context
3. Guides you through requirements clarification
4. Produces a spec file in `.aion/specs/{name}.md`

**Examples**:
```
/project:aion-design Add user authentication with OAuth
/project:aion-design                  # Interactive mode
```

---

## /project:aion-demo

**Purpose**: Generate interactive single-file HTML prototypes for UI features. Optional step between design and plan.

**Arguments**: Optional spec name, image path, URL, or feature description.

**What it does**:
1. Reads spec from `.aion/specs/` (or accepts image / URL / free-form description)
2. Reads `.aion/rules/` for style conventions
3. Checks for existing prototypes (avoids silent overwrites)
4. Shows prototype plan and gets user confirmation
5. Generates self-contained HTML prototype in `.aion/prototypes/{name}/index.html`

**Examples**:
```
/project:aion-demo login-page           # Prototype from spec
/project:aion-demo                       # Uses most recent spec
/project:aion-demo from image ./mockup.png   # From design image
/project:aion-demo from url https://example.com  # From reference site
/project:aion-demo update dashboard      # Update existing prototype
/project:aion-demo mobile checkout       # With phone frame
```

---

## /project:aion-plan

**Purpose**: Create step-by-step implementation plans from specs.

**Arguments**: Optional spec file name or feature description.

**What it does**:
1. Reads the target spec from `.aion/specs/`
2. Explores the codebase to understand existing architecture
3. Designs implementation steps with file lists and dependencies
4. Produces a plan file in `.aion/plans/{name}.md`

**Examples**:
```
/project:aion-plan auth.md            # Plan for specific spec
/project:aion-plan                    # Uses most recent spec
```

---

## /project:aion-impl

**Purpose**: Execute implementation plans, writing production code.

**Arguments**: Optional plan file name or step number.

**What it does**:
1. Reads plan, spec, rules, contracts, and prototypes
2. Implements code changes step by step
3. Updates plan progress markers (○ → 🔄 → ✅)
4. Runs verification strategy after each step

**Examples**:
```
/project:aion-impl                    # Continue from current step
/project:aion-impl auth.md           # Implement specific plan
/project:aion-impl step 3            # Start from step 3
```

---

## /project:aion-test

**Purpose**: Generate comprehensive tests, analyze coverage, create performance scripts, and validate UI structure.

**Arguments**: Optional mode (coverage, perf, ui, full) and options (--incremental, --comprehensive).

**What it does**:
1. Detects project test framework and conventions from existing tests
2. Reads spec/plan for acceptance criteria (or scans source in code-first mode)
3. Generates unit + integration tests following existing patterns
4. Optionally: runs coverage analysis, generates k6/locust scripts, audits UI/a11y

**Examples**:
```
/project:aion-test                       # Generate tests for current plan scope
/project:aion-test coverage              # Coverage analysis + gap-filling tests
/project:aion-test perf                  # Generate k6/locust scripts
/project:aion-test ui                    # UI checklist + accessibility audit
/project:aion-test full                  # All modes
/project:aion-test src/auth              # Code-first: test this module (no spec needed)
/project:aion-test auth --comprehensive  # Full test suite for auth feature
```

---

## /project:aion-review

**Purpose**: Review code changes with scoring and auto-learning.

**Arguments**: Optional file list or "all".

**What it does**:
1. Reviews all uncommitted changes (or specified files)
2. Scores on 3 dimensions: quality (40%), security (30%), architecture (30%)
3. Produces verdict: `approved` (≥70, no criticals) or `needs_fix`
4. Auto-extracts reusable rules to `.aion/rules/`
5. Writes review to `.aion/reviews/{name}.md`

**Examples**:
```
/project:aion-review                  # Review all changes
/project:aion-review src/auth/        # Review specific directory
```

---

## /project:aion-learn

**Purpose**: Deep-dive rule extraction from recent work. Core differentiator.

**Arguments**: Optional context source.

**What it does**:
1. Collects evidence (git diff, reviews, conversation)
2. Identifies candidate rules (pitfalls, style, perf)
3. Deduplicates against existing rules
4. Writes new rules to `.aion/rules/`
5. Reports what was learned

**Examples**:
```
/project:aion-learn                   # Analyze recent changes
/project:aion-learn from last review  # Extract from latest review
/project:aion-learn error handling    # Deep-dive on topic
```

---

## /project:aion-save

**Purpose**: Save conversation context to `.aion/` before it's lost.

**Arguments**: Optional type filter (spec, plan, rules, changelog).

**What it does**:
1. Analyzes conversation for important information
2. Routes to appropriate `.aion/` files by type
3. Appends (never overwrites) existing content
4. Deduplicates to avoid redundancy

**Examples**:
```
/project:aion-save                    # Save everything relevant
/project:aion-save spec              # Only save requirement info
/project:aion-save rules             # Only extract rules
```

---

## /project:aion-commit

**Purpose**: Safe git commit with changelog update.

**Arguments**: Optional context or "amend".

**What it does**:
1. Shows change summary and proposed commit message
2. Waits for user confirmation (never auto-commits)
3. Stages and commits
4. Updates `.aion/changelog.md`

**Safety**: Never pushes, never force-resets, never commits secrets.

**Examples**:
```
/project:aion-commit                  # Normal commit flow
/project:aion-commit amend           # Amend last commit
```

---

## /project:aion-status

**Purpose**: Show project intelligence overview.

**What it does**:
1. Counts rules by category
2. Lists project documents with status
3. Shows recent changelog entries
4. Shows git status and recent commits

**Examples**:
```
/project:aion-status
```

---

## /project:aion-help

**Purpose**: Show available commands, recommended workflows, and usage guidance.

**Arguments**: Optional command name, `workflow`, or `quick`.

**What it does**:
1. Shows all 16 commands grouped by phase (Planning / Execution / Quality / Learning / Operations)
2. Recommends workflows by scenario (new feature, bug fix, onboarding, testing, refactoring)
3. Shows individual command detail with examples
4. Provides a one-liner cheat sheet

**Examples**:
```
/project:aion-help                    # Full overview + scenarios
/project:aion-help design             # Detail for aion-design
/project:aion-help workflow           # Workflow diagrams
/project:aion-help quick              # Cheat sheet
```

---

## /project:aion-bug

**Purpose**: Manage bug reports — create, list, assign, close, reopen, and track statistics.

**Arguments**: Sub-command: `report` (default), `list`, `assign`, `close`, `reopen`, `stats`.

**What it does**:
1. `report`: Guides tester through bug description, auto-classifies (frontend/backend/mixed), auto-assigns via git blame + team.yml, checks risk keywords, enforces Evidence
2. `list`: Shows bugs with filters (category, status, assignee, severity)
3. `assign`: Manually assigns a bug (mainly for X-type mixed bugs)
4. `close/reopen`: Manages bug lifecycle
5. `stats`: Shows statistics including team load and resolution times

**Bug ID Format**: `{Category}-{MMDD}-{SEQ}` (e.g., `F-0321-001` = Frontend bug, Mar 21, #1)

**Examples**:
```
/project:aion-bug report              # Create a new bug report
/project:aion-bug list --category=F   # List frontend bugs
/project:aion-bug list --status=open  # List open bugs
/project:aion-bug assign X-0321-001 @张三  # Assign mixed bug
/project:aion-bug close F-0321-001    # Close a fixed bug
/project:aion-bug stats               # View statistics
```

---

## /project:aion-crosscheck

**Purpose**: Use a different AI model to analyze code and discover issues the primary model might miss.

**Arguments**: `--model {name}` (required), `--scope {dir-or-file}` (optional, defaults to changed files).

**What it does**:
1. Reads model config from `.aion/team.yml`
2. Sends code to the specified model's API for analysis
3. Parses and validates findings
4. Generates bug reports in `.aion/bugs/` with `source_model` field set

**Examples**:
```
/project:aion-crosscheck --model gemini --scope src/pages/
/project:aion-crosscheck --model gpt --scope src/api/
/project:aion-crosscheck --model deepseek           # Analyzes changed files
```
