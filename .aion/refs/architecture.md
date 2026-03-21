# Project Architecture

## Tech Stack
- Language: Python 3 (dashboard.py), Bash (install.sh), Markdown (commands)
- Framework: Python stdlib `http.server` (zero external dependencies)
- Database: N/A (JSON file persistence — `projects.json`)
- Test Framework: None (no tests exist)
- Build Tool: N/A (`install.sh` is the distribution mechanism)
- CI/CD: N/A (no workflows configured)

## Directory Structure
- `commands/` — 18 AionCode slash command files (Markdown prompts, ~200 lines avg)
- `templates/` — Installation templates: CLAUDE.md.tpl, aion/ scaffolding, hooks, settings
- `docs/` — Design docs: aion-design.md (system architecture), commands.md, how-it-works.md
- `.aion/` — Project intelligence directory (dogfooding — this project uses itself)
- `.claude/` — Claude Code configuration (hooks, settings, installed commands)

## Entry Points
- `dashboard.py` — Web UI server (port 19200), 4437 lines, single-file
- `install.sh` — Installation script (435 lines), 3 modes: install / --check / --upgrade
- `uninstall.sh` — Removal script (46 lines), preserves .aion/

## Key Patterns
- **Routing**: `path.startswith()` prefix matching in `do_GET/POST/PUT/DELETE`, specific routes before generic
- **Path encoding**: Base64 URL-safe encoding for project paths in URLs (`encode_project_path`/`decode_project_path`)
- **CLAUDE.md merge**: `<!-- AIONCODE:START/END -->` markers for idempotent content replacement
- **Custom YAML parser**: Hand-written state machine in `read_team_config()` (zero-dep constraint)
- **Event streaming**: SSE via `.aion/monitor/events.jsonl` with 2s polling and keepalive
- **File-driven collaboration**: All intelligence in `.aion/` (git-tracked), teams sync via commits
- **Commands are pure Markdown**: No executable code, interpreted by Claude Code at runtime

## API Surface (dashboard.py, port 19200)
- GET: 17 endpoints (projects, stats, files, bugs, team, monitor, commands, browse)
- POST: 7 endpoints (add/remove/init project, create file, write team, clear monitor, upgrade)
- PUT: 1 endpoint (update file)
- DELETE: 1 endpoint (delete file)

## Build & Run
- Dev: `python dashboard.py` (opens http://localhost:19200)
- Test: N/A (no tests)
- Build: N/A (no build step)
- Install: `bash install.sh /path/to/project`
- Check: `bash install.sh --check /path/to/project`
- Upgrade: `bash install.sh --upgrade /path/to/project`

## Known Gaps
- Zero test coverage
- No CI/CD pipeline
- `uninstall.sh` only removes 11 of 18 commands (missing: scan, demo, test, bug, crosscheck, upgrade, help)
- dashboard.py is 4437 lines in a single file (embedded HTML ~3000 lines)

<!-- aion:fingerprint:f892d9bb9b5db44ac700e8ec48afe051 -->
