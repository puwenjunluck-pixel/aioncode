# /project:aion-scan — 项目扫描与冷启动

Scan an existing project to bootstrap AionCode intelligence. Analyze codebase structure, conventions, and test coverage, then generate tailored artifacts based on user intent.

$ARGUMENTS — Optional: intent keyword(s) to skip the interactive question. E.g., "test", "frontend", "backend", "feature", "refactor". If empty, scan first then ask. Options: `--file {path}` import external documents (.docx/.pdf/.md/.txt/.pptx/.xlsx) as supplementary context for the scan. `--url {target_url}` specify the running application URL for browser exploration (requires Playwright MCP).

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

### Step 1.5: File Import (conditional — when `--file` is specified)

When `$ARGUMENTS` contains `--file {path}`:

1. **Convert to markdown**: Use markitdown skill to convert external documents (.docx/.pdf/.md/.txt/.pptx/.xlsx → markdown). If directory, batch convert all supported files.
2. **Classify content**: Identify document type:
   - Requirements / PRD → extract features, user stories, constraints
   - Architecture / Design → extract modules, tech stack, dependencies
   - API documentation / Swagger → extract endpoints, schemas, error codes
   - Mixed → classify by sections
3. **Merge with scan data**: Use extracted information to supplement the Deep Scan findings. Mark supplemented items `[from:file]`.
4. **Report**: "从 {N} 个文件中导入了补充上下文：{N} 项需求, {N} 个模块, {N} 个 API 端点"

### Step 1.7: Browser Exploration (conditional — Playwright MCP + running service)

Explore the running application through a browser to discover UI structure, navigation flows, and dynamic content that static code analysis cannot reveal.

**Prerequisites check**:
1. Check for Playwright MCP availability (look for browser-control MCP tools: `playwright_navigate`, `playwright_click`, `playwright_screenshot`)
2. Determine target URL:
   - If `--url` specified in `$ARGUMENTS` → use that
   - If not → try to detect from code: `package.json` scripts (dev/start), Docker config, Python server config
   - If cannot determine → ask user: "检测到 Playwright MCP，是否有可访问的开发环境？请提供 URL（如 http://localhost:3000）"
3. Verify URL is reachable (HTTP GET, check for 200/301/302)

**If Playwright MCP available AND URL reachable** → Live Exploration:

1. **Navigate to home page**, take full-page screenshot
2. **Map navigation structure**:
   - Identify all navigation elements (nav bars, sidebars, menus, tabs)
   - Click each navigation item, record: label, target URL/view, page title
   - Screenshot each view
3. **Explore key pages** (up to 15 pages):
   - Record: page title, key UI elements (buttons, forms, tables, lists)
   - Identify form fields: labels, types, required status, validation hints
   - Check states: empty state, loading indicator, error display
4. **Check responsive behavior**: Switch to mobile viewport (375×667), screenshot home page and one content page
5. **Handle login** (if encountered):
   - Detect login page (form with password field)
   - Ask user: "系统需要登录。请提供测试账号，或在弹出的浏览器中手动登录后告知我继续。"
   - After login, continue exploration
6. **Save screenshots** to `.aion/refs/screenshots/` (create directory if needed)
7. **Output**: UI Discovery Report

```markdown
# UI Discovery Report

## Navigation Structure
| Label | URL/View | Type | Notes |
|-------|---------|------|-------|
| {nav label} | {path} | {page|modal|tab} | {key elements} |

## Pages Discovered ({N} total)
| Page | Key Elements | Forms | States Observed |
|------|-------------|-------|-----------------|
| {page name} | {buttons, tables, lists} | {form fields} | {empty/loading/error} |

## Forms & Inputs
| Page | Field | Type | Required | Validation |
|------|-------|------|----------|-----------|

## Responsive Notes
- {observations about mobile layout}

## Screenshots
- {path to each screenshot with description}
```

**If NO Playwright MCP OR URL not reachable** → Static UI Analysis:

1. Read HTML templates / JSX / Vue / Svelte files → extract page structure
2. Read frontend router config → extract navigation/URL map
3. Read CSS/SCSS → identify responsive breakpoints, theme variables
4. Read API call patterns in frontend code → infer data fetching
5. Output: Static UI Analysis Report (same structure, marked `[from:static]`)

> Note: Static analysis misses dynamic content, JS-rendered elements, and actual runtime states. Suggest user provides `--url` for better results.

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

### Step 3.5: Generate _product.md (Product Design Document)

Cross-reference all scan data (code scan + file import + browser exploration) to generate the product design document.

**Source fusion**:
- **Code scan** (Step 1) → tech stack, modules, API endpoints, database models
- **File import** (Step 1.5, if used) → business requirements, user stories, architecture decisions
- **Browser exploration** (Step 1.7, if performed) → UI pages, navigation flows, forms, states
- **Cross-analysis**: Map code modules ↔ UI pages, API routes ↔ frontend calls, DB models ↔ business entities

**Write `.aion/specs/_product.md`**:

Follow Write Protocol category: **Versioned**.

1. **If FIRST_SCAN or `_product.md` does not exist** → Create full document:
   - 产品定位: Infer from README, package description, UI title. Mark `[INFERRED]` if uncertain.
   - 功能地图: One row per discovered module/feature. Sources tagged `[from:code]` / `[from:explore]` / `[from:file]`.
   - 核心业务流程: Infer from navigation flows (browser) or route structure (code). Mark `[INFERRED]`.
   - 模块架构: From directory structure + import analysis. Tag `[from:code]`.
   - 技术栈: From manifest files. Tag `[CONFIRMED]` (these are factual).
   - 数据模型: From DB models/migrations if found. Tag `[from:code]`.
   - Set `generation_method` in frontmatter based on which sources were used.
   - Set `confidence`: `high` (all 3 sources), `medium` (2 sources), `low` (code only).

2. **If RE_SCAN and `_product.md` exists** → Incremental update:
   - Read existing document, preserve all `[CONFIRMED]` entries
   - Add newly discovered modules/pages/endpoints
   - Update tech stack if versions changed
   - Mark new entries with source tags

**Frontmatter**:
```yaml
---
product: {project name}
updated_at: {YYYY-MM-DD}
generation_method: {scan | scan+file | scan+explore | scan+file+explore}
confidence: {high | medium | low}
sources:
  - code-scan
  - file-import (if used)
  - browser-explore (if performed)
---
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

### Step 6.5: AI Q&A — Confirm Product Design (always, when _product.md was generated/updated)

After the scan report, present the `_product.md` content to the user for confirmation:

1. **Show all `[INFERRED]` items** grouped by section:
   ```
   我从扫描中推断了以下产品信息，请确认或纠正：

   产品定位：
   - 目标用户：{推断} [INFERRED]
   - 核心价值：{推断} [INFERRED]

   功能地图中不确定的项：
   - {模块}: {推断的功能描述} [INFERRED]

   业务流程中不确定的项：
   - {流程}: {推断的步骤} [INFERRED]

   请回复需要修正的项，或回复"确认"接受所有推断。
   ```

2. **Process user response**:
   - User confirms → update all `[INFERRED]` → `[CONFIRMED]`
   - User corrects → apply corrections, mark corrected items `[CONFIRMED]`
   - User adds new info → append to relevant sections, mark `[from:user]` `[CONFIRMED]`

3. **Update `_product.md`** with confirmed content, update `confidence` level

> This step ensures the product design document is not just AI guesswork but validated knowledge. Every scan produces a Q&A round — the more the user confirms, the higher the confidence.

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
