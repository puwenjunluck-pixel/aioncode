---
status: completed
created_at: 2026-03-22
spec: dual-web-architecture.md
version: 1
previous_version: null
change_reason: null
author: unknown
scope: full
current_step: 10
total_steps: 10
---

# Plan: Dashboard v0.5 — 副驾驶重构

## Architecture Decisions

1. **Core 层统一**：新建 `aioncode/core/` 包，提取 `init_project` 等共享逻辑。CLI (`commands/init.py`) 和 Web (`routers/projects.py`) 共用同一套底层函数，消除代码重复。
   - 证据：`dashboard.py:161-243` 的 `init_project()` 是轻量版（~80 行），`commands/init.py:1-468` 的 `_init_project()` 是完整版。用户要求合并为 `core.project.init_project()`，取 CLI 的严谨性 + dashboard 的灵活性。

2. **FastAPI + uvicorn 替代 stdlib http.server**：异步非阻塞，原生 SSE/Pydantic 支持。
   - 证据：当前 `dashboard.py:828` 的 `DashboardHandler` 继承 `http.server.BaseHTTPRequestHandler`，路由用 `path.startswith()` 前缀匹配（`pitfalls.md:24-25` 已标记为顺序敏感陷阱）。FastAPI 路径参数彻底消除此问题。

3. **双进程隔离**：主进程 CLI 交互，子进程 uvicorn Web。
   - 证据：`commands/dashboard.py:1-15` 当前直接调用 `dashboard_main()`，改为 `multiprocessing.Process` 启动。

4. **前端一步到位**：后端 FastAPI 迁移 + 副驾驶 UI 重设计同步完成。
   - 当前 HTML_PAGE（`dashboard.py:1490-4111`，2621 行）和 MONITOR_HTML（`dashboard.py:4112-4775`，664 行）统一重写为副驾驶风格。

5. **前端构建时注入**：开发时 CSS/JS/HTML 分离，`build_frontend.py` 生成 `embedded.py`。
   - 证据：`style.md:21-22` 要求"分发物必须单文件自包含"。

6. **意图上报预留**：`services/intent_reporter.py` 作为可选模块预留，v0.6 实现。

7. **stdlib HTTP 客户端**：意图上报使用 `urllib.request`（复用 `utils/network.py:29-40` 的 `_github_get()` 模式），不引入 `httpx`/`requests`。

## Implementation Steps

### Step 1: 依赖更新 + 包结构创建
- **Description**: 添加 FastAPI/uvicorn 依赖，创建新包结构骨架（空文件），不删旧文件。验证 PyInstaller 能打包 FastAPI。
- **Files**:
  - 修改 `pyproject.toml` — 添加 `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0`
  - 创建 `aioncode/core/__init__.py`
  - 创建 `aioncode/core/project.py` — 空骨架
  - 创建 `aioncode/internal/dashboard/__init__.py`
  - 创建 `aioncode/internal/dashboard/app.py` — 最小 FastAPI app (仅 `GET /` 返回 "ok")
  - 创建 `aioncode/internal/dashboard/config.py`
  - 创建 `aioncode/internal/dashboard/routers/__init__.py`
  - 创建 `aioncode/internal/dashboard/services/__init__.py`
  - 创建 `aioncode/internal/dashboard/models/__init__.py`
  - 创建 `aioncode/internal/dashboard/frontend/__init__.py`
  - 修改 `aioncode.spec` — 添加 FastAPI/uvicorn hiddenimports（`fastapi`, `uvicorn`, `uvicorn.lifespan.on`, `uvicorn.protocols.http.h11_impl`, `starlette`, `pydantic`, `h11`, `anyio`, `sniffio`, `click`, `colorama`, `httptools`），更新 `aioncode.internal.dashboard` 为包
- **Dependencies**: None
- **Complexity**: medium
- **Verification**: `pip install -e .` + `python -c "from aioncode.internal.dashboard.app import create_app; print('ok')"` + `pyinstaller aioncode.spec` 打包验证
- **Status**: Not started

