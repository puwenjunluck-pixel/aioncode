# /project:aion-plan — 修订实现方案

Revise or add implementation steps to an existing plan. Use this when requirements are already captured (by /project:aion-design) but the implementation approach needs to be created or changed.

$ARGUMENTS — Optional: plan file name or feature description. If empty, use the most recent plan in `.aion/plans/`.

## Role

You are a **senior architect who reads code before designing**. You never plan in a vacuum — you explore the codebase first, understand existing patterns, and design implementation steps that respect what's already there.

> ⚠️ **CRITICAL**: NEVER plan without reading code first. Plans based on assumptions WILL be wrong. Violating this is the #1 cause of failure for this command.

> 遵循 `.aion/refs/command-conventions.md` 中的共享约定（提问方式、Evidence 要求、Completeness 原则、Stack 检测）。

## Steps

### Step 0: Context Loading (Lazy — ONLY read target plan)
1. **Find target plan**:
   - If `$ARGUMENTS` names a plan → read `.aion/plans/{name}.md`
   - If `$ARGUMENTS` is empty → use most recent plan in `.aion/plans/`
   - **Legacy fallback**: If `$ARGUMENTS` points to a file in `.aion/specs/` (old format spec) → read that spec file and treat its content as requirements for a new plan
   - If not found → check `.aion/plans/archive/INDEX.md`
   - If still not found → `BLOCKED`: "No plan found. Run /project:aion-design first."
2. **Determine mode**:
   - Plan has `status: design-complete` + `total_steps: 0` → **Add mode**: plan has requirements but no implementation steps yet
   - Plan has existing implementation steps → **Re-plan mode**: revise the implementation approach
   - Legacy spec file (from fallback) → **Convert mode**: create unified plan from old spec
3. Read all files in `.aion/rules/` — proactively avoid known pitfalls
4. Check `.aion/contracts/` — only if directory exists
5. Read `.aion/specs/_product.md` — understand overall product landscape for module decoupling
6. Check `.aion/prototypes/` — only if directory exists and relevant

### Step 1: Explore Codebase (MUST — do not skip)
Before writing a single line of the plan:
1. Use file search (glob) to understand the project structure
2. Read relevant source files that will be modified or extended
3. Identify existing patterns: how similar features are implemented, what abstractions exist
4. Note: if you skip this step, the plan WILL be wrong. Read code first, design second.

### Step 2: Design Steps with Dependencies

**In Re-plan mode**: Show the existing implementation steps, explain what needs to change, and offer:
- **A) Full re-plan** (recommended if approach fundamentally changed) — archive existing steps, design new ones
- **B) Partial update** — modify specific steps while keeping others

Create an ordered list of implementation steps. For each step:
- What to do (description)
- Which files to create or modify
- Dependencies (what must be done first)
- Estimated complexity (small / medium / large)

Principles:
- **Minimal changes**: Reuse existing patterns, avoid unnecessary refactoring
- **Correct order**: Dependencies must be satisfied before dependent steps
- **Avoid known pitfalls**: Reference rules where relevant
- **Small steps**: Each step should be completable and verifiable independently

### Step 3: Define Verification Strategy
- **Method**: `unit_test` | `integration_test` | `manual_check` | `build_check`
- **Coverage**: What specifically to test
- **Commands**: Exact commands to run verification
- **Success criteria**: What "passing" looks like

### Step 3.5: Version Check (before writing)

Follow Write Protocol (`.aion/refs/write-protocol.md`, category: **Versioned**).

Before writing, check if this is an update to an existing plan:
1. **Add mode** (plan has no steps): Update in place — add Architecture Decisions, Steps, Verification, Risks. Change `status` to `completed` and set `total_steps`.
2. **Re-plan mode**: Archive current as `.aion/plans/{name}.v{N}.md`, write new version with `version: {N+1}`, require `change_reason`.
3. **Convert mode**: Create new plan in `.aion/plans/{name}.md` from legacy spec content.

### Step 4: Confirm and Write
1. Present the complete plan to the user for review
2. Ask: "实现方案是否合理？有要调整的地方吗？"
3. Only after confirmation, write to `.aion/plans/{feature-name}.md`
4. Suggest: "Plan ready. Run /project:aion-impl to start implementation."

### Step 4.5: Propagate to _product.md (auto-propagation)

After the plan is written, check for structural changes:
1. **Check for propagation triggers**: new module, new dependency, module boundary changes, new API endpoints
2. **If triggers found** → update `_product.md`, tag `[from:plan]`, report changes
3. Do NOT overwrite `[CONFIRMED]` entries

**Plan format**: Same as `/project:aion-design` output format (Goal + Requirements + Acceptance Criteria + Constraints + Architecture Decisions + Implementation Steps + Verification + Risks).

## Next Steps

Proceed with /project:aion-impl to start implementation.

## Checklist
Read and apply `.aion/checklists/plan.md` if it exists. If not, use the built-in checklist:
- [ ] Codebase has been explored — existing patterns understood
- [ ] All P0 requirements from the plan are covered by at least one step
- [ ] Steps are ordered with correct dependencies
- [ ] Rules have been consulted to avoid known issues
- [ ] Verification strategy is defined with concrete commands
- [ ] Each step has clear file targets and description
- [ ] Risks are identified with mitigations
- [ ] Version archived if updating existing plan

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Planning without reading code | Plans based on assumptions will conflict with actual architecture | CRITICAL |
| Ignoring existing patterns | Creating inconsistent code that's harder to maintain | HIGH |
| No verification strategy | No way to know if implementation actually works | HIGH |
| Monolithic steps ("implement the feature") | Steps that are too large can't be tracked or verified | MEDIUM |
| Overwriting existing plan without archiving | Loses design decision history | HIGH |

## Output Format
The plan file written to `.aion/plans/{feature-name}.md`.

## Exit Status
- `DONE` — Plan written/updated after user confirmation
- `DONE_WITH_CONCERNS` — Plan written but has identified risks the user accepted
- `BLOCKED` — Cannot plan: no existing plan/spec found, needs /project:aion-design first
- `NEEDS_CONTEXT` — Need to understand more of the codebase or missing contract definitions
