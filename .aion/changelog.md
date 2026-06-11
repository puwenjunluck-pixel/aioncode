# Changelog

<!-- AionCode auto-appends entries here. Do not remove this file. -->

## 2026-06-12 | feat(v0.8.0): 插件形态重生 — P1-P4 完成

### Summary
按 contraction-to-plugin spec v2 完成 P1-P4：插件骨架（name: aion）+ 9 skills 蒸馏迁移 + 双 hook（安全 + 提交门禁）+ 机制层一次性删除（-20,086 行）+ 文档层重写。剩余：对标优化循环（Task 7）+ 用户侧动作（push / 开源 / marketplace 提交 / 本仓库 hooks.json 切换）。

### 核心改动
- **P1 骨架**：.claude-plugin/{plugin.json,marketplace.json}，`claude plugin validate` 通过
- **P2 skills**：think 手工旗舰 + 8 个并行代理蒸馏；评估确认的 prompts 缺陷全修（plan 三处矛盾、review 门禁字段 reviewed_files/base_commit、audit 并入 --deep、飞轮 stale 出口、纪律层随 init 分发、aion-help/loop 移除）
- **P3 hooks**：check-review.sh（8/8 测试）+ safety-check.sh 移植（7/7 测试，发现并修复测试用例自身 JSON 转义 bug——验证了 fail-open 设计）
- **机制层删除**：aioncode/ 80 文件、commands/、docs/、.claude/commands/、双安装脚本、pyproject、release.yml、Python 测试全退役；CI 重写为 hook 测试 + 一致性断言 + validate
- **P4 文档**：README（真实飞轮证据替换虚构周曲线，引用 pitfalls 13 条中的 3 条实例）+ MIGRATION.md（命令映射表）+ CHANGELOG.md + CREDITS.md（superpowers 致谢 + 原创增量声明）

### 受阻项
- `.claude/hooks.json` 门禁激活被权限分类器拦截（自我修改边界），已恢复 .aion/hooks/ 旧文件保持现状可用；切换内容见 .aion/reviews/mechanism-layer-removal.md

### Verification
- hook 双测试套 8/8 + 7/7；`claude plugin validate .` 通过；README 命令表与 skills/ 9=9 一致；死引用 grep 0 命中；版本 0.8.0 三处一致（plugin.json/CHANGELOG/changelog）

---

## 2026-06-12 | chore(P0): 战略收缩定界 — v0.7.6-final 封存 + 插件化决策记录

### Summary
基于 2026-06-11 多代理深度评估（29 项发现全核实成立）与竞品/平台调研，确定「方案 3 收缩」：砍机制层（CLI 二进制 / Dashboard / Antigravity），方法论层蒸馏为 Claude Code 官方插件（skills 形态，名 `aion`）并开源。本条目为 P0 定界封存。

### 核心改动
- **封存**：tag `v0.7.6-final` + 分支 `archive/v0.7-cli`（commit `7e09e4d`），旧形态可随时找回
- **收尾提交**：v0.7.6 遗留三处入库（changelog 补录 + pitfalls 2 条 rules learned + version.py 全量版本比较修复），review 见 `.aion/reviews/v0.7.6-final-seal.md`（95/100）
- **决策记录**：`.aion/specs/contraction-to-plugin.md` — 五项决策全部拍板（开源 MIT / 放弃 Antigravity / Dashboard 归档 / 插件名 aion / audit 并入 review），含 11 命令 → 8 skills 处置表、分阶段路线（P0-P4，预算 7-11 工作日）与验收标准
- **新惯例**：review 文件 frontmatter 自 `v0.7.6-final-seal.md` 起增加 `reviewed_files` + `base_commit` 字段（回应评估发现：门禁需可机械校验覆盖范围）

### Verification
- 本条目与 spec 为纯 `.aion/` 文档变更，Verification Gate N/A（依 aion-review 纯文档出口）
- 封存提交的验证：`pytest tests/ -q` 77 passed / `ruff check` + `ruff format --check` 全绿

### Next
- P1：插件骨架 + think 垂直切片（`.claude-plugin/plugin.json` + 端到端自装实测）

---

## 2026-04-14 | chore(v0.7.6): template version sync + docs refresh + legacy cleanup

### Summary
v0.7.6 发布后 dogfood 自升级(`aioncode init` on self)抓到 templates 版本号未同步(0.7.5 残留),由此顺势完成发布前应做的全面清理。已打 tag `v0.7.6` 并 push 到 origin。

### 核心改动
- **fix**: `aioncode/internal/templates/aion/config.yml` 0.7.5 → 0.7.6 + phases 刷新(`design/demo/impl/test/verify/...` → `think/plan/impl/qa/review/commit`)
- **docs refresh**: README + `docs/commands.md` + `docs/how-it-works.md` 重写至 v0.7.6 命令体系(11 命令),删 `docs/aion-design.md`(601 行老设计稿)
- **legacy cleanup**:
  - `git rm -r templates/`(根目录废弃,与 `aioncode/internal/templates/` 严重漂移,pyproject 不打包)
  - `git rm -r .aion/bin/`(v0.5 老 dashboard.py 4738 行 + 废弃 uninstall.sh)
  - 归档 `.aion/specs/{dashboard-brainstorm,design-plan-upgrade}.md` + `.aion/plans/design-plan-upgrade.md`(已实现 spec 移入 archive/)
  - 删 `.aion/checklists/design.md`(已被 think.md 取代)