### Step 2: 提取 config + 编码工具
- **Description**: 从 `dashboard.py` 提取配置常量和路径编码工具到独立模块。
- **Files**:
  - 创建 `aioncode/internal/dashboard/config.py` — 从 `dashboard.py:26-52` 提取 `PORT`, `AION_DIRS`, `MARKER_START/END`, 路径解析逻辑；从 `dashboard.py:474-475` 提取 `MONITOR_EVENTS_DIR/FILE`；从 `dashboard.py:589-590` 提取 `BUGS_DIR`, `TEAM_FILE`
  - 创建 `aioncode/internal/dashboard/services/encoding.py` — 从 `dashboard.py:456-467` 提取 `encode_project_path()`, `decode_project_path()`
- **Dependencies**: Step 1
- **Complexity**: small
- **Status**: Not started

### Step 3: 提取 services 层（7 模块）
- **Description**: 将 `dashboard.py` 的 30 个顶层函数原样迁移到 services/ 模块。纯函数搬迁，零逻辑改动。
- **Files**:
  - 创建 `services/project_registry.py` — 从 `dashboard.py:61-78,84-153` 提取 `_resolve_projects_file()`, `load_projects()`, `save_projects()`, `add_project()`, `remove_project()`
  - 创建 `services/stats.py` — 从 `dashboard.py:251-336` 提取 `_count_rules_in_file()`, `_count_files_in_dir()`, `_last_activity()`, `get_project_stats()`
  - 创建 `services/file_ops.py` — 从 `dashboard.py:343-449` 提取 `_validate_aion_path()`, `get_file_tree()`, `read_file()`, `write_file()`, `create_file()`, `delete_file()`
  - 创建 `services/monitor.py` — 从 `dashboard.py:478-582` 提取 `read_monitor_events()`, `compute_monitor_state()`
  - 创建 `services/bugs.py` — 从 `dashboard.py:593-683` 提取 `_parse_bug_frontmatter()`, `list_bugs()`, `get_bug_stats()`
  - 创建 `services/team.py` — 从 `dashboard.py:686-812` 提取 `read_team_config()`, `write_team_config()`, `is_admin()`（含自定义 YAML 解析器）
  - 创建 `services/intent_reporter.py` — 空骨架（v0.6 实现），仅定义 `class IntentReporter` stub
- **Dependencies**: Step 2
- **Complexity**: large（函数多，但每个都是简单搬迁）
- **Verification**: 为每个 service 模块写单元测试，确保函数签名和返回值不变
- **Status**: Not started

### Step 4: Core 层 — 统一 init_project
- **Description**: 创建 `aioncode/core/project.py`，合并 dashboard 和 CLI 的 init_project 逻辑。CLI 的 `commands/init.py` 改为调用 core 版本。
- **Files**:
  - 创建 `aioncode/core/project.py` — 合并逻辑：
    - CLI 版 `commands/init.py:_init_project()` 的严谨性（错误处理、路径校验）
    - dashboard 版 `dashboard.py:161-243` 的灵活性（可选参数）
    - 新增 `events.jsonl` 实时写入（init 时写入 `[System] Project initialized`）
    - 函数签名：`init_project(project_path: str, *, project_name: str | None = None, skip_commands: bool = False, quiet: bool = False) -> dict`
  - 修改 `aioncode/commands/init.py` — `_init_project()` 改为调用 `core.project.init_project()`，保留 CLI 交互层（rich 输出、用户提示）
  - 修改 `services/project_registry.py` — 原 dashboard `init_project()` 替换为导入 `core.project.init_project`
- **Dependencies**: Step 3
- **Complexity**: large（需要仔细合并两个实现的差异）
- **Verification**: `pytest tests/test_cli_init.py` 确保 CLI init 不回归 + 新增 `tests/test_core_project.py`
- **Status**: Not started

