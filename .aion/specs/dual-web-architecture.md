# AionCode 双 Web 系统架构设计

> 可实施 spec — 直接进入 aion-plan → aion-impl 流程
> 创建日期：2026-03-22

## Context

AionCode v0.4 完成了 CLI 重写，但 dashboard.py 仍是 4784 行单文件遗留代码。v0.5 需要重构本地 Dashboard，同时开始规划云端管理平台。

**两个方向：**
- **本地端** = 沉浸式"副驾驶"，CLI 的可视化外壳，极轻 UI
- **云端** = 运维监控中心 + 团队协作平台

两者独立设计、分开选型。核心创新点：**意图日志**（不传输代码，只传输开发意图）。

---

## 一、本地 Dashboard v0.5（副驾驶）

### 定位
不是传统 Web App，而是开发者的可视化"副驾驶"。极简 chrome，快速操作为主。

### 技术栈
| 组件 | 选择 | 理由 |
|------|------|------|
| 后端框架 | **FastAPI + uvicorn** | 替代 stdlib http.server，Asyncio 异步非阻塞性能优势 |
| 前端 | **Vanilla JS（构建时注入）** | 开发时分离文件，打包时通过 jinja2/字符串替换注入到单 HTML |
| 实时推送 | **SSE** | 保持现有模式，FastAPI StreamingResponse |
| 新增依赖 | `fastapi>=0.115.0`, `uvicorn[standard]>=0.30.0` | 约增 5-8MB 二进制体积 |

### 进程架构：双进程隔离
```
aioncode dashboard
  ├── 主进程：CLI 交互（aion-stop 等应急操作不受阻塞）
  └── 子进程：uvicorn Web 服务
```
**理由**：Web 后端如因复杂正则搜索等操作卡住，不应影响 CLI 的应急操作。主进程保持响应能力。

### 模块拆分（替代 4784 行单文件）

```
aioncode/internal/dashboard/          # 新包，替代 dashboard.py
  __init__.py                          # FastAPI app factory
  app.py                              # create_app(), 中间件, 生命周期
  config.py                           # 端口, 路径, PyInstaller 检测
  routers/                            # 7 个路由模块
    projects.py                        # /api/projects CRUD
    files.py                          # /api/projects/{id}/files
    monitor.py                        # /api/monitor/*, SSE 流
    bugs.py                           # /api/projects/{id}/bugs
    team.py                           # /api/projects/{id}/team
    commands.py                       # /api/commands
    browse.py                         # /api/browse 文件选择器
  services/                           # 7 个业务模块（纯逻辑，无 HTTP）
    project_registry.py               # 项目注册表
    stats.py                          # 统计计算
    file_ops.py                       # 文件树/读写
    monitor.py                        # 事件聚合
    bugs.py                           # Bug 管理
    team.py                           # 团队配置
    intent_reporter.py                # [新] 云端意图上报（可选）
  models/schemas.py                   # Pydantic 请求/响应模型
  frontend/embedded.py                # HTML/CSS/JS 嵌入（生产模式）
  frontend/static/                    # HTML/CSS/JS 分离（开发模式）
```

### 副驾驶 UI 设计理念
- **底部状态栏**（常驻）：当前项目、活跃会话数、最后事件时间、云端连接状态
- **命令面板**（Cmd+K）：快速操作入口，类 VS Code
- **折叠面板**（非页面切换）：Stats / Files / Monitor / Bugs / Team 可同时打开
- **窄图标栏**（48px 侧边）：hover 展开
- **纯暗色主题**

### 前端构建策略：零静态文件路径依赖
开发时 CSS/JS 分离编写，打包时自动注入到 `index.html` 的 `<style>` 和 `<script>` 标签中：
```
开发模式 (--dev):
  frontend/static/index.html + style.css + app.js → 直接从文件系统加载

生产/PyInstaller 模式:
  build_frontend.py → 读取 CSS/JS → 注入 HTML → 生成 embedded.py
  → 单个 Python 字符串 EMBEDDED_HTML，零 static/ 依赖
```
彻底消除"static/ 文件夹找不到"的打包问题。

### 迁移 9 步
1. 创建包结构（与旧文件并存）
2. 提取 services（纯函数迁移，零逻辑改动）
3. 创建 FastAPI routers（路由映射）
4. 添加 Pydantic models
5. SSE 迁移（blocking → async generator）
6. 前端重设计（副驾驶风格）
7. 更新 CLI 入口（uvicorn.run）
8. 更新 PyInstaller spec（hiddenimports）
9. 删除旧 dashboard.py

