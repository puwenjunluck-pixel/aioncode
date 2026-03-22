# Changelog

<!-- AionCode auto-appends entries here. Do not remove this file. -->

## 2026-03-22 | chore: auto 模式权限扩展 + loop 报告持久化

### Summary
- settings 模板新增 11 个 auto 模式常用权限（python3、kill、lsof、curl、find、sleep 等）
- aion-loop 新增 Step 4.5：执行报告持久化到 `.aion/monitor/loop-{timestamp}.md`
- 分析了 auto 模式下高频拦截 TOP 3：python3 命令、链式命令、进程管理

### Key Conclusions
- 权限越大审计越重要，loop 报告持久化是必要的安全审计手段

---

## 2026-03-22 | fix: dashboard 版本号动态显示 + 关于页命令补全

### Summary
- 底栏右下角 "AionCode" 改为动态 "AionCode v{version}"，从 stats API 读取
- 关于页命令速查表补全缺失的 4 个命令：aion-loop、aion-status、aion-upgrade、aion-learn
- stats API 新增 `aioncode_version` 字段

### Files Changed
- stats.py（新增 aioncode_version 字段）、app.js、index.html、views.js、embedded.py
- 新增 spec: .aion/specs/dashboard-polish.md

---

## 2026-03-22 | feat: Skills 管理视图 + CLAUDE.md 强制化 + 命令并行策略

### Summary
- Dashboard 新增「技能」视图：已安装 skill 列表 + 官方市场浏览 + 详情查看 + 一键卸载/安装
- Dashboard UI 改进：右上角 AIONCODE 品牌暗刻（深色蓝色/浅色灰色）、设置面板（主题 toggle switch）、命令面板移除
- 内置 2 个基础 skill：find-skills（原样复制）+ aion-skill-creator（自研轻量版 skill 创建引导）
- `aioncode init` 新增步骤 2.5：自动安装内置 skill 到 ~/.claude/skills/（绝不覆盖已有）
- CLAUDE.md 模板从信息性措辞强化为强制性措辞（NEVER/ALWAYS），新增 3 条 key rules
- 分析发现 18 个 aion 命令均未引用 subagent/Agent Team，导致并行能力从未触发
- 6 个命令新增可选并行策略：aion-impl（Agent Team 前后端分工/多 bug 并行）、aion-scan（Explore subagent）、aion-verify/review（subagent 并行检查）、aion-crosscheck（多模型并行）、aion-bug（提示 impl 的 Team 能力）
- 关于页公司信息更新：成都奕贝科技公司

### Key Decisions
- 不内置特定第三方 skill，而是提供 skill 管理平台（浏览 + 搜索引导 + 创建引导）
- skill-creator 自研轻量版：只做脚手架生成和编写指南，不含 eval/benchmark 重量级功能
- 并行策略用 "consider using" 措辞，Claude 根据复杂度自行判断，不强制
- Agent Team 适合 impl 前后端分工和多 bug 并行，Subagent 适合 scan/verify/review/crosscheck
- 讨论了 Opus plan + Sonnet execute 模型路由方案，暂不实现，需要时可加到 aion 命令

### Files Changed
- 新增: services/skills.py, routers/skills.py（backend）
- 新增: templates/skills/find-skills/SKILL.md, templates/skills/aion-skill-creator/SKILL.md
- 修改: app.py, index.html, app.js, views.js, views.css, style.css（frontend）
- 修改: core/project.py（init 步骤 2.5）
- 修改: CLAUDE.md.tpl + .claude/CLAUDE.md（强制措辞）
- 修改: commands/aion-impl.md, aion-scan.md, aion-verify.md, aion-review.md, aion-crosscheck.md, aion-bug.md（并行策略）
- 重建: embedded.py

### 后续补充（同一会话）
- aion-save 增强：新增 git diff 代码变更审计 + CLAUDE.md 标记外 Project Notes 智能更新 + 追溯性 spec/plan 生成
- 注释规则：5 条新规则写入 .aion/rules/style.md（Python docstring + JS 函数说明 + 注释只解释 why）
- 发现并修正 aion 命令的 subagent/Agent Team 从未触发问题（18 个命令均未引用）

