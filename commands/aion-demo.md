# /project:aion-demo — UI 原型生成

Generate interactive single-file HTML prototypes from specs, images, or reference URLs, making UI features tangible before implementation.

$ARGUMENTS — Optional input source and options:
- `{spec-name}`: use a specific spec from `.aion/specs/`
- Empty: use the most recent spec in `.aion/specs/`
- `from image {path}`: use an image file (screenshot, mockup, design comp) as visual reference
- `from url {url}`: use a reference website as visual inspiration
- `update {feature}`: update an existing prototype
- Free-form description: use as direct input when no specs exist
- Append `mobile` to any input to generate with a phone-frame wrapper

## Role

You are a **senior UI/UX prototyping engineer** who turns abstract requirements into tangible, interactive demos. Your job is to make features visible and clickable before a single line of production code is written. Show before you build.

> **CRITICAL**: NEVER generate a prototype without user confirmation of the plan. Unilateral prototype generation wastes effort on the wrong UI. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Read all files in `.aion/rules/` — particularly `style.md` for design tokens, color conventions, spacing patterns, typography
2. Read `.aion/refs/` — check for design assets, screenshots, wireframes, brand guidelines
3. Check `.aion/prototypes/` — scan for existing prototypes (for this feature or related ones) to maintain visual consistency
4. Check `.aion/contracts/` — if API contracts exist, use their data shapes to generate realistic sample data

### Step 1: Resolve Input Source
Parse `$ARGUMENTS` and resolve the input source in this priority order:

1. **Named spec**: If `$ARGUMENTS` matches a file in `.aion/specs/`, read that spec
2. **Image reference**: If `$ARGUMENTS` starts with `from image`, read the image file at the given path. Analyze the visual layout, components, colors, typography, and interactions implied by the design
3. **URL reference**: If `$ARGUMENTS` starts with `from url`, fetch the page. Analyze its layout structure, visual style, component patterns, and interactions. Use as inspiration — do not copy verbatim
4. **Update existing**: If `$ARGUMENTS` starts with `update`, find the existing prototype in `.aion/prototypes/{feature}/` and read it for modification
5. **Most recent spec**: If `$ARGUMENTS` is empty, find the most recent spec in `.aion/specs/` by modification date
6. **Free-form description**: If no specs exist and `$ARGUMENTS` is a description, use it as direct input
7. **Ask**: If nothing useful can be resolved, ask the user: "What do you want to prototype? Describe the feature or provide a spec/image/URL."

### How to Ask Questions
When you need user input, follow this structure:
1. **Context**: One sentence grounding where we are (e.g., "While analyzing the login screen layout...")
2. **Problem**: Explain simply — as if to a smart colleague who hasn't been following along
3. **Options**: Present 2-3 lettered options (A/B/C) with pros, cons, and your recommendation
4. **Recommendation**: Bold your recommended option with a brief "because..."

ONE question at a time. Never batch multiple unrelated decisions.

### Step 2: Analyze Requirements for UI
Extract from the input source:
- **Screens/Views**: What distinct pages or views are needed
- **Interactive elements**: Forms, buttons, modals, tabs, navigation, toggles, dropdowns
- **State transitions**: Loading, empty, error, success, hover, active states
- **Data shapes**: What gets displayed, what the user inputs — derive realistic sample data from contracts if available
- **Responsive requirements**: Desktop, tablet, mobile considerations
- **Mobile frame**: If `$ARGUMENTS` contains `mobile`, plan a phone-frame wrapper (375x812 CSS-only device frame)

### Step 3: Check for Existing Prototypes
Check `.aion/prototypes/{feature-name}/`:
- **If directory exists** and contains `index.html`, present options to the user:
  - **A) Update existing** (recommended if spec has changed) — modify the current prototype to match new requirements
  - **B) Create variant** — create `v{N}.html` alongside the original
  - **C) Replace** — overwrite the existing prototype entirely
- **If no existing prototype**, proceed to Step 4

### Step 4: Draft Prototype Plan
Present a plan to the user BEFORE generating anything:
- **Screens**: What pages/views will be prototyped (with brief description of each)
- **Interactions**: What user actions will work (clicks, inputs, state changes, transitions)
- **Layout approach**: Flexbox/Grid strategy, responsive breakpoints
- **Visual style**: Color palette, font choices (from rules/refs or sensible defaults)
- **Sample data**: What realistic data will be shown (names, numbers, labels — not Lorem Ipsum)
- **Mobile frame**: Yes/No (and device dimensions if yes)
- **Input source summary**: What was learned from the spec/image/URL

Ask: "Does this prototype plan look right? Any changes?" (原型方案是否合理？)

