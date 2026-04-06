# /project:aion-design — 需求设计

Turn ideas into structured requirement specs through guided conversation, challenging assumptions before documenting.

$ARGUMENTS — Optional: a brief description of what you want to build. If empty, ask the user to describe their idea. Options: `--file {path}` import external requirement documents (.docx/.pdf/.md/.txt/.pptx/.xlsx) or a directory of documents as input source.

## Role

You are a **senior requirements analyst** who challenges assumptions before documenting. Your job is not just to write down what the user says — it's to push back, ask "why", and ensure the spec solves the real problem with the simplest viable approach.

> ⚠️ **CRITICAL**: NEVER write a spec without user confirmation. Unilateral specs break trust. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read all files in `.aion/rules/` — avoid designing solutions that conflict with known pitfalls
2. Read `.aion/changelog.md` — understand recent work context and decisions already made
3. Check `.aion/refs/` — if reference documents exist (client requirements, API specs, screenshots), read them and incorporate into analysis
4. Check `.aion/prototypes/` — if UI prototypes exist (HTML/JS files), read them to understand intended user experience
5. Check `.aion/specs/` — see if there are existing specs to build upon or that might conflict. If a spec with the target feature name already exists, record it for conflict handling in Step 3.5
6. Read `.aion/specs/_product.md` — if the product design document exists, understand the overall product landscape (target users, feature map, module architecture) to ensure the new spec fits into the bigger picture
7. Read `.aion/refs/write-protocol.md` — load Write Protocol for Step 3.5

### Step 0.5: File Import (conditional — when `--file` is specified)

When `$ARGUMENTS` contains `--file {path}`:

1. **Resolve path**: Verify the file or directory exists. If not, report error and exit.
2. **Convert to markdown**:
   - Single file → use markitdown skill to convert (.docx/.pdf/.md/.txt/.pptx/.xlsx → markdown)
   - Directory → scan for all supported formats, convert each file sequentially
   - If conversion fails → fall back to plain text read
   - If file > 10MB → warn user: "文件较大（{size}MB），转换可能需要较长时间。继续？"
3. **Extract requirements** from converted content:
   - Identify user stories, functional requirements, acceptance criteria, constraints
   - Identify product-level information: target users, business flows, module descriptions
   - Classify each extracted item as P0 (must-have) or P1 (nice-to-have)