### Step 5: Pydantic 模型
- **Description**: 为所有 API 请求/响应定义 Pydantic 模型，提供类型安全和自动验证。
- **Files**:
  - 创建 `models/schemas.py` — 定义：
    - `ProjectInfo`, `ProjectAddRequest`, `ProjectRemoveRequest`
    - `FileReadResponse`, `FileWriteRequest`, `FileCreateRequest`
    - `ProjectStats`
    - `MonitorState`, `MonitorEvent`
    - `BugItem`, `BugStats`, `BugFilters`
    - `TeamConfig`, `TeamWriteRequest`
    - `CommandInfo`
    - `SSEEvent`
    - 通用 `ApiResponse(ok: bool, message: str, data: Any = None)`
- **Dependencies**: Step 3
- **Complexity**: medium
- **Status**: Not started

### Step 6: FastAPI 路由层（7 个 router）
- **Description**: 将 `dashboard.py` 的 25 个 `_handle_*` 方法映射到 FastAPI 路由函数。SSE 从 blocking `while True` + `time.sleep(2)` 迁移为 async generator + `asyncio.sleep(2)`。
- **Files**:
  - 创建 `routers/projects.py` — 映射 `_handle_list_projects` → `GET /api/projects`；`_handle_add_project` → `POST /api/projects/add`；`_handle_remove_project` → `POST /api/projects/remove`；`_handle_init_project` → `POST /api/projects/init`；`_handle_stats` → `GET /api/projects/{encoded}/stats`；`_handle_upgrade_project` → `POST /api/projects/{encoded}/upgrade`
  - 创建 `routers/files.py` — 映射 `_handle_file_tree` → `GET /api/projects/{encoded}/files`；`_handle_read_file` → `GET /api/projects/{encoded}/file`；`_handle_write_file` → `PUT /api/projects/{encoded}/file`；`_handle_create_file` → `POST /api/projects/{encoded}/file`；`_handle_delete_file` → `DELETE /api/projects/{encoded}/file`
  - 创建 `routers/monitor.py` — 映射 `_handle_monitor_events` → `GET /api/monitor/{encoded}/events`；`_handle_monitor_state` → `GET /api/monitor/{encoded}/state`；`_handle_monitor_clear` → `POST /api/monitor/{encoded}/clear`；`_handle_events_stream` → `GET /api/projects/{encoded}/events/stream`（SSE async）；`_handle_recent_events` → `GET /api/projects/{encoded}/events/recent`
  - 创建 `routers/bugs.py` — 映射 `_handle_list_bugs` → `GET /api/projects/{encoded}/bugs`；`_handle_bug_stats` → `GET /api/projects/{encoded}/bugs/stats`
  - 创建 `routers/team.py` — 映射 `_handle_read_team` → `GET /api/projects/{encoded}/team`；`_handle_write_team` → `POST /api/projects/{encoded}/team`
  - 创建 `routers/commands.py` — 映射 `_handle_list_commands` → `GET /api/commands`；`_handle_read_command` → `GET /api/commands/{name}`
  - 创建 `routers/browse.py` — 映射 `_handle_browse` → `GET /api/browse`
  - 创建 `routers/logs.py` — 映射 `_handle_sessions` → `GET /api/projects/{encoded}/sessions`；`_handle_changelog` → `GET /api/projects/{encoded}/changelog`
  - 修改 `app.py` — 注册所有 router，配置 CORS 中间件，定义 lifespan（启动时 load_projects）
- **Dependencies**: Step 5（Pydantic 模型）, Step 3/4（services）
- **Complexity**: large（25 个路由，但每个都是简单的 service 调用包装）
- **SSE 迁移关键代码**:
  ```python
  # 旧: dashboard.py:1257-1298 (blocking)
  # while True: time.sleep(2)
  # 新: routers/monitor.py (async)
  async def _event_generator(project_path: str):
      last_line = 0
      while True:
          events, total = read_monitor_events(project_path, last_line)
          for event in events:
              yield f"data: {json.dumps(event)}\n\n"
          last_line = total
          yield ": keepalive\n\n"
          await asyncio.sleep(2)
  ```
- **Status**: Not started

