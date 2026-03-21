---
status: active
created_at: 2026-03-21
version: 3
previous_version: 2
change_reason: "新增 aion-demo/aion-test/aion-help 三个命令，更新工作流和目录结构"
---

# AionCode System Design

> AI-native development system for Claude Code — structured workflow + auto-learning rules that make AI smarter with every iteration.

---

## 1. System Overview

### 1.1 Core Problem

每次 AI 编码会话都从零开始。Claude 不记得你上周踩过的坑、团队约定的代码规范、或者从线上事故中学到的性能教训。

### 1.2 Solution: Learning Flywheel

```
Write Code → Review → Extract Rules → Rules Loaded Next Time
     ↑                                        ↓
     └──── AI avoids past mistakes ←──────────┘
```

AionCode 通过三个支柱解决这个问题：

| 支柱 | 机制 | 载体 |
|------|------|------|
| **开发方法论** | 结构化工作流：需求 → 原型 → 规划 → 实现 → 测试 → 审查 → 提交 | 16 个 slash 命令 |
| **项目智能** | 自动学习规则，累积项目经验 | `.aion/rules/` 目录 |
| **团队协作** | 文件驱动的协作，通过 git 同步 | `.aion/` 全目录 |

### 1.3 Architecture Principles

| 原则 | 说明 |
|------|------|
| **零外部依赖** | Dashboard 仅用 Python 标准库；命令是纯 Markdown；hooks 是 bash/python |
| **文件驱动协作** | 所有智能存储在 `.aion/` 文件中（git tracked），无中心服务器 |
| **幂等安装** | `install.sh` 不会破坏已有文件，可重复执行 |
| **零信任 AI 决策** | 提交必须用户确认；永不自动 push；阻止危险命令 |
| **规则学习飞轮** | review 自动提取规则；引用追踪实现规则淘汰 |

---

## 2. System Architecture

### 2.1 Overall Structure

```
aioncode/                          # AionCode 源码（安装源）
├── commands/                      # 16 个 slash 命令定义
│   ├── aion-design.md
│   ├── aion-demo.md               # 交互式 HTML 原型生成
│   ├── aion-plan.md
│   ├── aion-impl.md
│   ├── aion-test.md               # 测试生成与分析
│   ├── aion-verify.md
│   ├── aion-review.md
│   ├── aion-learn.md
│   ├── aion-save.md
│   ├── aion-commit.md
│   ├── aion-think.md
│   ├── aion-scan.md
│   ├── aion-status.md
│   ├── aion-loop.md
│   └── aion-help.md               # 帮助与工作流引导
├── templates/                     # 安装模板
│   ├── aion/                      # .aion/ 目录脚手架
│   │   ├── config.yml
│   │   ├── changelog.md
│   │   ├── rules/                 # 规则模板（pitfalls/style/perf）
│   │   ├── checklists/            # 阶段检查清单（6 个）
│   │   └── hooks/                 # Hook 脚本（3 个）
│   ├── CLAUDE.md.tpl              # CLAUDE.md 模板
│   ├── claude-hooks.json          # Hook 配置
│   └── claude-settings.json       # 权限配置
├── dashboard.py                   # 本地管理 Web UI（单文件，零依赖）
├── install.sh                     # 安装脚本
├── uninstall.sh                   # 卸载脚本
├── projects.json                  # Dashboard 项目注册表
├── monitor-demo-*.html            # 监控大屏设计原型（4 套主题）
└── docs/                          # 文档
```

### 2.2 Installed Project Structure

安装后，目标项目中产生的文件：

