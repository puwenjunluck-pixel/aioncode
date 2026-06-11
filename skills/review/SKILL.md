---
name: review
description: 代码审查 + 学习飞轮 — 审查改动、评分、提取规则、产出供 commit 门禁 hook 机械消费的 review 报告。Use after ANY code change and ALWAYS before commit（门禁 hook 只放行被 approved review 覆盖的提交）。`--quick` 跳过 test gap 分析；`--deep` 切换为全项目安全+性能审计；`--auto` 自动应用机械修复。Not for pure Q&A or 无改动场景。
---

# /aion:review — 代码审查

Review code changes, score quality, extract reusable rules, and write a review report whose frontmatter is mechanically consumed by the commit gate hook（`scripts/check-review.sh`）。

**Arguments**: 可选指定文件或 "all"。`--quick`（跳过 test gap 分析）| `--deep`（全项目审计，见 Deep Mode）| `--auto`（AUTO-FIX 类自动应用，ASK 类跳过并记录）。为空 = 审查全部未提交改动。

## Iron Laws（不可协商 — 宿主 `.aion/rules/metacognition.md` 存在时以宿主版为准）

```
1. NO REVIEW WITHOUT READING FULL FILE（不是只看 diff）
2. NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
   — 本次 review session 跑过验证命令才能判"通过"。上次的结果不算。
3. NO APPROVAL WITHOUT SPEC COVERAGE CHECK — 每条 P0 指向实现它的代码；缺失 = major issue
```

## Role

你是**严格且会提取可复用教训的 code reviewer**。对照 spec / plan / rules / contracts 审查每处改动，证据化评分，提取值得记住的模式，并主动提出修复而不只是指出问题。

> ⚠️ **CRITICAL**: NEVER review diffs alone — read the FULL file. Context-free review 是本命令的 #1 失败原因。

## Step 0 — Context Loading

1. 读 `.aion/rules/` 全部文件（如存在）— 解析每条规则的 `cite_count` / `last_cited` / `status`；`status: deprecated|archived` 的不执行；记录本次引用了哪些规则（供 Step 4c）
2. 读相关 `.aion/specs/`、`.aion/plans/`、`.aion/contracts/`（如存在）
3. **`.aion/` 不存在时优雅降级**：仍执行全部审查步骤，但跳过 rules/spec/plan 对照与规则提取，报告直接呈现在对话中，并告知用户"无 `.aion/`：本次 review 不沉淀、commit 门禁不生效"
4. `--deep` → 直接进入 Deep Mode（文末）

## Step 1 — Gather Changes

1. `git diff`（或 `git diff --cached`）+ `git diff --stat`；`$ARGUMENTS` 指定文件则聚焦之
2. 记录 `git rev-parse --short HEAD` → 报告的 `base_commit`；changed files 列表 → `reviewed_files`

**Evidence requirement**：每个论断必须引 `file:line` 或具体测试名。禁用 "likely / probably / should be fine" — verify and cite, or mark `[UNVERIFIED]`。
**提问纪律**：一次只问一个问题；给 A/B/C 选项 + 加粗推荐 + because。
**并行策略**：5+ 文件或独立关注点时，用 Agent tool 派 subagent（按 Stage 或按模块拆）；每个 subagent 仍须读全文件并对照 `.aion/rules/`。

## Step 2 — Two-Stage Review

两个独立 stage，都读 COMPLETE file（不只 diff），可并行派发后合并去重。

**Stage A — Spec Compliance（30%，"在做对的东西吗"）**：逐文件对照 spec 验收标准、plan 步骤、contracts 接口、`.aion/prototypes/`（UI 结构性错位才 flag）。任一验收标准未满足 = `major`。
**Stage B — Code Quality（40%）+ Security（30%，"做得好吗"）**：rules 违反；可读性 / DRY / 抽象 / 类型 / 错误处理；注入 / XSS / 认证 / secrets / OWASP Top 10。
**Test gap 检查（`--quick` 时跳过并在报告标明）**：每个改动的源文件，检查有无对应测试新增/更新；新逻辑无测试覆盖 → 按风险计 major/minor issue。

## Step 2.5 — Quantitative Gate

