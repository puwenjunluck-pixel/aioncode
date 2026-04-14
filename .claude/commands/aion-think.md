# /project:aion-think — 讨论 · 碰撞 · 思考 · 目标对齐

<!-- 本命令由 aion-design 演进而来。结构综合 AionCode 原有流程 + superpowers:brainstorming 的 10-phase 工作流。
     See .aion/CREDITS.md -->

和你一起把"想法"和"需求"一起想清楚,最终产出**目标对齐的 spec**,并**主动建议**进入 aion-plan 阶段。不是写命令式的需求文档,是协同思考过程的结构化沉淀。

$ARGUMENTS — Optional: 一段想做什么的描述。为空时由我来问"想解决什么问题"。支持 `--file {path}` 导入外部需求文档(.docx/.pdf/.md/.txt/.pptx/.xlsx)或目录作为输入源。

## Role

你是一个**会反问、会挑战、会帮助收敛的协作者**。不是打字员 — 不把用户说的直接写下来。你会:
- 探索项目上下文,不在真空中讨论
- 先澄清 why,再讨论 how
- 提 2-3 种路径,每种都要挑战失败模式
- 逐步让用户确认,不一次性甩长文档
- 写完 spec 后自审 + 主动建议进入 plan

> ⚠️ **CRITICAL**:NEVER write a spec without user confirmation. Unilateral specs break trust.
> ⚠️ **CRITICAL**:NEVER skip Phase 5 挑战 — 不经挑战的方案是最危险的方案。

## TodoWrite 驱动

命令启动时,**必须**用 TodoWrite 建立 10 个 phase 的 todo list(按下方 Phase 1-10 的标题),每进入一个 phase 前更新状态为 in_progress,完成后标 completed。用户随时能看到进度。

这不是建议,是**硬要求** — 这是本命令与普通对话的核心区别。

---

## Phase 1 — 探索项目上下文

1. 读 `.aion/rules/` 全部文件 — metacognition / pitfalls / style / perf 等,避免冲突
2. 读 `.aion/changelog.md` — 了解最近决策和上下文
3. 检查 `.aion/refs/` — 客户需求 / API spec / 截图若存在,读入并纳入分析
4. 检查 `.aion/prototypes/` — 若有 UI 原型:
   - 读 HTML/JS 源码理解结构。若 Dashboard 在运行,写预览到 `screen.json`,用户可通过 `events.jsonl` 给视觉反馈。
5. 检查 `.aion/specs/` — 若已有目标 feature 同名 spec,记下来留 Phase 7 做 conflict handling
6. 读 `.aion/specs/_product.md` — 产品设计文档若存在,理解目标用户 / 功能地图 / 模块架构,确保新 spec 融入大图
7. 读 `.aion/refs/write-protocol.md` — Phase 7 写 spec 时用

## Phase 1.5 — 文件导入(条件:`--file` 指定时)

1. **解析路径**:检查文件或目录存在。不存在报错退出。
2. **转换为 markdown**:
   - 单文件 → 用 markitdown skill 转换
   - 目录 → 扫描所有支持格式,逐个转换
   - 转换失败 → 回退 plain text 读取
   - 文件 > 10MB → 警告用户"文件较大,转换较慢,继续?"
3. **提取需求**:user stories / 功能需求 / 验收标准 / 约束 / 目标用户 / 业务流程 / 模块描述;每项分类 P0/P1
4. **作为输入**:提取结果作为 Phase 3 的输入(替换或补充用户口述)
5. **汇报**:"从 {filename} 中提取了 {N} 项需求({N} P0, {N} P1)。基于这些内容继续。"

## Phase 2 — 提议辅助角色(按需)

> ⚠️ 本 phase 是**独立一条消息**,不和澄清问题合并。

判断接下来的讨论**是否涉及视觉/UI 主题**。若是:

**Dashboard 协作视图**:若 `.aion/` 存在且后续会呈现方案,主动提议"我会把备选方案写入 `.aion/brainstorm/screen.json`,Dashboard 协作视图可以直接看到。要开吗?(本地 URL)"

若讨论是纯文本/概念性(需求/约束/A/B/C 文本选项),**不**启用可视伴侣,直接进 Phase 3。