```
your-project/
├── .claude/
│   ├── commands/                  # 16 个 aion-* 命令（从源码复制）
│   ├── hooks.json                 # Hook 事件绑定
│   ├── settings.local.json        # 权限白名单/黑名单
│   └── CLAUDE.md                  # 规则自动加载指令（Claude 每次启动读取）
└── .aion/                         # 项目智能目录（git tracked）
    ├── config.yml                 # 配置（版本、规则上限等）
    ├── changelog.md               # 工作日志（aion-commit 自动追加）
    ├── sessions.jsonl             # 会话摘要（session-digest.py 自动生成）
    ├── rules/                     # 自动学习规则
    │   ├── pitfalls.md            # 陷阱与坑
    │   ├── style.md               # 代码规范
    │   └── perf.md                # 性能准则
    ├── checklists/                # 阶段检查清单（可自定义）
    │   ├── design.md
    │   ├── plan.md
    │   ├── impl.md
    │   ├── test.md                # 测试阶段清单
    │   ├── review.md
    │   └── commit.md
    ├── specs/                     # 需求规格（aion-design 输出）
    ├── plans/                     # 实施计划（aion-plan 输出，支持版本归档）
    ├── reviews/                   # 审查报告（aion-review 输出）
    ├── contracts/                 # 接口契约（跨团队协作）
    ├── refs/                      # 外部参考文档
    ├── prototypes/                # UI 原型（aion-demo 输出）
    ├── tests/                     # 测试相关（aion-test 输出）
    │   ├── reports/               # 测试生成报告
    │   ├── perf/                  # k6/locust 性能脚本
    │   └── ui/                    # UI 测试清单 + 无障碍审计
    ├── bugs/                      # Bug 报告（aion-bug 输出）
    ├── team.yml                   # 团队配置（成员/模型/风险关键词）
    └── monitor/
        └── events.jsonl           # 事件流日志（hook 自动写入）
```

### 2.3 Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Code Session                   │
│                                                         │
│  CLAUDE.md ──→ 加载 .aion/rules/ ──→ AI 决策受规则约束  │
│                                                         │
│  命令执行：                                              │
│  design ──→ specs/                                      │
│  demo   ──→ prototypes/ (可选)                          │
│  plan   ──→ plans/ (versioned)                          │
│  impl   ──→ source code + plan status                   │
│  test   ──→ test files + tests/ (可选)                  │
│  verify ──→ build/test/lint results                     │
│  review ──→ reviews/ + rules/ (extract + cite)          │
│  learn  ──→ rules/ (extract + cite)                     │
│  commit ──→ git commit + changelog.md                   │
│                                                         │
│  Hook 系统：                                            │
│  tool use ──→ monitor-hook.sh ──→ events.jsonl          │
│  session end ──→ session-digest.py ──→ sessions.jsonl   │
│  bash cmd ──→ safety-check.sh ──→ block/allow           │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│                Dashboard (localhost:19200)                │
│                                                         │
│  项目管理 ──→ projects.json                              │
│  文件浏览/编辑 ──→ .aion/ 目录                           │
│  实时活动 ──→ events.jsonl (轮询 3s)                     │
│  会话历史 ──→ sessions.jsonl                             │
│  Mission Control ──→ 监控大屏（独立页面）                │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Command System（命令系统）

### 3.1 Command Overview