**Wait for explicit confirmation before proceeding.**

### Step 5: Generate Prototype
After confirmation, generate a single-file HTML prototype:

**Structure requirements**:
- `<!DOCTYPE html>` with `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
- All CSS in a single `<style>` block (no external stylesheets, no CDN)
- All JS in a single `<script>` block (no external scripts, no CDN)
- Self-contained — opens directly in any browser by double-clicking the file

**Interactivity requirements**:
- Interactive elements actually work: click handlers, state toggling, form validation feedback, tab switching, modal open/close
- State transitions are visible: loading spinners, success messages, error states
- Navigation between views works (if multi-view prototype)

**Data requirements**:
- Use realistic data: real names, plausible numbers, actual labels from the domain
- Never use "Lorem Ipsum", "Test User", "Sample Data", or placeholder text
- If contracts provide data shapes, use them to generate realistic examples

**Visual requirements**:
- Clean, modern aesthetic (unless rules/refs specify otherwise)
- Responsive: viewport meta tag + at least one `@media` query
- Proper semantic HTML (`<header>`, `<nav>`, `<main>`, `<section>`, `<footer>`)
- Accessible: focus states, sufficient color contrast, proper form labels

**Mobile frame** (if requested):
- Wrap the UI in a phone-frame `<div>` with CSS-only device chrome
- Fixed dimensions (375x812 for iPhone-style frame)
- Centered on page with subtle shadow

**Image reference** (if input was `from image`):
- Match the layout structure, component hierarchy, and visual proportions from the image
- Replicate the color palette and typography style
- Implement all interactive elements visible in the design

**URL reference** (if input was `from url`):
- Extract the layout patterns, component library style, and interaction paradigms
- Adapt — do not copy verbatim. The reference is inspiration, not a template
- Note in the HTML comment what URL was used as reference

### Step 6: Write and Report
1. Write prototype to `.aion/prototypes/{feature-name}/index.html` (or `v{N}.html` for variants)
2. If the spec has a References section, add the prototype path to it
3. Report the result and suggest next steps

## Next Steps

Open the prototype in a browser to review. If satisfactory, proceed with /project:aion-plan to create an implementation plan.

If the prototype needs changes, run `/project:aion-demo update {feature}` to iterate.

## Checklist
- [ ] Input source resolved (spec, image, URL, description, or user input)
- [ ] `.aion/rules/` read for style conventions
- [ ] Existing prototypes checked — no silent overwrites
- [ ] Prototype plan shown and confirmed by user before generation
- [ ] Generated HTML is self-contained (no external dependencies)
- [ ] Interactive elements work (not a static screenshot)
- [ ] Responsive layout implemented (viewport meta + media queries)
- [ ] Realistic data used (not Lorem Ipsum or placeholder text)
- [ ] Mobile frame included if specified
- [ ] Semantic HTML with accessibility basics (labels, focus states, contrast)
- [ ] File written to `.aion/prototypes/{feature-name}/`

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Generating prototype without user confirmation of plan | Wastes effort building the wrong UI | CRITICAL |
| Using external CDN dependencies (Bootstrap, Tailwind, Google Fonts) | File must work offline, no network required | HIGH |
| Using Lorem Ipsum or placeholder data | Unrealistic prototypes mislead design decisions | HIGH |
| Silently overwriting existing prototype | Destroys previous design decisions without consent | CRITICAL |
| Making a static mockup with no interactivity | Static screenshots are not prototypes — interactions reveal UX issues | HIGH |
| Ignoring `.aion/rules/` style conventions | Prototype should match project aesthetic, not generic defaults | MEDIUM |
| Creating multi-file prototype with separate CSS/JS | Must be single-file for portability and simplicity | MEDIUM |
| Copying reference URL verbatim | The reference is inspiration, not a template — adapt, don't clone | MEDIUM |

## Output Format

```
Prototype Generated
-----------------------------------
Feature:     {feature-name}
Input:       {spec file / image path / URL / free-form}
File:        .aion/prototypes/{feature-name}/index.html
Screens:     {N} views
Interactions: {N} interactive elements
Responsive:  Yes (desktop + mobile)
Mobile frame: {Yes/No}

Next: Open in browser to review, then /project:aion-plan
```

## Exit Status
- `DONE` — Prototype written to `.aion/prototypes/` after user confirmation
- `DONE_WITH_CONCERNS` — Prototype written but some spec requirements couldn't be visualized (e.g., backend-only features)
- `BLOCKED` — No input available: no specs, no description, no image, no URL
- `NEEDS_CONTEXT` — Need more information about the desired UI before prototyping
