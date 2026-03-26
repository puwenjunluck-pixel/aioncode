# Changelog

<!-- AionCode auto-appends entries here. Do not remove this file. -->

## 2026-03-26 | chore: commands/ + profiles.py 同步 v0.7 10 命令
- `commands/` 源目录清理旧命令、新增 aion-fix/aion-qa、更新 8 个命令文件
- `profiles.py` ALL_COMMANDS 18→10，ROLE_PRESETS 更新为新命令集
- `init.py` Next Steps 提示 aion-status → aion-help
- 修复：`aioncode init` 会重装已删除的 aion-learn/aion-status
- Commit: 8501be5

## 2026-03-26 | feat: dashboard 帮助/关于拆分 + 命令体系精简（18→10）+ bump 0.6.8
- 版本号从 0.6.7 → 0.6.8
- Dashboard 帮助/关于拆分：帮助（高频使用指南）+ 关于（低频产品身份）
- _renderTestingGuide() 完整重写为 v0.7 体系（aion-qa/fix/review）
- 命令体系 18→10：新增 aion-qa / aion-fix，删除 10 个旧命令
- network.py SSL certifi fallback 修复
- Commit: 26e4930

## 2026-03-26 | feat: Dashboard 帮助/关于拆分 + 命令体系精简（18→10）

### Summary
- Dashboard「关于」拆分为「帮助」（使用指南，高频）+「关于」（产品身份，低频）
- 帮助页：新 10 命令速查表、4 步工作流图（design→plan→review→commit）、常见场景、测试最佳实践、副驾驶面板说明、FAQ（9 项）
- 关于页：精简为产品介绍 + 安装升级 + 路线图 + 更新日志（4 章节）
- 命令体系从 18 → 10：删除 aion-think/demo/impl/test/verify/learn/bug/crosscheck/status/upgrade
- 新增 aion-qa（浏览器 QA + bug 报告，基于 project_type 智能 split/unified 目录）
- 新增 aion-fix（按角色过滤 bugs，atomic commit 逐个修复）
- aion-review 重写：verify + 审查 + test gap + 自动学习一站式，--quick 跳过 gap 分析
- aion-design 重写：Anti-Sycophancy + PREMISES 假设挑战 + 3 方案对比（A/B/C）+ --demo/--file/--skip-challenge
- aion-plan 重写：Scope Challenge（8+ 文件 = smell）+ ASCII 图 + 用户确认后直接执行
- 更新 .aion/bin/dashboard.py 遗留命令表 → 新 10 命令架构

### Key Conclusions
- 10 命令完整覆盖工作流：scan→design→plan→review→qa→fix→commit→loop→save→help
- 帮助/关于拆分遵循「高频/低频分离」原则
- project_type（frontend/backend/fullstack/monorepo）驱动 aion-qa/aion-fix 的 split/unified bug 目录

### Pending
- ~~aioncode Python 包尚未同步 10 命令~~ ✅ 已完成（profiles.py + init.py），仅 install.sh / uninstall.sh 待确认
- _renderTestingGuide() 内部命令引用仍是旧体系（aion-test e2e 等），需后续更新
- gstack 借鉴功能（aion-design --demo 0-10 维度评分）推迟到下次迭代

---

## 2026-03-25 | fix: CI 构建 certifi 缺失 + SSL fallback 防护

### Summary
- GitHub Actions release CI 构建因 `certifi` 未安装导致 PyInstaller 报 `(None, 'certifi')` 错误
- `release.yml` pip install 步骤添加 `certifi` 依赖
- `aioncode.spec` 添加系统 CA 路径 fallback 搜索（Ubuntu/RHEL/macOS）
- `network.py` `_setup_ssl()` 添加系统 CA 路径 fallback，解决旧二进制升级时 SSL 失败问题
- 已提交 commit 14bbb5f，重新打 v0.6.7 tag 触发 CI 重建

### Key Conclusions
- 旧版本二进制（v0.6.6）因缺 SSL 证书无法自我升级，需手动下载新版替换
- 新版本同时修复了构建端和运行端的 SSL 问题，后续版本不再有此问题

---

## 2026-03-25 | fix: 关于页使用说明更新 + init.py ruff 修复
- Dashboard 关于页同步 v0.6.6 变更：命令速查、工作流、常见场景、安装说明、FAQ、路线图、更新日志
- 修复 init.py ruff F821/UP037：InitProfile import 提升到模块顶层
- Commit: 56e304c

---

## 2026-03-25 | feat: design-plan 工作流合并 + init 交互式安装

### Summary
- design→spec→plan 三步合并为 design→plan 一步流程，消除冗余
- aion-design 重写：直出 plan.md + 自动更新 _product.md，支持 --design-only
- aion-plan 降级为"修订实现方案"，仅用于已有 plan 的修订
- 10 个命令文件更新 spec→plan 引用，全部添加 legacy fallback
- init 新增交互式安装：项目类型→角色→命令推荐→自由选择
- 新建 profiles.py（角色预设矩阵）、console.py 新增 choose_one/toggle_select
- 11 个已完成 spec/plan 归档至 archive/，changelog 滚动归档
- architecture.md 更新至 v0.6.4 基线
- Commit: 751c94f