| 命令 | 角色 | 输入 | 输出 | 核心机制 |
|------|------|------|------|---------|
| `aion-design` | 需求分析师 | 功能描述 | `.aion/specs/` | 假设挑战 → 结构化提问 → 用户确认后写入 |
| `aion-demo` | 原型工程师 | Spec/图片/URL | `.aion/prototypes/` | 多输入源 → 方案确认 → 单文件 HTML 原型 |
| `aion-plan` | 架构师 | Spec 文件名 | `.aion/plans/` | 必须先读代码 → 步骤设计 → 版本管理 |
| `aion-impl` | 开发者 | Plan 文件名 | 源代码 + plan 更新 | 逐步执行 → 每步验证 → TDD 可选 |
| `aion-test` | 测试工程师 | 模式 + 范围 | 测试文件 + `.aion/tests/` | 检测框架 → 生成测试 → 覆盖率 → 性能脚本 → UI 审计 |
| `aion-verify` | QA 工程师 | 验证模式 | 检查报告 | 自动检测技术栈 → build/type/lint/test |
| `aion-review` | 代码审查员 | 文件列表 | `.aion/reviews/` + 规则 | 读全文件 → 三维评分 → 自动提取规则 → 修复循环 |
| `aion-learn` | 学习引擎 | 上下文来源 | `.aion/rules/` | 收集证据 → 去重 → 质量筛选 → 引用追踪 |
| `aion-save` | 上下文管理 | 类型过滤 | `.aion/*` 文件 | 对话分析 → 路由到正确文件 → 追加不覆盖 |
| `aion-commit` | 提交守卫 | 提交上下文 | git commit + changelog | 展示变更 → 秘钥扫描 → 用户确认 → 更新日志 |
| `aion-think` | 魔鬼代言人 | 想法描述 | 分析报告 | 三问法 → 替代方案 → 推荐 |
| `aion-scan` | 项目扫描器 | 意图关键词 | `.aion/refs/` + 规则 + 清单 | 深度扫描代码库 → 按意图生成制品 |
| `aion-status` | 状态面板 | 无 | 状态报告 | 只读扫描 → 规则健康度 → 版本历史 |
| `aion-loop` | 流水线编排 | 模式 + 选项 | 全阶段执行 | 多阶段串联 → 修复循环 → 提交需确认 |
| `aion-help` | 帮助向导 | 命令名/模式 | 终端输出 | 命令总览 → 场景引导 → 速查表（只读） |
| `aion-bug` | Bug 协调员 | 子命令 + 参数 | `.aion/bugs/` | git blame 自动分配 → 资损检测 → Evidence 强制 |
| `aion-crosscheck` | 交叉验证 | --model + --scope | `.aion/bugs/` | 调用第三方模型 API → 自动生成 bug 报告 |

### 3.2 Recommended Workflow

```
design → (demo) → plan → impl → (test) → verify → review → learn → commit
```

括号表示可选步骤。每个命令可独立使用，但按推荐流程使用效果最佳。

常见场景的推荐流程：

| 场景 | 推荐流程 |
|------|---------|
| 新功能开发 | design → (demo) → plan → impl → (test) → verify → review → commit |
| 修复 Bug | think → impl → verify → review → commit |
| 接手老项目 | scan → status → design/impl → verify → review → commit |
| 补充测试 | scan → test --comprehensive → verify |
| 重构/优化 | think → design → plan → impl → verify → review → learn → commit |
| 测试提 Bug → 工程师修 | 测试: bug report → 工程师: impl {BUG-ID} → verify → commit |
| 交叉验证 | crosscheck --model gemini → 自动生成 bugs/ |

`aion-loop` 可自动编排：

| Loop 模式 | 执行阶段 |
|-----------|---------|
| `default` | impl → test → verify → review (→ fix loop) → commit |
| `full` | design → plan → impl → test → verify → review (→ fix loop) → learn → commit |
| `fix` | verify → review → fix（循环直到通过） |
| `verify-only` | 仅验证 |

### 3.3 Cross-Command Rule Enforcement

所有命令共享 `.aion/rules/`，形成闭环：

- **design** — 读取规则，避免设计出与已知陷阱冲突的方案
- **demo** — 读取规则中的 style 约定，原型视觉风格与项目一致
- **plan** — 读取规则，避免规划违反已知约束的实现路径；读取原型指导组件层级
- **impl** — 读取规则，实现过程中严格遵循；读取原型匹配视觉风格
- **test** — 读取规则中的测试约定，生成的测试遵循已有模式
- **review** — 读取规则检查合规性，检查原型一致性，**提取新规则**，**更新引用计数**
- **learn** — 读取规则去重，**提取新规则**，**更新引用计数**

### 3.4 Evidence Requirement

所有命令中的断言必须引用证据：

- GOOD: `src/services/auth.ts:23` uses dependency injection
- BAD: The codebase probably uses dependency injection

禁止使用 "likely", "probably", "should be fine" — 必须验证并引用，否则标记 `[UNVERIFIED]`。

### 3.5 Question Protocol

当命令需要用户输入时，统一遵循：

1. **Context** — 一句话说明当前所处阶段
2. **Problem** — 简单解释（像跟聪明但不了解背景的同事说话）
3. **Options** — 2-3 个选项（A/B/C），各有利弊，附推荐
4. **Recommendation** — 加粗推荐项，简述原因

每次只问一个问题，不批量提问。

