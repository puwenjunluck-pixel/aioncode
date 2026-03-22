# /project:aion-scan — 项目扫描与冷启动

Scan an existing project to bootstrap AionCode intelligence. Analyze codebase structure, conventions, and test coverage, then generate tailored artifacts based on user intent.

$ARGUMENTS — Optional: intent keyword(s) to skip the interactive question. E.g., "test", "frontend", "backend", "feature", "refactor". If empty, scan first then ask.

## Role

You are a **senior architect onboarding onto an existing codebase**. Your job is to quickly understand a project's structure, conventions, and gaps, then produce actionable artifacts that make AI-assisted work immediately effective. You are thorough but efficient — scan what matters, skip what doesn't.

> ⚠️ **CRITICAL**: NEVER assume project conventions — discover them from evidence. NEVER generate generic checklists — every item must be grounded in this project's actual stack, patterns, and structure. On RE_SCAN, NEVER overwrite existing rules or user-customized checklists — follow the Write Protocol (`.aion/refs/write-protocol.md`).

## Steps

### Step 0: Pre-flight Check
1. Verify `.aion/` directory exists. If not, tell the user to install AionCode first (`bash install.sh` or via Dashboard), then exit with `BLOCKED`.
2. Read `.aion/rules/` — check if rules already exist
3. Read `.aion/refs/` — check if architecture docs already exist
4. Read `.aion/refs/write-protocol.md` — load Write Protocol for Steps 3-5
5. **Determine scan mode**:
   - Rules files contain only frontmatter (no rule entries) AND `refs/architecture.md` does not exist → **FIRST_SCAN**
   - Otherwise → **RE_SCAN**
   Record this mode — it controls write behavior in Steps 3, 4, and 5.

### Step 1: Deep Scan

Scan the project systematically. For medium-to-large projects, consider using the Agent tool (subagent_type=Explore) to parallelize independent scan dimensions — e.g., one agent for code structure + conventions, another for test landscape + CI/CD. For small projects, sequential scanning is fine.

#### 1a. Project Identity
- Read `README.md`, `CONTRIBUTING.md`, `ARCHITECTURE.md` (if they exist)
- Read `package.json` / `requirements.txt` / `go.mod` / `Cargo.toml` / `pom.xml` / `build.gradle` — identify tech stack, dependencies, scripts
- Read `docker-compose.yml` / `Dockerfile` — understand deployment model
- Read `.env.example` / `.env.template` — understand config structure

#### 1b. Code Structure
- Run `find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.vue" -o -name "*.py" -o -name "*.go" -o -name "*.java" -o -name "*.rs" | head -100` — understand file distribution
- Use Glob to map the top-level directory structure (2 levels deep)
- Identify entry points: `main.ts`, `index.ts`, `app.py`, `main.go`, etc.
- Identify routing files: `router/`, `routes/`, URL patterns
- Identify state management: stores, reducers, context

#### 1c. Conventions
- Read `.eslintrc*`, `.prettierrc*`, `tsconfig.json`, `.editorconfig`, `setup.cfg`, `pyproject.toml` — extract coding standards
- Read 2-3 representative source files to observe naming, patterns, structure
- Run `git log --oneline -30` — understand commit message style
- Check for monorepo indicators: `workspaces`, `lerna.json`, `nx.json`, `turbo.json`

#### 1d. Test Landscape
- Glob for test files: `**/*.test.*`, `**/*.spec.*`, `**/test_*.py`, `**/*_test.go`, `**/tests/**`
- Read test config: `jest.config.*`, `vitest.config.*`, `pytest.ini`, `conftest.py`
- Count test files vs source files — rough coverage indicator
- Identify test framework and patterns from 1-2 sample test files

#### 1e. CI/CD
- Read `.github/workflows/*.yml`, `Jenkinsfile`, `.gitlab-ci.yml`, `.circleci/config.yml`
- Identify: what gets tested, what gets deployed, what checks run on PR

#### 1f. API Surface (if applicable)
- Search for API route definitions: `@app.route`, `router.get`, `@Get()`, `http.HandleFunc`
- Search for database models/schemas: `@Entity`, `class.*Model`, `CREATE TABLE`, migration files
- Check for API docs: `swagger`, `openapi`, GraphQL schema files

### Step 2: Determine Intent

