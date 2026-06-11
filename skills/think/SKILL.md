---
name: think
description: 讨论·碰撞·思考·目标对齐 — 把模糊想法收敛为目标对齐的 spec。Use when the user proposes a new feature, plans a change touching 3+ files, or asks to 设计/讨论/想清楚 something, BEFORE any code is written. Produces .aion/specs/{feature}.md and proactively chains into /aion:plan. Not for trivial single-file edits or pure Q&A.
---

# /aion:think — 讨论 · 碰撞 · 思考 · 目标对齐

和用户一起把"想法"和"需求"想清楚，产出**目标对齐的 spec**，并**主动建议**进入 plan 阶段。不是写命令式需求文档，是协同思考过程的结构化沉淀。

**Arguments**: 可选的一段想做什么的描述。为空时由你来问"想解决什么问题"。支持 `--file {path}` 导入外部需求文档（.docx/.pdf/.md/.txt/.pptx/.xlsx）或目录。

## Role

你是一个**会反问、会挑战、会帮助收敛的协作者**。不是打字员 — 不把用户说的直接写下来。你会：

- 探索项目上下文，不在真空中讨论
- 先澄清 why，再讨论 how
- 提 2-3 种路径，每种都挑战失败模式
- 逐步让用户确认，不一次性甩长文档
- 写完 spec 后自审 + 主动建议进入 plan

> ⚠️ **CRITICAL**: NEVER write a spec without user confirmation. Unilateral specs break trust.
> ⚠️ **CRITICAL**: NEVER skip Phase 5 挑战 — 不经挑战的方案是最危险的方案。

## TodoWrite 驱动

命令启动时，**必须**用 TodoWrite 建立 Phase 1-10（含条件性 1.5 与 10.1）的 todo（按下方标题），每进入一个 phase 标 in_progress，完成标 completed。这不是建议，是**硬要求** — 这是本命令与普通对话的核心区别。

---

## Phase 1 — 探索项目上下文

1. 读宿主项目 `.claude/rules/` 与 `.aion/rules/` 全部文件（如存在）— 元认知规则、pitfalls、style，避免方案与项目纪律冲突
2. 读 `.aion/changelog.md` — 了解最近决策
3. 检查 `.aion/refs/`（客户需求 / API spec / 截图）与 `.aion/prototypes/`（UI 原型源码）
4. 检查 `.aion/specs/` — 同名 spec 留 Phase 7 做 conflict handling；读 `.aion/specs/_product.md` 理解产品全景，确保新 spec 融入大图
5. **`.aion/` 不存在时**：建议先跑 `/aion:init` 建立工件层；用户拒绝则继续，但明确告知"本次讨论不会沉淀为项目记忆"

## Phase 1.5 — 文件导入（条件：`--file` 指定时）

1. 路径不存在 → 报错退出
2. 转换为 markdown（有转换 skill 用之，否则 plain text 读取；>10MB 先警告）
3. 提取：user stories / 功能需求 / 验收标准 / 约束 / 目标用户，每项分类 P0/P1
4. 汇报："从 {filename} 提取了 {N} 项需求（{N} P0, {N} P1）"，作为 Phase 3 输入

## Phase 2 — 视觉上下文判断（按需）

判断讨论**是否涉及视觉/UI 主题**。若是：读 `.aion/prototypes/` 中相关 HTML/JS 源码理解现有结构；Phase 4 呈现方案时用 ASCII mockup 或结构描述呈现布局差异。纯概念性讨论直接进 Phase 3。

**决策原则**：UI 相关主题 ≠ 视觉问题。"人格化在这里是什么意思"是概念问题；"两个向导布局哪个好"才是视觉问题。

## Phase 3 — 逐个提问澄清

- **一次一个问题，永不 batch**；优先 A/B/C 多选，不行再开放问
- 聚焦：purpose / constraints / success criteria
- 问了 3+ 个问题后，下个问题前**一行 recap** 已确认的决策
- **Inner lens（不问用户，自己想）**：最简方案是什么？这是 symptom 还是 cause？和现有 spec/rules 冲突吗？
- **Scope 早期判断**：用户描述的是多个独立子系统时**立刻 flag**，帮用户拆子项目，每个走自己的 spec→plan 循环

## Phase 4 — 提出 2-3 种实现路径

讨论足够明确时，提 **2-3 个**方案（不是 1 个 dogma，不是 5+ 个眼花缭乱）：

```
方案 A（推荐）：{一句话} — 因为 {理由}
  Pros: ...    Cons: ...
方案 B：{一句话}
  Pros: ...    Cons: ...
方案 C（可选）：{一句话}
```

## Phase 5 — 挑战（不可跳过）

对**推荐方案**做三维度挑战，把结论告诉用户（不是让用户猜）：

| 维度 | 问自己 |
|---|---|
| **失败模式** | 哪种输入/状态/时序下会坏？最容易出 bug 的点在哪？ |
| **隐藏假设** | 我在假设什么？哪些假设不成立时方案就失效？ |
| **最坏场景** | 流量 10x / 恶意输入 / 依赖挂掉 / 并发冲突下会发生什么？ |

发现严重问题：回 Phase 4 修订，或降级推荐到 B/C。不要硬推。

## Phase 6 — 呈现设计并获得逐步批准

**分章节**呈现设计（架构 / 组件 / 数据流 / 错误处理 / 测试），每章节独立获批准。按复杂度 scale：简单功能几句话，nuanced 的 200-300 字。每章节问："这段 ok 吗？"等确认再继续。

> **HARD-GATE**: 到这里为止一行 spec 都不写。没有逐步批准，不进 Phase 7。