---

## 二、云端管理 Web（独立项目）

### 定位
运维监控中心 + 团队协作平台。多项目/多机器的全局视图。

### 技术栈
| 组件 | 选择 | 理由 |
|------|------|------|
| 后端 | **FastAPI** | 与本地统一语言，团队复用知识 |
| 数据库 | **PostgreSQL** | 多租户、并发写入、JSONB 灵活存储 |
| ORM | **SQLAlchemy 2.0 (async)** | Python 标准 ORM |
| 迁移 | **Alembic** | 自动生成 migration |
| 认证 | **JWT + bcrypt** | 无状态 API 认证 + Web 会话 |
| 前端 | **Vue 3 + Vite + TypeScript** | 适合 Dashboard 类 SPA，比 React 轻量 |
| 图表 | **Apache ECharts** | 开箱即用的统计图表 |
| 实时 | **SSE 优先，WebSocket 备选** | 服务器→浏览器单向推送用 SSE（自动重连更强），仅在需要双向通信时用 WebSocket |
| 部署 | **Docker Compose → K8s** | 起步简单，后续可扩展 |

### 仓库结构
```
aioncode-cloud/                      # 独立仓库
  backend/
    app/
      auth/                          # JWT + API Key
      models/                        # SQLAlchemy 模型
      schemas/                       # Pydantic 模型
      routers/                       # API 路由
      services/                      # 业务逻辑
    migrations/                      # Alembic
    Dockerfile
    docker-compose.yml
  frontend/
    src/
      views/                         # Dashboard / Sessions / Rules / Bugs / Team
      components/                    # IntentTimeline / StatsChart / RuleCard
      stores/                        # Pinia 状态管理
```

### 4 大模块

#### 1. 多项目统计聚合
- 本地 agent 定期（5 分钟）POST 项目统计快照
- 云端汇总为跨项目/跨机器趋势图
- 指标：规则数、Bug 分布、会话频率、代码活动热力图

#### 2. 实时会话监控（意图日志）
**核心创新：只传意图，不传代码**

本地 → 云端数据流：
```
Claude Code Hook → events.jsonl → Intent Extractor → HTTPS POST → Cloud Ingest
```

意图日志格式：
```json
{
  "ts": "2026-03-22T01:00:00Z",
  "intent": "edit_file",
  "tool": "Edit",
  "target": "src/auth/login.py",
  "phase": "impl",
  "session_id": "abc-123",
  "meta": {}
}
```

**安全规则（三层防线）：**

**第一层 — 数据剥离：**
- NEVER 传输 old_string/new_string/content
- 单字段最大 500 字节硬截断
- 服务端验证拒绝含代码模式的数据

**第二层 — 模糊化 (Obfuscation)：**
- 路径脱敏：屏蔽用户家目录
  - Bad: `/Users/shibei/projects/secret/auth.py`
  - Good: `[ROOT]/auth.py`
- 命令摘要攻击防护：前 100 字符截断 + 自动剥离 password/token/key/secret 等敏感参数值
- 环境变量值替换为 `***`

**第三层 — 意图聚合 (Intent Aggregation)：**
- 本地微聚合：10 秒内对同一文件连续 5 次 Edit → 云端只记录 1 条 `edit_file (active)` 事件
- 显著减少 IO 和带宽消耗
- 聚合窗口可配置（默认 10 秒）

**意图类型表：**
| 工具 | 意图 | target |
|------|------|--------|
| Read | `read_file` | 相对路径 |
| Edit | `edit_file` | 相对路径 |
| Write | `create_file` | 相对路径 |
| Bash | `run_command` | 命令摘要(100字符) |
| Grep/Glob | `search_code`/`find_files` | 搜索模式 |
| Session* | `session_start`/`session_end` | - |

**离线缓冲：** 云端不可达时，意图缓存到 `~/.config/aioncode/intent_buffer.jsonl`（最大 10000 条 FIFO），重连后排空。

**意图上报方式 — Dashboard 内置 agent（后台 asyncio 任务）：**
- Dashboard 启动时自动启动后台任务 tail events.jsonl
- 每 30s 或攒满 50 条 → HTTPS POST 到云端
- Dashboard 关闭即停止上报
- 云端不可达时缓冲到 `~/.config/aioncode/intent_buffer.jsonl`

