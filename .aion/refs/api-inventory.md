# API Inventory

## Endpoints (dashboard.py, port 19200)

### GET
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| GET | `/` | `_serve_html()` | Serve embedded dashboard UI |
| GET | `/api/projects` | `_handle_list_projects()` | List registered projects |
| GET | `/api/projects/{enc}/stats` | `_handle_stats()` | Project statistics |
| GET | `/api/projects/{enc}/bugs/stats` | `_handle_bug_stats()` | Bug aggregation stats |
| GET | `/api/projects/{enc}/files` | `_handle_file_tree()` | .aion/ file tree |
| GET | `/api/projects/{enc}/file` | `_handle_read_file()` | Read single file (query: path) |
| GET | `/api/projects/{enc}/sessions` | `_handle_sessions()` | Session entries (query: limit) |
| GET | `/api/projects/{enc}/events/stream` | `_handle_events_stream()` | SSE real-time events |
| GET | `/api/projects/{enc}/events/recent` | `_handle_recent_events()` | Recent events summary |
| GET | `/api/projects/{enc}/bugs` | `_handle_list_bugs()` | List bugs (query: category, status, assignee, severity) |
| GET | `/api/projects/{enc}/team` | `_handle_read_team()` | Read team.yml |
| GET | `/api/commands` | `_handle_list_commands()` | List command files |
| GET | `/api/commands/{name}` | `_handle_read_command()` | Read command content |
| GET | `/api/browse` | `_handle_browse()` | Filesystem browser (query: path) |
| GET | `/monitor/{enc}` | `_serve_monitor_html()` | Monitor page |
| GET | `/api/monitor/{enc}/events` | `_handle_monitor_events()` | Monitor events (query: since) |
| GET | `/api/monitor/{enc}/state` | `_handle_monitor_state()` | Aggregated monitor state |

### POST
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| POST | `/api/projects/add` | `_handle_add_project()` | Register project |
| POST | `/api/projects/remove` | `_handle_remove_project()` | Unregister project |
| POST | `/api/projects/init` | `_handle_init_project()` | Initialize AionCode |
| POST | `/api/projects/{enc}/file` | `_handle_create_file()` | Create file in .aion/ |
| POST | `/api/projects/{enc}/team` | `_handle_write_team()` | Update team.yml |
| POST | `/monitor/{enc}/clear` | `_handle_monitor_clear()` | Clear monitor events |
| POST | `/api/projects/{enc}/upgrade` | `_handle_upgrade_project()` | Run --upgrade |

### PUT
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| PUT | `/api/projects/{enc}/file` | `_handle_write_file()` | Update file in .aion/ |

### DELETE
| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| DELETE | `/api/projects/{enc}/file` | `_handle_delete_file()` | Delete file from .aion/ |

## Auth
- Phase 1: `is_admin()` always returns True (local mode)
- Phase 2+: Will check team.yml role

## Path Encoding
- `{enc}` = base64 URL-safe encoded project path
- Encoder: `encode_project_path()`, Decoder: `decode_project_path()` (handles padding)

## Security
- `_validate_aion_path()` prevents path traversal — all file ops restricted to .aion/
- Command name sanitized (remove `/`, `\\`, `..`)

<!-- aion:fingerprint:0df2b7cff5176e43d7fac87ce91c04f0 -->
