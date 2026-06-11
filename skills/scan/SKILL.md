---
name: scan
description: 项目扫描 — 产品全景 + 规则种子 + E2E 测试定义。Use when 接手已有项目 needs AionCode onboarding, when the user wants to 建立或刷新产品全景 (_product.md), 导入需求文档 (--file), or explore a running app (--url). Covers what native /init does NOT — product map, rule seeds, E2E definitions. Not for codebase documentation or CLAUDE.md (use native /init).
---

# /aion:scan — 产品全景 · 规则种子 · E2E 定义

> **定位**：代码库通识（技术栈、目录结构、构建命令、CLAUDE.md）请用原生 `/init`。本命令做的是 `/init` 不做的三件事：**产品全景**（`.aion/specs/_product.md`）、**规则种子**（`.aion/rules/`）、**E2E 测试定义**（`.aion/tests/e2e/`）。

**Arguments**: 可选。`--file {path}` 导入外部文档（.docx/.pdf/.pptx/.xlsx/.md/.txt 或目录）作补充上下文；`--url {target_url}` 指定运行中应用的 URL 做浏览器探索。

## Role

你是 **onboarding 到已有代码库的资深架构师**：快速理解产品是什么、规则有哪些、关键流程怎么验证，产出立即可用的工件。彻底但高效 — 扫该扫的，跳过无关的。

> ⚠️ **CRITICAL**: NEVER 假设项目约定 — 一切从证据中发现。NEVER 生成泛型内容 — 每条产出必须 trace 到本项目的代码/文档/页面。RE_SCAN 时 NEVER 覆盖用户修改过的文件 — follow `../think/references/write-protocol.md`。

启动时用 TodoWrite 建立各 Step 的 todo，全程驱动。

## Step 0 — Pre-flight

1. `.aion/` 不存在 → 建议先跑 `/aion:init` 建立工件层，exit `BLOCKED`
2. 读 `.aion/rules/`、`.aion/specs/_product.md`、`.aion/tests/e2e/`（如存在）
3. 加载 `../think/references/write-protocol.md` — 后续所有写入按 category 执行
4. **判定模式**：rules 无实际条目 AND `_product.md` 不存在 → **FIRST_SCAN**；否则 **RE_SCAN**（控制 Step 2-4 写行为）

## Step 1 — 产品导向扫描（纯代码策略）

只扫支撑三类产出的内容，**不做通识探索**（那是 /init 的事）：

- **功能/模块**：入口、路由定义、顶层目录语义 → 功能地图候选
- **数据模型**：models / migrations / schema → 业务实体
- **API surface**：route 定义、swagger/openapi → 端点清单
- **UI 结构（静态）**：模板/JSX/Vue、前端路由、表单 → 页面与流程候选
- **代码模式（规则种子素材）**：linter 配置、2-3 个代表性源文件、`git log` 中的 fix commits

中大型项目可用 Agent tool（Explore subagent）并行扫描独立维度。

## Step 1.5 — 文件导入（条件：`--file`）

1. 转换为 markdown（有转换 skill 用之；**转换失败或无转换工具 → plain text 读取回退**；目录则批量处理支持格式）
2. 分类：需求/PRD → 功能、user stories、验收标准；架构/设计 → 模块、依赖；API 文档 → 端点、schema；混合 → 按章节拆
3. 提取项标 `[from:file]`，并入 Step 2-4 输入
4. 汇报："从 {N} 个文件导入：{N} 项需求、{N} 个模块、{N} 个 API 端点"

## Step 1.7 — 浏览器探索（条件：`--url`，且浏览器工具可用）

**前提检测**（与 `/aion:qa` 同样的通用检测原则）：

1. 检测可用的浏览器自动化工具（Playwright MCP 或其他浏览器 skill/tool）；**不可用 → 回退静态 UI 分析**（读模板/路由/CSS 推断页面结构，产出标 `[from:static]`），并建议配置浏览器工具后重跑
2. 目标 URL：`--url` 优先 > 从代码探测（dev scripts / Docker / server 配置）> 问用户
3. 验证 URL 可达（HTTP 200/30x）；不可达 → 静态回退

