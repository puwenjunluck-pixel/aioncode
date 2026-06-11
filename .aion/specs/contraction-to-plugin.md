---
status: completed
created_at: 2026-06-12
version: 1
author: waynepo
scope: full
change_reason: null
---

# 战略收缩：AionCode → 开源方法论插件

## 1. Goal (目标)

砍掉正在被 Claude Code 原生能力吞噬的机制层（CLI 二进制 / Dashboard / Antigravity 适配），把方法论层蒸馏为官方插件（skills 形态）开源上架，将维护负担从「产品级」降到「作品级」。

## 2. Context (背景)

2026-06 多代理深度评估（36 agents，29 项发现全部经对抗核实成立）+ 竞品/平台联网调研的结论：

- **赛道已收敛**：superpowers ~225K★（官方插件目录 75 万安装）、Spec Kit ~111K★、OpenSpec ~54K★、BMAD ~49K★，全部开源；腰部项目 2026 上半年集体减速。闭源 + 裸 `.claude/commands/` 分发在此格局下无获客路径。
- **平台风险评级「高」**：原生 `.claude/rules/`、auto memory、新版 `/init`、plan mode、hooks、插件市场已覆盖 AionCode 大半机制层。先例：`.cursorrules` 生态被原生化后崩塌；SuperClaude 靠迁入官方插件体系存活。
- **相对安全区**：方法论与观点本身、`.aion/` 工件层（bugs 角色化流转、_product.md）、中文深度（中文区方法论级产品空白，ZCF 仅 6K★ 且浅）。
- 若不收缩：机制层维护成本（8K 行 Python、三平台发布、Dashboard 安全债）持续吃掉迭代速度，方向上对抗平台演进，期望值为负。

## 3. Requirements

### P0 (必须有)

- 旧形态封存：tag `v0.7.6-final` + 分支 `archive/v0.7-cli`，可随时找回（本 spec 提交时已完成）
- 插件骨架：`.claude-plugin/plugin.json`（name: `aion`，version 为唯一版本事实来源）+ `marketplace.json` 自有市场入口
- 8 个 skills 迁移完成：init / think / plan / review / commit / fix / qa / scan（11 命令 → 8 skills，处置表见 §5）
- 纪律层文件（metacognition / spec-template / plan-template）以 skill references 形式随插件分发；`/aion:init` 在宿主项目创建 `.aion/` 工件目录并写入 `.claude/rules/` 种子
- review→commit 门禁 hook 化：PreToolUse 拦 `Bash(git commit *)`，校验 review frontmatter `reviewed_files`/`base_commit` 覆盖当前 diff，否则 exit 2 阻断
- 迁移时修复评估确认的内容层缺陷：aion-plan 新旧格式自相矛盾、Iron Law 三套编号冲突、学习飞轮 stale 清理引用已删除命令、`<!-- PLATFORM -->` 标记全清
- 开源发布：MIT、README 重写（用 pitfalls.md 真实规则替换虚构周曲线）、`claude plugin validate` 通过

### P1 (锦上添花,本期可延)

- 提交 community marketplace（platform.claude.com/plugins/submit）过审
- MIGRATION.md（老用户 CLI → 插件两步迁移）
- 中文渠道发布文（掘金 / 知乎 / V2EX）

## 4. Acceptance Criteria (验收标准)

- [ ] 在一个全新测试项目中，`/plugin marketplace add puwenjunluck-pixel/aioncode` + `/plugin install aion` 后，`/aion:think` 完整跑通 10-phase 流程
- [ ] `/aion:init` 后测试项目存在 `.aion/{specs,plans,bugs,reviews}` 与 `.claude/rules/metacognition.md` 等种子文件
- [ ] 无覆盖当前 diff 的 review 文件时，`git commit` 被 hook 阻断并给出指引；存在合规 review 时放行
- [ ] 迁移后的 skills 中 `grep -rn "PLATFORM:\|aion-loop\|aion-help\|aion-audit"` 为 0（已砍/已并入命令无残留引用）
- [ ] `claude plugin validate` 通过，README 含 ≥2 条来自 pitfalls.md 的真实规则示例
- [ ] 仓库公开，LICENSE 为 MIT

## 5. Architecture (架构)

