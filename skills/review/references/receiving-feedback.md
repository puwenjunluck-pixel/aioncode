# Receiving Code Review Feedback

收到审查反馈（来自用户、其他 agent 或本 skill 的产出）时：技术评估优先于社交舒适。核心：verify before implementing, ask before assuming。

## Response Pattern（强制顺序）

1. **READ** — 读完整反馈，不急着回应
2. **UNDERSTAND** — 用自己的话复述每条要求；复述不出来 = 不理解
3. **VERIFY** — 对照代码库现实独立验证（读代码 / 跑测试），不信任转述
4. **EVALUATE** — 对**这个**代码库技术上成立吗（会不会破坏现有功能 / 当前实现有没有存在理由 / reviewer 有没有完整上下文）
5. **RESPOND** — 技术性确认或带证据的 pushback
6. **IMPLEMENT** — 逐项实现，逐项验证（见下）

## 任一条不清晰 → 阻断全部条目

任一条反馈不清晰时，**STOP — 不实现任何条目**，包括已理解的那些。条目之间可能相关，部分理解 = 错误实现。先把全部条目澄清，再动手。

- ❌ WRONG：理解了 1/2/3/6，先做掉，4/5 之后再问
- ✅ RIGHT："1/2/3/6 已理解。4 和 5 需要先澄清，澄清前不开始实现。"

## 逐项实现 + 逐项验证（强制顺序）

多条反馈：全部澄清后，按 阻断性问题（崩溃/安全）→ 简单修复（typo/import）→ 复杂修复（重构/逻辑）排序，然后**每实现一项，立即单独验证该项 + 确认无回归，才进入下一项**。禁止批量实现完再批量测 — 批量测一旦挂掉，无法定位是哪个修复引入的。

## Do / Never

**Do**：反馈正确 → 默默修好，actions > words；反馈错误 → 用 `file:line` / 测试输出技术性说明 WHY；当修复会破坏其他功能、reviewer 缺上下文、违反 YAGNI 或技术性错误时 push back —— **push back 必须带 file:line 证据**；无法验证时明说："没有 {X} 我验证不了，要 investigate / ask / proceed？"
**Never**："Great point!" / "You're absolutely right!" 式 performative agreement；未经技术评估盲改；嘴上说 fixed 代码没改；无证据驳回（"I think it's fine" 不是 rebuttal）。

## Pushback 错了时的纠正姿势

自己 push back 后被证明是错的：

- ✅ "你是对的 — 我查了 {X}，它确实 {Y}。我之前错在 {引用自己哪条依据错了}。现在按正确理解实现。" → 立即动手
- ❌ 长篇道歉 / 反复辩解当初为什么 pushback / 过度解释

陈述事实性纠正（明确指出自己哪里引用错了），立即按正确理解实现，move on。不重复辩解。