---

## 2026-03-24 | session: Review + Scan

### Summary
- aion-review 审查 11 文件 1215 行变更，发现 8 个问题（1 critical + 3 major + 4 minor）
- 全部 8 个问题修复：embedded.py 重建、views.js renderAboutPage 拆分（287→57行）、Playwright 规则统一、格式列表一致化
- 提交 ca1806c (feat: 产品设计层+测试体系升级) + 43c464a (chore: bump 0.6.3)
- aion-scan 生成 _product.md 产品设计全景文档（8 章节，confidence: high）

### Key Conclusions
- _product.md 全部 [INFERRED] 项已确认为 [CONFIRMED]，商业模式定为"当前闭源，稳定后考虑开源"

### Pending
- CI/CD 构建 v0.6.3 后手动下载替换二进制
- architecture.md 仍为 v0.4 基线，需更新到 v0.6

---

## 2026-03-24 | feat: 产品设计层 + Dashboard 使用指南完善

### Summary
- 新增 `_product.md` 产品设计全景文档层：产品定位、功能地图、核心业务流程、模块架构、技术栈、数据模型
- `aion-design` 新增 `--file` 参数：从 .docx/.pdf/.pptx 导入外部需求 → 自动生成 spec + 更新 _product.md
- `aion-scan` 新增 `--file` / `--url` 参数：浏览器实地探索（Playwright MCP）+ 外部文档导入 → 生成 _product.md
- `aion-scan` 新增 Step 6.5 AI Q&A：展示 [INFERRED] 推断项，用户确认后升级为 [CONFIRMED]
- `aion-plan` 新增 Step 4.5：完成后自动传播模块/技术栈变更到 _product.md
- `aion-test e2e` Phase 1 新增 Source 0：读取 _product.md 作为全局上下文
- `aion-test e2e` 新增 Step 5.0 智能目标匹配：支持中文描述/spec 名/模块路径/交互式选择
- Dashboard「关于」全面更新：命令速查表、常见场景、副驾驶面板视图（5→14）、FAQ（+4 条）、版本路线图
- Dashboard 新增「更新日志」板块：4 条版本记录（测试升级、GitHub Token、auto 模式、v0.6.0）

### Key Conclusions
- 产品设计层填补了 spec（做什么）和 plan（怎么做）之间的"做成什么样"断层
- 三种生成策略：Design 聚合（新项目）、浏览器探索+代码扫描（能跑的旧项目）、代码扫描+AI 提问（跑不起来的旧项目）
- `--file` 支持让 AionCode 能接入团队已有的需求文档，不要求从零开始

### Pending
- views.js 修改后需运行 build_frontend.py 更新 embedded.py（生产环境）
- _product.md 模板不随 init 分发（运行时由命令动态生成）
- commands/ 修改需用户手动同步到 .claude/commands/

---

## 2026-03-23 | feat: 测试体系升级 — 自愈 + E2E + 多代理管道

### Summary
- 行业调研（OpenObserve 多代理管道、Shipyard TDD、Quinn AI QA、TestDino Playwright Skill）
- `aion-test.md` 重构（357→849 行）：新增 `--heal` 自愈、`e2e` 三阶段（勘察→多源生成→执行）、`pipeline` 多代理管道
- `aion-verify.md` 升级：新增 `--fix` 自动修复模式（lint auto-fix、test self-healing）
- E2E 自然语言测试定义格式（`.aion/tests/e2e/*.md`，Given/When/Then + Edge Cases）
- 多源 E2E 用例生成：spec + 源码 + 实地勘察 + API 契约 + Bug 历史，覆盖率估计 ~90%
- Dashboard 关于页新增"测试人员最佳实践"板块（11 个子章节）
- 4 个模拟测试（default/e2e/heal/verify）发现 13 个问题并全部修复
- pitfalls.md 新增 Playwright 限制规则

### Key Conclusions
- 测试人员不需要手写用例，AI 从多源自动生成，人工仅审核补充
- `--heal` 的 CRITICAL 规则区分源码修复（需 spec）和测试修复（允许无 spec）
- ImportError 诊断拆分为"依赖未装 [ENV_ISSUE]"和"模块改名 [TEST_FIX]"

### Pending
- views.js 修改后需运行 build_frontend.py 更新 embedded.py（生产环境）
- Playwright MCP 实际集成测试（当前无 MCP 环境）
- commands/ 修改需用户手动同步到 .claude/commands/

---

## 2026-03-23 | feat: GitHub Token 认证支持私有仓库升级
- network.py 新增 `_get_token()` / `_build_headers()` 认证辅助，私有仓库 API 和 asset 下载均支持 token
- upgrade.py 适配认证下载，401/403/404 给出明确中文提示
- 版本号同步至 v0.6.3（含 templates/aion/config.yml 从 0.5.0 补齐）
- Review: approved (94/100)
- Commit: 35f114a

<!-- Older entries archived to changelog.archive.md -->