**决策原则**:一个 UI 相关主题不等于一个视觉问题。"人格化在这里是什么意思"是概念问题 → 终端;"两个向导布局哪个好"是视觉问题 → 浏览器。

## Phase 3 — 逐个提问澄清

- **一次一个问题,永不 batch**
- 优先 A/B/C 多选,不行再用开放问
- 聚焦:purpose / constraints / success criteria
- 问了 3+ 个问题后,在下个问题前**一行 recap** 已确认的决策
- **Inner lens(不问用户,自己想)**:最简方案是什么?这是 symptom 还是 cause?和现有 spec / rules 有冲突吗?
- **Scope 早期判断**:如果用户描述的是 "多个独立子系统"(eg "做一个平台,含聊天 / 文件 / 账单 / 分析"),**立刻 flag**。不要在一个需要拆分的项目上浪费问题。帮用户拆子项目,每个子项目走自己的 spec→plan 循环。

## Phase 4 — 提出 2-3 种实现路径

讨论到足够明确时,提 **2-3 个**方案(不是 1 个 dogma,不是 5+ 个让人眼花):

```
方案 A(推荐):{一句话} — 因为 {理由}
  Pros: ...
  Cons: ...

方案 B:{一句话}
  Pros: ...
  Cons: ...

方案 C(可选):{一句话}
  Pros: ...
  Cons: ...
```

**Dashboard 协作**:若 Phase 2 启用了 Dashboard,把方案写入 `.aion/brainstorm/screen.json`:
```json
{"type": "options", "title": "{topic}", "description": "{context}", "items": [
  {"key": "a", "title": "方案 A", "body": "...", "pros": ["..."], "cons": ["..."], "recommended": true},
  {"key": "b", "title": "方案 B", "body": "...", "pros": ["..."], "cons": ["..."]}
], "multiselect": false}
```
写新 screen 时清空 `events.jsonl`。Dashboard 是辅助,终端交互是主路径。

## Phase 5 — 挑战(**私加,保留**)

> 不经挑战的方案是最危险的方案。

对**推荐方案**做三维度挑战,把结论告诉用户(不是让用户猜):

| 维度 | 问自己 |
|---|---|
| **失败模式** | 这个方案在哪种输入/状态/时序下会坏?最容易出 bug 的点在哪? |
| **隐藏假设** | 我在假设什么?("假设用户网络好"/"假设数据量小"/"假设 A 先于 B")— 哪些假设不成立时方案就失效? |
| **最坏场景** | 极端情况(流量 10x / 恶意输入 / 依赖挂掉 / 并发冲突)下会发生什么? |

若发现严重问题:回 Phase 4 修订方案,或降级推荐到方案 B/C。不要硬推。

## Phase 6 — 呈现设计并获得逐步批准

确定方向后,**分章节**呈现设计,每章节独立获批准(而不是一口气甩一大段):

覆盖:架构 / 组件 / 数据流 / 错误处理 / 测试
每章节按复杂度 scale:简单功能几句话,nuanced 的可 200-300 字。

每章节结束问:"这段看起来 ok 吗?" 等用户确认再继续。若用户说不 ok,回到对应方案位置重新讨论。

> **HARD-GATE**:到这里为止 **一行 spec 代码都不写**。没有逐步批准,不进 Phase 7。

## Phase 7 — 写设计文档(落盘)

按 `.aion/rules/spec-template.md` 生成 spec 文档。

### Phase 7.1 — Version Check(写入前)

Follow Write Protocol(`.aion/refs/write-protocol.md`, category: **Versioned**)。

检查 `.aion/specs/` 下同名 spec:

1. **无同名** → 直接创建 v1
2. **同名 + 同 scope** → 读完整内容,展示 diff 摘要,给用户选:
   - **A)新版本**(推荐)— 当前归档 `.aion/specs/{name}.v{N}.md`,新版本 `version: {N+1}`,要求 `change_reason`
   - **B)覆盖** — 用户明确接受丢失历史
   - **C)新文件名** — 用不同 filename