**Live 探索**（产出标 `[from:explore]`）：

1. 首页截图 → 映射导航结构（逐项点击，记录 label / 目标 / 页面标题）
2. 探索关键页面（≤15 个）：UI 元素、表单字段（label/类型/必填/校验）、empty/loading/error 状态
3. 响应式抽查：375×667 视口截两页
4. 遇登录页 → 问用户要测试账号，或请用户手动登录后继续
5. 截图存 `.aion/refs/screenshots/`

> ⚠️ 浏览器自动化**仅允许**在 `/aion:qa` 与 `scan --url` 中使用（pitfalls 规则）。其他场景不碰浏览器。

## Step 2 — 生成 `_product.md`（产品全景）

Write Protocol category: **Versioned**。结构按 `../think/references/product-template.md`。

**三源融合**：code scan（模块/端点/模型）+ file import（需求/user stories）+ browser explore（页面/导航/表单）。交叉对照：代码模块 ↔ UI 页面，API 路由 ↔ 前端调用，DB 模型 ↔ 业务实体。

- **FIRST_SCAN 或不存在**：生成完整文档。推断性内容（产品定位/业务流程）标 `[INFERRED]`；条目按来源标 `[from:code]` / `[from:file]` / `[from:explore]`；技术栈类事实标 `[CONFIRMED]`。frontmatter 设 `generation_method`（scan / scan+file / scan+explore / scan+file+explore）与 `confidence`（3 源 high / 2 源 medium / 仅 code low）
- **RE_SCAN**：增量更新 — 保留所有 `[CONFIRMED]` 项不动，追加新发现的模块/页面/端点（带来源标），刷新 `updated_at`

## Step 3 — 规则种子（`.aion/rules/`）

Write Protocol category: **Accumulative**（先读去重、只追加、NEVER 覆盖）。每条规则标 `[from:code]`：

- **style.md** ← linter 配置 + 代表性代码模式（命名/结构约定）
- **pitfalls.md** ← git log 的 fix commits + 危险代码模式

格式：`- **{约定}** (scan, {date}) [from:code] [cite_count: 0, last_cited: {date}]` + 一行带本项目实例的说明。**只写有证据的规则** — 找不到证据就不写。

**RE_SCAN**：先读全部既有规则（Refusal Condition — 不读不许写）；新发现的约定**逐条向用户提议后追加**；疑似过时的规则只标注、不修改。NEVER 覆盖已有条目。

## Step 4 — E2E 测试定义（`.aion/tests/e2e/*.md`）

Write Protocol category: **Regenerable**（fingerprint）。**多源自动生成**：路由/页面结构 `[from:code]` + 浏览器探索的真实流程 `[from:explore]` + 导入文档的验收标准 `[from:file]`。

每个 feature 一个文件，格式：

```markdown
---
feature: {功能名}
target_url: {URL}
viewport: [desktop]
preconditions: [{全局前置}]
---
## TC-001: {标题}
**Given**: {前置状态}
**When**: {操作} → {操作}
**Then**:
  - {可验证断言}
**Edge Cases**:
  - {边界场景}
```

要求：Then 必须可验证（"显示'保存成功'提示"，不是"页面正确"）；Edge Cases 覆盖空值/超长/异常路径；**RE_SCAN 只补新 feature 文件**，已有文件按 fingerprint 保护。

## Step 5 — 产品确认 Q&A（生成/更新 `_product.md` 后必做）

把所有 `[INFERRED]` 项分组呈现："请确认或纠正，或回复'确认'接受全部推断"。用户确认 → 改 `[CONFIRMED]`；纠正 → 应用后标 `[CONFIRMED]`；补充 → 追加标 `[from:user] [CONFIRMED]`。最后更新 `confidence`。