### Step 7: 前端重设计 — 副驾驶 UI + 构建系统
- **Description**: 重写前端为副驾驶风格（命令面板 + 折叠面板 + 图标栏 + 状态栏），CSS/JS 分离为 static/ 文件，创建 `build_frontend.py` 构建脚本生成 `embedded.py`。
- **Files**:
  - 创建 `frontend/static/index.html` — 副驾驶主页面（替代 `dashboard.py:1490-4111` 的 HTML_PAGE）
    - 窄图标栏（48px，hover 展开）
    - 命令面板（Cmd+K / Ctrl+K）
    - 折叠面板：Overview / Files / Monitor / Bugs / Team（可同时打开）
    - 底部状态栏：当前项目、活跃会话数、最后事件、云端状态
  - 创建 `frontend/static/monitor.html` — 任务控制台页面（替代 `dashboard.py:4112-4775` 的 MONITOR_HTML）
    - 保留空间主题风格（MET 时钟、遥测条、终端面板）
    - SSE 实时更新
  - 创建 `frontend/static/style.css` — 纯暗色主题 CSS（CSS 变量、Flexbox 布局）
  - 创建 `frontend/static/app.js` — 主 JS 逻辑（API 调用、面板管理、命令面板、SSE 连接）
  - 创建 `frontend/static/monitor.js` — 任务控制台 JS
  - 创建 `frontend/build_frontend.py` — 构建脚本：读取 CSS/JS → 注入 HTML `<style>`/`<script>` → 生成 `frontend/embedded.py`（EMBEDDED_HTML / EMBEDDED_MONITOR_HTML 字符串常量）
  - 创建 `frontend/embedded.py` — 由 build 脚本生成，git tracked
  - 修改 `app.py` — 添加 dev 模式检测（`--dev` 参数时从 static/ 加载，否则从 embedded.py 加载）
- **Dependencies**: Step 6（路由层已就位，前端 API 调用需要对应端点）
- **Complexity**: large（前端重写 3285 行 HTML/CSS/JS）
- **Status**: Not started

### Step 8: CLI 入口 + 双进程隔离
- **Description**: 重写 `commands/dashboard.py`，主进程保持 CLI 交互能力，子进程运行 uvicorn。
- **Files**:
  - 修改 `aioncode/commands/dashboard.py` — 重写为：
    ```python
    def run_dashboard(args):
        from multiprocessing import Process
        from aioncode.internal.dashboard import create_app
        import uvicorn

        def _run_server():
            app = create_app(dev=args.dev)
            uvicorn.run(app, host=args.host, port=args.port, workers=1, loop="asyncio")

        proc = Process(target=_run_server, daemon=True)
        proc.start()
        # 主进程: 打印信息 + 等待 Ctrl+C
    ```
  - 修改 `aioncode/main.py` — 添加 `--dev` 参数到 dashboard 子命令
- **Dependencies**: Step 6, Step 7
- **Complexity**: medium
- **Verification**: `aioncode dashboard` 启动验证，`aioncode dashboard --dev` dev 模式验证
- **Status**: Not started

### Step 9: PyInstaller 打包 + 集成测试
- **Description**: 验证完整打包流程，编写集成测试覆盖所有 API 端点。
- **Files**:
  - 修改 `aioncode.spec` — 最终调整 hiddenimports 和 datas
  - 创建 `tests/test_dashboard_api.py` — 集成测试：用 FastAPI TestClient 测试所有路由端点
  - 创建 `tests/test_dashboard_sse.py` — SSE 流测试
  - 修改 `tests/conftest.py` — 添加 dashboard app fixture
- **Dependencies**: Step 8
- **Complexity**: large
- **Verification**: `pytest tests/test_dashboard_*.py` + `pyinstaller aioncode.spec` + 手动验证 macOS/Linux/Windows 二进制
- **Status**: Not started

