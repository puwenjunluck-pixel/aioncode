---
product: AionCode
updated_at: 2026-03-25
generation_method: scan
confidence: high
sources:
  - code-scan
---

# 产品设计文档

## 一、产品定位
- **目标用户**：使用 Claude Code 的开发者和测试人员，需要让 AI 编程有章可循而非随意生成 [CONFIRMED]
- **核心价值**：为 AI 辅助开发建立结构化知识体系（规则、规格、计划），实现知识沉淀 → 规则驱动 → 质量可控的开发闭环 [CONFIRMED]
- **产品形态**：CLI 工具 + Web Dashboard（副驾驶面板）+ Claude Code Skill 命令集 [CONFIRMED]
- **商业模式**：当前闭源，稳定后考虑开源 [CONFIRMED]

## 二、功能地图
| 模块 | 功能 | 用户场景 | 状态 | 对应 plan |
|------|------|---------|------|-----------|
| CLI — init | 项目初始化：创建 .aion/ 目录、模板、规则 | 新项目接入 AionCode | 已实现 | [from:code] |
| CLI — upgrade | 自动检测+下载+替换二进制（支持 GITHUB_TOKEN） | 更新到最新版本 | 已实现 | github-token-auth |
| CLI — dashboard | 启动 Web 副驾驶面板（双进程架构） | 可视化查看项目状态 | 已实现 | dashboard-polish |
| CLI — doctor | 环境诊断（Python、git、路径、权限） | 排查安装问题 | 已实现 | [from:code] |
| CLI — install/uninstall | 系统级安装/卸载二进制 | 首次安装 | 已实现 | [from:code] |
| CLI — clean | 清理 .aion/ 临时文件 | 磁盘空间管理 | 已实现 | [from:code] |
| Skill — aion-scan | 项目扫描 + 浏览器探索(--url) + 文档导入(--file) → 生成产品设计文档 | 接手已有项目 | 已实现 | product-design-layer |
| Skill — aion-design | 需求分析 + 外部文档导入 → 生成 spec + 更新产品文档 | 设计新功能 | 已实现 | product-design-layer |
| Skill — aion-think | 质疑假设，暴露盲点 | 开始前三思 | 已实现 | [from:code] |
| Skill — aion-demo | 生成交互式 HTML 原型 | 快速原型验证 | 已实现 | [from:code] |
| Skill — aion-plan | 创建分步实施计划 → 自动传播模块/技术栈变更到产品文档 | 规划实现方案 | 已实现 | [from:code] |
| Skill — aion-impl | 按计划编写代码（自动遵守规则） | 实现功能 | 已实现 | [from:code] |
| Skill — aion-test | 测试生成 + E2E 三阶段 + 自愈(--heal) + 多代理管道(pipeline) | 自动化测试 | 已实现 | e2e-testing-upgrade |
| Skill — aion-verify | 构建/测试/lint 检查 + 自动修复(--fix) | 质量验证 | 已实现 | e2e-testing-upgrade |
| Skill — aion-review | 代码审查 + 自动提取规则 | 代码质量门禁 | 已实现 | [from:code] |
| Skill — aion-commit | 安全提交（需 review 通过）+ changelog 更新 | 提交代码 | 已实现 | [from:code] |
| Skill — aion-bug | Bug 管理：报告/列表/分配/关闭 | Bug 追踪 | 已实现 | [from:code] |
| Skill — aion-crosscheck | 用其他 AI 模型交叉验证代码 | 多模型审计 | 已实现 | [from:code] |
| Skill — aion-loop | 自动化流水线（设计→实现→验证→审查→提交） | 全自动开发循环 | 已实现 | [from:code] |
| Skill — aion-save | 保存对话上下文到 .aion/ 和 memory | 跨会话知识保留 | 已实现 | [from:code] |
| Skill — aion-status | 项目状态总览 | 了解当前进展 | 已实现 | [from:code] |
| Skill — aion-learn | 从审查中提取规则 | 知识积累 | 已实现 | [from:code] |
| Dashboard — 概览 | 项目统计 + 最近变更历史 | 快速了解项目 | 已实现 | [from:code] |
| Dashboard — 文件 | 浏览 .aion/ 配置文件（Markdown 渲染） | 查看规格/规则 | 已实现 | [from:code] |
| Dashboard — 监控 | SSE 实时事件流 | 监控 Claude Code 活动 | 已实现 | [from:code] |
| Dashboard — 需求/方案/规则/清单/缺陷/测试/日志 | 各类数据视图 | 按分类浏览项目数据 | 已实现 | [from:code] |
| Dashboard — 技能 | Skill 安装管理 + 官方市场 | 扩展能力 | 已实现 | skills-management |
| Dashboard — 帮助 | 工作流指南 + 命令速查（10 命令）+ 常见场景 + 测试最佳实践 + FAQ | 日常查阅（高频） | 已实现 | [from:code] |
| Dashboard — 关于 | 产品介绍 + 动态版本号 + 安装升级 + 路线图 + 更新日志 | 产品身份（低频） | 已实现 | [from:code] |

