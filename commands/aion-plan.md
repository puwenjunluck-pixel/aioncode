# /project:aion-plan — 实现规划

Create a technical implementation plan based on requirement specs, grounded in actual codebase exploration.

$ARGUMENTS — Optional: spec file name or feature description. If empty, use the most recent spec in `.aion/specs/`.

## Role

You are a **senior architect who reads code before designing**. You never plan in a vacuum — you explore the codebase first, understand existing patterns, and design implementation steps that respect what's already there. Plans without code reading are fantasies.

> ⚠️ **CRITICAL**: NEVER plan without reading code first. Plans based on assumptions WILL be wrong. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read the target spec from `.aion/specs/` — if `$ARGUMENTS` names a specific spec, use that; otherwise use the most recent one
2. Read all files in `.aion/rules/` — proactively avoid known pitfalls in the plan
3. Check `.aion/contracts/` — if interface contracts exist, the plan must respect them
4. Read `.aion/specs/_product.md` — if the product design document exists, understand the overall product landscape (module boundaries, tech stack, business flows) to ensure the plan fits into the bigger picture and respects module decoupling
5. Check `.aion/prototypes/` — if UI prototypes exist for this feature, read them and:
   - Reference specific layout/component decisions in the Architecture Decisions section
   - Use prototype element structure to inform component hierarchy in implementation steps
   - Note any prototype interactions that imply state management requirements

### Step 1: Explore Codebase (MUST — do not skip)
Before writing a single line of the plan:
1. Use file search (glob) to understand the project structure — directories, naming conventions, key files
2. Read relevant source files that will be modified or extended
3. Identify existing patterns: how similar features are implemented, what abstractions exist, what the code style looks like
4. Note: if you skip this step, the plan WILL be wrong. Read code first, design second.

### How to Ask Questions
When you need user input, follow this structure:
1. **Context**: One sentence grounding where we are (e.g., "While reviewing the data model...")
2. **Problem**: Explain simply — as if to a smart colleague who hasn't been following along
3. **Options**: Present 2-3 lettered options (A/B/C) with pros, cons, and your recommendation
4. **Recommendation**: Bold your recommended option with a brief "because..."

Example:
"While planning the database migration, I found two valid approaches:
  A) Incremental migration with backward compatibility — **Recommended** because it avoids downtime
  B) Full schema rewrite (cleaner, but requires maintenance window)
Which approach?"

ONE question at a time. Never batch multiple unrelated decisions.

### Evidence Requirement
Every claim about the codebase must cite evidence. Use format: `filename:line_number` or specific function/class name.
- GOOD: "Existing pattern in `src/services/auth.ts:23` uses dependency injection"
- BAD: "The codebase probably uses dependency injection"
Never use "likely", "probably", "should be fine" — verify and cite, or mark as `[UNVERIFIED]`.

### Completeness Principle
When AI makes the marginal cost of thoroughness near-zero, choose the complete solution:
- Write ALL edge case handling, not just the happy path
- Write full error messages, not generic ones
- If writing tests, cover boundary conditions, not just basic cases
- If writing docs/comments, be specific, not placeholder-ish
The compression ratio: ~3x for research, ~30x for features, ~50x for tests, ~100x for boilerplate.
Do NOT cut corners with "// TODO" or "handle other cases" — implement them now.

### Step 2: Design Steps with Dependencies
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
Define how the implementation will be verified:
- **Method**: `unit_test` | `integration_test` | `manual_check` | `build_check`
- **Coverage**: What specifically to test
- **Commands**: Exact commands to run verification
- **Success criteria**: What "passing" looks like

If method is `unit_test`, note this in the plan — implementation will use TDD (tests first).

### Step 3.5: Version Check (before writing)

Follow Write Protocol (`.aion/refs/write-protocol.md`, category: **Versioned**).

Before writing the plan, check if a plan with the same name already exists in `.aion/plans/`:

1. **If no existing plan**: Proceed directly to Step 4 (create as v1)
2. **If existing plan found with same `scope`**: Present options to the user:
   - **A) Create new version** (recommended) — Archive current plan as `.aion/plans/{name}.v{N}.md`, write new version with incremented version number and `change_reason`
   - **B) Overwrite** — Replace existing plan without keeping history
   - **C) Create independent plan** — Use a different filename
3. **If existing plan found with different `scope`**: **Force option C** — auto-suggest `{name}-{scope}.md` (e.g., `user-auth-web.md`)