### Pending
- 未提交，待用户确认后提交
- MCP 可视化是否纳入 dashboard 待讨论
- 模型路由（Opus plan / Sonnet execute）待需要时实现

---

## 2026-03-22 23:30 | feat: v0.5 收尾 — 数据视图 + CLAUDE.md 重塑 + 发布准备

### Summary
- CLAUDE.md 定位重塑：从"笔记本"回归"索引页"（212→19 行），删除 LEARNED 概念
- merge_claude_md() 重写为正则严格对齐 + >100 行 size warning
- aion-save 移除 CLAUDE.md 写入，防止 AI 导致的无限膨胀
- 副驾驶新增 6 个数据视图：需求/方案/规则/清单/缺陷/测试/日志
- 前端拆分为 4 文件（app.js + views.js + style.css + views.css）控制在 500 行内
- 移除控制台独立入口（openMonitor + /monitor 路由），功能由监控视图覆盖
- 关于页面扩展为完整用户教程（9 章节 + 侧边栏目录导航）
- 旧 dashboard.py 4810 行已删除，零残留引用
- 53 个测试全过，ruff 0 违规
- 版本号 0.4.0 → 0.5.0，模板 config.yml 同步更新
- init 命令新增 Claude Code CLI 检测（warning 级，不阻断）
- 发布前阻塞项全部修复（ruff UP045/SIM108、httpx 依赖）
- 项目自身成功执行 aioncode init（upgrade 模式），config 升至 0.5.0

### Key Conclusions
- CLAUDE.md 只做索引页，学习内容沉淀到 .aion/rules/ 或 Claude Memory
- 前端文件拆分是必要的（app.js 668 行超限），views.js 承载视图渲染 + markdown 解析
- dogfooding 升级验证通过：所有 rules/specs/plans/changelog 零损失

### Pending
- 提交全部变更 → merge 到 master → tag v0.5.0 → push
- GitHub Release 自动构建 4 平台二进制
- README.md 需更新（仍引用旧 install.sh 和 .aion/bin/）

---

## 2026-03-22 22:00 | feat: Dashboard v0.5 — FastAPI 重构 + 副驾驶 UI

### Summary
- 设计双 Web 系统架构（本地副驾驶 + 云端管理平台），输出 spec `.aion/specs/dual-web-architecture.md`
- 本地 Dashboard 完整重构：4810 行单文件 → 28 个模块化文件（FastAPI + uvicorn）
- 新建 Core 层 `aioncode/core/project.py`，统一 CLI 和 Web 的 init_project 逻辑
- 副驾驶 UI：双栏 IDE 布局（图标栏 + 侧边栏 + 详情区），视图切换模式
- 5 个视图：概览/文件/监控/缺陷/团队，左栏列表右栏详情
- 深色/浅色主题切换（暖灰底色浅色主题，非纯白）
- 关于页面：完整使用说明和工作流指南
- 命令面板（⌘K）、SSE 实时事件流、文件预览器
- PyInstaller spec 更新（FastAPI/uvicorn 全部 hiddenimports）
- `build_frontend.py` 构建脚本：CSS/JS 注入 HTML → embedded.py，零 static/ 依赖
- 双进程隔离 CLI 入口（主进程 CLI + 子进程 uvicorn）