If `$ARGUMENTS` specifies an intent, use it directly. Otherwise, present a question:

"I've completed the project scan. What do you want to use AI for?

A) **补测试** — Generate test plan and test cases for existing code
B) **迭代前端** — Iterate on frontend UI and components
C) **迭代后端** — Iterate on backend API and business logic
D) **新功能开发** — Full-stack feature development
E) **重构/优化** — Refactoring or performance optimization
F) **全面扫描** — Generate all of the above

You can choose multiple (e.g., A+C). **Recommended**: based on the scan, I suggest {recommendation} because {reason}."

The recommendation should be based on what the scan revealed (e.g., if tests are sparse, recommend A; if it's a frontend-heavy project, recommend B).

### Step 3: Generate Architecture Reference

Follow Write Protocol category: **Regenerable**.

**FIRST_SCAN**: Write `.aion/refs/architecture.md` with fingerprint appended at end of file.

**RE_SCAN**: Read existing `architecture.md`, verify fingerprint:
- Hash match (unmodified) → regenerate silently with updated content and new fingerprint
- Hash mismatch (user-modified) → show diff summary of changes, ask: "Update architecture reference? [Y/Keep existing/Replace]"
- No fingerprint (legacy) → treat as user-modified, ask before overwriting

Architecture file format:

```markdown
# Project Architecture

## Tech Stack
- Language: {detected}
- Framework: {detected}
- Database: {detected or N/A}
- Test Framework: {detected}
- Build Tool: {detected}
- CI/CD: {detected or N/A}

## Directory Structure
{key directories with one-line descriptions}

## Entry Points
- {main entry files}

## Key Patterns
- {routing pattern}
- {state management pattern}
- {data access pattern}

## Build & Run
- Dev: {command}
- Test: {command}
- Build: {command}
- Lint: {command}
```

### Step 4: Generate Rules

Follow Write Protocol category: **Accumulative**.

**FIRST_SCAN**: Generate initial rules based on scan findings. Write to `.aion/rules/`:

**style.md** — Extracted from linter configs, existing code patterns:
```markdown
- **{Convention}** (scan, {date}) [cite_count: 0, last_cited: {date}]
  {Description with concrete example from this project}
```

**pitfalls.md** — Extracted from git log fix commits and code patterns:
```markdown
- **{Known issue}** (scan, {date}) [cite_count: 0, last_cited: {date}]
  {Description of the pitfall and how to avoid it}
```

Only write rules that are project-specific and evidenced. If you can't find evidence for a rule, don't write it.

**RE_SCAN**: Do NOT regenerate or overwrite existing rules. Instead:
1. Read all existing rules (MANDATORY — Write Protocol Refusal Condition applies)
2. Compare scan findings against existing rules
3. If scan reveals conventions NOT covered by existing rules → propose additions (append only), show each candidate to user
4. If scan reveals existing rules that may be outdated → note them but do NOT modify — suggest running `/aion-learn` to update
5. Never overwrite or replace existing rule entries

### Step 5: Generate Intent-Specific Artifacts

> **RE_SCAN write rules for intent-specific artifacts**:
> - **Checklists** (`checklists/*.md`): Follow Write Protocol category: Regenerable. Verify fingerprint — if user-modified (hash mismatch), skip regeneration. Only create missing checklists.
> - **Refs** (`refs/*.md`): Follow Write Protocol category: Regenerable. Verify fingerprint before overwriting.
> - **Specs** (`specs/*.md`): Follow Write Protocol category: Versioned. Check for existing file, apply version/scope conflict handling.
> - **Contracts** (`contracts/*.md`): Follow Write Protocol category: Regenerable.

#### Intent A: 补测试

1. Write `.aion/specs/test-coverage.md`:
   ```markdown
   # Test Coverage Analysis

   ## Current State
   - Test files: {count}
   - Source files: {count}
   - Estimated coverage: {rough %}
   - Framework: {name}

   ## Untested Modules (High Priority)
   {modules with business logic but no tests, sorted by importance}

   ## Untested Modules (Medium Priority)
   {utility modules, helpers, etc.}

   ## Existing Test Patterns
   {patterns observed in existing tests — mock style, assertion style, setup/teardown}
   ```

2. Write `.aion/checklists/test-plan.md`:
   ```markdown
   # Test Plan

   ## Unit Tests
   {per-module checklist with specific test scenarios derived from reading the code}
   - [ ] {module}: {scenario 1}
   - [ ] {module}: {scenario 2}

   ## Integration Tests
   - [ ] {API endpoint / service interaction}: {scenario}

   ## E2E Tests (if applicable)
   - [ ] {user flow}: {steps}
   ```

3. Write `.aion/rules/test-style.md`:
   ```markdown
   # Test Style Rules

   {extracted from existing tests, or derived from project config}
   - **{Rule}** (scan, {date})
     {e.g., "Use vitest + @testing-library/vue, not manual DOM queries"}
   ```

#### Intent B: 迭代前端

1. Write `.aion/refs/component-map.md`:
   ```markdown
   # Component Map

   ## Routes
   {path → component mapping}

   ## Component Tree
   {key components with their props/dependencies}

   ## State Management
   {stores/reducers and what they manage}

   ## Design Tokens
   {CSS variables, theme, breakpoints if detected}
   ```

2. Write `.aion/checklists/frontend.md`:
   ```markdown
   # Frontend Iteration Checklist

   ## Before Changes
   - [ ] Read the target component and its parent
   - [ ] Check props interface / type definitions
   - [ ] Check related store/state
   - [ ] Read .aion/rules/ for style constraints

   ## During Changes
   - [ ] {project-specific items based on scan, e.g.:}
   - [ ] Use CSS variables from {file} (don't hardcode colors)
   - [ ] Follow {naming convention} for new components
   - [ ] New routes need entry in {router file}

   ## After Changes
   - [ ] Visual check in browser
   - [ ] Responsive test (if applicable)
   - [ ] No console errors
   ```

3. Write `.aion/contracts/api-interface.md` (if backend exists):
   ```markdown
   # API Interface Contract

   {endpoint → request/response shape, extracted from code}
   ```

#### Intent C: 迭代后端

1. Write `.aion/refs/api-inventory.md`:
   ```markdown
   # API Inventory

   ## Endpoints
   {method, path, handler, auth requirement}

   ## Database Schema
   {tables/models and their relationships}

   ## Middleware / Interceptors
   {what runs on each request}
   ```

2. Write `.aion/checklists/backend.md`:
   ```markdown
   # Backend Iteration Checklist

   ## Before Changes
   - [ ] Read the target module and its dependencies
   - [ ] Check database schema / models involved
   - [ ] Read .aion/rules/

   ## During Changes
   - [ ] {project-specific items, e.g.:}
   - [ ] New endpoints registered in {router file}
   - [ ] Database changes need migration in {migrations dir}
   - [ ] Error responses follow {existing pattern}
   - [ ] Auth/permission checks where needed

   ## After Changes
   - [ ] Run tests: {test command}
   - [ ] Check for N+1 queries
   - [ ] Verify error handling paths
   ```

3. Write `.aion/refs/db-schema.md` (if database detected):
   ```markdown
   # Database Schema

   {models/tables, fields, relationships, indexes}
   ```

#### Intent D: 新功能开发

Generate all artifacts from B + C, plus:

1. Write `.aion/checklists/feature.md`:
   ```markdown
   # Full-Stack Feature Checklist

   ## Design Phase
   - [ ] Spec written to .aion/specs/
   - [ ] API contract defined in .aion/contracts/
   - [ ] UI prototype in .aion/prototypes/ (if visual)

   ## Plan Phase
   - [ ] Backend steps (models → services → routes → tests)
   - [ ] Frontend steps (types → store → components → integration)

   ## Implementation
   - [ ] Backend API implemented and tested
   - [ ] Frontend connected to API
   - [ ] Error states handled (loading, empty, error)

   ## Verification
   - [ ] {project test command} passes
   - [ ] Manual E2E test
   - [ ] Edge cases covered
   ```

#### Intent E: 重构/优化

1. Write `.aion/specs/refactor-targets.md`:
   ```markdown
   # Refactor Targets

   ## Code Smells Detected
   {large files, deep nesting, duplicated logic, etc. — with file:line references}

   ## Dependency Issues
   {circular imports, heavy unused deps, outdated packages}

   ## Performance Concerns
   {N+1 queries, missing indexes, large bundle, etc.}
   ```

2. Write `.aion/checklists/refactor.md`:
   ```markdown
   # Refactor Checklist

   - [ ] Identify the refactor scope (don't boil the ocean)
   - [ ] Write tests for current behavior FIRST
   - [ ] Refactor in small, testable steps
   - [ ] Run tests after each step
   - [ ] No behavior changes unless explicitly intended
   - [ ] {project-specific items}
   ```

#### Intent F: 全面扫描

Generate all artifacts from A through E. This is comprehensive but takes longer.

### Step 6: Report

**FIRST_SCAN** — Present generation summary:

```
Scan Complete
-----------------------------------
Project: {name} ({tech stack summary})
Intent: {selected intent(s)}

Generated:
  refs/architecture.md    ← Project architecture overview
  rules/style.md          ← {N} conventions extracted
  rules/pitfalls.md       ← {N} pitfalls identified
  {intent-specific files with one-line descriptions}

Quick Start:
  {1-2 sentences on what to do next based on intent}
```

**RE_SCAN** — Present a Delta Report (MANDATORY):

```
Delta Report
-----------------------------------
Project: {name} | Mode: RE_SCAN

New findings:
  - {concrete new discoveries, e.g., "2 new API endpoints (POST /users, DELETE /users/:id)"}
  - {e.g., "1 new dependency (redis)"}

Updated:
  - {file}: {what changed and why, e.g., "refs/architecture.md: Auth module restructured (fingerprint mismatch, user confirmed)"}

Skipped (protected):
  - {file}: {reason, e.g., "checklists/backend.md: user-customized (fingerprint mismatch)"}
  - {file}: {reason, e.g., "rules/style.md: 3 existing rules, no new conventions found"}

Suggested follow-up:
  - {e.g., "Run /aion-learn to update potentially stale rules"}
```

## Next Steps

Based on intent:
- Testing → /project:aion-impl with the test plan
- Frontend/Backend iteration → /project:aion-design for new features, or /project:aion-impl for planned changes
- New feature → /project:aion-design to start the full workflow
- Refactor → /project:aion-plan to plan the refactoring steps

## Checklist
- [ ] `.aion/` existence verified
- [ ] Scan mode determined (FIRST_SCAN or RE_SCAN)
- [ ] Write Protocol loaded from `.aion/refs/write-protocol.md`
- [ ] Project identity scanned (README, package manifest)
- [ ] Code structure mapped (directories, entry points)
- [ ] Conventions extracted (linter configs, code patterns, commit style)
- [ ] Test landscape analyzed (files, framework, coverage gaps)
- [ ] CI/CD configuration reviewed
- [ ] User intent determined
- [ ] Architecture reference written (fingerprint appended)
- [ ] Rules: FIRST_SCAN = generated with evidence; RE_SCAN = existing rules read, only new appended
- [ ] Intent-specific artifacts follow Write Protocol per category
- [ ] RE_SCAN: Delta Report presented with new/updated/skipped/suggested sections
- [ ] All artifacts are project-specific, not generic

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Writing generic checklists not grounded in the project | Users get no value from "write good code" — they need "use {this framework} pattern from {this file}" | CRITICAL |
| Assuming conventions without evidence | Wrong conventions are worse than no conventions | CRITICAL |
| Scanning too deeply (reading every file) | Scan should be fast — read representative samples, not everything | HIGH |
| Skipping test landscape analysis | Test gaps are the #1 reason existing projects adopt AI tooling | HIGH |
| Not asking user intent | Generating everything wastes time; targeted output is more useful | MEDIUM |
| Overwriting existing rules/refs on RE_SCAN | Write Protocol Refusal Condition: must read existing files and verify fingerprint/dedup before writing | CRITICAL |
| RE_SCAN without Delta Report | User cannot assess what the re-scan discovered vs what was protected | HIGH |

## Output Format
The scan report shown in Step 6, plus all generated files in `.aion/`.

## Exit Status
- `DONE` — Scan completed, all artifacts generated for selected intent(s)
- `DONE_WITH_CONCERNS` — Scan completed but some areas couldn't be analyzed (e.g., no tests found, no CI config)
- `BLOCKED` — `.aion/` not initialized, or project directory is empty
- `NEEDS_CONTEXT` — User needs to clarify intent before artifacts can be generated
