# /project:aion-plan — 实现规划

<!-- 本命令结构 + bite-sized step 模板综合 AionCode 原有 plan 流程 + superpowers:writing-plans 精髓。
     See .aion/CREDITS.md -->

Create a technical implementation plan based on requirement specs, grounded in actual codebase exploration.

$ARGUMENTS — Optional: spec file name or feature description. If empty, use the most recent spec in `.aion/specs/`.

## 触发方式 (v0.7.6 起)

本命令支持**两种触发路径**:

1. **主动建议触发(主路径)** — 由 `aion-think` Phase 10 自动衔接,或用户说"进入 plan / 生成 plan / 写 plan"时 AI 主动调用本流程,**不需要用户显式输入命令**
2. **显式命令触发(修改路径)** — `/project:aion-plan {spec-name}` 用于**修改已有 plan**(主路径用于初次生成)

无论哪种触发,流程不变 — 下方 Steps 描述的就是完整流程。

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

### Asking Questions
When you need user input: ONE question at a time, A/B/C format with recommendation. Only ask when you genuinely don't know — most technical decisions you can make from the code you just read.

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
Create an ordered list of implementation steps. Each step must be scoped to **one file or one function-level change** — no monolithic "implement the feature" steps.

**Step format** (use for each step):
```
### Step N: {Title}
- **What**: One sentence — what this step accomplishes
- **Files**: Exact files to create or modify
- **How**: 2-3 sentences on implementation approach (function/method level, no code blocks)
- **Verify**: Concrete check — command to run, output to expect, or condition to confirm
- **Dependencies**: Which prior steps must be done first, or "None"
- **Complexity**: small | medium | large
```

**Granularity rules**:
- Each step targets one file or one cohesive function group
- Every step MUST have a `Verify` field — no unverifiable steps

**Forbidden descriptions** (these are too vague — expand them):
- "Similar to Step N" — repeat the specifics; executor may read steps out of order
- "Add appropriate error handling" — specify which errors and how to handle them
- "Write tests" / "Add tests for the above" — specify which cases and assertions
- "Update as needed" / "Make necessary changes" — list the exact changes

Principles:
- **Minimal changes**: Reuse existing patterns, avoid unnecessary refactoring
- **Correct order**: Dependencies must be satisfied before dependent steps
- **Avoid known pitfalls**: Reference rules where relevant

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

### Step 3.8: Plan Self-Review (before showing to user)

Before presenting the plan to the user, run an internal quality check. Fix issues inline — the user should see a reviewed version, not a draft.

**Three checks**:
1. **Spec coverage** — Walk through each P0 requirement in the spec. For each, identify the implementing step(s). If a requirement has no corresponding step, add the missing step.
2. **Step completeness** — For each step, verify it handles edge cases and error conditions relevant to that step (not just the happy path). If a step says "modify function X" but doesn't mention what happens when X receives invalid input, add that detail.
3. **Name consistency** — Verify that file names, function names, and variable names referenced in later steps match exactly what was defined in earlier steps. Mismatches (e.g., `clearLayers()` in Step 2 vs `clearFullLayers()` in Step 5) are bugs — fix them.

This step is internal — do NOT ask the user to review the self-review. Just fix issues and proceed.

### Step 4: Confirm, Write, and Execute
1. Present the complete plan to the user for review
2. Ask: "方案是否合理？确认后直接开始实现。"
3. Only after confirmation, write to `.aion/plans/{feature-name}.md`
4. **Immediately begin execution** — implement each step in order, following the plan's steps and verification strategy. Update each step's Status from "Not started" to "Done" as completed. Do NOT wait for the user to say "开始" — confirmation of the plan IS the go signal.

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

**Format**: 严格按 `.aion/rules/plan-template.md` 生成(含 frontmatter / Goal / Architecture / Tech Stack / File Structure / Implementation Tasks with bite-sized Steps / Verification Strategy / Risks)。

**核心要求**(`plan-template.md` 的精髓):
- 每个 Step 是 2-5 分钟动作(不是"实现整个 X")
- 改代码的 Step 必须有完整代码块,不能是占位符
- 每个 Step 有明确 `Verify`(命令 + 预期输出)
- TDD 节奏:Write failing test → Run (fail) → Implement → Run (pass) → Commit
- 禁忌:TBD / "similar to Task N" / "add error handling" / "write tests"(无代码)

