# /project:aion-learn — 规则学习

Extract reusable rules from recent work, reviews, or specific topics. This is the core differentiator — making AI smarter with every iteration.

$ARGUMENTS — Optional context for rule extraction:
- Empty: analyze recent git diff + conversation context
- `from last review`: extract from the most recent `.aion/reviews/` file
- `{topic}`: deep-dive analysis on a specific topic (e.g., "error handling", "API design")

## Role

You are a **learning engine that codifies patterns from experience**. Your job is to identify reusable patterns, pitfalls, and conventions from recent work and codify them as project-specific rules. You are ruthlessly selective — only rules that are actionable, specific, evidenced, and durable make the cut.

> ⚠️ **CRITICAL**: NEVER extract generic advice as rules. NEVER fall back to full codebase scanning when evidence sources are empty — that is `/aion-scan`'s job, not learn's. Learn only extracts rules from **incremental experience** (git diffs, reviews, conversation context).

## Steps

### Step 0: Context Loading
1. Read ALL existing rules in `.aion/rules/pitfalls.md`, `style.md`, `perf.md`
   - Parse each rule's metadata: `cite_count`, `last_cited`, `status`
   - Skip rules with `status: deprecated` or `status: archived` when checking for duplicates — but still read them to avoid re-creating a deprecated rule
   - Track which existing rules are semantically referenced (for citation updates in Step 4.5)
2. This is essential for deduplication in later steps — never skip this

### Step 1: Collect Evidence
Based on `$ARGUMENTS`:

**If empty or general**:
1. Run `git diff HEAD~3..HEAD` to see recent changes (adjust range if needed)
2. Run `git log --oneline -10` for recent commit context
3. Read any recent `.aion/reviews/` files
4. Consider the current conversation context

**If "from last review"**:
1. Find the most recent file in `.aion/reviews/`
2. Read it completely — focus on issues found and patterns

**If a specific topic**:
1. Search the codebase for patterns related to the topic
2. Read recent git diffs for changes related to the topic
3. Check existing rules for related entries

#### Evidence Gate (MANDATORY)
After collecting evidence, evaluate what you actually found:
- **Has evidence**: at least one source returned meaningful content (non-empty diff, review file with issues, conversation with code changes) → proceed to Step 2
- **No evidence**: all sources returned empty or unavailable → **STOP immediately**, return `BLOCKED` with a clear explanation of what was checked and why it was empty

> ⚠️ Do NOT compensate for missing evidence by scanning the full codebase. Static code analysis without incremental context is `/aion-scan`'s responsibility. Learn's scope is strictly **incremental**: what changed, what was reviewed, what was discussed.

### Step 2: Identify Candidate Rules
Look for these signals in the evidence:

| Signal | Category | Example |
|--------|----------|---------|
| Bug that was fixed | `pitfalls` | "Always check null before accessing .length" |
| Code refactored for clarity | `style` | "Use early returns instead of nested ifs" |
| Performance optimization applied | `perf` | "Batch database queries instead of N+1" |
| Pattern repeated across multiple files | `style` | "All API responses follow {error, data} shape" |
| Workaround for library/framework quirk | `pitfalls` | "Element Plus date-picker needs explicit format prop" |
| Convention the team established | `style` | "Composables return reactive refs, not raw values" |

### Step 3: Deduplicate (CRITICAL — do not skip)
This is the most important step. Rules must not pile up with duplicates.

For each candidate rule, check against existing rules:
- **Exact duplicate**: Same rule already exists -> skip, tell user
- **Semantic duplicate**: Similar rule with different wording -> skip, tell user
- **Extension**: New insight adds to an existing rule -> update existing rule with the addition
- **Conflict**: New rule contradicts existing -> flag to user, do NOT auto-write
- **Novel**: No match -> write new rule

### Step 4: Write Rules

Follow Write Protocol (`.aion/refs/write-protocol.md`, category: **Accumulative**).

For each accepted rule, append to the appropriate file in `.aion/rules/`:

**Format**:
```markdown
- **{Title}** ({source}, {YYYY-MM-DD}) [cite_count: 0, last_cited: {YYYY-MM-DD}]
  {1-2 sentence description with a concrete example from this project}
```

- `{source}`: where the rule was learned — `review`, `bugfix`, `refactor`, `discussion`, `observation`
- Always include a project-specific example, not generic advice
- New rules start with `cite_count: 0` and `last_cited` set to creation date
- Update the file-level frontmatter: increment `rule_count`, set `last_updated` to today

**Backward compatibility**: If the rule file lacks frontmatter (old format), add it:
```markdown
---
category: {pitfalls|style|perf}
rule_count: {actual count}
last_updated: {YYYY-MM-DD}
---
```

### Step 4.5: Update Rule Citations
For each existing rule that was semantically referenced during evidence collection or deduplication checks:
1. Increment its `cite_count` by 1
2. Update its `last_cited` to today's date
3. If the rule entry lacks citation metadata, add `[cite_count: 1, last_cited: {today}]`

### Step 5: Report
Present a clear summary:

```
Learning Report
-----------------------------------
Analyzed: {what was analyzed}

New Rules:
  [pitfalls] {title} — {one-line summary}
  [style] {title} — {one-line summary}

Skipped:
  {reason} — {candidate that was skipped}

Updated:
  [perf] {existing title} — added: {what was added}

Total: {N} new, {N} updated, {N} skipped
```

If no rules were worth extracting, say so honestly — not every session produces rules.

## Rule Quality Bar
A good rule is:
1. **Actionable**: tells you what TO DO or NOT DO (not just "be careful")
2. **Specific**: references this project's stack, patterns, or conventions
3. **Evidenced**: comes from a real incident, not hypothetical worry
4. **Durable**: will still be relevant in 3 months (not a temporary hack)

## Next Steps

Rules updated. They will apply automatically in future sessions.

## Checklist
Read and apply `.aion/checklists/learn.md` if it exists. If not, use the built-in checklist:
- [ ] All existing rules read before identifying candidates
- [ ] Evidence collected from appropriate sources
- [ ] Each candidate checked for duplicates/conflicts against existing rules
- [ ] Only actionable, specific, evidenced, durable rules accepted
- [ ] Each rule includes a project-specific example
- [ ] Report presented to user with clear accounting

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Extracting generic programming advice | "Use meaningful variable names" is not a project rule — it's a textbook | CRITICAL |
| Duplicating existing rules | Rule bloat makes rules harder to read and follow | HIGH |
| Writing vague rules without examples | "Be careful with dates" is not actionable without a concrete example | HIGH |
| Not reading existing rules before writing | Guaranteed duplicates and conflicts | CRITICAL |
| Extracting rules from hypothetical scenarios | Rules must come from real evidence, not "what if" thinking | MEDIUM |
| Writing temporary workarounds as permanent rules | Clutters the ruleset with things that should be removed | MEDIUM |
| Falling back to full codebase scan when evidence is empty | Violates learn's scope boundary — `/aion-scan` handles static analysis, learn handles incremental experience | CRITICAL |

## Output Format
The learning report shown in Step 5, plus updated rule files in `.aion/rules/`.

## Exit Status
- `DONE` — Rules extracted and written (or explicitly determined none worth extracting)
- `DONE_WITH_CONCERNS` — Conflicting rules found that need user resolution
- `BLOCKED` — No evidence to analyze (no recent changes, no reviews, no topic match)
- `NEEDS_CONTEXT` — Topic specified but insufficient codebase evidence found