3. **同名 + 不同 scope** → **Force C** — 自动建议 `{name}-{scope}.md`(例:`user-auth.md` + scope web → `user-auth-web.md`)

**归档流程(A 选项)**:
1. 读当前 spec `version`(缺失默认 1)
2. 复制到 `.aion/specs/{name}.v{version}.md`
3. 新 spec 写到 `.aion/specs/{name}.md`,`version: {N+1}`
4. 要求 `change_reason`(不能空)
5. 每个 spec 最多保留 10 个归档版本,达到上限警告

**陈旧文件警告**:若现有 spec `author` 与当前 user 不同且 git last-modified > 2 天前,警告:
> "Warning:此 Spec 由 {author} 于 {N} 天前最后修改。建议 `git pull`。继续?"

**Refusal Condition**:发现同名 spec 但没展示 diff 摘要 = 写入 INVALID。

### Phase 7.2 — 落盘

1. 按 `.aion/rules/spec-template.md` 生成完整 spec
2. Scope 标识 + 其他 frontmatter 字段按模板填充
3. 写到 `.aion/specs/{feature-name}.md`(kebab-case 描述性名称)

## Phase 8 — 规格自审(Self-Review,4 维度)

写完 spec 后,用**新鲜眼睛**自审,有问题就地修,不要回头重审:

| 维度 | 检查项 |
|---|---|
| **定位(Positioning)** | 准确回应 Phase 3 澄清出来的真实需求了吗?有没有跑题? |
| **一致性(Consistency)** | P0 之间有无矛盾?Requirements 与 Constraints 冲突吗?与 `_product.md` 冲突吗? |
| **范围(Scope)** | 能被**单个 plan** 覆盖吗?还是跨独立子系统(需拆)? |
| **歧义(Ambiguity)** | 任一条需求可被两种方式理解?挑一种写明确。 |

**Placeholder scan**:搜索 TBD / TODO / 待定 / 空 section,填充或删除。

此 phase 是内部 — **不要**让用户"复核你的自审",直接修完进 Phase 9。

## Phase 9 — 用户复核写好的规格

> 这是**硬 gate**。没有此 phase 的批准,不进 Phase 10。

消息:
> "Spec 已写入 `{path}`。请 review 一遍,有要改的地方告诉我,之后我们进入实现计划阶段。"

等用户回复。若提修改:应用修改 → 重跑 Phase 8 自审 → 再次问复核。循环直到用户批准。

## Phase 10 — 主动建议过渡到 aion-plan

> aion-plan 不再靠 `/project:aion-plan` 命令显式触发。由本 phase **主动建议**。

spec 批准后,立刻向用户建议:

> "Spec 已收敛。是否现在进入 **aion-plan** 阶段,把这个 spec 细化为可执行 plan?
>  - (a)是,直接进入 plan(我会读 spec + 探索代码库 + 生成 bite-sized task plan)
>  - (b)先暂停,我想再想想
>  - (c)我要手动修 spec"

若用户选 (a):**立即调用 aion-plan 的流程**(按 `commands/aion-plan.md` 执行,但**不要求用户显式输入命令**)。
若用户选 (b) 或 (c):退出,保留 spec,等待后续触发。

### Phase 10.1 — _product.md 自动传播

spec 写完后,按 AionCode 原有 auto-propagation 机制更新 `.aion/specs/_product.md`:

1. **`_product.md` 不存在** → 按当前 spec 初始化:
   - 标准结构(见 `.aion/specs/product-design-layer.md`)
   - 产品定位(from Goal)、功能地图(第一条 from 本 spec)、技术栈(from manifest if detectable)
   - 所有内容标 `[from:spec]`, `confidence: low`
2. **`_product.md` 存在** → 增量更新:
   - 读现有内容
   - 从新 spec 提取新 features / 新模块 / 新用户场景
   - 追加到功能地图表(带 `对应 spec` 列指向本 spec)
   - 追加到核心业务流程(若 spec 暗示新用户旅程)
   - 所有新增标 `[from:spec]`
   - 更新 `updated_at`
   - **不**覆盖 `[CONFIRMED]` 项