### Step 10: 清理 + 文档
- **Description**: 删除旧 `dashboard.py` 单文件，更新 changelog，验证全流程。
- **Files**:
  - 删除 `aioncode/internal/dashboard.py`（旧 4810 行单文件）
  - 修改 `.aion/changelog.md` — 记录 v0.5 重构
  - 修改 `aioncode/__init__.py` — 版本号更新为 `0.5.0`
  - 验证 `.aion/rules/pitfalls.md` — "dashboard.py 路由匹配顺序敏感" 规则标记为 deprecated（FastAPI 路径参数已消除此问题）
  - 验证 `.aion/rules/style.md` — "dashboard.py 4784 行单文件" 豁免标记为 resolved
- **Dependencies**: Step 9（所有测试通过）
- **Complexity**: small
- **Verification**: `ruff check aioncode/` + `pytest` 全量 + `aioncode dashboard` 端到端验证
- **Status**: Not started

## Verification Strategy

### 方法: integration_test + build_check + manual_check

### 覆盖范围:
1. **单元测试** — 每个 service 模块的核心函数
2. **API 集成测试** — 使用 FastAPI TestClient 测试所有 29 个 API 端点
3. **SSE 测试** — 验证事件流正常推送
4. **PyInstaller 构建** — 四平台打包验证
5. **端到端** — 浏览器手动验证 UI 功能

### 命令:
```bash
# 单元测试
pytest tests/ -v

# Lint
ruff check aioncode/
ruff format --check aioncode/

# 构建验证
pyinstaller aioncode.spec
./dist/aioncode dashboard --port 19201  # 打包后验证

# 行数检查
find aioncode/internal/dashboard -name "*.py" -exec wc -l {} \; | sort -rn
# 每个文件 ≤ 500 行
```

### 成功标准:
- [ ] 所有现有功能不回归（项目列表、文件浏览编辑、统计、SSE 监控、Bug 看板、团队）
- [ ] `aioncode dashboard` 正常启动，浏览器访问 `http://localhost:19200`
- [ ] `aioncode dashboard --dev` 从 static/ 加载前端
- [ ] 每个拆分文件 ≤ 500 行，每个函数 ≤ 50 行
- [ ] `ruff check` + `pytest` 全部通过
- [ ] PyInstaller 打包后可运行（至少 macOS 验证）
- [ ] CLI `aioncode init` 不回归（core 层统一后）
- [ ] 副驾驶 UI 功能完整：命令面板(Cmd+K)、折叠面板、图标栏、状态栏

## Risks

| 风险 | 影响 | 缓解 |
|------|------|------|
| **uvicorn + PyInstaller 隐式依赖** | 打包后崩溃 | Step 1 立即验证打包，穷举 hiddenimports。参考 `aioncode.spec:25-35` |
| **Core 层合并引入回归** | CLI init 功能异常 | Step 4 必须通过 `test_cli_init.py` 原有测试 |
| **前端重写丢失功能** | 用户操作异常 | Step 7 逐功能对照 `dashboard.py:1490-4111` 的 HTML_PAGE 确认不遗漏 |
| **SSE async 迁移** | 事件流中断 | Step 6 专门测试，对照 `dashboard.py:1257-1298` 的 blocking 实现 |
| **双进程 + PyInstaller** | Windows 上 `multiprocessing.freeze_support()` | Step 8 在 `__main__.py` 添加 `freeze_support()` |
| **监控页面空间主题丢失** | UI 风格退化 | Step 7 保留 MONITOR_HTML 的 CSS 变量和星空动画 |
| **style.md 500 行限制** | embedded.py 超限 | embedded.py 是自动生成文件，豁免行数限制（在 style.md 中注明） |

## Checklist
- [x] Codebase has been explored — 完整映射 dashboard.py 4810 行结构
- [x] All P0 requirements from the spec are covered — 9 步迁移全覆盖 + core 层统一
- [x] Steps are ordered with correct dependencies — 依赖链清晰
- [x] Rules have been consulted — pitfalls.md (路由顺序→FastAPI 消除), style.md (500 行限制)
- [x] Verification strategy is defined — integration_test + build_check + manual_check
- [x] Each step has clear file targets — 精确到函数级别的迁移映射
- [x] Risks are identified with mitigations — 7 个风险 + 缓解方案
- [x] Existing plan checked — 无同名计划，v1 新建