**11 命令 → 8 skills 处置表**：think / plan / review / commit / fix 保留并修缺陷；qa 保留标记可选（浏览器 MCP 依赖）；scan 蒸馏（砍与原生 `/init` 重叠的冷启动，留 `_product.md` 全景 + `--file` 导入）；save 蒸馏（记忆职能让位原生 auto memory，只留工件落盘）；**audit 并入 review**（作为 `--deep` 模式）；**loop 砍**（原生 background tasks / agent teams 覆盖）；**help 砍**（原生 `/help` + README 接管）。

**目标结构**（同仓库重构，调用前缀 `/aion:*`）：

```
.claude-plugin/{plugin.json, marketplace.json}
skills/{init,think,plan,review,commit,fix,qa,scan}/SKILL.md (+references/)
hooks/hooks.json + scripts/check-review.sh
README.md / MIGRATION.md / LICENSE
```

**关键机制约束**（2026-06 官方文档核实）：插件不能向宿主注入 `.claude/rules/`，规则种子必须由 init skill 代写；skills 形态 always-on 成本约 250-300 tokens，progressive disclosure 解决旧命令链式加载 ~58KB 的问题。

**已拍板决策**（2026-06-12，用户确认）：

| # | 决策 | 备注 |
|---|---|---|
| 1 | 开源（MIT） | **推翻**此前「仓库 private，刻意的」决策 |
| 2 | 放弃 Antigravity | **推翻** v0.7.4-0.7.5 多平台战略；调研：信任危机 + 目录约定年内一改 |
| 3 | Dashboard 归档 | 连同其全部安全债（0.0.0.0 / CORS * / 无认证 / embedded.py 损坏）一并退役 |
| 4 | 插件名 `aion` | 调用形如 `/aion:think` |
| 5 | aion-audit 并入 review | 与原生 `/security-review` 重叠，留项目级中文审计视角 |

## 6. Error Handling (风险与降级)

- community marketplace 审核周期未知 / 不过审 → 自有 marketplace.json 让用户直接从仓库安装，发布不被审核阻塞
- skills 形态出现未预期的加载/兼容问题 → P1 阶段只迁 think 一个做垂直切片验证，形态不对在第 2 天即暴露，可退回 flat commands 形态（同插件体系内调整，不影响已砍决策）
- hook 误拦合法 commit → check-review.sh 对无 `.aion/` 的项目直接放行（插件可能被装进非 AionCode 工作流的项目）

## 7. Testing Strategy (测试策略)

- check-review.sh 为纯 shell 逻辑：用 fixture review 文件 + 临时 git 仓库做表驱动测试（阻断/放行/无 .aion 放行三类）
- skills 无法单元测试：每个 skill 迁移后在干净测试项目实跑一遍作为验收（AC 1-2）
- `claude plugin validate` 进发布前 checklist；旧 Python 测试套件随机制层一起归档，不再维护

## 8. Constraints (约束)

- solo 开发者业余时间：总预算 7-11 个工作日（约 3-4 周），P2 内容蒸馏是大头（3-5 天）
- 迁移期间不在 master 引入「半插件半 CLI」的混合形态：P1 骨架在子目录内自洽，CLI 代码删除集中在一次提交完成
- pitfalls.md 既有规则中与机制层绑定的条目（embedded.py、PyInstaller、settings.json 写入等）随归档标记 `status: archived`，不删除（历史证据）

## 9. Out of Scope (明确不做什么)

- 不再维护：Python CLI 全部子命令、PyInstaller 三平台发布、install.sh/uninstall.sh、Dashboard 全栈、Antigravity 适配层
- 不修复已归档组件的评估发现（embedded.py 转义、Dashboard 安全四件套、upgrade 校验等约 15 项——随归档蒸发）
- 不做英文优先文档（README 中文为主 + 英文 TL;DR，完整英文化视开源后反馈再议）
- 不做云端/商业化形态（v0.8 云端 MVP 路线随本次收缩作废）

## 10. References

- 评估与调研：2026-06-11 多代理评估（本会话 workflow wf_a0967bb9-9e4），五维度 29 项核实发现 + 竞品/平台报告
- Product landscape: `.aion/specs/_product.md`（待 P2 末同步更新产品定位与商业模式字段）
- 插件规范：https://code.claude.com/docs/en/plugins.md 、plugins-reference.md 、plugin-marketplaces.md（2026-06 核实）
- 旧形态封存点：tag `v0.7.6-final` / branch `archive/v0.7-cli`