---

## 4. Rule System（规则系统）

### 4.1 Rule Categories

| 类别 | 文件 | 内容来源 |
|------|------|---------|
| **pitfalls** | `rules/pitfalls.md` | 修复的 bug、踩过的坑、框架/库的怪癖 |
| **style** | `rules/style.md` | 代码规范、模式约定、团队习惯 |
| **perf** | `rules/perf.md` | 性能优化、N+1 查询、批处理策略 |

### 4.2 Rule Format

```markdown
---
category: pitfalls
rule_count: 3
last_updated: 2026-03-21
---

# Pitfalls — Known gotchas and traps

- **Element Plus DatePicker 需要显式 format** (bugfix, 2026-03-15) [cite_count: 5, last_cited: 2026-03-20]
  DatePicker 组件不设 format prop 会导致日期序列化为 Date 对象而非字符串，API 调用时报错。
  必须设 `format="YYYY-MM-DD"` 和 `value-format="YYYY-MM-DD"`。

- **Prisma 事务中不能用 $queryRaw** (review, 2026-03-18) [cite_count: 2, last_cited: 2026-03-19]
  $queryRaw 在 interactive transaction 内会死锁。改用 $executeRaw 或在事务外执行。
```

### 4.3 Rule Quality Bar

一条好规则必须同时满足：

1. **Actionable** — 明确告诉你该做什么或不该做什么（不是 "注意一下"）
2. **Specific** — 引用本项目的技术栈、模式、文件（不是通用编程建议）
3. **Evidenced** — 来自真实事故，不是假设性担忧
4. **Durable** — 3 个月后仍然相关（不是临时 workaround）

### 4.4 Rule Lifecycle

```
提取 → 活跃使用 → 逐渐衰减 → 标记为 stale → 人工确认后淘汰
```

| 状态 | 含义 | 触发条件 |
|------|------|---------|
| `active` | 活跃规则，正常执行 | 默认状态 |
| `stale` | 超过 60 天未被引用 | `aion-status` 自动标记 |
| `deprecated` | 已过时，不再执行 | 用户手动标记 |
| `archived` | 已归档，保留历史 | 用户手动标记 |

引用追踪机制：
- `cite_count` — 每次 review/learn 引用该规则时 +1
- `last_cited` — 最后一次被引用的日期
- `aion-status` 展示 Top 5 高频 / Bottom 5 低频规则
- 相似度 >80% 的规则会被建议合并

### 4.5 Rule Deduplication

新规则提取前，必须与所有已有规则对比：

| 关系 | 处理 |
|------|------|
| 精确重复 | 跳过，告知用户 |
| 语义重复 | 跳过，告知用户 |
| 扩展已有 | 更新已有规则，追加新信息 |
| 冲突 | 标记给用户决定，不自动写入 |
| 全新 | 写入新规则 |

### 4.6 Learning Flywheel Trajectory

```
Week 1:   0 rules → Claude makes common mistakes
Week 2:   5 rules → Claude avoids the same mistakes
Week 4:  15 rules → Claude knows your project's quirks
Week 8:  25 rules → Claude codes like a senior team member
```

---

## 5. Hook System（钩子系统）

### 5.1 Hook Configuration

通过 `.claude/hooks.json` 注册，绑定到 Claude Code 事件：

| 事件 | Hook | 功能 |
|------|------|------|
| PreToolUse (Bash) | `safety-check.sh` | 阻止危险命令（rm -rf, git push --force 等） |
| PreToolUse (all) | `monitor-hook.sh` | 记录工具调用事件 |
| PostToolUse | `monitor-hook.sh` | 记录工具完成事件 |
| SubagentStart | `monitor-hook.sh` | 记录子代理启动 |
| SubagentStop | `monitor-hook.sh` | 记录子代理返回 |
| Stop | `monitor-hook.sh` | 记录会话周期结束 |
| Stop | `session-digest.py` | 生成会话摘要 |

### 5.2 safety-check.sh

阻止的危险模式：
- `rm -rf /`, `rm -rf ~`, `rm -rf .`
- `git push --force`, `git reset --hard`, `git clean -fd`
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- `> /dev/sda`, `mkfs.`, fork bomb

