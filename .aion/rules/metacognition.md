---
category: metacognition
rule_count: 0
last_updated: 2026-06-12
---

# Metacognition — 元认知与反合理化

<!-- 本仓库自身加载的元规则（dogfood）。与分发源 skills/init/references/metacognition.md
     保持同步——后者由 /aion:init 安装到宿主 .claude/rules/metacognition.md。
     手写纪律层（非 /aion:review 自动提取），基于 superpowers:using-superpowers
     和 verification-before-completion 改编。Rules 一律在动作前生效。 -->

## Iron Laws (不可协商)

```
RULE 1 · NO RULE SKIP
在编辑任何代码文件之前，MUST 读完 .aion/rules/ 全部文件。
RULE 2 · NO COMPLETION WITHOUT VERIFICATION
在声称"完成 / 通过 / 修好"之前，MUST 在本轮消息中跑过验证命令。
RULE 3 · NO FIX WITHOUT ROOT CAUSE
在提出修复之前，MUST 完成 /aion:fix 的根因阶段（Phase 1）。
RULE 4 · NO DESIGN WITHOUT APPROVAL
3+ 文件改动之前，MUST 先走 /aion:think 并获得用户批准。
```

## Red Flags — 听到内心这样说就 STOP

这些念头意味着你在**合理化**，不是在判断：

| 念头 | 现实 |
|---|---|
| "这只是简单问题" | 简单问题有简单根因。走流程只花 1 分钟。 |
| "我先看看再说" | 流程告诉你怎么看。流程**先于**看。 |
| "文件路径我记得" | 文件会被重命名/删除。Grep 一下 2 秒。 |
| "我跑过测试，应该还过" | Should pass ≠ passes。**Run it.** |
| "这是微调不算任务" | 任何 edit 都是任务。检查规则。 |
| "规则太繁琐" | 繁琐是你的合理化。规则在那里是因为**过去已经翻过车**。 |
| "Agent 说成功了" | Agent 的汇报是声明，不是证据。看 diff。 |
| "我就改一行" | 最短的 diff 也能破坏最多的 invariant。 |
| "不走 /aion:think，直接改" | 直接改 → 遗漏约束 → 返工 → 比走流程慢 3 倍。 |
| "You're absolutely right!" 式空洞附和 | 反馈要么有道理（指出哪里对）要么有疑问（带证据 push back），没有第三种。 |

**STOP 的判断标准**:如果你在句子里出现了 should / probably / seems / 应该 / 估计 / 大概 / 看起来 — 这些是**模糊词**,意味着你没有证据。

## Verification Before Claim (证据先于声明)

声称任何状态(passes / works / fixed / complete)之前:

```
1. IDENTIFY — 什么命令/输出能证明这个声明?
2. RUN      — 在本轮消息里执行完整命令(不是上一轮)
3. READ     — 看完整输出、退出码、失败数
4. VERIFY   — 输出是否真的确认了声明?
5. ONLY THEN — 说出这个声明，并附上证据
```

**违反此流程 = 说谎，不是效率。**

对照表:

| 声明 | 需要的证据 | 不够的 |
|---|---|---|
| "测试通过" | 测试命令输出 `0 failures` | "上次跑是通过的" / "应该能过" |
| "构建成功" | 构建命令 `exit 0` | Linter 过了 / Log 看起来正常 |
| "Bug 修好了" | 原始复现用例现在通过 | 改完代码 / 自觉应该好了 |
| "回归测试生效" | 先断言失败 → 修复 → 断言通过(红-绿循环) | 测试跑了一次通过 |
| "需求全部满足" | 逐条 checklist 核对 | 测试通过 |

## 合理化阻断表

| 借口 | 真相 |
|---|---|
| "Should work now" | 跑一下验证。 |
| "我很有把握" | 把握 ≠ 证据。 |
| "就这一次跳过" | 没有例外。流程就是不容例外才叫流程。 |
| "Linter 过了" | Linter 不等于编译器，编译器不等于测试。 |
| "Agent 汇报成功" | 独立验证。看 diff。 |
| "我累了" | 疲惫不是借口。它是犯错的信号，恰好是要加验证的时刻。 |
| "部分检查就够了" | 部分证明等于没证明。 |
| "换个词这条规则就不适用" | 规则的**精神**优先于字面。 |
| "测试事后补也一样" | 事后测试只验证你写了什么，不验证需求要什么。可自动验证的改动默认测试先行。 |

## 优先级 (当规则冲突时)

1. **用户显式指令** (CLAUDE.md / 直接对话) — 最高
2. **.claude/rules/ 与 .aion/rules/** 硬约束 (含本文件)
3. **superpowers / 默认系统行为** — 最低

若 CLAUDE.md 说"别用 TDD"而 skill 说"必须用 TDD" — 听 CLAUDE.md,用户在掌控。

**例外：机械门禁与安全底线（review 门禁 / commit 确认 / 不自动 push）不受单次对话指令豁免**——它们的变更只能通过修改 rules 文件或 hook 配置完成，不能通过会话内说服。

## 本规则何时生效

**每次对话的每次回复**。不是仅在 /aion:think / /aion:review / /aion:fix — 而是**所有编辑、提交、宣称完成**的动作。

If you think there is even a 1% chance a rule here applies — **apply it**. This is not negotiable.