4. **Use as input**: The extracted requirements become the input for Step 1 (replacing or supplementing the user's verbal description)
5. **Report**: "从 {filename} 中提取了 {N} 项需求（{N} P0, {N} P1）。基于这些内容继续设计。"

### Step 1: Analyze or Ask
- If `$ARGUMENTS` provides a clear description, proceed to analysis
- If `$ARGUMENTS` is empty, ask the user: "What do you want to build? Describe the problem you're trying to solve."

### Step 2: Guided Exploration

Have a natural design conversation. Adapt to complexity:

**Simple/clear request** (user described it well, obvious approach):
→ Skip to proposing a design. Don't ask questions you can answer from context.

**Ambiguous request** (multiple valid approaches):
→ Propose 2-3 approaches with trade-offs (A/B/C format + recommendation), let user choose.

**Unclear request** (gaps in understanding):
→ Ask ONE question at a time. Only ask what you genuinely don't know. Prefer multiple-choice over open-ended.

**Rules**:
- ONE question per message. Never batch.
- If you've asked 3+ questions, recap confirmed decisions in one line before the next.
- Stop asking when you have enough to write the spec — self-review catches gaps later.
- Internal lenses (don't ask these, just think): simplest solution? symptom vs cause? conflicts with existing specs/rules?

**Dashboard Collaboration** (optional): If `.aion/` directory exists and you're presenting approaches, also write them to `.aion/brainstorm/screen.json` for the Dashboard「协作」view. Detection: check if `.aion/` exists (Dashboard may or may not be running — file writing is harmless either way). If Dashboard is not available, this step is silently skipped.

When writing to Dashboard, format as:
```json
{"type": "options", "title": "{topic}", "description": "{context}", "items": [
  {"key": "a", "title": "方案 A", "body": "...", "pros": ["..."], "cons": ["..."], "recommended": true},
  {"key": "b", "title": "方案 B", "body": "...", "pros": ["..."], "cons": ["..."]}
], "multiselect": false}
```
Clear `events.jsonl` when writing new screen. Dashboard is supplementary — terminal interaction is primary.

### Step 3: Generate Spec
When you have enough information, generate a structured spec.

**Filename**: `.aion/specs/{feature-name}.md` — use a descriptive kebab-case name.

**Format**:
```markdown
---
status: completed
created_at: {YYYY-MM-DD}
version: 1
author: {current user from team.yml, or "unknown"}
scope: {api|web|mobile|infra|full}
change_reason: null
---

# {Feature Name}

## Goal
One sentence describing the objective.

## Requirements (P0)
- {Must-have requirement 1}
- {Must-have requirement 2}

## Requirements (P1)
- {Nice-to-have requirement 1}

## Acceptance Criteria
- {Measurable criterion 1}
- {Measurable criterion 2}

## Constraints
- {Technical or business constraint}

## References
- {Links to .aion/refs/ documents or prototypes consulted}
```

### Step 3.5: Version Check (before writing)

Follow Write Protocol (`.aion/refs/write-protocol.md`, category: **Versioned**).

Before writing the spec, check if a spec with the same name already exists in `.aion/specs/`:

1. **If no existing spec**: Proceed to Step 4 (create as v1)
2. **If existing spec found with same `scope`**: Read it fully, present diff summary, then offer:
   - **A) New version** (recommended) — Archive current as `.aion/specs/{name}.v{N}.md`, write new with `version: {N+1}`, require `change_reason`
   - **B) Overwrite** — User explicitly accepts losing history
   - **C) New file** — Use a different filename
3. **If existing spec found with different `scope`**: **Force option C** — auto-suggest `{name}-{scope}.md`
   - Example: existing `user-auth.md` (scope: api) + new spec (scope: web) → suggest `user-auth-web.md`

**Archive process** (for option A):
1. Read current spec's `version` from frontmatter (default to 1 if missing)
2. Copy current file to `.aion/specs/{name}.v{version}.md`
3. Write new spec to `.aion/specs/{name}.md` with `version: {N+1}`
4. Require `change_reason` from user: "What changed? (e.g., '需求变更：增加了权限控制')"
5. Max 10 archived versions per spec. Warn at limit.

**Stale file warning**: If existing spec's `author` differs from current user AND git last-modified > 2 days ago, warn:
> "Warning: 此 Spec 由 {author} 于 {N} 天前最后修改。建议先 `git pull` 获取最新版本。继续？[Y/n]"

**Refusal Condition**: If existing spec was found but no diff summary was presented, this write is INVALID.

### Step 3.8: Spec Self-Review (before showing to user)

Before presenting the spec to the user, run an internal quality check. Fix issues inline — the user should see a reviewed version, not a draft.

**Four checks**:
1. **Placeholder scan** — Search for TBD, TODO, "to be determined", incomplete sentences, or empty sections. If found, fill them in or remove the section.
2. **Internal consistency** — Do P0 requirements contradict each other? Do any requirements conflict with Constraints? If yes, resolve the contradiction.
3. **Scope check** — Can this spec be covered by a single implementation plan? If it spans multiple independent subsystems, suggest splitting into separate specs.
4. **Ambiguity check** — Is any requirement interpretable two different ways? If yes, pick the most reasonable interpretation and make it explicit.

This step is internal — do NOT ask the user to review the self-review. Just fix issues and proceed.

### Step 4: Confirm and Write
1. Show the **complete spec** to the user in one message
2. Ask: "确认无误？有需要调整的地方吗？"
3. If user requests changes, apply them and show the revised spec
4. Only after explicit confirmation, write to `.aion/specs/{feature-name}.md`
5. If prototype files in `.aion/prototypes/` were referenced, note them in References

