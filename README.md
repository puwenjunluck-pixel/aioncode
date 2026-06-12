# Aion — AI 开发方法论插件

**让 Claude Code 有章可循、越用越聪明。** think → plan → review → commit 纪律闭环 + 机械化提交门禁 + 可审计的学习飞轮。

> **EN TL;DR**: Aion is a Chinese-first development methodology plugin for Claude Code: a disciplined think→plan→review→commit loop, a PreToolUse hook that *mechanically* blocks unreviewed commits (not a prompt suggestion — an actual deny), and an auditable learning flywheel that turns review findings into per-project rules under `.aion/`. Dogfooded to the point that its own v0.8 contraction mechanically archived 18 stale rules in one sweep.

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

这会创建 `.aion/` 工件层、把元认知规则装进 `.claude/rules/`（每次会话自动加载）、用标记把工作流段合并进你的 CLAUDE.md（幂等，绝不动你自己的内容）。安全 hook 与提交门禁 hook 随插件自动生效（门禁只在「git 仓库 + `.aion/` 存在」的项目里拦截）。

### 第一次会话长什么样

Aion 的流程是刻意"重交互"的——这是 feature，不是 bug。以一个小功能为例：

1. `/aion:think 给设置页加深色模式` → Claude **一次一个问题**澄清目标（小需求 2-3 问，几分钟），提 2-3 个方案并自我挑战，分章节征求你批准，落盘 spec
2. spec 批准后它**主动**衔接 plan，生成 bite-sized 步骤（每步含完整代码 + 验证命令）
3. 实现后跑 `/aion:review` → 评分 + 提取规则 + 产出门禁报告
4. `/aion:commit` → 门禁校验通过，确认后提交（确认永不跳过）

第一次被连环提问时请相信流程：这 5 分钟换来的是不返工。赶时间的小改动可以不走全流程——门禁只看 review 是否覆盖提交，不强制 think/plan。

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

Aion 用自己开发自己。以下规则是它在自己仓库里真实踩坑后由 review 自动提取的（规则库当前 5 条活跃 + 18 条已归档，全部见 `.aion/rules/`）：

> **NEVER 忘记同步模板版本号** [cite_count: 2] — v0.5 因此遗留 0.3 版本号；v0.7.6 发布时同一坑**再次**触发，靠 dogfood 自升级才抓到。规则被引用 2 次后，最终在 v0.8 收缩中从根上消灭了多版本号源。

> **命令 rename 必须跨层扫描七件套** [cite_count: 1] — v0.7.6 重命名命令时第一轮 review 只查了 2 层，漏掉 6 层引用，成为 Iron Law 2（evidence before claims）的反面教材，事故复盘直接写进规则正文。

> **CC daemon 将 env vars 广播给所有会话** — 调试模型切换时发现的平台行为：所有打开的会话共用 daemon，`settings.local.json` 的 env 变化会立即广播到其他项目的窗口。这类生态知识一旦沉淀，团队每个人的 Claude 都知道。

每条规则带 `cite_count` / `last_cited` 元数据：review 引用它就 +1，超过 60 天无引用会被建议归档——**飞轮有进有出，不会积累噪音**。而且出口不是口头约定：`scripts/rules-status.sh` 做机械化 stale 扫描，`/aion:review` 每次调用它。本仓库自己就是活样本：v0.8 收缩当天，该脚本扫出一批因机制层退役而失效的规则，当场归档 18 条——归档动作全部留痕在 git 历史里，这就是"可审计"的含义。

## 机械门禁长什么样

```
$ git commit -m "quick fix"
⛔ Aion 门禁：以下改动没有被任何 approved review 覆盖（base_commit 需等于
   当前 HEAD）：src/auth.py。请先运行 /aion:review。
```

review 报告的 frontmatter 含 `reviewed_files` + `base_commit`，hook 做集合校验（多份 review 取并集）。豁免四种：`fix(bug): ` 开头的原子修复（锚定校验，消息中间出现不算）、纯 `.aion/` 工件提交、merge 进行中、非 Aion 项目。**被拦最常见的原因**：刚提交过一次，HEAD 前移导致旧 review 失效——重跑 `/aion:review` 即可。两个 hook 共 49 个测试用例（外加 rules-status 5 个，合计 54），含旗标乱序/捆绑/空白变体、`/bin/rm` 路径、伪 `approved` 前缀等红队对抗输入；解析失败时 fail-open，绝不 brick 你的提交。

## `.aion/` 工件层

```
.aion/                # /aion:init 创建以下全部目录
├── rules/        # 学习飞轮产出（pitfalls/style/perf，带引用计数）
├── specs/        # 需求规格（版本化归档）+ _product.md 产品全景
├── plans/        # bite-sized 实现计划
├── reviews/      # 审查报告（门禁 hook 消费）
├── bugs/         # QA 产出的 bug 报告（fix 按角色消费）
├── refs/         # 导入的参考资料（API spec / 需求文档）
├── prototypes/   # UI 原型（think 读取）
├── contracts/    # 接口契约
├── tests/e2e/    # Given/When/Then 测试定义
└── changelog.md  # 工作日志（append-only）
```

建议整个目录提交进 git——这就是项目的"第二大脑"，而且是可 review 的那种。

## 与其他工具的关系

- **原生 `/init` / memory / plan mode**：不竞争，互补。`/aion:scan` 开头第一句就是"代码库通识请用原生 /init"。
- **从 AionCode CLI（≤ v0.7.6）迁移**：见 [MIGRATION.md](MIGRATION.md)，`.aion/` 数据完全兼容。

## 更新、禁用与卸载

```
/plugin update aion@aion-marketplace     # 更新
/plugin disable aion                     # 临时禁用（含全部 hook）
/plugin uninstall aion                   # 卸载（.aion/ 数据保留）
```

安全 hook 拦截了你认为合法的命令？它防的是手滑不是你——确有需要就在 Claude Code 外手动执行该命令，并欢迎到 [Issues](https://github.com/puwenjunluck-pixel/aioncode/issues) 报告误杀样本。某个项目不想要提交门禁：不跑 `/aion:init`（无 `.aion/` 即不拦截）。

## 支持

- 问题与误杀反馈：[GitHub Issues](https://github.com/puwenjunluck-pixel/aioncode/issues)
- 从 CLI 版迁移：[MIGRATION.md](MIGRATION.md)
- 说明：本仓库自带的 `.aion/` 是 Aion 开发自身的 dogfood 数据（也是学习飞轮的活样本），不会注入你的项目

## License

MIT — [LICENSE](LICENSE) · 纪律层部分内容改编自 [obra/superpowers](https://github.com/obra/superpowers)（MIT），致谢见 [CREDITS.md](CREDITS.md)