### Key Decisions
- 本地端定位"沉浸式副驾驶"，CLI 的可视化外壳，不是独立 Web App
- 云端独立仓库 aioncode-cloud，FastAPI + PostgreSQL + Vue 3
- 意图日志三层防线：数据剥离 + 模糊化 + 意图聚合
- Core 层统一：CLI 和 Web 共享 init_project，取 CLI 严谨性 + Web 灵活性
- 前端不用框架，Vanilla JS + 构建时注入，保持 PyInstaller 单文件分发
- 布局采用视图切换（类 VS Code），非手风琴折叠
- 浅色主题用暖灰底色(#f0f0ee) + 白色表面(#fff) 拉层级

### Files Changed
- 新增 28 个文件：core/、internal/dashboard/ 包（app, config, 8 routers, 7 services, frontend）
- 修改 4 个文件：pyproject.toml, aioncode.spec, main.py, commands/dashboard.py
- 修改 1 个测试：tests/test_cli_init.py（适配 core 层导入）
- 新增 spec：.aion/specs/dual-web-architecture.md
- 新增 plan：.aion/plans/dashboard-v05-refactor.md
- 分支：feat/dashboard-v05-refactor（未提交）

### v0.5 收尾（2026-03-22）
- 删除旧 dashboard.py（4810 行）→ 零残留引用
- 集成测试 23 个 API 端点（TestClient），53 个测试全过
- 版本号 0.4.0 → 0.5.0
- CLAUDE.md 定位重塑：从"笔记本"回归"索引页"（212 行 → 19 行）
- 删除 LEARNED 概念，merge_claude_md() 重写为正则严格对齐 + size warning
- aion-save 移除 CLAUDE.md 写入（Layer 2），防止 AI 导致的无限膨胀
- pitfalls: dashboard 路由规则标记 deprecated，新增 embedded.py 规则
- style: dashboard.py 豁免更新为 embedded.py
- bugs.py 修复 Python 3.9 兼容性（`str | None` → `Optional[str]`）

### Pending
- 提交 v0.5 完整工作
- v0.6 云端 MVP 开发

---

## 2026-03-22 03:00 | feat: CI/CD pipeline + quality gates + test framework
- 完整 CI/CD：ci.yml (ruff + pytest 3 版本矩阵 + 熔断 smoke test) + release.yml (CI 前置 + 版本铁律)
- 50 个测试（integrity 18 + main 10 + platform 11 + version 3 + cli_init 3 + conftest fixtures）
- 屎山防治 5 缺口全覆盖：复用扫描、复杂度门禁、TDD、Review Gate、技术债台账
- learn 吸收进 review，工作流 8→7 节点
- commit 前必须 review（docs-only 可豁免）
- 修复 init.py 逻辑错误 + 测试硬编码
- pyproject.toml：requests→packaging，+ruff/pytest 配置
- Review: approved (78/100)
- Commit: 6c8aa46

---

## 2026-03-22 01:00 | feat: AionCode v0.4 — Python unified CLI rewrite
- 将 install.sh/uninstall.sh/dashboard.py 合并为统一 Python CLI 包
- 8 个子命令：init, install, upgrade, uninstall, dashboard, doctor, version, clean
- 跨平台支持（pathlib + UTF-8 + Windows 长路径 + UAC）
- rich 终端渲染，PyInstaller 单文件打包
- GitHub Actions CI 四平台构建（macOS-arm64/x64, Linux-x64, Windows-x64）
- 旧脚本 install.sh / uninstall.sh 标记 deprecated
- 47 个文件新增，8460 行代码
- Commit: d7bbd5c

---

## 2026-03-21 23:30 | feat: initial commit — AionCode v0.3
- 首次 git 提交，94 个文件入库
- 排除 projects.json（含本地路径），加入 .gitignore
- Commit: 251a3a5

---

## 2026-03-21 22:00 | feat: Write Protocol + Dashboard 日志/帮助中心 + 升级机制重构

### Summary
- 设计并实现 Write Protocol 统一写入保护协议（四类文件分级保护 + Refusal Condition + Fingerprint + Scope 冲突检测）
- 修复 aion-learn 边界问题（Evidence Gate：证据源全空时返回 BLOCKED，不越界做全量扫描）
- 修复 aion-scan（FIRST_SCAN/RE_SCAN 双模式 + Delta Report）
- 修复 aion-design（新增 Step 3.5 版本检查 + scope 冲突）
- 修复 aion-test（Regenerable fingerprint 保护）
- 重写 uninstall.sh（动态扫描命令、CLAUDE.md 只删标记区域、hooks/settings 备份、防误卸载确认）
- Dashboard 新增日志中心（Changelog/Sessions/Events 三源聚合）
- Dashboard 新增帮助中心（使用说明 + 更新日志）
- 最佳实践页面重构为角色/场景导向，去命令化
- 升级机制：dashboard.py + uninstall.sh 纳入 .aion/bin/ 统一管理
- 版本升至 v0.3

### Key Decisions
- Write Protocol 四类文件：Accumulative / Versioned / Regenerable / Unique-by-ID
- learn 的范围严格限定为增量经验，全量扫描是 scan 的职责
- Versioned 文件必须声明 scope（api/web/mobile/infra/full），不同 scope 同名文件强制换名
- Regenerable 文件用 MD5 fingerprint 检测用户修改
- uninstall.sh 需输入"aioncode"确认，防误操作
- .aion/bin/ 作为工具目录，安装/升级时无条件覆盖
- 仓库将公开，通过 GitHub Releases 分发 tarball
- v0.4 目标：Python 重写脚本实现跨平台（Windows 支持）

### Files Changed
- 新增: templates/aion/refs/write-protocol.md
- 修改: commands/aion-learn.md, aion-scan.md, aion-design.md, aion-test.md, aion-plan.md, aion-save.md
- 修改: dashboard.py（日志中心 + 帮助中心 + 最佳实践重构 + changelog API）
- 重写: uninstall.sh（安全卸载）
- 修改: install.sh（.aion/bin/ 复制 + Dashboard 提示）
- 修改: README.md（路径更新）
- 修改: templates/aion/config.yml（v0.2 → v0.3）
- 新增: .aion/refs/architecture.md, api-inventory.md（scan 产物）
- 新增: .aion/specs/refactor-targets.md（scan 产物）
- 新增: .aion/rules/ 初始规则（2 style + 3 pitfalls）

### Pending
- 创建 GitHub 公开仓库，首次提交
- 编写 build.sh / install-remote.sh / upgrade.sh（远程安装/升级）
- v0.4: Python 重写 install/upgrade/uninstall 实现 Windows 支持

---

## 2026-03-21 20:30 | enhance: aion-save 完成后提醒执行 aion-learn

### Summary
- 讨论了在何处提醒用户执行 /aion-learn 以避免遗忘
- 评估了 review/commit/verify/save 等多个触发时机
- 决定在 aion-save 完成后添加条件性提示

### Key Conclusions
- aion-save 是最自然的触发点：用户已在做"沉淀"动作，心智负担最小
- 条件性提示（涉及代码变更时才建议），避免提醒疲劳

### Files Changed
- commands/aion-save.md — Next Steps 末尾新增 learn 提示语

---

## 2026-03-21 17:00 | feat: Bug 追踪系统 + 交叉验证 + 版本升级

### Summary
- 设计并实现了完整的 Bug 追踪与团队协作系统
- 新增 3 个命令：aion-bug、aion-crosscheck、aion-upgrade
- 增强 6 个命令：aion-save（三层持久化）、aion-impl/verify/commit/status/help
- 实现版本升级机制（install.sh --upgrade + Dashboard UI + /aion-upgrade）
- 重写 install.sh：预检 + CLAUDE.md marker 合并 + 安装报告
- Dashboard 新增 Bug 看板页面、团队管理页面、7 个新 API

### Key Decisions
- Bug ID 格式：`{F|B|X}-{MMDD}-{SEQ}`，分类即分配
- git blame + team.yml 自动识别 Bug 责任人
- 交叉验证（/aion-crosscheck）与 Bug 管理（/aion-bug）完全解耦
- aion-save 三层持久化：.aion/ + CLAUDE.md + Claude memory
- CLAUDE.md 使用 markers 合并，永不覆盖用户内容
- 版本号从 0.1 升至 0.2

### Files Changed
- 新增: commands/aion-bug.md, aion-crosscheck.md, aion-upgrade.md
- 新增: templates/aion/team.yml
- 修改: commands/aion-save.md, aion-impl.md, aion-verify.md, aion-commit.md, aion-status.md, aion-help.md
- 修改: templates/CLAUDE.md.tpl, templates/aion/config.yml
- 修改: install.sh (重写), dashboard.py (Bug 看板+团队管理+升级)
- 修改: docs/aion-design.md, docs/commands.md
- 命令总数: 15 → 18

### Pending
- 在实际项目中验证 Bug 工作流（report → assign → impl → close）
- 交叉验证需配置第三方模型 API key 才能测试
- 云端部署方案待后续讨论