- **dogfood**: 同步 `.claude/commands/`(11 命令,aion-think/audit 入,aion-design 出)+ `.aion/config.yml`(phases/commands 刷新)

### Rules learned: 2
- pitfalls (updated cite_count): **NEVER 忘记同步模板 config.yml 版本号** — v0.7.6 同一坑再次触发,补强 bump 三件套 checklist
- pitfalls (new): **发布前必须扫查 docs/ 与非打包目录的过时引用** — docs/ 不在包内,import/ruff 测不到,差点带 4 个旧 `/project:aion-design` 引用 tag 发布

### Verification
- `aioncode.core.profiles` import + 11 commands 断言 ✓
- `embedded.py` 合规 ✓
- `ruff check aioncode/` all checks passed ✓
- `grep "aion-design"` 活跃引用 0 处(仅 changelog / reviews / archive / think.md:3 历史注释 / dashboard release log 保留)
- `grep "0.7.5"` 活跃引用 0 处

### Release
- commit `ed0852a` + 前置 `eef8556`/`b7ae451`/`9e84eca` 共 4 个 commit 已 push origin/master
- tag `v0.7.6` 已 push

---

## 2026-04-14 | feat: surgical superpowers fusion v0.7.6

### Summary
手术刀般吸收 superpowers 的纪律层(metacognition / Iron Laws / Verification Gate / 10-phase brainstorming / bite-sized plan / 4-phase debugging),同时保留 AionCode 骨架(命令结构 / `.aion/` 状态层 / 平台裁剪 / 中文工作流)。aion-design 整体重命名为 aion-think,语感从"命令式设计"转为"协作式思考碰撞"。

### 核心改动
- **rename**: `aion-design` → `aion-think`(git mv 保留历史)
- **新增规则模板**(抄录 superpowers,不依赖其包):
  - `.aion/rules/metacognition.md` — Iron Laws + 红旗表 + 合理化阻断表
  - `.aion/rules/spec-template.md` — 融合 AionCode P0/P1 + superpowers Architecture/Error Handling/Testing Strategy
  - `.aion/rules/plan-template.md` — bite-sized TDD step + 完整代码 + Verify + No Placeholders
- **aion-think 10-phase**: 探索 / 辅助角色 / 澄清 / 方案 / **挑战(AionCode 私加)** / 逐步批准 / 写 spec / 自审 / 用户复核 / 主动建议 plan
- **aion-plan 主动建议触发**: 由 aion-think Phase 10 自动衔接,命令保留仅用于修改已有 plan
- **aion-review Iron Laws + Verification Gate**: Step 2.8 强制在本次 session 跑验证命令才能 approve
- **aion-fix Iron Laws + 4-phase 根因分析**: 推荐默认 `--deep`
- **CREDITS.md**: 明确 superpowers(MIT)归属 + 借鉴/不借鉴对照表 + 升级追踪策略
- **rename 跨层传播**: profiles.py / init.py / install.sh / CLAUDE.md.tpl / GEMINI.md.tpl / checklists(design.md → think.md)/ dashboard UI(views.js/brainstorm.js/index.html/embedded.py rebuilt)

### Rules learned: 1 new
- pitfalls: **命令 rename 必须跨层扫描七件套** — surgical fusion 第一轮 review 只查 `.aion/` 和 `commands/`,漏掉 profiles.py 等 6 层,Iron Law 2 反面教材

### Verification
- `/project:aion-review` 两轮:第一轮 62/100 needs_fix(发现 rename 残留)→ 修复 16 文件 → 第二轮 93/100 approved
- profiles.py / init.py / embedded.py 实跑 import + 断言通过
- PLATFORM 标签配对 ✓(think 6/6, fix 6/6, review 2/2)