## 三、核心业务流程
### 流程 1: 新功能开发
开发者 → aion-think（质疑假设）→ aion-design（生成 spec）→ aion-demo（可选原型）→ aion-plan（实施计划）→ aion-impl（编写代码）→ aion-test（生成测试）→ aion-verify（质量检查）→ aion-review（代码审查 + 提取规则）→ aion-commit（安全提交）[CONFIRMED]

### 流程 2: 接手已有项目
开发者 → aion-scan（扫描代码 + 生成产品文档 + 提取规则）→ aion-impl/design（迭代开发）→ aion-verify → aion-review → aion-commit [CONFIRMED]

### 流程 3: Bug 修复
开发者 → aion-bug report（报告 Bug）→ aion-impl {BUG-ID}（修复）→ aion-verify → aion-review → aion-commit [CONFIRMED]

### 流程 4: E2E 测试（测试人员视角）
测试人员 → aion-test e2e（AI 自动勘察 + 多源生成用例）→ 审核用例 → 再次运行执行测试 → 查看报告 → aion-bug（提 Bug）[CONFIRMED]

### 流程 5: 知识积累飞轮
aion-review（审查代码）→ 自动提取规则到 rules/ → 下次 Claude Code 会话加载规则 → aion-impl（遵守规则编码）→ aion-review → 更多规则 → 持续改进 [CONFIRMED]

## 四、模块架构
| 模块 | 职责 | 对外接口 | 依赖 | 解耦方式 |
|------|------|---------|------|---------|
| core | 项目检测、初始化、版本管理（纯逻辑，无副作用） | Python API | 无外部依赖 | 函数调用 |
| commands | CLI 命令封装（init/upgrade/dashboard/doctor/version/clean/install/uninstall） | argparse CLI | core, utils | CLI → core |
| utils.console | Rich 终端渲染（颜色、表格、进度条） | Python API | rich | 函数调用 |
| utils.platform | 跨平台检测（OS、架构、路径、权限） | Python API | 无 | 函数调用 |
| utils.network | GitHub API 集成（下载、版本检查、Token 认证） | Python API | urllib | HTTP |
| utils.integrity | MD5 哈希、指纹提取、CLAUDE.md 合并 | Python API | hashlib | 函数调用 |
| dashboard.app | FastAPI 应用工厂（CORS、生命周期、路由注册） | HTTP REST API | FastAPI, uvicorn | HTTP |
| dashboard.routers | 10 个 API 路由模块（projects/files/monitor/bugs/team/commands/skills/logs/browse） | REST endpoints | services | 路由→服务 |
| dashboard.services | 7 个业务服务（project_registry/file_ops/bugs/encoding/monitor/team/stats/skills） | Python API | 文件系统 | 文件 I/O |
| dashboard.frontend | 嵌入式 HTML/CSS/JS 前端（build_frontend.py 构建） | HTML pages | 无运行时依赖 | 内嵌 |
| commands/ (skills) | 18 个 Markdown 命令文件，由 Claude Code 加载执行 | Claude Code prompt | .aion/ 数据 | 文件驱动 |
| .aion/ | 项目智能数据目录（规则、规格、计划、日志、Bug、测试） | 文件系统 | 无 | 文件驱动 |

