# Changelog

<!-- AionCode auto-appends entries here. Do not remove this file. -->

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

## 2026-03-23 | docs: 关于页安装升级教程 + 版本路线图更新

### Summary
- 关于页"安装与初始化"重写为"安装与升级"，包含 3 平台安装命令表格
- 升级流程修正为 `aioncode upgrade` + `aioncode init`（非 init --upgrade）
- FAQ 升级问题修正
- 版本路线图更新：v0.6（当前）

### Pending
- GitHub 仓库为 private，`aioncode upgrade` 无法访问 API（需要 token 或改为 public）
- 关于页内容未提交

---

<!-- Older entries archived to changelog.archive.md -->