> 这一步把 AI 猜测变成验证过的知识 — 每次 scan 都要有一轮 Q&A。

## Step 6 — 报告

**FIRST_SCAN**：

```
Scan Complete — {project}
Generated:
  specs/_product.md   ← 产品全景（confidence: {level}）
  rules/style.md      ← {N} 条约定种子
  rules/pitfalls.md   ← {N} 条 pitfall 种子
  tests/e2e/{f}.md    ← {N} 个 TC
Next: {基于发现的 1-2 句建议}
```

**RE_SCAN — Delta Report（MANDATORY）**：

```
Delta Report — {project}
New:     {新端点/页面/模块…}
Updated: {file}: {改了什么、为什么}
Skipped: {file}: {保护原因，如 fingerprint mismatch / [CONFIRMED]}
Suggest: {后续建议}
```

## Next Steps

新功能 → `/aion:think`；重构规划 → `/aion:plan`；发现 bug → `/aion:fix`；执行 E2E → `/aion:qa`。

## Checklist

- [ ] `.aion/` 验证 + 模式判定（FIRST_SCAN / RE_SCAN）
- [ ] Write Protocol 已加载并按 category 执行
- [ ] 扫描只覆盖三类产出所需，未做 /init 式通识探索
- [ ] `--file`：转换/回退/分类/`[from:file]` 标注完成
- [ ] `--url`：工具检测 → live 或 static 回退，截图入 refs/screenshots/
- [ ] `_product.md` 按 product-template 生成/增量，`[CONFIRMED]` 未被覆盖
- [ ] 规则种子全部有证据 + `[from:code]`（Accumulative：先读去重、只追加）
- [ ] E2E 定义多源生成，Then 全部可验证
- [ ] 产品确认 Q&A 完成，confidence 已更新
- [ ] RE_SCAN：Delta Report 已呈现

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 重做 /init 的事（CLAUDE.md/技术栈清单/通识文档） | 与原生能力重复，浪费上下文 | CRITICAL |
| 在 qa 和 scan --url 之外使用浏览器自动化 | pitfalls 规则：浏览器自动化只许这两处 | CRITICAL |
| 无证据写规则 | 错误约定比没有约定更糟 | CRITICAL |
| RE_SCAN 覆盖已有规则或 `[CONFIRMED]` 项 | Write Protocol Refusal Condition | CRITICAL |
| 泛型产出（"write good code"式） | 不 trace 到本项目 = 零价值 | CRITICAL |
| 读遍每个文件的深扫 | scan 要快 — 读代表性样本 | HIGH |
| RE_SCAN 无 Delta Report | 用户无法评估增量 vs 保护项 | HIGH |
| E2E 的 Then 写不可验证断言 | 测试定义无法执行 | HIGH |
| 跳过产品确认 Q&A | `_product.md` 永远停在 AI 猜测 | HIGH |

### Rationalization Prevention

以下念头 = STOP，你在合理化（见宿主 `.claude/rules/metacognition.md`）：

| 借口 | 真相 |
|--------|---------|
| "顺手把架构文档也生成了" | 那是 /init 的领地。越界 = 双倍维护成本。 |
| "这条约定很常见，不用找证据" | 常见 ≠ 本项目在用。找不到证据就不写。 |
| "用户改过的文件，我的版本更好" | fingerprint mismatch = 用户主权。问，不要覆盖。 |
| "浏览器工具在，顺便点两下验证" | scan --url 之外的浏览器操作是违规，不是勤奋。 |
| "[INFERRED] 大概率对，跳过 Q&A" | 未确认的推断会污染后续所有 think/plan。 |

## Exit Status

- `DONE` — 三类工件按需生成，Q&A 完成
- `DONE_WITH_CONCERNS` — 完成但有盲区（如无法探索 UI、无 fix commits 可提取）
- `BLOCKED` — `.aion/` 未初始化或项目目录为空
- `NEEDS_CONTEXT` — 需要 URL/测试账号/文档等用户输入才能继续