生成 plan 后,必须执行下方 Step 3.8(Plan Self-Review)已在生成前完成;落盘后执行 Step 5(Execution Handoff)。

### Step 5: Execution Handoff

Plan 落盘后,向用户提供执行选项:

> "Plan 已保存到 `.aion/plans/{filename}.md`。两种执行方式:
>
> **(a) Subagent-Driven(推荐)** — 每个 task 派一个新 subagent,task 间 review,快速迭代
> **(b) Inline Execution** — 本会话内逐 task 执行,checkpoint 分批 review
>
> 选哪个?"

**若用户选 (a)**:按 `commands/aion-loop.md` 启动并行 agent 分发,或用 Agent 工具手动派发。
**若用户选 (b)**:本会话继续,逐 task 执行,每 task 完成后汇报并 pause 供 review。
**若用户暂不想执行**:退出 DONE。保留 plan 供后续触发。

## Next Steps

实现完成后,运行 `/project:aion-review` 审查,然后 `/project:aion-commit` 提交。

## Checklist
Read and apply `.aion/checklists/plan.md` if it exists. If not, use the built-in checklist:
- [ ] Codebase has been explored — existing patterns understood
- [ ] All P0 requirements from the spec are covered by at least one step
- [ ] Steps are ordered with correct dependencies
- [ ] Each step is scoped to one file or one function-level change
- [ ] Each step has a verify field with concrete check method
- [ ] No vague descriptions ("similar to Step N", "add error handling", "write tests")
- [ ] Plan Self-Review passed (spec coverage, step completeness, name consistency)
- [ ] Rules have been consulted to avoid known issues
- [ ] Verification strategy is defined with concrete commands
- [ ] Risks are identified with mitigations
- [ ] Existing plan checked — version archived if updating

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Planning without reading code | Plans based on assumptions will conflict with actual architecture | CRITICAL |
| Ignoring existing patterns | Creating inconsistent code that's harder to maintain | HIGH |
| No verification strategy | No way to know if implementation actually works | HIGH |
| Monolithic steps ("implement the feature") | Steps that are too large can't be tracked or verified | MEDIUM |
| Vague step descriptions ("add error handling", "similar to Step N") | Executor must guess intent; results diverge from plan | HIGH |
| Steps without verify field | No way to confirm a step was done correctly before moving on | MEDIUM |
| Skipping Plan Self-Review | Spec gaps and name inconsistencies reach the user, cause rework | HIGH |
| Ignoring contracts | Breaking interface agreements causes integration failures | HIGH |
| Not referencing rules in the plan | Known pitfalls will be repeated during implementation | MEDIUM |
| Overwriting existing plan without archiving | Loses design decision history; can't trace why approach changed | HIGH |
| Empty change_reason when versioning | Version history is useless without context on what changed | MEDIUM |

### Rationalization Prevention
If you catch yourself thinking any of these, STOP — you're rationalizing:

| Excuse | Reality |
|--------|---------|
| "I know this codebase well enough, no need to read code" | You know what you remember. The code knows what actually exists |
| "The spec is clear, the plan writes itself" | Clear specs still need codebase exploration — existing patterns dictate HOW |
| "I'll figure out the details during implementation" | Vague plans produce vague implementations. Specify now or debug later |
| "This step is obvious, no need for a verify field" | If it's obvious, writing the verify takes 10 seconds. If it's not, you just proved why you need it |
| "It's similar to Step N, no need to repeat" | The executor may read steps out of order. Repeat the specifics |
| "Adding error handling details will bloat the plan" | Missing error handling in the plan means missing error handling in the code |

## Output Format
The plan file written to `.aion/plans/{feature-name}.md` using the format defined in `.aion/rules/plan-template.md` (referenced from Step 4's Format section).

## Exit Status
- `DONE` — Plan written to `.aion/plans/` after user confirmation
- `DONE_WITH_CONCERNS` — Plan written but has identified risks the user accepted
- `BLOCKED` — Cannot plan: spec is incomplete or contradictory, needs /project:aion-think first
- `NEEDS_CONTEXT` — Need to understand more of the codebase or missing contract definitions
