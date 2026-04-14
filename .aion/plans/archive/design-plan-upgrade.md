---
status: completed
created_at: 2026-04-06
spec: design-plan-upgrade.md
version: 1
previous_version: null
change_reason: null
author: wayne
scope: full
current_step: 8
total_steps: 8
---

# Plan: Design-Plan 体验升级

## Architecture Decisions
- 只改 prompt 内容（2 个 .md 文件），不改命令架构
- 两文件已有 "How to Ask Questions" 公共段落，保留并强化，让各 Step 引用而非重复定义
- Self-Review 统一放在 Step 3.8（Version Check 之后、Confirm 之前）
- P1 需求（R8 上下文回顾、R9 步骤模板）一并实现，改动量小

## Implementation Steps

### Step 1: aion-design — 重构 Step 1.5（R2: 方案共创）
- **What**: "Challenge Assumptions" → "Explore Approaches"，质疑变共创
- **Files**: `commands/aion-design.md` Step 1.5 段落
- **How**: 重写为 2-3 方案探索格式（Core idea/Pros/Cons/Recommendation），内部保留防过度工程透镜
- **Verify**: 标题含"Explore"，内容含"2-3 viable approaches"，无"push back"措辞
- **Dependencies**: None
- **Complexity**: small
- **Status**: Done

### Step 2: aion-design — 重写 Step 2（R1 + R8）
- **What**: 批量提问 → 逐个提问 + 上下文回顾
- **Files**: `commands/aion-design.md` Step 2 段落
- **How**: 删除"Ask 2-3"，改为 question pool + one-at-a-time + 3 题后 context recall
- **Verify**: 无"Ask 2-3"，有"one at a time"，有 context recall 规则
- **Dependencies**: None
- **Complexity**: small
- **Status**: Done

### Step 3: aion-design — 新增 Step 3.8 Self-Review（R4）
- **What**: 插入 Spec 自审门禁
- **Files**: `commands/aion-design.md`，Step 3.5 和 Step 4 之间
- **How**: 四项检查（placeholder/consistency/scope/ambiguity），内部修复不增加交互
- **Verify**: 段落位于 3.5 和 4 之间，含四项检查
- **Dependencies**: None
- **Complexity**: small
- **Status**: Done

### Step 4: aion-design — 重写 Step 4（R3: 逐段确认）
- **What**: 一次性确认 → 五段逐步确认
- **Files**: `commands/aion-design.md` Step 4 段落
- **How**: 按 Goal→P0→P1→AC→Constraints 顺序展示，每段等确认后再下一段
- **Verify**: 有五段确认序列，有"apply immediately"措辞
- **Dependencies**: Step 3（段落顺序）
- **Complexity**: small
- **Status**: Done

### Step 5: aion-design — 更新 Next Steps + Checklist + Anti-Patterns（R7）
- **What**: 强化过渡引导 + 补充新增能力检查项
- **Files**: `commands/aion-design.md` 三个段落
- **How**: Next Steps 加路径引导，Checklist +3 项，Anti-Patterns +2 行
- **Verify**: Next Steps 含"无需额外指定参数"，Checklist 有 self-review 项
- **Dependencies**: Steps 3, 4
- **Complexity**: small
- **Status**: Done

### Step 6: aion-plan — 强化 Step 2 + 格式模板（R6 + R9）
- **What**: 步骤粒度 + 禁止短语 + 模板升级
- **Files**: `commands/aion-plan.md` Step 2 段落和 Format 模板
- **How**: 新增粒度规则和 Forbidden descriptions 列表，模板加 What/How/Verify 字段
- **Verify**: Step 2 有禁止短语列表，Format 含 What/How/Verify
- **Dependencies**: None
- **Complexity**: medium
- **Status**: Done

### Step 7: aion-plan — 新增 Step 3.8 Self-Review（R5）
- **What**: 插入 Plan 自审门禁
- **Files**: `commands/aion-plan.md`，Step 3.5 和 Step 4 之间
- **How**: 三项检查（spec coverage/step completeness/name consistency），内部修复
- **Verify**: 段落位于 3.5 和 4 之间，含三项检查
- **Dependencies**: None
- **Complexity**: small
- **Status**: Done

### Step 8: aion-plan — 更新 Checklist + Anti-Patterns
- **What**: 补充新增能力检查项
- **Files**: `commands/aion-plan.md` 两个段落
- **How**: Checklist +3 项，Anti-Patterns +3 行
- **Verify**: Checklist 有 verify/vague/self-review 项，Anti-Patterns 有对应行
- **Dependencies**: Step 7
- **Complexity**: small
- **Status**: Done

## Verification Strategy
- **Method**: manual_check
- **Coverage**: 两个命令文件所有改动点
- **Commands**: `wc -l commands/aion-design.md commands/aion-plan.md`（< 500 行）+ 逐条 AC 验证
- **Success criteria**: 两文件均 < 500 行，8 条 AC 全部通过

## Risks
- 行数增长：~270 行/文件，距 500 行上限仍有余量，无需缓解
