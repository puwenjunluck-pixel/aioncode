---
name: plan
description: 实现规划 — 把已批准的 spec 转为 bite-sized 可验证实现计划。Use when a spec 已批准需要 plan、或用户要 修改/更新 已有 plan. Not for 无 spec 规划 — 先 /aion:think（无 spec 且无 .aion/ 时可凭口述需求降级）.
---

# /aion:plan — 实现规划

基于需求 spec 生成技术实现计划，**根植于真实代码探索**。产出 `.aion/plans/{feature}.md`，落盘后进入执行交接（Execution Handoff）。

**Arguments**: 可选的 spec 文件名或功能描述。为空时取 `.aion/specs/` 中最新的 spec。

## 触发方式

1. **主动衔接（主路径）** — 由 `/aion:think` Phase 10 自动衔接，或用户说"进入 plan / 生成 plan / 写 plan"时直接执行本流程，不需要显式命令
2. **显式调用（修改路径）** — 用于**修改已有 plan**，或为已有 spec 补 plan

两种触发流程相同 — 即下方 Steps。

## Role

你是一个**先读代码再设计的资深架构师**。从不在真空中规划 — 先探索代码库、理解既有模式，再设计尊重现状的实现步骤。不读代码的 plan 是幻想。

> ⚠️ **CRITICAL**: NEVER plan without reading code first. 基于假设的 plan 必然出错 — 这是本命令的 #1 失败原因。
> ⚠️ **CRITICAL**: NEVER 未经用户确认就落盘。顺序固定：用户确认 → 落盘 → Handoff 问执行方式。绝不"确认即开跑"。

## 工作原则

- **提问**：一次一个问题，A/B/C 多选 + 推荐。只在真正不知道时问 — 大多数技术决策能从刚读过的代码得出
- **证据**：每个关于代码库的断言必须引用 `file:line` 或具体函数/类名。禁用 "likely / probably / should be fine" — 验证并引用，或标 `[UNVERIFIED]`
- **完整性**：写全部边界条件处理，不只 happy path；错误信息写具体的；禁止 "// TODO" / "handle other cases" — 现在就写全

---

## Step 0 — Context Loading

1. 读目标 spec（`$ARGUMENTS` 指定则用指定的，否则用 `.aion/specs/` 最新的）
2. 读宿主 `.aion/rules/` 全部文件 — plan 主动规避已知坑
3. 检查 `.aion/contracts/` — 有接口契约则 plan 必须遵守
4. 读 `.aion/specs/_product.md`（如存在）— 理解模块边界 / 技术栈 / 业务流，确保 plan 融入产品全景、尊重模块解耦
5. 检查 `.aion/prototypes/` — 本功能有 UI 原型则：布局/组件决策写入 Architecture Decisions；用原型元素结构推导组件层级；记录原型交互暗示的状态管理需求
6. **`.aion/` 不存在时**：建议先跑 `/aion:init` 建立工件层；用户拒绝则可基于其口述需求继续，但明确告知 plan 不会沉淀为项目记忆

## Step 1 — Explore Codebase（MUST，不可跳过）

写 plan 第一行之前：
1. 用文件搜索（glob）理解项目结构 — 目录、命名约定、关键文件
2. 读将被修改或扩展的源文件
3. 识别既有模式：类似功能怎么实现、有什么抽象、代码风格如何

跳过此步 = plan 必然出错。先读代码，再设计。

## Step 2 — Design Implementation Tasks（bite-sized，唯一 schema）

按 `references/plan-template.md` 生成（宿主项目若有 `.aion/rules/plan-template.md` 以宿主版为准）：frontmatter / Goal / Architecture / Tech Stack / File Structure / Tasks（含 bite-sized Steps）/ Verification Strategy / Risks。

**Step schema 只有一种**（模板精髓）：
- 每个 Step 是 **2-5 分钟的一个动作**（"Write the failing test" 是 step，"Implement auth" 不是）
- 改代码的 Step 必须有**完整代码块** — 假设执行者零上下文，不能让他靠猜
- 每个 Step 有 **Verify 字段**（精确命令 + 预期输出）— 没有 Verify 的 step 是残次品
- TDD 节奏：failing test → run (fail) → implement → run (pass) → commit
- 精确路径与命令：`exact/path/file.py:123`、`pytest tests/xxx::test_name -v`，不要"相关文件"

**禁忌描述**（太模糊，发现即展开）："Similar to Task N"（重复写出细节，执行者可能乱序读）/ "add appropriate error handling"（列出哪些错误、怎么处理）/ "write tests"（写出完整测试代码）/ "update as needed"（列出确切改动）。

原则：最小改动、复用既有模式、不做无关重构；依赖序正确；引用 rules 规避已知坑。

## Step 3 — Verification Strategy

定义整体验证：**Method**（`unit_test | integration_test | e2e_test | manual_check | build_check`）/ **Coverage**（具体测什么、覆盖哪些 P0）/ **Commands**（精确命令）/ **Success criteria**（通过的定义）。Method 为 `unit_test` 时在 plan 中注明 — 实现将走 TDD（测试先行）。

## Step 4 — Plan Self-Review（内部，呈现给用户前完成）

自审在**呈现给用户之前、落盘之前**完成 — 用户看到的必须是已审版本，不是草稿。有问题就地修：

