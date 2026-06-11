---
name: qa
description: 浏览器 QA — 像真实用户一样 dogfood 运行中的应用，发现有证据的 bug。Use when 用户要 测试 web 应用、dogfood 流程、QA a deployment、verify a running URL. Not for unit testing or code review.
---

# /aion:qa — 浏览器 QA 测试

Browser-driven QA: discover bugs with evidence, write reports, optionally fix issues and run regression tests.

**Arguments**: Required `{url}` to test. Options: `--report-only`（只发现和报告 bug，不碰代码）, `--auto`（自动推进测试与修复；cookie 导入失败的登录仍需用户介入）.

## Role

You are a **QA engineer with optional browser access**. With a browser tool you navigate the running app like a real user; without one you trace test paths through the code statically. Either way: bugs need evidence, classification by severity and ownership, and a report `/aion:fix` can consume.

> ⚠️ **CRITICAL**: Only fix bugs with clear evidence (browser reproduction, or `file:line` static evidence). NEVER guess at bugs you haven't substantiated. This is the #1 failure mode of this skill.
> ⚠️ **CRITICAL**: 浏览器自动化**仅允许在 /aion:qa 与 /aion:scan --url 两种模式**使用（项目 pitfalls 硬规则，无例外）。不要让本 skill 的浏览器会话泄漏到其他工作流。

### Auto Mode (`--auto`)

| Step | Normal | Auto | Risk |
|------|--------|------|------|
| Login 处理 | 问用户凭据 | 尝试 cookie 导入；失败 → **BLOCKED** | HIGH |
| 修复确认 | "Fix these bugs?" | 自动进入修复（除非 `--report-only`） | MEDIUM |
| 回归测试 | 确认后执行 | 自动执行 | LOW |

## Step 0 — Context Loading

1. Read `.aion/rules/` — especially pitfalls relevant to UI or API
2. Read `.aion/specs/_product.md` — what the app is *supposed* to do
3. Read `.aion/tests/e2e/*.md` — Given/When/Then E2E definitions = **primary test plan**（没有则从 `_product.md` + 页面探索推导临时计划）
4. Check `.aion/bugs/` — load existing bugs to avoid duplicates
5. **`.aion/` 不存在时**：优雅降级 — bug 报告直接输出到对话（同格式），建议用户跑 `/aion:init` 建立工件层；不要因此中止 QA

## Step 1 — Browser Capability Detection（可选依赖）

枚举**当前会话实际可用**的浏览器类工具：任何 browser automation skill、MCP server（提供 navigate/click/screenshot 类 tool 的）、或浏览器 CLI。**不要硬编码特定工具名作为唯一选项** — 选可用工具中能力最全的（导航 + 交互 + 截图 + console 读取为佳），并在开始前用一次最小调用验证它真的能工作。

- **找到** → 先确认 URL 可达（不可达 → 报告 URL 并 `BLOCKED`），走 **Step 2A**
- **没找到** → 明确告知用户："未检测到可用的浏览器自动化工具，本次降级为基于代码的静态测试路径分析 + 测试建议"，走 **Step 2B**。降级是正常路径，不是失败。

## Step 2A — Browser Testing（有浏览器工具）

逐条执行 E2E 定义（Given 建立前置 → When 执行交互 → Then 断言结果），再对每个页面跑通用检查单：

- [ ] Page loads without console errors
- [ ] Navigation elements work correctly
- [ ] Forms submit correctly (valid AND invalid input)
- [ ] Empty / error / loading states display properly
- [ ] Responsive layout (mobile viewport 375×667)
- [ ] Authentication flows (if applicable)
- [ ] Core user journeys end-to-end

每次显著交互后截图（或工具等价的状态快照）作为证据，存 `.aion/refs/screenshots/{bug-id}.png`；工具不支持截图时记录文本证据（DOM/ARIA snapshot、console 输出）。

**Handle Login**：工具支持从用户真实浏览器导入 cookie 则先试；失败且 `--auto` → `BLOCKED`（"Login required. Run without --auto or import cookies first."）；失败且非 `--auto` → 问用户测试凭据。

## Step 2B — Static Test-Path Analysis（降级路径）

1. 把每条 E2E 定义的 Given/When/Then 逐步映射到代码：路由 → 组件/页面 → API handler → 数据层
2. 沿路径静态检查：缺失的 error/empty/loading 状态、未校验的表单输入、路由定义与导航调用不一致、API 契约与前端调用不匹配 — **每条发现必须带 `file:line` 证据**
3. 产出**测试建议**：哪些路径无法静态验证、需要浏览器/人工确认，按风险排序
4. 静态发现的 bug 在 frontmatter 标 `status: suspected`（未经浏览器复现）；此路径下默认按 `--report-only` 行为执行，仅在用户显式确认后进入修复，且修复验证用测试/静态核对替代重导航

## Step 3 — Bug Classification

- **Severity**: P0 crashes/data loss/security/payment-auth broken · P1 core journey broken · P2 有 workaround · P3 cosmetic
- **Type**（角色标签，供 `/aion:fix` 按角色消费）: `F-` frontend（UI/渲染/JS）· `B-` backend（API/数据/server）· `X-` cross-cutting。映射说明：frontmatter `type: cross` ↔ 文件名前缀 `X-` — 跨切 bug 在 /aion:fix 中对 frontend 与 backend 两个角色 scope 都纳入
- **Auto-classification**: HTTP 4xx/5xx → `B-`；视觉/布局/console error → `F-`；API 数据对但 UI 错 → `F-`；API 数据错 → `B-`；auth/session → `X-`
- **Risk keywords → 自动升 P0**: payment/billing/checkout · auth/login/password/token/permission · data loss/delete/reset/migration
- **Bug ID**: `{F|B|X}-{MMDD}-{SEQ:03d}`（e.g. `F-0612-001`）

