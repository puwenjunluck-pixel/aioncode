# AionCode

**AI-native development system for Claude Code** — structured workflow + auto-learning rules that make AI smarter with every iteration.

> AionCode is NOT another AI coding tool. It's a skill pack that runs inside Claude Code, adding methodology, project memory, and team collaboration on top of Claude's native capabilities.

## Why AionCode?

Every AI coding session starts from zero. Claude doesn't remember the pitfalls you hit last week, the code conventions your team agreed on, or the performance lessons you learned the hard way.

**AionCode fixes this with a learning flywheel:**

```
Write Code → Review → Extract Rules → Rules Loaded Next Time
     ↑                                        ↓
     └──── AI avoids past mistakes ←──────────┘
```

Your `.aion/rules/` directory accumulates project intelligence over time. Every review, every bugfix, every refactoring teaches the AI something new. After a few weeks, Claude knows your project's quirks better than a new team member.

## Quick Start

### Install

```bash
# Clone AionCode
git clone https://github.com/user/aioncode.git

# Install into your project
bash aioncode/install.sh /path/to/your/project
```

This creates:
- `.claude/commands/` — 18 slash commands
- `.aion/` — project intelligence directory (commit this to git!)
- `.aion/bin/` — tools (dashboard.py, uninstall.sh)
- `CLAUDE.md` — rules auto-loading (Claude reads this automatically)

### Use

Open Claude Code in your project and use the commands:

```
/project:aion-design    Design a new feature
/project:aion-demo      Generate interactive HTML prototype (optional)
/project:aion-plan      Create an implementation plan
/project:aion-impl      Execute the plan step by step
/project:aion-test      Generate tests, coverage analysis, perf scripts
/project:aion-review    Review changes + auto-extract rules
/project:aion-learn     Deep-dive rule extraction
/project:aion-save      Save conversation context before it's lost
/project:aion-commit    Safe commit with changelog
/project:aion-status    See your project intelligence stats
/project:aion-help      Show commands, workflows, and usage guide
```

**The recommended flow** (not enforced):
```
design → (demo) → plan → impl → (test) → verify → review → learn → commit
```

But each command works independently — use what you need.

### Dashboard

```bash
python3 .aion/bin/dashboard.py
# Opens http://localhost:19200
```

### Uninstall

```bash
bash .aion/bin/uninstall.sh /path/to/your/project
```

This removes commands and CLAUDE.md section but preserves `.aion/` (your rules are valuable!).

## Three Pillars

### 1. Development Methodology
Structured workflow: requirements → planning → implementation → review → commit. Each phase has a dedicated command with best practices baked in.

### 2. Project Intelligence (Core Differentiator)
Auto-learning rules in `.aion/rules/`:
- **pitfalls.md** — Gotchas and traps specific to your project
- **style.md** — Code conventions your team follows
- **perf.md** — Performance guidelines learned from experience

Rules are auto-extracted during reviews and can be manually extracted with `/aion-learn`. They're loaded into EVERY Claude session via `CLAUDE.md` — even without slash commands.

### 3. Team Collaboration
File-driven collaboration through `.aion/`:

```
Designer: places prototypes in .aion/prototypes/ → git push
Developer: /aion-impl reads prototypes automatically

Backend: writes .aion/contracts/api-v2.md → git push
Frontend: /aion-impl reads contracts automatically

Anyone: /aion-save before ending conversation → git push
Next person: Claude loads all context automatically
```

## Project Structure

```
your-project/
├── .claude/commands/         # 8 AionCode slash commands
├── .aion/                    # Project intelligence (git tracked)
│   ├── rules/                # Auto-learned rules
│   │   ├── pitfalls.md
│   │   ├── style.md
│   │   └── perf.md
│   ├── refs/                 # External docs (client requirements, etc.)
│   ├── prototypes/           # UI prototypes (HTML/JS demos)
│   ├── specs/                # Requirement specs (/aion-design output)
│   ├── plans/                # Implementation plans (/aion-plan output)
│   ├── reviews/              # Review results (/aion-review output)
│   ├── contracts/            # Interface contracts (cross-team)
│   ├── config.yml            # AionCode configuration
│   └── changelog.md          # Auto-maintained work log
└── CLAUDE.md                 # Rules auto-loading
```

## The Learning Flywheel

```
Week 1:  0 rules  → Claude makes common mistakes
Week 2:  5 rules  → Claude avoids the same mistakes
Week 4:  15 rules → Claude knows your project's quirks
Week 8:  25 rules → Claude codes like a senior team member
```

Every rule is:
- **Actionable** — tells you what to do or not do
- **Specific** — references your project's stack and patterns
- **Evidenced** — comes from a real incident, not theory
- **Durable** — still relevant months later

## Verification

```bash
# Check installation
bash aioncode/install.sh --check /path/to/your/project

# Verify rules are loaded (just ask Claude anything in your project)
# Claude will mention reading .aion/rules/ files
```

## Requirements

- [Claude Code](https://claude.com/claude-code) CLI
- A git repository

## License

MIT
