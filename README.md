# Aion — AI 开发方法论插件

**让 Claude Code 有章可循、越用越聪明。** think → plan → review → commit 纪律闭环 + 机械化提交门禁 + 可审计的学习飞轮。

> **EN TL;DR**: Aion is a Chinese-first development methodology plugin for Claude Code: a disciplined think→plan→review→commit loop, a PreToolUse hook that *mechanically* blocks unreviewed commits (not a prompt suggestion — an actual deny), and an auditable learning flywheel that turns review findings into per-project rules under `.aion/`. Born from 13 real rules extracted while building itself.

## 为什么存在

Claude Code 原生已经给了你机制：rules 自动加载、auto memory、plan mode、hooks。**Aion 给的是机制之上的方法论和闭环**——平台告诉你"可以装规则"，Aion 告诉你"规则从哪来、怎么沉淀、怎么强制执行"：

1. **纪律层是拦截，不是提醒。** 大多数工作流框架把"commit 前必须 review"写在 prompt 里，模型想绕就绕。Aion 把它做成 PreToolUse hook：没有覆盖当前改动的 approved review，`git commit` 直接被 deny。
2. **学习飞轮是可审计的资产，不是黑盒记忆。** 原生 memory 是 Claude 自己记笔记；Aion 的规则提取发生在 review 时，落盘为 `.aion/rules/*.md`——带引用计数、带事故出处、可 git 追溯、可团队共享。
3. **工件闭环。** spec（think 产）→ plan → review 报告 → bug 报告（qa 产）→ fix 按角色消费——全在 `.aion/` 一个目录里，接手项目的人 5 分钟看清全部上下文。

## 安装

```
/plugin marketplace add puwenjunluck-pixel/aioncode
/plugin install aion@aion-marketplace
```

然后在你的项目里跑一次：

```
/aion:init
```

这会创建 `.aion/` 工件层、把元认知规则装进 `.claude/rules/`（每次会话自动加载）、用标记把工作流段合并进你的 CLAUDE.md（幂等，绝不动你自己的内容）。安全 hook 与提交门禁 hook 随插件自动生效。

## 命令

| 命令 | 用途 |
|---|---|
| `/aion:init` | 初始化/升级工作流层（幂等） |
| `/aion:scan` | 接手已有项目：产品全景 + 规则种子 + E2E 定义（原生 `/init` 不做的部分） |
| `/aion:think` | 讨论·碰撞·思考——10-phase 把想法收敛为 spec，完成后主动衔接 plan |
| `/aion:plan` | bite-sized 实现计划（主路径由 think 自动衔接；单独调用用于修改已有 plan） |
| `/aion:fix` | Bug 修复：4-phase 根因分析 + 红→绿验证 + 按角色消费 bug 报告 |
| `/aion:qa` | 浏览器 QA：像真实用户一样测试，产出带证据的 bug 报告 |
| `/aion:review` | 代码审查 + 规则提取（`--deep` 全项目审计；产出门禁 hook 消费的报告） |
| `/aion:commit` | 安全提交（确认永不跳过，绝不自动 push） |
| `/aion:save` | 会话工件落盘（跨会话记忆交给原生 memory） |

**推荐工作流**：新功能 `think → plan(主动衔接) → 实现 → review → commit`；接手项目从 `scan` 起步；bug 走 `fix`。

## 学习飞轮：来自本项目自身的真实证据

Aion 用自己开发自己。以下规则是它在自己仓库里真实踩坑后由 review 自动提取的（完整 13 条见 `.aion/rules/pitfalls.md`）：

> **NEVER 忘记同步模板版本号** [cite_count: 2] — v0.5 因此遗留 0.3 版本号；v0.7.6 发布时同一坑**再次**触发，靠 dogfood 自升级才抓到。规则被引用 2 次后，最终在 v0.8 收缩中从根上消灭了多版本号源。

> **命令 rename 必须跨层扫描七件套** [cite_count: 1] — v0.7.6 重命名命令时第一轮 review 只查了 2 层，漏掉 6 层引用，成为 Iron Law 2（evidence before claims）的反面教材，事故复盘直接写进规则正文。

> **CC daemon 将 env vars 广播给所有会话** — 调试模型切换时发现的平台行为：所有打开的会话共用 daemon，`settings.local.json` 的 env 变化会立即广播到其他项目的窗口。这类生态知识一旦沉淀，团队每个人的 Claude 都知道。

每条规则带 `cite_count` / `last_cited` 元数据：review 引用它就 +1，60 天无引用会被建议归档——**飞轮有进有出，不会积累噪音**。

## 机械门禁长什么样

```
$ git commit -m "quick fix"
⛔ Aion 门禁：以下改动没有被任何 approved review 覆盖（base_commit 需等于
   当前 HEAD）：src/auth.py。请先运行 /aion:review。
```

review 报告的 frontmatter 含 `reviewed_files` + `base_commit`，hook 做集合校验。豁免三种：`fix(bug):` 原子修复、纯 `.aion/` 工件提交、非 Aion 项目（fail-open，绝不 brick 你的提交）。

## `.aion/` 工件层

```
.aion/
├── rules/        # 学习飞轮产出（pitfalls/style/perf，带引用计数）
├── specs/        # 需求规格（版本化归档）+ _product.md 产品全景
├── plans/        # bite-sized 实现计划
├── reviews/      # 审查报告（门禁 hook 消费）
├── bugs/         # QA 产出的 bug 报告（fix 按角色消费）
├── tests/e2e/    # Given/When/Then 测试定义
└── changelog.md  # 工作日志（append-only）
```

建议整个目录提交进 git——这就是项目的"第二大脑"，而且是可 review 的那种。

## 与其他工具的关系

- **superpowers**：Aion 的纪律层（Iron Laws / Verification Gate / 反合理化）基于 superpowers 改编并中文化，见 [CREDITS](CREDITS.md)。差异：Aion 加了机械门禁 hook、`.aion/` 工件闭环和学习飞轮。
- **原生 `/init` / memory / plan mode**：不竞争，互补。`/aion:scan` 开头第一句就是"代码库通识请用原生 /init"。
- **从 AionCode CLI（≤ v0.7.6）迁移**：见 [MIGRATION.md](MIGRATION.md)，`.aion/` 数据完全兼容。

## License

MIT — [LICENSE](LICENSE) · 纪律层部分内容改编自 [obra/superpowers](https://github.com/obra/superpowers)（MIT），致谢见 [CREDITS.md](CREDITS.md)