退出码：0 = 允许，2 = 阻止。超时 5 秒。

### 5.3 monitor-hook.sh

将事件追加到 `.aion/monitor/events.jsonl`：

```json
{"ts": "2026-03-21T10:30:00Z", "data": {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": "src/app.ts"}, "session_id": "abc123"}}
```

非阻塞，必须在 5 秒内完成。首次运行自动创建 `.aion/monitor/` 目录。

### 5.4 session-digest.py

在 Stop 事件后运行，读取 events.jsonl 新增事件，生成会话摘要追加到 `.aion/sessions.jsonl`：

```json
{
  "ts": "2026-03-21T10:45:00Z",
  "duration_sec": 900,
  "tools": {"Edit": 15, "Read": 8, "Bash": 3},
  "files_changed": ["src/app.ts", "src/utils.ts"],
  "subagents": 2,
  "ops": 26,
  "last_file": "src/utils.ts",
  "last_tool": "Edit"
}
```

使用 checkpoint 机制避免重复消化。少于 3 次工具调用的会话自动跳过。

---

## 6. Dashboard（管理面板）

### 6.1 Architecture

- **运行方式**: `python3 dashboard.py` → `http://localhost:19200`
- **技术栈**: 单文件 Python，零外部依赖，ThreadingMixIn 多线程
- **前端**: 内嵌 HTML/CSS/JS 的 SPA，3 个页面（项目 / 命令 / 指南）

### 6.2 Core Features

| 功能 | 说明 |
|------|------|
| **项目注册** | 添加/移除项目，持久化到 `projects.json` |
| **一键安装** | 从 Dashboard 中直接初始化 `.aion/` |
| **项目统计** | 规则数、文档数、最近活动 |
| **文件浏览/编辑** | 浏览 `.aion/` 文件树，查看/编辑/创建/删除文件 |
| **Markdown 渲染** | 内置 MD 渲染器，支持代码块、表格、列表等 |
| **实时活动** | 轮询 `events.jsonl`（3 秒间隔），展示最新事件流 |
| **会话历史** | 展示最近会话的工具使用、文件变更、持续时间 |
| **Mission Control** | 独立监控大屏，实时展示代理状态、子代理、工具统计 |

### 6.3 API Endpoints

**项目管理：**
- `GET /api/projects` — 项目列表
- `POST /api/projects/add` — 添加项目
- `POST /api/projects/remove` — 移除项目
- `POST /api/projects/init` — 初始化 AionCode
- `GET /api/projects/{enc}/stats` — 项目统计
- `GET /api/projects/{enc}/files` — 文件树
- `GET /api/projects/{enc}/file?path=` — 读取文件
- `PUT /api/projects/{enc}/file` — 写入文件
- `POST /api/projects/{enc}/file` — 创建文件
- `DELETE /api/projects/{enc}/file?path=` — 删除文件
- `GET /api/projects/{enc}/sessions` — 会话列表

**事件监控：**
- `GET /api/projects/{enc}/events/recent?limit=N` — 最近事件（REST）
- `GET /api/projects/{enc}/events/stream` — 事件流（SSE）
- `GET /api/monitor/{enc}/events?since=N` — Monitor 事件轮询
- `GET /api/monitor/{enc}/state` — Monitor 聚合状态
- `POST /api/monitor/{enc}/clear` — 清除事件日志

**命令查看：**
- `GET /api/commands` — 命令列表
- `GET /api/commands/{name}` — 命令内容

### 6.4 Monitor（Mission Control）

独立页面 `/monitor/{encoded-project}`，CRT 复古风格大屏：

- **主代理状态**: STANDBY / ACTIVE / IDLE / OFFLINE
- **子代理舰队**: 网格展示每个子代理的类型和状态
- **工具统计**: 柱状图展示各工具使用次数
- **通讯日志**: 时间线展示事件详情
- **雷达动画**: 视觉化代理活动
- **MET 计时器**: Mission Elapsed Time

轮询间隔 1000ms，通过 `processEvent()` 状态机处理事件。