#### 3. 规则/模板共享 + 契约锁 (Protocol Lock)
- 上传：`POST /api/v1/rules` 从本地项目分享规则到云端
- 下载：`POST /api/v1/rules/{id}/import` 导入到本地 .aion/rules/
- 内容哈希去重，使用计数追踪
- **契约锁机制**：云端更新规则后，本地 Dashboard 显示"待同步"小红点。用户确认前，本地 aion-verify 仍执行旧契约，确保生产环境稳定性

#### 4. 团队管理 + Bug 看板
- 云端权威模式：本地 .aion/bugs/ 作为只读缓存
- 成员管理、角色分配、邀请机制
- Bug 跨项目聚合视图
- **Bug 时空溯源**：Bug 条目可直接跳转到对应的意图时间线（Intent Timeline），提供"黑匣子"复盘数据
  - 场景：看到 Bug #402 → 点击跳转 → 发现 1 小时前 AI 连续 3 次 Edit + 1 次 pytest 失败后强行 Commit

### 数据库核心表
`orgs` → `users` / `api_keys` → `projects` → `intent_logs` / `sessions` / `bugs` / `shared_rules` / `project_stats`

### 部署方案
- **Phase 1**: Docker Compose（app + postgres + nginx），1vCPU/2GB VPS，约$10-20/月
- **Phase 2**: K8s + Redis（WebSocket pub/sub）+ PgBouncer

### 认证分期
1. Phase 1: 仅 API Key（本地 agent 用），管理员通过 CLI/env 创建
2. Phase 2: JWT + 密码登录（Web UI）
3. Phase 3: SSO/OAuth（企业需求时）

---

## 三、风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| PyInstaller 体积增加 5-8MB | 低 | 排除未使用 uvicorn 协议，从 15MB→20-23MB 可接受 |
| uvicorn + PyInstaller 兼容性 | 中 | 强制 workers=1，用 asyncio 不用 uvloop，4 平台早期测试 |
| uvicorn 隐式依赖打包遗漏 | 高 | **穷举 hiddenimports**：h11, click, colorama, anyio, sniffio, httptools 等 |
| 意图日志意外泄露代码 | 高 | 三层防线：白名单字段提取 + 模糊化 + 意图聚合 |
| intent_logs 表增长过快 | 中 | 按月分区 + 90 天归档策略 |
| 本地 Dashboard 迁移回归 | 中 | 迁移前写集成测试，新旧并存直到功能完整 |
| 前端嵌入式开发痛苦 | 中 | --dev 模式从文件系统加载，构建脚本自动内联 |

---

## 四、实施优先级

```
Phase 1 (v0.5): 本地 Dashboard 重构
  ├── FastAPI 替换 http.server（双进程隔离）
  ├── 4784 行拆分为 ~18 个文件
  └── 副驾驶 UI 重设计

Phase 2 (v0.6): 云端 MVP
  ├── 独立仓库 aioncode-cloud
  ├── 意图日志管道（本地 agent → 云端）
  ├── 多项目统计面板
  └── API Key 认证

Phase 3 (v0.7): 云端完整功能
  ├── 团队管理 + Bug 看板（时空溯源）
  ├── 规则共享中心（契约锁）
  ├── Web 登录 + JWT
  └── Vue 前端完整 SPA
```

---

## 五、验证方案

### 本地 Dashboard v0.5 验证
1. `aioncode dashboard` 启动成功，浏览器访问 `http://localhost:19200`
2. 所有现有功能不回归：项目列表、文件浏览编辑、统计、监控 SSE、Bug 看板、团队
3. `aioncode dashboard --dev` 可从文件系统加载前端
4. PyInstaller 打包后在 macOS/Linux/Windows 正常运行
5. `ruff check` + `pytest` 全部通过
6. 每个拆分文件 ≤500 行

### 云端 MVP 验证
1. `docker-compose up` 一键启动
2. 本地 agent 能通过 API Key 认证上报意图
3. 云端面板显示多项目统计 + 实时意图时间线
4. 意图日志不含任何代码内容（人工审计 + 自动检测）
5. SSE 推送正常
6. 断网重连后缓冲区排空

---

## 六、关键文件清单
- `aioncode/internal/dashboard.py` — 待拆分的 4784 行单文件
- `aioncode/commands/dashboard.py` — CLI 入口，需更新为 uvicorn
- `aioncode.spec` — PyInstaller 配置，需加 FastAPI hiddenimports
- `pyproject.toml` — 依赖声明
- `templates/aion/hooks/session-digest.py` — 事件解析逻辑，意图提取需兼容