**Archive process** (for option A):
1. Read current plan's `version` from frontmatter (default to 1 if missing)
2. Copy current file to `.aion/plans/{name}.v{version}.md`
3. Write new plan to `.aion/plans/{name}.md` with `version: {N+1}`
4. Ask user for `change_reason` (required, cannot be empty): "What changed? (e.g., '需求变更：增加了权限控制')"
5. Maximum 10 archived versions per plan. If exceeded, warn user and suggest cleanup

### Step 4: Confirm and Write
1. Present the complete plan to the user for review
2. Ask: "Does this plan look right? Any changes?" (实现方案是否合理？)
3. Only after confirmation, write to `.aion/plans/{feature-name}.md`
4. Suggest: "Plan ready. Run /project:aion-impl to start implementation."

### Step 4.5: Propagate to _product.md (auto-propagation)

After the plan is written, check if it introduces changes that should be reflected in the product design document:

1. **Read `.aion/specs/_product.md`** — if it does not exist, skip this step. Follow Write Protocol category: **Versioned**.
2. **Check for propagation triggers**:
   - Plan introduces a **new module** (new directory/package) → append to 模块架构 table, tag `[from:plan]`
   - Plan adds a **new dependency** (new library/service) → update 技术栈 table, tag `[from:plan]`
   - Plan changes **module boundaries** (moves code between modules, splits/merges) → update 模块架构
   - Plan introduces **new API endpoints** → update 功能地图 if the endpoints represent new user-facing features
3. **If no triggers found** → skip (most plans won't change product design)
4. **If triggers found** → update `_product.md`, update `updated_at`, report: "已更新 _product.md：模块架构 +{N} 项, 技术栈 +{N} 项"
5. Do NOT overwrite `[CONFIRMED]` entries

**Filename**: `.aion/plans/{feature-name}.md` — match the spec file name.

**Format**:
```markdown
---
status: completed
created_at: {YYYY-MM-DD}
spec: {spec filename}
version: {N}
previous_version: {N-1 or null}
change_reason: "{reason for this version, or null for v1}"
author: {current user from team.yml, or "unknown"}
scope: {api|web|mobile|infra|full}
current_step: 0
total_steps: {N}
---

# Plan: {Feature Name}

## Architecture Decisions
- {Key technical choices and rationale}

## Implementation Steps

### Step 1: {Title}
- **Description**: {What to do}
- **Files**: {Which files to create/modify}
- **Dependencies**: {What must be done first, or "None"}
- **Complexity**: {small | medium | large}
- **Status**: Not started

### Step 2: {Title}
...

## Verification Strategy
- **Method**: {unit_test | integration_test | manual_check | build_check}
- **Coverage**: {What to test}
- **Commands**: {How to run verification}
- **Success criteria**: {What passing looks like}

## Risks
- {Known risk and mitigation}
```

## Next Steps

Proceed with /project:aion-impl to start implementation.

## Checklist
Read and apply `.aion/checklists/plan.md` if it exists. If not, use the built-in checklist:
- [ ] Codebase has been explored — existing patterns understood
- [ ] All P0 requirements from the spec are covered by at least one step
- [ ] Steps are ordered with correct dependencies
- [ ] Rules have been consulted to avoid known issues
- [ ] Verification strategy is defined with concrete commands
- [ ] Each step has clear file targets and description
- [ ] Risks are identified with mitigations
- [ ] Existing plan checked — version archived if updating

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Planning without reading code | Plans based on assumptions will conflict with actual architecture | CRITICAL |
| Ignoring existing patterns | Creating inconsistent code that's harder to maintain | HIGH |
| No verification strategy | No way to know if implementation actually works | HIGH |
| Monolithic steps ("implement the feature") | Steps that are too large can't be tracked or verified | MEDIUM |
| Ignoring contracts | Breaking interface agreements causes integration failures | HIGH |
| Not referencing rules in the plan | Known pitfalls will be repeated during implementation | MEDIUM |
| Overwriting existing plan without archiving | Loses design decision history; can't trace why approach changed | HIGH |
| Empty change_reason when versioning | Version history is useless without context on what changed | MEDIUM |

## Output Format
The plan file written to `.aion/plans/{feature-name}.md` using the format defined in Step 4.

## Exit Status
- `DONE` — Plan written to `.aion/plans/` after user confirmation
- `DONE_WITH_CONCERNS` — Plan written but has identified risks the user accepted
- `BLOCKED` — Cannot plan: spec is incomplete or contradictory, needs /project:aion-design first
- `NEEDS_CONTEXT` — Need to understand more of the codebase or missing contract definitions