---

## 7. Installation System（安装系统）

### 7.1 install.sh

```bash
bash aioncode/install.sh /path/to/your/project
```

执行步骤：
1. 复制 16 个命令文件 → `.claude/commands/`
2. 创建 `.aion/` 脚手架（已有文件不覆盖）
3. 创建子目录：refs, prototypes, specs, plans, reviews, contracts, monitor, tests, tests/reports, tests/perf, tests/ui
4. 安装 hooks 配置 → `.claude/hooks.json`, `.claude/settings.local.json`
5. 写入 CLAUDE.md → `.claude/CLAUDE.md`

支持 `--check` 模式验证安装完整性。

### 7.2 uninstall.sh

```bash
bash aioncode/uninstall.sh /path/to/your/project
```

移除：命令文件、CLAUDE.md、hooks.json、settings.local.json
保留：`.aion/`（规则和文档有价值）

### 7.3 Dashboard Installation

```bash
# 通过 Dashboard UI 安装
POST /api/projects/init { "path": "/path/to/project" }
```

与 `install.sh` 相同逻辑，但通过 Web UI 操作，返回安装日志。

---

## 8. Team Collaboration（团队协作）

### 8.1 File-Driven Collaboration

```
Designer: .aion/prototypes/mockup.html → git push
Developer: /aion-impl reads prototypes automatically

Backend:  .aion/contracts/api-v2.md → git push
Frontend: /aion-impl reads contracts automatically

Developer A: /aion-save before ending → git push
Developer B: Claude loads all context automatically
```

### 8.2 Shared Intelligence

`.aion/` 目录通过 git 共享，团队成员共享：
- 规则（rules/）— 所有人的 AI 避免同样的错误
- 契约（contracts/）— 接口约定自动执行
- 规格（specs/）— 需求共识
- 计划（plans/）— 实现方案及其版本演变历史

---

## 9. Safety & Verification（安全与验证）

### 9.1 Multi-Layer Safety

| 层级 | 机制 | 保护范围 |
|------|------|---------|
| **Hook** | safety-check.sh | 阻止 rm -rf, git push --force 等 |
| **Permissions** | settings.local.json | 白名单/黑名单工具和命令 |
| **Commit Guard** | aion-commit | 秘钥扫描、用户确认、禁止 auto-push |
| **Review Score** | aion-review | Security 维度占 30% 权重 |
| **Fix Loop Limit** | aion-loop | 最大修复轮次，防止无限循环 |

### 9.2 Review Scoring

三维评分体系：

- **Code Quality (40%)**: 可读性、可维护性、DRY、抽象、类型安全、错误处理
- **Security (30%)**: 注入、XSS、认证、秘钥暴露、OWASP Top 10
- **Architecture (30%)**: 计划合规、模式一致性、契约遵守

评分 ≥ 70 且无 Critical 问题 → `approved`；否则 → `needs_fix`

### 9.3 Escape Conditions

| 场景 | 处理 |
|------|------|
| 同一错误出现 3 次 | STOP，不再循环 |
| 修改超过 10 个文件 | 暂停确认 |
| 修复循环零进展 | 立即退出 |
| 在 main/master 分支 | BLOCKED，要求创建特性分支 |

---

## 10. Plan Versioning（计划版本管理）

### 10.1 Version Flow

```
首次创建：aion-plan → .aion/plans/feature.md (v1)

需求变更后：
  aion-plan → 检测到同名 plan → 提示用户选择：
    A) 新版本（推荐）→ 归档旧版本为 feature.v1.md → 写入新版本 feature.md (v2)
    B) 覆盖 → 直接替换
    C) 独立文件 → 使用新文件名
```

### 10.2 Version Metadata

```markdown
---
status: completed
created_at: 2026-03-21
spec: feature-name.md
version: 2
previous_version: 1
change_reason: "需求变更：增加了权限控制要求"
current_step: 0
total_steps: 8
---
```

- `aion-impl` 始终读取无版本后缀的最新文件
- 归档文件命名：`feature-name.v1.md`、`feature-name.v2.md`
- 每个 plan 最多保留 10 个归档版本
- `change_reason` 必填，不允许空白