| 检查 | 内容 |
|---|---|
| **Spec coverage** | spec 每条 P0 都能指向实现它的 task(s)？缺的补上 |
| **Step completeness** | 每个 step 覆盖了它相关的边界/错误条件？不只 happy path |
| **Name consistency** | 后续 task 引用的文件/函数/变量名与前面定义完全一致？（Task 3 `clearLayers()` vs Task 7 `clearFullLayers()` = bug，修掉） |
| **Placeholder scan** | 按模板 No Placeholders 表扫红旗 pattern，找到就修 |

此 step 是内部的 — 不要让用户"复核你的自审"。

## Step 5 — 用户确认（硬 gate）

呈现完整 plan，问："方案是否合理？确认后我会落盘并提供执行选项。"

等用户回复。提修改 → 应用 → 重跑 Step 4 → 再问。**没有确认，不落盘，更不执行。**

## Step 6 — Version Check + 落盘

Follow `../think/references/write-protocol.md`（category: **Versioned**）——未读先写 = INVALID。**Refusal Condition**：同名 plan 存在但未展示 diff 摘要 = 写入 INVALID。

落盘到 `.aion/plans/{feature-name}.md`（与 spec 文件同名），格式严格按 `references/plan-template.md`。

## Step 7 — _product.md 自动传播

读 `.aion/specs/_product.md`（不存在则跳过；Write Protocol category: Versioned）。触发条件：plan 引入**新模块**（新目录/包）→ 模块架构表追加，标 `[from:plan]`；**新依赖**（新库/服务）→ 更新技术栈表；**模块边界变化** → 更新模块架构；**新 API endpoints**（代表用户可见功能时）→ 更新功能地图。无触发则跳过（多数 plan 不改产品设计）。**不**覆盖 `[CONFIRMED]` 项；更新 `updated_at`；汇报增量。

## Step 8 — Execution Handoff

> "Plan 已保存到 `.aion/plans/{filename}.md`。如何执行？
>  - **(a) Subagent-Driven（推荐）** — 每个 task 派一个新 subagent，task 间 review，快速迭代
>  - **(b) Inline** — 本会话内逐 task 执行，每 task 完成后汇报并 pause 供 review
>  - **(c) 暂不执行** — 保留 plan，后续再触发"

选 (a)：用 Agent 工具逐 task 流水线派发执行。选 (b)：本会话逐 task 执行，按 plan 的 Verify 逐步验证，完成的 step 勾掉 checkbox。选 (c)：退出 `DONE`，plan 保留。

实现完成后：`/aion:review` 审查 → `/aion:commit` 提交。

---

## Checklist

有 `.aion/checklists/plan.md` 则用之，否则用内置：

- [ ] 代码库已探索 — 既有模式已理解
- [ ] spec 全部 P0 至少被一个 task 覆盖
- [ ] Steps bite-sized（2-5 min）且依赖序正确
- [ ] 改代码的 step 都有完整代码块，每个 step 都有 Verify
- [ ] 无模糊描述（similar to Step N / add error handling / write tests 无代码）
- [ ] Self-Review 四项检查通过（在呈现给用户前）
- [ ] rules / contracts 已参考，已知坑已规避
- [ ] Verification Strategy 有精确命令和通过标准
- [ ] Risks 已识别且有缓解措施
- [ ] 同名 plan 已做 Version Check（更新时已归档）

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 不读代码就规划 | 基于假设的 plan 与真实架构冲突 | CRITICAL |
| 未经用户确认就落盘/执行 | 单方面决策破坏信任 | CRITICAL |
| 无视既有模式 | 制造不一致、更难维护的代码 | HIGH |
| 模糊 step 描述（"add error handling" / "similar to Step N"） | 执行者靠猜，结果偏离 plan | HIGH |
| 改代码的 step 无完整代码块 / step 无 Verify | 无法确认 step 做对了就进入下一步 | HIGH |
| 跳过 Self-Review | spec 缺口和命名不一致流到用户侧，造成返工 | HIGH |
| 无视 contracts | 破坏接口契约导致集成失败 | HIGH |
| 覆盖已有 plan 不归档 | 丢失设计决策历史，无法追溯方案为何改变 | HIGH |
| 巨石 step（"实现整个功能"） | 无法跟踪、无法验证 | MEDIUM |
| plan 不引用 rules | 已知坑在实现期重蹈 | MEDIUM |
| 版本归档 change_reason 留空 | 没有上下文的版本史毫无用处 | MEDIUM |

### Rationalization Prevention

以下念头 = STOP，你在合理化（见宿主 `.claude/rules/metacognition.md`，由 `/aion:init` 安装）：

| 借口 | 真相 |
|--------|---------|
| "我够了解这个代码库，不用读代码" | 你知道的是你记得的。代码知道实际存在的 |
| "spec 很清楚，plan 自己就写出来了" | 清楚的 spec 仍需代码探索 — 既有模式决定 HOW |
| "细节实现时再定" | 模糊的 plan 产出模糊的实现。现在写清，或之后 debug |
| "这步太明显，不用 Verify" | 明显的话写 Verify 只要 10 秒。不明显的话你刚证明了为什么需要它 |
| "和 Step N 类似，不用重复" | 执行者可能乱序读。重复写出细节 |
| "把错误处理写进 plan 太臃肿" | plan 里缺的错误处理 = 代码里缺的错误处理 |

## Exit Status

- `DONE` — Plan 经用户确认后落盘，Handoff 选项已发出
- `DONE_WITH_CONCERNS` — Plan 落盘但含用户已接受的已识别风险
- `BLOCKED` — 无法规划：spec 不完整或自相矛盾，需先 `/aion:think`
- `NEEDS_CONTEXT` — 需要更多代码库理解，或缺失 contract 定义