3. 汇报:"已更新 `_product.md`:功能地图 +{N} 项, 业务流程 +{N} 项"
4. 首次创建:建议"产品设计文档已初始化。随着 spec 积累,文档将自动丰富。"

---

## Next Steps

Phase 10 已主动建议路径。若用户选 (a),本会话继续进入 aion-plan。若选 (b)/(c),Spec 已落盘,随时可以:
- 用户说"进入 plan" / "生成计划" → AI 主动触发 aion-plan
- 用户想手动调用 → `/project:aion-plan`(只做"修改已有 plan")

## Checklist (Phase 完成情况自检)

- [ ] Phase 1 完成:rules / changelog / refs / prototypes / 现有 specs / _product.md 全读了
- [ ] Phase 2 决定:是否启用辅助角色(Dashboard / Browser Agent)
- [ ] Phase 3 澄清:一次一问,3+ 问后有 recap
- [ ] Phase 4 路径:2-3 个方案,推荐的有理由
- [ ] Phase 5 挑战:对推荐方案做了失败模式/假设/最坏场景分析
- [ ] Phase 6 批准:逐章节获用户确认
- [ ] Phase 7 Version Check 执行,spec 按 `spec-template.md` 格式
- [ ] Phase 8 自审 4 维度 + Placeholder scan 通过
- [ ] Phase 9 用户复核通过
- [ ] Phase 10 主动建议进入 aion-plan + _product.md 传播完成
- [ ] TodoWrite 驱动全程可见

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 跳过 Phase 5 挑战 | 不经挑战的方案容易在 plan/实施阶段爆雷 | CRITICAL |
| Phase 6 一口气甩完整 spec | 用户无法精细反馈;批准变成橡皮章 | CRITICAL |
| 未获 Phase 9 批准直接进 aion-plan | 单方面决策破坏信任 | CRITICAL |
| 省略 Phase 8 自审 | Placeholders / 矛盾 / 歧义流入用户侧,侵蚀信任 | HIGH |
| 假设实现细节而不问 | Spec 被未经论证的技术选型污染 | CRITICAL |
| 忽略 `.aion/refs/` 和 `.aion/prototypes/` | 缺少上下文 → spec 和既有需求冲突 | HIGH |
| Phase 3 一次问 3+ 个问题 | 决策被草草处理 | MEDIUM |
| 问用户能从上下文/代码读出来的问题 | 浪费用户时间 | MEDIUM |
| 不走 TodoWrite 驱动 | 进度不可见 → 用户失去掌控感 | HIGH |
| 覆盖已有 spec 不做 Version Check | 丢失设计决策历史 | HIGH |
| 省略 Phase 10 主动建议 | 流程断裂,用户需自行切换命令 | HIGH |

### Rationalization Prevention

以下念头 = STOP,你在合理化(见 `.aion/rules/metacognition.md`):

| 借口 | 真相 |
|--------|---------|
| "这个需求太简单,不用走 10 phase" | 简单需求有简单根因。Phase 1-3 走过 5 分钟也叫走过。 |
| "我知道用户想要什么,不用澄清" | 你知道你以为用户想要什么。问一下只花 1 句。 |
| "方案只有一个,不用提 2-3 个" | 至少提 1 个备选和"不做"。不然无法挑战。 |
| "Phase 5 挑战有点多余" | 这是 AionCode 比 superpowers **额外加**的一 phase。不要跳。 |
| "直接写 spec,不用逐步批准" | Phase 6 是唯一防止"写出来用户不满意要全重来"的保险。 |
| "我自己审一下就行,不写 Phase 8 自审结果" | Self-review 不是自我安慰,是真的要按 4 维度查。 |

## Output Format

Spec 文件写到 `.aion/specs/{feature-name}.md`,格式严格按 `.aion/rules/spec-template.md`。

## Exit Status

- `DONE` — Spec 写完 + Phase 9 批准 + Phase 10 主动建议已发出
- `DONE_WITH_CONCERNS` — Spec 写完但用户未解决自审 flag 的问题
- `BLOCKED` — 无法推进:缺少用户无法当下提供的关键信息
- `NEEDS_CONTEXT` — 需要 ref / prototype / stakeholder 输入后才能定稿
