# /project:aion-design — 需求设计

Turn ideas into structured requirement specs through guided conversation, challenging assumptions before documenting.

$ARGUMENTS — Optional: a brief description of what you want to build. If empty, ask the user to describe their idea.

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
6. Read `.aion/refs/write-protocol.md` — load Write Protocol for Step 3.5

### Step 1: Analyze or Ask
- If `$ARGUMENTS` provides a clear description, proceed to analysis
- If `$ARGUMENTS` is empty, ask the user: "What do you want to build? Describe the problem you're trying to solve."

### Step 1.5: Challenge Assumptions (CRITICAL — do not skip)
Before accepting the user's framing, ask yourself and the user:
- "Is this the simplest solution to the real problem?"
- "What's the actual problem behind this request? Are we solving the symptom or the cause?"
- "Does this conflict with or duplicate anything in existing specs or rules?"
- "What happens if we do nothing — how bad is it really?"

Push back if the proposed approach is over-engineered, vague, or solves the wrong problem. Be respectful but direct.

### How to Ask Questions
When you need user input, follow this structure:
1. **Context**: One sentence grounding where we are (e.g., "While analyzing the auth requirements...")
2. **Problem**: Explain simply — as if to a smart colleague who hasn't been following along
3. **Options**: Present 2-3 lettered options (A/B/C) with pros, cons, and your recommendation
4. **Recommendation**: Bold your recommended option with a brief "because..."

Example:
"While designing the auth module, I found two valid approaches:
  A) JWT tokens (stateless, scales better) — **Recommended** because the app is multi-server
  B) Session cookies (simpler, but requires sticky sessions)
Which approach?"

ONE question at a time. Never batch multiple unrelated decisions.

### Step 2: Clarifying Questions
Ask 2-3 targeted questions to fill gaps. Focus on:
- What problem does this solve? Who is the user?
- What are the boundaries — what is NOT in scope?
- Are there technical constraints (existing stack, APIs, performance)?
- What does "done" look like — how do we verify success?
- Distinguish P0 (must-have) from P1 (nice-to-have) requirements

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

### Step 4: Confirm and Write
1. Show the complete spec to the user in the conversation for review
2. Ask: "Does this accurately capture what you want? Any changes?" (确认需求是否准确？)
3. Only after explicit confirmation, write to `.aion/specs/{feature-name}.md`
4. If prototype files in `.aion/prototypes/` were referenced, note them in the References section

## Next Steps

If this feature has a UI component, consider running /project:aion-demo to generate an interactive prototype before planning.

Otherwise, proceed with /project:aion-plan to create an implementation plan.

## Checklist
Read and apply `.aion/checklists/design.md` if it exists. If not, use the built-in checklist:
- [ ] Goal is clear and can be summarized in one sentence
- [ ] P0 requirements are complete and actionable
- [ ] P1 requirements are separated from P0
- [ ] Acceptance criteria are measurable (not vague like "should work well")
- [ ] Known rules/pitfalls have been checked and no conflicts exist
- [ ] Reference documents and prototypes have been consulted (if available)
- [ ] Assumptions have been challenged — simplest viable solution chosen
- [ ] Scope boundaries are explicit (what is NOT included)
- [ ] Existing spec checked — Write Protocol followed (version archived if updating)
- [ ] Scope conflict checked — different scope forces different filename

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Assuming implementation details without asking | Specs get bloated with unjustified technical choices | CRITICAL |
| Ignoring `.aion/refs/` and `.aion/prototypes/` | Missing context leads to specs that contradict existing requirements | HIGH |
| Designing what conflicts with existing rules | Repeating known mistakes wastes everyone's time | HIGH |
| Writing spec without user confirmation | Specs must be agreed upon — unilateral writing breaks trust | CRITICAL |
| Accepting vague requirements without pushback | "Make it better" is not a requirement — challenge it | HIGH |
| Skipping the assumption challenge step | Over-engineering and wrong-problem-solving sneak through | MEDIUM |
| Overwriting existing spec without version check | Loses design decision history; can't trace why requirements changed | HIGH |
| Same filename for different scopes (api vs web) | Frontend and backend specs overwrite each other | HIGH |

## Output Format
The spec file written to `.aion/specs/{feature-name}.md` using the format defined in Step 3.

## Exit Status
- `DONE` — Spec written to `.aion/specs/` after user confirmation
- `DONE_WITH_CONCERNS` — Spec written but user declined to address flagged issues
- `BLOCKED` — Cannot proceed: missing critical information that user cannot provide now
- `NEEDS_CONTEXT` — Need reference documents, prototypes, or stakeholder input before spec can be finalized
