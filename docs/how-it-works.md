# How AionCode Works

## The Core Idea

AionCode is built on one insight: **Claude Code already has great tools — what it lacks is memory, methodology, and discipline.**

Every time you start a Claude Code session, it reads `CLAUDE.md`. AionCode uses this mechanism to inject project-specific rules (loaded from `.aion/rules/`) that Claude must follow, and provides a set of slash commands that enforce a disciplined workflow (Iron Laws + Verification Gate + bite-sized planning + root-cause debugging).

Rules and context accumulate over time through code reviews and explicit save/learn steps.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  Claude Code (or Antigravity)                              │
│  ┌───────────────────┐                                     │
│  │ CLAUDE.md         │  ← auto-loaded every session        │
│  │   ├─ metacognition │    "read ALL rules before editing" │
│  │   └─ workflow      │                                    │
│  └───────┬───────────┘                                     │
│          │ enforces                                         │
│  ┌───────▼───────────┐                                     │
│  │ .aion/rules/      │  ← accumulated rules                │
│  │   metacognition   │     Iron Laws, reflection           │
│  │   pitfalls        │     project-specific traps          │
│  │   style / perf    │     conventions                     │
│  └───────────────────┘                                     │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Slash Commands (v0.7.6 — 11 commands)                │  │
│  │   aion-scan   — cold-start scan                      │  │
│  │   aion-think  — 10-phase brainstorm / spec           │  │
│  │   aion-plan   — bite-sized TDD plan                  │  │
│  │   aion-qa     — browser QA → bug reports             │  │
│  │   aion-fix    — 4-phase root-cause debug             │  │
│  │   aion-audit  — security + performance               │  │
│  │   aion-review ─ Verification Gate + auto-learn ──┐   │  │
│  │   aion-save   — context → .aion/                 │   │  │
│  │   aion-commit — safe commit (review + gate req) │   │  │
│  │   aion-loop   — think→plan→impl→review→commit   │   │  │
│  │   aion-help   — self-guide                      ▼   │  │
│  │                                         .aion/rules/ │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## The Learning Flywheel

### How Rules Are Created

1. **`aion-review`**: After each review, patterns worth remembering — bugs, conventions, performance insights — are auto-extracted to `.aion/rules/`.
2. **`aion-save`**: Captures conversation context and routes it to `.aion/` by type (rules / spec / plan / changelog). Always appends, never overwrites.
3. **Manually**: Edit `.aion/rules/*.md` directly whenever you want.

### How Rules Are Used

Every Claude Code session reads `CLAUDE.md`, which says:

```
NEVER write or edit any code file without first reading ALL rules in .aion/rules/
```

Rules are therefore enforced **even without invoking any slash command**. Just chatting with Claude in a project that has AionCode rules benefits from the accumulated intelligence.

### Deduplication

When extracting rules, AionCode checks for:

- **Exact duplicates**: same rule exists → skip
- **Semantic duplicates**: similar meaning, different wording → skip
- **Extensions**: new insight adds to existing rule → update existing
- **Conflicts**: new rule contradicts existing → ask user

This prevents rules from ballooning with redundant entries.

## Discipline Layer (v0.7.6)

AionCode surgically fuses a discipline layer on top of the command structure:

- **Iron Laws**: four non-negotiable rules (no rule skip / no completion without verification / no fix without root cause / no design without approval). Injected into `aion-think`, `aion-review`, `aion-fix`.
- **Verification Gate**: evidence table required before claiming completion. Enforced by `aion-review` Step 2.8.
- **10-phase brainstorming**: `aion-think` explores approaches, challenges assumptions (Phase 5), and only then converges on a spec.
- **Bite-sized TDD plans**: `aion-plan` targets 2–5 min per step, TDD-oriented.

## File-Driven Collaboration

`.aion/` is a shared knowledge base versioned in Git:

### Designer → Developer
```
1. Designer places prototypes in .aion/prototypes/login/
2. Designer runs /project:aion-think → produces .aion/specs/login.md
3. git push
4. Developer pulls and asks Claude to implement — specs + prototypes load automatically
```

### Backend → Frontend
```
1. Backend writes .aion/contracts/api-v2.md
2. git push
3. Frontend pulls and implements — contract loads automatically
```

### Context Preservation
```
1. Long conversation with lots of decisions
2. Before ending: /project:aion-save
3. Context saved to .aion/
4. Next session: Claude loads everything from .aion/
```

## Why Not Build a Full App?

We considered a complete AI coding application (Vue + FastAPI + custom LLM adapters). We chose not to:

1. **Claude Code already has great tools** — file read/write/edit, bash, search, git
2. **Claude Code already has great UI** — terminal-native, fast, integrated
3. **The value is in the methodology and memory**, not the tool layer
4. **Maintenance burden** — a full app needs ongoing updates for every Claude API change

By building on Claude Code (and Antigravity), we get tool improvements for free and focus entirely on what makes AionCode unique: the learning flywheel and the disciplined workflow.