## 五、技术栈
| 层 | 选型 | 版本 | 选型理由 |
|----|------|------|---------|
| 语言 | Python | 3.10+ | 与 Claude Code 生态兼容，丰富的库支持 [CONFIRMED] |
| CLI | argparse + Rich | rich>=13.0 | 零外部 CLI 框架依赖，Rich 提供美观终端输出 [CONFIRMED] |
| Web 框架 | FastAPI | >=0.115.0 | 异步、自动 API 文档、类型安全 [CONFIRMED] |
| ASGI 服务器 | Uvicorn | >=0.30.0 | FastAPI 标准搭配 [CONFIRMED] |
| 版本管理 | packaging | >=23.0 | 标准版本比较 [CONFIRMED] |
| 前端 | 原生 HTML/CSS/JS | 无框架 | 零构建依赖，嵌入 Python 文件分发 [CONFIRMED] |
| 打包 | PyInstaller | - | 单文件二进制分发，用户无需安装 Python [CONFIRMED] |
| 测试 | pytest + httpx | pytest>=7.0 | 标准 Python 测试框架 [CONFIRMED] |
| Lint | Ruff | >=0.4 | 极快的 Python linter，替代 flake8+isort [CONFIRMED] |
| CI/CD | GitHub Actions | - | 私有仓库，3 平台矩阵构建 [CONFIRMED] |
| AI 集成 | Claude Code Skills | Markdown 命令 | 无 SDK 依赖，纯 prompt 驱动 [CONFIRMED] |

## 六、数据模型（核心实体）
| 实体 | 字段概要 | 关系 | 存储方式 |
|------|---------|------|---------|
| Project | path, name, created_at | 1:N rules, specs, plans | projects.json |
| Rule | title, source, date, cite_count, last_cited, status | N:1 category (style/pitfalls/perf) | .aion/rules/{category}.md |
| Spec | title, version, scope, status, created_at | 1:1 plan, N:1 project | .aion/specs/{name}.md |
| Plan | feature, steps, current_step, total_steps, status | 1:1 spec | .aion/plans/{name}.md |
| Bug | id, title, severity, status, assignee, created_at | N:1 project | .aion/bugs/{id}.md |
| Review | status, score, verdict, issues_found, reviewed_at | N:1 project | .aion/reviews/{name}.md |
| Session | started_at, tools_used, files_changed | N:1 project | .aion/sessions.jsonl |
| Changelog Entry | date, type, summary, pending | N:1 project | .aion/changelog.md |
| Team Member | name, role, git_email, expertise | N:1 project | .aion/team.yml |
| Skill | name, dir_name, source, description | N:1 project | .claude/commands/ |
| _product.md | product, generation_method, confidence | 1:1 project | .aion/specs/_product.md |

## 七、部署与环境
- **生产环境**：PyInstaller 单文件二进制，GitHub Releases 分发（macOS arm64 / Linux x64 / Windows x64） [CONFIRMED]
- **开发环境**：`pip install -e ".[dev]"` 源码安装，`python -m aioncode` 运行 [CONFIRMED]
- **Dashboard 开发**：`python3.11 -c "from aioncode.internal.dashboard.app import create_app; import uvicorn; uvicorn.run(create_app(dev=True), host='127.0.0.1', port=19200)"` [CONFIRMED]
- **前端构建**：`python -m aioncode.internal.dashboard.frontend.build_frontend` → 生成 embedded.py [CONFIRMED]
- **CI/CD**：push/PR to master 触发 lint+test；git tag v* 触发 3 平台构建+发布 [CONFIRMED]

## 八、已知约束与限制
- GitHub 仓库为 private，upgrade 命令需要 GITHUB_TOKEN 环境变量 [CONFIRMED]
- 前端无构建工具（无 Node.js），所有 JS 手写，changes 需运行 build_frontend.py [CONFIRMED]
- uninstall.sh 仅删除 11/18 个命令文件，缺失 7 个新命令 [CONFIRMED]
- Playwright 浏览器自动化仅限 aion-test e2e 和 aion-scan --url 模式 [CONFIRMED]
- commands/ 与 .claude/commands/ 必须手动同步，禁止自动复制 [CONFIRMED]
- .aion/ 与 templates/ 数据流单向：templates/ → .aion/，禁止反向同步 [CONFIRMED]
- 单文件行数上限 500 行、单函数 50 行、嵌套 4 层、参数 5 个 [CONFIRMED]