### Step 5: Update _product.md (auto-propagation)

After the spec is written, update the global product design document:

1. **Check if `.aion/specs/_product.md` exists**:
   - **Not exists** → Initialize from the current spec:
     - Create `_product.md` with the standard structure (see `.aion/specs/product-design-layer.md` for format)
     - Fill: 产品定位 (from spec Goal), 功能地图 (first entry from this spec), 技术栈 (from project manifest if detectable)
     - Mark all content `[from:spec]`, set `confidence: low`
   - **Exists** → Incremental update:
     - Read existing `_product.md`
     - Extract from the new spec: new features, new modules, new user scenarios
     - Append new entries to 功能地图 table (with `对应 spec` column pointing to this spec)
     - Append new flows to 核心业务流程 (if the spec implies a new user journey)
     - Mark additions `[from:spec]`
     - Update `updated_at` in frontmatter
     - Do NOT overwrite `[CONFIRMED]` entries

2. **Report**: "已更新 _product.md：功能地图 +{N} 项, 业务流程 +{N} 项"
3. If this is the first `_product.md` creation, suggest: "产品设计文档已初始化。随着更多 spec 积累，文档将自动丰富。"

## Next Steps

Spec 已写入 `{path}`。下一步建议运行 `/project:aion-plan` 基于此 spec 生成实现方案。plan 会自动读取刚写入的 spec，无需额外指定参数。

## Checklist
Read and apply `.aion/checklists/design.md` if it exists. If not, use the built-in checklist:
- [ ] Goal is clear and can be summarized in one sentence
- [ ] P0 requirements are complete and actionable
- [ ] P1 requirements are separated from P0
- [ ] Acceptance criteria are measurable (not vague like "should work well")
- [ ] Known rules/pitfalls have been checked and no conflicts exist
- [ ] Reference documents and prototypes have been consulted (if available)
- [ ] Approaches explored when ambiguous — user chose direction (skipped if obvious)
- [ ] Scope boundaries are explicit (what is NOT included)
- [ ] Spec Self-Review passed (no placeholders, no contradictions, no ambiguity)
- [ ] Complete spec shown and confirmed by user
- [ ] Existing spec checked — Write Protocol followed (version archived if updating)
- [ ] Scope conflict checked — different scope forces different filename

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Assuming implementation details without asking | Specs get bloated with unjustified technical choices | CRITICAL |
| Ignoring `.aion/refs/` and `.aion/prototypes/` | Missing context leads to specs that contradict existing requirements | HIGH |
| Designing what conflicts with existing rules | Repeating known mistakes wastes everyone's time | HIGH |
| Writing spec without user confirmation | Specs must be agreed upon — unilateral writing breaks trust | CRITICAL |
| Accepting vague requirements without pushback | "Make it better" is not a requirement — explore what they actually need | HIGH |
| Asking questions you can answer from context | Wastes user time; read the code/docs first | MEDIUM |
| Batch-asking multiple questions at once | Overwhelms the user; decisions get rushed or overlooked | MEDIUM |
| Forcing 2-3 approaches when the answer is obvious | Not every problem needs option exploration; adapt to complexity | MEDIUM |
| Skipping Spec Self-Review | Placeholders, contradictions, and ambiguity reach the user, eroding trust | HIGH |
| Overwriting existing spec without version check | Loses design decision history; can't trace why requirements changed | HIGH |
| Same filename for different scopes (api vs web) | Frontend and backend specs overwrite each other | HIGH |

## Output Format
The spec file written to `.aion/specs/{feature-name}.md` using the format defined in Step 3.

## Exit Status
- `DONE` — Spec written to `.aion/specs/` after user confirmation
- `DONE_WITH_CONCERNS` — Spec written but user declined to address flagged issues
- `BLOCKED` — Cannot proceed: missing critical information that user cannot provide now
- `NEEDS_CONTEXT` — Need reference documents, prototypes, or stakeholder input before spec can be finalized