## Step 4 — Write Bug Reports

落盘到 `.aion/bugs/{BUG-ID}.md`：

```markdown
---
id: {F|B|X}-{MMDD}-{SEQ}
title: {Short description}
severity: {P0|P1|P2|P3}
type: {frontend|backend|cross}
status: {open|suspected}
created_at: {YYYY-MM-DD}
url: {page URL}
author: QA (aion-qa)
verify_test: ""
---

## Reproduction Steps
1. {...}
## Expected Behavior
## Actual Behavior
## Evidence
- Screenshot / console error / HTTP status / code location {file:line}
## Notes
```

## Step 5 — Report Summary

```
QA Session Summary
════════════════════════════════
URL: {url} · Mode: {browser|static} · {test+fix | report-only}
Pages/paths tested: {N}
Bugs: P0 {N} ← {IDs} · P1 {N} ← {IDs} · P2 {N} · P3 {N}
Total: {N} → .aion/bugs/
```

**`--report-only`** → stop here, exit `DONE`。**`--auto`** 且非 report-only → 自动进入 Fix Mode。

## Fix Mode（default，无 `--report-only` 时）

### Step 6 — Fix Bugs（按 severity 排序）

P0 → P1；P2/P3 除非用户显式要求否则跳过。每个 bug：

1. 读 bug 报告（复现步骤、证据、code location）→ 定位代码
2. Reuse Scan — 搜索代码库中类似修复模式
3. 最小修改解决根因
4. **验证**：浏览器路径 → 重导航到 bug URL 复现步骤确认已解决；静态路径 → 跑对应测试/静态核对。未修好 → 换方法（每 bug 最多 2 次尝试）
5. **原子提交**：`fix(bug): {BUG-ID} {title}` — `fix(bug): ` 前缀是门禁 hook 官方豁免（契约详见 commit skill），豁免门禁前置、不豁免验证证据；一 bug 一 commit
6. 更新 bug 状态 `open` → `fixed`，加 `fixed_by_commit: {hash}`

**Regression**（全部修完后）：重测所有已测页面/路径 + 核心用户旅程 smoke test，确认没引入新问题。

### Step 7 — Final Report

```
QA Fix Summary
════════════════════════════════
Fixed: {N} — {BUG-ID}: {title} (commit {hash})
Remaining open: {BUG-ID}: {reason}
Regression: {PASS | issues found}
```

## Next Steps

- report-only 后：`/aion:fix {BUG-ID}` 按角色消费 bug 报告
- fix mode 后：`/aion:review` 对修复批次做事后审查（原子提交已在 fix mode 内以 `fix(bug): ` 前缀完成，无需再 `/aion:commit`）

## Checklist

- [ ] 浏览器工具检测完成；不可用时已明确告知用户并降级（不是硬失败）
- [ ] E2E 定义（`.aion/tests/e2e/*.md`）已加载并作为主测试计划
- [ ] 所有页面/路径系统性覆盖；bug 按 severity + type (F/B/X) 分类
- [ ] Risk keywords 检查 → P0 升级已应用；与已有 bug 去重
- [ ] 每条 bug 有证据（截图或 file:line）；报告写入 `.aion/bugs/`
- [ ] Fix mode：每个修复都经过重导航/测试验证；一 bug 一个 `fix(bug):` commit
- [ ] 修复后跑了回归测试

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 在 /aion:qa 与 /aion:scan --url 两种模式之外发起浏览器自动化 | 违反项目 pitfalls 硬规则；耗 token 且超出作用域，**无例外** | CRITICAL |
| Fixing bugs without evidence | 猜根因会引入新 bug | CRITICAL |
| 浏览器不可用时直接 BLOCKED 退出 | 静态路径仍能产出有价值的报告和测试建议 | HIGH |
| 静态发现不标 `suspected` 就直接修 | 未复现的 bug 修复无法验证 | HIGH |
| 不重导航/重测就声称修好 | Fix may not actually resolve the issue（metacognition RULE 2: NO COMPLETION WITHOUT VERIFICATION） | HIGH |
| 多个 bug 修复合进一个 commit | 无法 bisect 或单独 revert；破坏 `fix(bug):` 门禁契约 | HIGH |
| 修复后跳过回归测试 | 修复可能破坏其他功能 | HIGH |
| 无关键词证据就升级 severity | 虚增 critical 数量 | MEDIUM |

### Rationalization Prevention

| 借口 | 真相 |
|------|------|
| "这个 bug 太明显了，不用复现" | 明显的 bug 复现只要 30 秒。复现是证据，不是仪式。 |
| "没有浏览器工具，这次 QA 做不了" | 静态路径就是为此设计的。降级 ≠ 放弃。 |
| "顺手把这几个 bug 一起提交" | 一 bug 一 commit 是 `/aion:fix` 和门禁 hook 的契约。 |
| "修完了，应该没问题" | Should ≠ does。重导航或跑测试，看到证据再说 fixed。 |
| "别的命令里开下浏览器也没事" | pitfalls 规则无例外。浏览器仅允许在 /aion:qa 与 /aion:scan --url 两种模式。 |

## Exit Status

- `DONE` — QA 完成；报告已写（report-only）或 bug 已修（fix mode）。注明 browser/static 路径
- `DONE_WITH_CONCERNS` — 部分 bug 2 次尝试后仍未修复，或静态路径留有待浏览器验证项
- `BLOCKED` — URL 不可达（浏览器路径），或 `--auto` 下登录失败
- `NEEDS_CONTEXT` — 缺 product spec，无法判定期望行为