对照 `rules/style.md` 阈值：文件 >500 行 / 函数 >50 行 / 嵌套 >4 层 / 参数 >5 个 / 重复块 >10 行 → 各计 WARNING，每个从 Code Quality 扣 5 分。输出 metrics 表。历史豁免文件标注但不扣分；新代码超标必须列为 issue。

## Step 2.8 — Verification Gate（Iron Law 2）

打分前必须**在本 session** 跑验证命令：识别（什么命令证明代码真的能跑）→ 执行 → 读完整输出/exit code → 记入报告 `Verification` 段。

| 声明 | 需要的证据 |
|---|---|
| "测试通过" | 测试命令输出 `0 failures` |
| "构建成功" | 构建命令 `exit 0` |
| "Bug 修好了" | 原始复现用例现在通过 |
| "需求全部满足" | 逐条 P0 checklist 核对 |

**未跑验证 = 不能 approve**，verdict 降为 `needs_fix`。唯一豁免出口：纯文档/配置变更，报告明确标 `Verification: N/A — pure doc/config` 并写明判断依据。

## Step 3 — Score & Verdict

Score 0-100 = **Code Quality（40）+ Security（30）+ Spec Compliance（30）**。报告中 Dimension Scores 三个维度名必须与此处完全一致（历史报告曾把 Spec Compliance 误写成 Architecture Compliance — 命名错位会让评分不可对照，禁止）。

- `approved` — score ≥ 70 且无 critical issue 且 Verification Gate 通过
- `needs_fix` — 其余一切情况

## Step 4 — 学习飞轮：提取 + 维护

### 4a 规则提取
从 findings 提取：bug 模式 → `pitfalls.md`；代码约定 → `style.md`；性能教训 → `perf.md`。标准：会在本项目复发、非语义重复、非 trivial 常识。格式：
`- **{Title}** (review, {YYYY-MM-DD}) [cite_count: 0, last_cited: {YYYY-MM-DD}]`
写入遵循 `../think/references/write-protocol.md`（category: **Accumulative**）：写前必读目标文件做语义去重 — duplicate → skip；extends → 原地更新；conflict → flag 用户，不自动写。**未读先写 = 写入 INVALID**。

### 4b 风格模式提取
扫描 ≥3 个文件一致的模式（错误处理约定 / import 风格 / 命名 / 类型标注风格），写入 `rules/style.md`（同 Accumulative 纪律）。不一致的模式作为 issue 报告，不提取。

### 4c 引用更新 + 退役建议（学习飞轮的出口 — MUST，不可跳过）
1. 本次 review 引用过的每条规则（违反或遵守都算）：`cite_count` +1，`last_cited` = 今天；缺元数据的条目补 `[cite_count: 1, last_cited: 今天]`
2. **退役扫描**：遍历 `.aion/rules/`，找出 `cite_count: 0` 且 `last_cited` 距今 **>60 天**的规则，列表呈现给用户并建议标 `status: archived` — 用户确认后才改标记，**NEVER 自动删除规则内容**
3. 更新各规则文件 frontmatter 的 `last_updated` 与 `rule_count`

## Step 5 — 写 Review 报告（commit 门禁联动）

写入 `.aion/reviews/{feature-name}.md`。**`reviewed_files` 与 `base_commit` 为必填字段**：

```markdown
---
status: {approved | needs_fix}
score: {N}
verdict: {approved | needs_fix}
issues_found: {N}
rules_extracted: {N}
reviewed_at: {YYYY-MM-DD}
review_rounds: {N}
reviewed_files:
  - {repo 相对路径，与 `git diff --name-only` 输出一致，逐文件一行}
base_commit: {`git rev-parse --short HEAD` 的输出}
---

# Review: {Feature Name}
## Score: {N}/100
**Verdict**: {approved | needs_fix}
### Dimension Scores
- Code Quality: {N}/40
- Security: {N}/30
- Spec Compliance: {N}/30
## Verification
| 验证项 | 命令 | 结果 |
## Issues
- **[critical|major|minor]** {描述} — {建议修复}
## Rules Extracted / Retired
- Added to `rules/{category}.md`: {title}；建议归档：{list 或 none}
```

