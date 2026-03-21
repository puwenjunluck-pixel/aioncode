# How AionCode Works

## The Core Idea

AionCode is built on one insight: **Claude Code already has great tools — what it lacks is memory and methodology.**

Every time you start a new Claude Code session, it reads `CLAUDE.md`. AionCode uses this mechanism to inject project-specific rules that Claude must follow. The rules are accumulated over time through code reviews and explicit learning sessions.

## Architecture

```
┌─────────────────────────────────────────────┐
│  Claude Code                                │
│  ┌───────────────────┐                      │
│  │ CLAUDE.md         │ ← "Read .aion/rules/ │
│  │ (auto-loaded)     │    before ANY change" │
│  └───────┬───────────┘                      │
│          │ reads                             │
│  ┌───────▼───────────┐                      │
│  │ .aion/rules/      │ ← Accumulated rules  │
│  │  pitfalls.md      │                      │
│  │  style.md         │                      │
│  │  perf.md          │                      │
│  └───────────────────┘                      │
│                                             │
│  ┌───────────────────┐                      │
│  │ Slash Commands    │ ← Structured workflow │
│  │  /aion-design     │                      │
│  │  /aion-plan       │                      │
│  │  /aion-impl       │                      │
│  │  /aion-review ────┼── extracts rules ──┐ │
│  │  /aion-learn ─────┼── extracts rules ──┤ │
│  │  /aion-save       │                    │ │
│  │  /aion-commit     │                    │ │
│  │  /aion-status     │                    ▼ │
│  └───────────────────┘     .aion/rules/     │
└─────────────────────────────────────────────┘
```

## The Learning Flywheel

### How Rules Are Created

1. **During /aion-review**: After reviewing code changes, the review command automatically identifies patterns worth remembering — bugs, conventions, performance insights — and writes them to `.aion/rules/`.

2. **During /aion-learn**: A deeper, more targeted extraction. Can analyze git history, specific topics, or review results. Use this for focused learning sessions.

3. **Manually**: You can always edit `.aion/rules/*.md` directly.

### How Rules Are Used

Every Claude Code session reads `CLAUDE.md`, which contains:
```
Before making ANY code changes, read and strictly follow all rules in .aion/rules/
```

This means rules are enforced **even when users don't use any slash commands**. Just chatting with Claude in a project with AionCode rules will benefit from accumulated intelligence.

### Deduplication

When extracting rules, AionCode checks for:
- **Exact duplicates**: Same rule already exists → skip
- **Semantic duplicates**: Similar meaning, different wording → skip
- **Extensions**: New insight adds to existing rule → update existing
- **Conflicts**: New rule contradicts existing → ask user

This prevents rules from ballooning with redundant entries.

## File-Driven Collaboration

AionCode uses `.aion/` as a shared knowledge base:

### Scenario: Designer → Developer
```
1. Designer places prototypes in .aion/prototypes/login/
2. Designer runs /aion-design → produces .aion/specs/login.md
3. git push
4. Developer: git pull → /aion-impl
5. Claude reads specs + prototypes automatically
```

### Scenario: Backend → Frontend
```
1. Backend writes .aion/contracts/api-v2.md
2. git push
3. Frontend: git pull → /aion-impl
4. Claude implements frontend according to contract
```

### Scenario: Context Preservation
```
1. Long conversation with lots of decisions
2. Before ending: /aion-save
3. Conversation context saved to .aion/ docs
4. Next session: Claude loads everything from .aion/
```

## Why Not Build a Full App?

We considered building a complete AI coding application (Vue + FastAPI + custom LLM adapters). We realized:

1. **Claude Code already has great tools** — file read/write/edit, bash, search, git
2. **Claude Code already has great UI** — terminal-native, fast, integrated
3. **The value is in the methodology and memory**, not the tool layer
4. **Maintenance burden** — a full app needs ongoing updates for every Claude API change

By building on Claude Code, we get tool improvements for free and focus entirely on what makes AionCode unique: the learning flywheel and structured workflow.