---

## 11. CLAUDE.md Integration

`CLAUDE.md` 是 Claude Code 每次启动自动读取的文件，AionCode 在其中注入规则加载指令：

```markdown
<!-- AIONCODE:START -->
## AionCode Rules

Before making any changes, read and follow ALL rules in:
- .aion/rules/pitfalls.md
- .aion/rules/style.md
- .aion/rules/perf.md

## Available Commands
/project:aion-design, /project:aion-plan, /project:aion-impl, ...

## Project Context
Read .aion/changelog.md for recent work history.
Check .aion/refs/, .aion/prototypes/, .aion/specs/, .aion/plans/, .aion/contracts/ for context.
<!-- AIONCODE:END -->
```

这确保即使用户不显式调用命令，规则也会在每个会话中生效。

---

## 12. Iteration History（迭代历史）

### v0.1 — Initial Release (12 commands)

- 12 个 slash 命令完整实现
- `.aion/` 目录结构和模板
- Dashboard 基础版（项目管理、文件浏览、会话历史）
- Mission Control 监控大屏
- Hook 系统（安全检查、事件捕获、会话摘要）
- install.sh / uninstall.sh
- 4 套监控大屏主题原型

### v0.2 — P0 Iteration (2026-03-21)

**Feature 1: Rule Lifecycle Management**
- 规则文件增加 frontmatter 元数据（category, rule_count, last_updated）
- 规则条目增加引用追踪（cite_count, last_cited）
- aion-review / aion-learn 自动更新引用计数
- aion-status 增加规则健康度报告（stale 检测、合并建议、Top/Bottom 统计）
- 向后兼容旧格式规则文件

**Feature 2: Plan Versioning**
- aion-plan 支持版本检测和归档（.v{N}.md）
- 新版本必须填写 change_reason
- aion-status 展示 plan 版本历史

**Feature 3: Dashboard Real-time**
- 新增 `/api/projects/{enc}/events/recent` REST 端点
- 新增 `/api/projects/{enc}/events/stream` SSE 端点
- 主 Dashboard 增加实时活动面板（3 秒轮询）
- 服务器升级为 ThreadingMixIn 多线程
- 文件打开增加错误捕获
- browser-area 增加最小高度保证

### v0.3 — Feature Expansion (16 commands, 2026-03-21)

**New Command: aion-demo（交互式原型生成）**
- 支持多种输入源：spec / 图片 / URL / 自由描述
- 生成单文件自包含 HTML 原型（inline CSS + JS，零外部依赖）
- 支持手机框架模式（mobile 参数）
- 与 plan/impl/review 集成：plan 读取原型指导组件设计，review 检查原型一致性
- 可选环节，不进入 aion-loop 自动流水线

**New Command: aion-test（测试生成与分析）**
- 五种模式：默认（unit+integration）、coverage、perf、ui、full
- 自动检测项目测试框架和约定，读取已有测试文件学习模式
- 老项目冷启动：scan 后可直接 test，无需 spec/plan（代码优先模式）
- 覆盖率分析：运行覆盖率工具，识别未覆盖路径，生成补充测试
- 性能脚本：读取 contracts 生成 k6/locust 脚本（三种场景）
- UI 测试：轻量静态分析（测试清单 + 结构验证 + 无障碍审计），无 Playwright
- 集成到 aion-loop 流水线（impl → test → verify）

**New Command: aion-help（帮助与引导）**
- 四种模式：全部概览、单命令详情、工作流图解、速查表
- 按场景推荐工作流（新功能/修 bug/接手老项目/补测试/重构）
- 只读命令，不修改任何文件

**Workflow Updates**
- 推荐流程更新为：design → (demo) → plan → impl → (test) → verify → review → learn → commit
- aion-loop default 模式加入 test 阶段
- aion-loop 增加 --auto 参数跳过启动确认
- install.sh 新增 .aion/tests/ 子目录（reports/perf/ui）
- 新增 checklists/test.md 测试阶段检查清单

---

## 13. Bug Tracking & Cross-Verification（Bug 追踪与交叉验证）