**Hook 联动（为什么必填）**：`scripts/check-review.sh` 是 PreToolUse hook，拦截 `git commit`，只放行同时满足三条的提交：① 存在 `status: approved` 的 review；② 其 `base_commit` == 当前 HEAD（short 或 full hash）；③ staged 文件 ⊆ 满足①②的所有 review 的 `reviewed_files` 并集。推论：路径必须是 repo 相对路径；review 之后又改了文件 → 把新文件补入 `reviewed_files` 重审或重新 review，否则门禁拒绝。门禁豁免（hook 内置）：纯 `.aion/` 提交、`fix(bug):` 前缀提交、非 aion 项目。

## Step 5.5 — Auto-Fix Loop（verdict = needs_fix 时）

分类：**AUTO-FIX**（机械无歧义：缺 import / 未用变量 / 格式 / typo / 上下文显然的类型标注）vs **ASK**（需判断：逻辑 / API 设计 / 架构 / >3 文件 / 可能改行为）。呈现两类清单问 "Apply auto-fixes? [Y/n]" → 批准后应用 AUTO-FIX、逐项决策 ASK → 重跑验证 → 回 Step 2 重审。**最多 3 轮**，仍 fail = `DONE_WITH_CONCERNS`。
`--auto`：AUTO-FIX 直接应用，ASK 跳过并记入报告；**>5 critical 仍然 STOP**（不受 --auto 影响）。
`approved` 时建议："Review passed. Run `/aion:commit` to commit."；needs_fix 且用户拒绝修复 → 可走 `/aion:fix`。

---

## Deep Mode（`--deep`）— 全项目安全+性能审计

默认 review 是**改动级**（diff scope）；`--deep` 是**项目级**：扫整个代码库，read-only 分析，审计中不修改任何代码。

1. **范围**：全部源文件；排除 `node_modules/`、`vendor/`、`__pycache__/`、`.git/`、`dist/`、`build/` 及 `rules/style.md` 豁免的生成文件；尊重行级 `# audit:ignore` 标记；支持 `--focus security|perf`、`--ignore {pattern}`
2. **Security（S1-S5）**：依赖漏洞（已知 CVE / 未 pin 版本）；硬编码 secrets（`sk-`/`AKIA`/`ghp_`/`Bearer `/`password=`/PRIVATE KEY，含被 git 跟踪的 `.env`）；注入（SQL 拼接、命令执行、XSS、路径穿越）；认证与访问控制（无鉴权端点 / 硬编码角色 / token 无过期 / `allow_origins=["*"]`）；其余 OWASP 静态可查项（弱哈希、prod debug 模式、日志泄敏感数据）
3. **Performance（P1-P5）**：循环内 DB/API 调用（N+1）；算法复杂度（≥3 层嵌套循环、线性查找、无分页）；资源泄漏（无 `with`、连接不还池、无界缓存）；阻塞操作（async 中同步 I/O、整文件读入内存）；冗余计算（热循环内重复昂贵操作、缺 cache）
4. **评分**：Security 与 Performance 各 0-100，按 finding 扣分（critical −20 / high −10 / medium −5 / low −2，floor 0）；Overall = Security×0.6 + Performance×0.4（`--focus` 时聚焦维度 100%）
5. **基线对比**：读 `.aion/reviews/` 中最近的 `audit-*.md`，逐条标 NEW / FIXED / PERSISTENT / REGRESSED，输出 Δ 与分数趋势；无基线则标 "First audit"
6. **规则提取**：跨 ≥2 个文件复发的模式 → `rules/security.md` / `rules/perf.md`（Accumulative 纪律 + Step 4c 引用维护与退役扫描同样执行）
7. **报告**：写入 `.aion/reviews/audit-{YYYY-MM-DD}.md`，frontmatter 含 `date / scope / security_score / performance_score / overall_score / total_findings / critical / high / medium / low`。每条 finding 格式：`- **[severity]** [S2] \`file:line\` — 描述` + `Fix: 具体建议`。**注意**：audit 报告不含 `reviewed_files` / `base_commit`，不解锁 commit 门禁 — 修复审计问题后仍需常规 `/aion:review`。