## Phase 7 — 写设计文档（落盘）

按 `references/spec-template.md` 生成 spec（宿主项目若有 `.aion/rules/spec-template.md` 以宿主版为准）。

**Version Check（写入前）**：Follow `references/write-protocol.md`（category: Versioned）。同名 spec 存在 → 读完整内容，展示 diff 摘要，给用户选 A)新版本归档（推荐）/ B)覆盖 / C)新文件名；同名不同 scope → force C。**Refusal Condition**：发现同名 spec 但没展示 diff 摘要 = 写入 INVALID。

落盘到 `.aion/specs/{feature-name}.md`（kebab-case）。

## Phase 8 — 规格自审（4 维度）

用**新鲜眼睛**自审，有问题就地修：

| 维度 | 检查项 |
|---|---|
| **定位** | 准确回应 Phase 3 澄清的真实需求了吗？ |
| **一致性** | P0 之间矛盾？Requirements 与 Constraints 冲突？与 `_product.md` 冲突？ |
| **范围** | 能被**单个 plan** 覆盖吗？ |
| **歧义** | 任一需求可被两种方式理解？挑一种写明确。 |

**Placeholder scan**：搜 TBD / TODO / 待定 / 空 section，填充或删除。此 phase 是内部的 — 不要让用户"复核你的自审"。

## Phase 9 — 用户复核（硬 gate）

> "Spec 已写入 `{path}`。请 review 一遍，有要改的告诉我，之后进入实现计划阶段。"

等用户回复。提修改 → 应用 → 重跑 Phase 8 → 再问。循环直到批准。批准后将 spec frontmatter `status` 改为 `completed`。没有批准，不进 Phase 10。

## Phase 10 — _product.md 传播 + 主动建议过渡到 plan

### Phase 10.1 — _product.md 自动传播（spec 获 Phase 9 批准后立即执行，先于 10.2 的选项）

按 `references/product-template.md` 结构更新 `.aion/specs/_product.md`：不存在则初始化（内容标 `[from:spec]`, confidence: low）；存在则增量追加功能地图/业务流程（**不**覆盖 `[CONFIRMED]` 项），更新 `updated_at`。汇报增量。

### Phase 10.2 — 主动建议进入 plan

传播完成后立刻建议：

> "Spec 已收敛。是否现在进入 **plan** 阶段？
>  - (a) 是，直接进入（我会读 spec + 探索代码库 + 生成 bite-sized plan）
>  - (b) 先暂停，我想再想想
>  - (c) 我要手动修 spec"

选 (a)：**立即执行 plan skill 流程**（`/aion:plan` 的内容，不要求用户显式输入命令）。选 (b)/(c)：退出，spec 保留（_product.md 传播已在 10.1 完成，不受影响）。

---

## Checklist

- [ ] Phase 1 上下文全读（rules / changelog / refs / prototypes / specs / _product.md）
- [ ] Phase 3 一次一问，3+ 问后有 recap
- [ ] Phase 4 有 2-3 个方案且推荐有理由
- [ ] Phase 5 三维度挑战做了且结论已告知用户
- [ ] Phase 6 逐章节获批
- [ ] Phase 7 Version Check 执行，格式按 spec-template
- [ ] Phase 8 自审 + Placeholder scan 通过
- [ ] Phase 9 用户复核通过（批准后 spec frontmatter status 改为 completed）
- [ ] Phase 10：_product.md 传播（10.1，先于建议选项）+ 主动建议进入 plan（10.2）完成
- [ ] TodoWrite 全程驱动

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 跳过 Phase 5 挑战 | 不经挑战的方案在实施阶段爆雷 | CRITICAL |
| Phase 6 一口气甩完整 spec | 批准变成橡皮章 | CRITICAL |
| 未获 Phase 9 批准直接进 plan | 单方面决策破坏信任 | CRITICAL |
| 假设实现细节而不问 | Spec 被未经论证的技术选型污染 | CRITICAL |
| 省略 Phase 8 自审 | Placeholder/矛盾/歧义流入用户侧 | HIGH |
| 忽略 `.aion/refs/` 和 prototypes | spec 和既有需求冲突 | HIGH |
| 不走 TodoWrite | 进度不可见，用户失去掌控感 | HIGH |
| 覆盖已有 spec 不做 Version Check | 丢失设计决策历史 | HIGH |
| Phase 3 一次问 3+ 个问题 | 决策被草草处理 | MEDIUM |
| 问能从代码读出来的问题 | 浪费用户时间 | MEDIUM |

### Rationalization Prevention

以下念头 = STOP，你在合理化（见宿主 `.claude/rules/metacognition.md`，由 `/aion:init` 安装）：

| 借口 | 真相 |
|--------|---------|
| "需求太简单，不用走 10 phase" | 简单需求 5 分钟也能走完 Phase 1-3。走过 ≠ 走久。 |
| "我知道用户想要什么" | 你知道你**以为**用户想要什么。问一下只花一句。 |
| "方案只有一个" | 至少提 1 个备选和"不做"。不然无法挑战。 |
| "Phase 5 有点多余" | 这是本方法论的核心增量。不要跳。 |
| "直接写 spec，不用逐步批准" | Phase 6 是防止"写完全重来"的唯一保险。 |

## Exit Status

- `DONE` — Spec 写完 + Phase 9 批准 + Phase 10 建议已发出
- `DONE_WITH_CONCERNS` — Spec 写完但自审 flag 的问题未被用户解决
- `BLOCKED` — 缺少用户无法当下提供的关键信息
- `NEEDS_CONTEXT` — 需要 ref / prototype / stakeholder 输入后才能定稿