### 13.1 Bug 管理系统

支持测试与工程师之间的结构化 Bug 协作：

```
测试: /aion-bug report → AI 分析 → git blame 自动分配 → .aion/bugs/F-0321-001.md
工程师: /aion-impl F-0321-001 → 自动领取 → 修复 → verify → commit
测试: /aion-bug close F-0321-001 → 验证关闭
```

**Bug ID 格式**：`{分类}-{日期}-{序号}`
- `F-` Frontend | `B-` Backend | `X-` Cross/Mixed
- 分类即分配：F-* 自动归前端，B-* 自动归后端

**核心特性**：
- **git blame 自动分配** — 通过代码作者邮箱匹配 team.yml 自动识别责任人
- **能力画像** — AI 通过 git log 分析模块贡献占比，建议领域专家抄送
- **资损风险检测** — 关键词匹配自动提升 severity（payment/order → critical）
- **Evidence 强制** — Bug 报告必须包含代码定位/verify 输出/测试脚本
- **状态自动流转** — open → assigned → in-progress → fixed → verified → closed
- **verify_test 守门** — commit 时运行关联测试，100% 通过才能自动 fixed

### 13.2 团队配置

`.aion/team.yml` 管理团队成员、AI 模型、风险关键词：

```yaml
team:
  - name: 张三
    role: frontend
    git_email: zhangsan@company.com
    expertise: []          # AI 自动生成
    active_bugs: 0         # 系统自动计算

models:
  - name: gemini
    provider: google
    api_key_env: GEMINI_API_KEY
    default_model: gemini-2.5-pro

risk_keywords:
  critical: [payment, order, account, refund]
  low: [typo, ui, color, font]
```

**管理方式**：Dashboard Web UI + 新成员 git config 自动检测引导

### 13.3 交叉验证

`/aion-crosscheck` 使用其他 AI 模型分析代码，发现 Claude 可能遗漏的问题：

```
/aion-crosscheck --model gemini --scope src/pages/
  → 调用 Gemini API 分析代码
  → 发现的问题自动写入 .aion/bugs/（source_model: gemini）
```

**设计原则**：Bug 管理和交叉验证完全解耦。`.aion/bugs/` 的 Markdown 格式是模型无关的通用接口。

### 13.4 Dashboard Bug 看板

Dashboard 新增 Bug Board 页面和 Admin 页面：
- **Bug Board** — 按状态分列看板，支持筛选，显示停留时长和团队负载
- **Admin / Team** — 团队成员管理、AI 模型配置
- **/admin 路由预留** — 代码中预留 `is_admin()` 检查点，为将来权限控制做准备

---

## 14. Future Roadmap（未来规划）

### P1: Capability Expansion

- **规则标签系统** — security / performance / style / architecture 分类标签
- **规则导入/导出** — 跨项目共享通用规则
- **种子规则** — 常见技术栈的预置规则集（Node.js, Python, Go）
- **CI/CD 模板** — GitHub Actions workflow 集成
- **aion-refactor** — 引导式重构命令
- **aion-search** — 全文搜索 .aion/ 文档

### P2: Team & Analytics

- ~~**团队协作增强** — 多人规则冲突解决、角色区分~~（已实现：Bug 系统 + team.yml）
- **规则效果度量** — 统计引用频次、避免问题数量
- **Dashboard 增强** — Plan diff 视图、事件统计图表、多主题支持
- **aion-scan 轻量模式** — 降低首次使用门槛

### P3: Cloud & Permissions

- **云端部署** — Dashboard 云端部署，通过 Git API 读取 .aion/
- **权限控制** — 基于 team.yml role 的权限矩阵
- **OAuth 认证** — GitHub/GitLab OAuth 登录

---

## 14. Constraints（约束）

- 零外部依赖：dashboard.py 仅使用 Python 标准库
- 命令文件为纯 Markdown，不包含可执行代码
- `.aion/` 目录设计为 git 可追踪
- 向后兼容：新版本必须能处理旧版本生成的文件
- 安装幂等：install.sh 不破坏已有文件
- Dashboard 保持单文件架构