## Receiving Code Review Feedback

收到审查反馈（来自用户、其他 agent 或本 skill 的产出）时：

**Do**：读完整反馈再回应；独立验证（读代码 / 跑测试）；反馈正确 → 默默修好，actions > words；反馈错误 → 用 `file:line` / 测试输出技术性说明 WHY；当修复会破坏其他功能、reviewer 缺上下文、违反 YAGNI 或技术性错误时 push back —— **push back 必须带 file:line 证据**。
**Never**："Great point!" / "You're absolutely right!" 式 performative agreement；未经技术评估盲改；嘴上说 fixed 代码没改；无证据驳回（"I think it's fine" 不是 rebuttal）。

## Checklist

- [ ] 所有改动文件读了全文（非 diff-only）
- [ ] spec / plan / contracts 对照完成（如存在）
- [ ] Test gap 检查执行（或 `--quick` 在报告中标明跳过）
- [ ] Quantitative Gate 执行（文件/函数/嵌套/参数）
- [ ] Verification Gate：本 session 跑过验证命令，或标 `N/A — pure doc/config`
- [ ] 评分三维度命名与 Step 3 完全一致
- [ ] 规则提取走 write-protocol 去重；引用更新 + 60 天退役扫描执行（4c）
- [ ] 报告 frontmatter 含 `reviewed_files`（全部被审文件）+ `base_commit`（当前 HEAD short hash）
- [ ] `--deep`：全库扫描 + 基线对比 + 报告写入 `audit-{date}.md`

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 只看 diff 不读全文件 | 漏掉依赖上下文的真 bug | CRITICAL |
| 报告缺 `reviewed_files` / `base_commit` | commit 门禁无法机械验证，用户被 hook 拦死 | CRITICAL |
| 未经用户许可 auto-fix | 用户必须批准修复 — 不要悄悄改代码 | CRITICAL |
| `--deep` 只扫 diff | 审计是项目级 — 改动级是默认模式的职责 | CRITICAL |
| 不对照 spec/plan | review 退化成 style-only，漏功能正确性 | HIGH |
| 提取泛化编程常识为规则 | 噪音稀释规则库（如"用有意义的变量名"） | HIGH |
| 规则只进不出（跳过 4c 退役扫描） | 规则库无限膨胀，每次 review 的读取成本递增、信噪比衰减 | HIGH |
| 审计中修改代码 | audit 是 read-only 分析 — 修复走后续流程 | HIGH |
| 无证据给高分 | 评分必须 evidence-based，不是感觉 | MEDIUM |
| 超过 3 轮 fix 不升级 | 死循环浪费时间；多半是 plan/spec 需要修订 | MEDIUM |

### Rationalization Prevention

以下念头 = STOP，你在合理化：

| 借口 | 真相 |
|--------|---------|
| "改动很小，扫一眼就行" | 小改动出最坏的 bug — 上下文越少假设越多 |
| "写代码时我已经在脑子里 review 过了" | 自审客观性为 0。新鲜眼睛才能看见熟悉感掩盖的东西 |
| "只是 refactor，不会坏" | "不可能坏"的 refactor 是回归的 #1 来源 |
| "测试过了，肯定没问题" | 测试只验证你想到要测的。review 抓你没想到的 |
| "上次跑过验证了" | Iron Law 2：只有本 session 的证据才算数 |
| "这条老规则也许还有用，先留着" | 0 引用 + 60 天 = 建议归档。留着的成本是每次 review 都要读它 |
| "代码库太大，--deep 抽几个文件看看" | 审计 = 全量扫描。用 `--ignore` 显式排除，不要静默抽样 |

## Exit Status

- `DONE` — review 完成且 verdict 为 `approved`（或 `--deep` 审计完成、报告落盘）
- `DONE_WITH_CONCERNS` — `needs_fix` 且用户拒绝修复 / 超 3 轮仍 fail / 审计存在 critical（overall < 50）
- `BLOCKED` — 无改动可审，或 `--deep` 下无源文件可扫
- `NEEDS_CONTEXT` — 需要 spec / plan 才能评估 compliance
