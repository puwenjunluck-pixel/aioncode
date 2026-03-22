---
name: aion-skill-creator
description: Create new Claude Code skills from scratch with guided scaffolding. Use when users want to create a skill, make a skill, build a skill, write a SKILL.md, scaffold a skill directory, or say "新建技能", "创建技能", "写一个 skill". Also triggers when users say "turn this into a skill" or want to capture a workflow as a reusable skill. ALWAYS use this skill for any skill creation task, even if the user doesn't explicitly mention "skill creator".
---

# Aion Skill Creator

A lightweight, guided skill creation tool. Walks you through intent capture, generates a standard SKILL.md with proper structure, and scaffolds the skill directory.

## Workflow

### Step 1: Capture Intent

Ask the user these 4 questions (skip any already answered in conversation):

1. **What should this skill do?** — The core capability (e.g., "generate API documentation from code", "review CSS for accessibility")
2. **When should it trigger?** — User phrases and contexts that should activate the skill (e.g., "when the user asks to review their CSS", "when working with .proto files")
3. **What's the output?** — Expected format: files, terminal output, conversation guidance, code changes, etc.
4. **Does it need scripts or reference docs?** — Whether the skill needs executable scripts (`scripts/`), supporting docs (`references/`), or template files (`assets/`)

If the user says "turn this into a skill" — extract answers from the current conversation: tools used, step sequence, corrections made, input/output observed. Confirm with the user before proceeding.

### Step 2: Generate SKILL.md

Use this template structure:

```markdown
---
name: {skill-name}
description: {what it does + when to trigger — be specific and slightly "pushy" to ensure triggering}
---

# {Skill Title}

{1-2 sentence overview of what the skill does and why it's useful.}

## When to Use

{Bullet list of specific scenarios and user phrases that should trigger this skill.}

## How It Works

{Step-by-step instructions for Claude to follow when this skill is activated.
Use imperative form. Explain the WHY behind each step, not just the what.}

## Output Format

{Expected output structure, examples if helpful.}
```

### Step 3: Scaffold Directory

Create the skill directory structure:

```bash
mkdir -p ~/.claude/skills/{skill-name}
```

Write SKILL.md to `~/.claude/skills/{skill-name}/SKILL.md`.

If the user needs supporting files, also create:
```bash
mkdir -p ~/.claude/skills/{skill-name}/scripts
mkdir -p ~/.claude/skills/{skill-name}/references
mkdir -p ~/.claude/skills/{skill-name}/assets
```

### Step 4: Confirm

Tell the user:
- The skill is installed at `~/.claude/skills/{skill-name}/`
- They can test it immediately by starting a new Claude Code conversation and using a trigger phrase
- They can edit SKILL.md anytime to refine behavior

## Writing Guidelines

### Description Field (Most Important)

The `description` in frontmatter is the **primary trigger mechanism**. Claude reads all skill descriptions to decide which to load. Write it to be:

- **Specific**: Include exact user phrases, file types, domain terms
- **Slightly pushy**: Err on the side of over-triggering. Better to be consulted and not needed than to miss a relevant request
- **Action-oriented**: Start with what the skill does, then list contexts

**Good example:**
```
Generate comprehensive API documentation from source code. Use when the user mentions API docs, documentation generation, endpoint documentation, OpenAPI, Swagger, or asks to document their API, REST endpoints, or service interfaces. Also use when working with route files and the user wants to understand or document the API surface.
```

**Bad example:**
```
Helps with documentation.
```

### SKILL.md Body

- **Under 500 lines** — Keep it focused. If approaching the limit, split into `references/` files with clear pointers
- **Explain WHY** — `"Check for unused imports because they slow CI lint times"` beats `"ALWAYS remove unused imports"`
- **Use imperative form** — `"Read the file"`, not `"You should read the file"`
- **Include examples** — Show input/output pairs for clarity
- **Avoid rigid MUSTs** — Explain reasoning so Claude can handle edge cases intelligently

### Progressive Disclosure (Three Levels)

1. **Metadata** (name + description) — Always loaded into context (~100 words). This is your trigger surface.
2. **SKILL.md body** — Loaded when skill activates. Keep under 500 lines for fast loading.
3. **Bundled resources** — Loaded on demand. Scripts execute without being read into context.

```
my-skill/
├── SKILL.md           ← Level 1 (frontmatter) + Level 2 (body)
├── scripts/           ← Level 3: executable code for deterministic tasks
│   └── transform.py
├── references/        ← Level 3: docs loaded as needed
│   └── api-spec.md
└── assets/            ← Level 3: template files, icons, etc.
    └── template.html
```

### When to Use Scripts vs Instructions

- **Scripts** (`scripts/`): For deterministic, repeatable operations — file transforms, data parsing, validation checks. Claude runs them without reading the source.
- **Instructions** (in SKILL.md body): For judgment-based tasks — code review criteria, design decisions, workflow guidance. Claude interprets and adapts them.

## Advanced

For eval-driven skill development with benchmarking, blind comparison, and description optimization — install the full `skill-creator`:

```bash
npx skills add anthropics/skill-creator
```