### 归属
本次纪律层改编基于 Obra Works 的 [superpowers](https://github.com/obra/superpowers) (MIT License v5.0.7)。详见 `.aion/CREDITS.md`。

---

## 2026-04-07 | feat: 多平台支持 v0.7.5 (Claude Code + Antigravity)
- PlatformConfig 数据类 + PLATFORMS 映射，抽象所有平台差异
- init 交互流新增平台检测 + 选择步骤
- project.py 全部路径参数化：命令目录、指令文件、前缀转换、hooks/settings 条件安装
- GEMINI.md.tpl 模板新建（Antigravity 项目指令）
- 修复升级路径丢失 platform 的 bug（review 发现）
- 6 命令加入平台感知段：Browser Agent (qa/scan/design/fix) + Manager View (review/loop/fix)
- `<!-- PLATFORM:name -->` 标记 + `_strip_platform_blocks()` 裁剪，安装时只保留目标平台内容
- 策略决策：同一套命令，不同 IDE 走各自最优路径（不是 if-else，是按平台裁剪）
- Rules learned: 1 new (pitfalls: upgrade 必须恢复完整 profile)
- Commits: 4a2b0e1, c9b402a, 64bb267, a3e5b13

## 2026-04-06 | feat: 命令体系升级 — superpowers 体验吸收

### Summary
- 对比 superpowers 14 个 skill 与 AionCode 10 命令体系，识别 7 项可借鉴能力（F1-F7）+ 1 项 gstack 遗留（G1）
- 升级 6 个命令文件，实现 F2-F7：
  - aion-design: 方案共创（Explore Approaches）+ 逐段确认 + Spec Self-Review
  - aion-plan: 步骤粒度强化（What/How/Verify）+ Plan Self-Review + 禁止短语
  - aion-review: 双阶段 Review（Spec Compliance + Code Quality）+ Rationalization Prevention + Receiving Code Review
  - aion-commit: Rationalization Prevention（6 条借口表）
  - aion-loop: --tdd（Red-Green-Refactor）+ --worktree（隔离工作树 + 四选一完成）
  - aion-fix: --deep（四阶段根因分析 + 3 次失败升级）
- 14 文件变更，+613/-53 行
- Commit: 5ffb0a6

### Key Conclusions
- superpowers 强在流程纪律（TDD/Debug/Review），AionCode 强在知识积累（rules/product doc/QA）
- 两者互补，本次吸收了 superpowers 的方法论优势，保留了 AionCode 的项目智能特色
- F1（Dashboard 设计协作视图）和 G1（aion-audit）scope 大，留待后续独立 spec

### Pending
- 无（C1 已提交 525ebbd，F1 已提交 9681d02，G1 已提交 9681d02）

## 2026-03-29 | fix: Dashboard 模型切换机制修正

### Summary
- 修复第三方模型切换报错"There's an issue with the selected model"：改为同时设置所有 model-family env vars（ANTHROPIC_MODEL + ANTHROPIC_SMALL/SONNET/OPUS/HAIKU_MODEL）才能绕过 CC 内置模型名白名单校验
- 切换目标从 `{project}/.claude/settings.local.json` 改回全局 `~/.claude/settings.json`：发现 CC daemon 会将 env vars 广播给所有已连接会话，settings.local.json 无法实现运行时项目级隔离
- 切回官方时改用空字符串 `""` 代替 pop 清除 env vars：运行中进程无法通过删除 settings.json 字段来 unset 已注入的 env var，空字符串在 CC JS 层为 falsy 等效未设置
- 第三方 Provider 改用 ANTHROPIC_AUTH_TOKEN（非 ANTHROPIC_API_KEY），参考 cc-switch 最佳实践
- Dashboard server 由 settings.local.json → global settings.json 全局热重载，切换立即生效无需重启

### Key Conclusions
- CC 模型名校验绕过：单设 ANTHROPIC_MODEL 不够，需五个 model-family vars 全设
- CC env var 清除：只能覆盖（设 ""），不能删除——运行中进程的 env 无法被 settings 文件更新 unset
- CC 全局性：settings.local.json 的 env 段同样全局生效，无"项目级模型"可言，确认采用全局 settings.json 方案

### Pending
- 无

## 2026-03-28 | feat: Dashboard 模型 API 可视化配置（v0.7.3）

### Summary
- 新增 Dashboard 设置页「模型配置」功能，支持可视化管理 Provider 和切换模型
- 内置 Anthropic 官方订阅卡片（opus/sonnet/haiku），始终置顶不可删除
- 自定义 Provider 支持增删改，预设 OpenAI / Google / DeepSeek 一键填充
- 切换模型自动写入 `~/.claude/settings.json`（官方模式清除 env，自定义模式设置 BASE_URL + MODEL）
- 修复后端 `services/team.py` models 解析 bug（flat dict → list-of-objects）
- 新增 3 个 API 端点：check-env / switch-model / current-model
- 前端模型配置逻辑独立为 `models.js`（291 行），遵守 500 行文件上限
- 切换后显示 toast 提示"重启 Claude Code 会话后生效"
- 版本号 0.7.2 → 0.7.3，17 个文件变更，+1216/-43 行
- Commit: 4df2022, Tag: v0.7.3

### Key Conclusions
- API Key 永不存储在文件中，仅存环境变量名，/check-env 仅返回 boolean
- 切换机制复用 Claude Code 原生 settings.json，无需额外配置文件

### Pending
- 无

## 2026-03-26 | fix: 清理 .claude/commands/ 中已删除命令的残留引用

### Summary
- 9 个已删除命令（impl/think/demo/test/verify/learn/bug/crosscheck/upgrade/status）的引用从所有命令文件中清除
- 影响 9 个文件：CLAUDE.md + 8 个命令文件（help/plan/design/loop/review/save/scan/commit）
- aion-help.md 重写：命令总览、场景推荐、工作流图、速查表全部更新为 10 命令体系
- 解决用户反馈：不再出现 "运行 /project:aion-impl" 等无效提示

### Key Conclusions
- v0.7 命令精简后，.claude/commands/ 中残留大量旧命令引用，导致 AI 频繁推荐不存在的命令
- 全量 grep 验证已无残留

### Pending
- 无

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
