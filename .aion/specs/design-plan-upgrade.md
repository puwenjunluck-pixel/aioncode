---
status: completed
created_at: 2026-04-06
version: 1
author: wayne
scope: full
change_reason: null
---

# Design-Plan 体验升级

## Goal
改进 aion-design 和 aion-plan 的对话体验，吸收 superpowers brainstorming + writing-plans 的小步决策、自审门禁、方案共创等优点，同时保留 AionCode 的项目知识积累优势。

## Requirements (P0)

### R1: 逐步提问 + 选项式对话（aion-design + aion-plan）
- 所有需要用户决策的问题改为一次只问一个
- 每个问题提供 2-3 个选项（A/B/C），标注推荐项和理由
- 选择题优先，开放题仅在无法预判选项时使用
- 适用范围：aion-design 的 Step 1.5（假设挑战）和 Step 2（澄清问题）；aion-plan 的架构决策和技术选型

### R2: 方案共创替代单向质疑（aion-design）
- Step 1.5 从"挑战假设"改为"探索方案"：先提出 2-3 个可行方案 + 权衡对比 + 推荐，再让用户选择
- 保留 Challenge 的本质（推敲假设、防止过度工程），但姿态从"质疑你的想法"变为"一起找最佳路径"
- 方案对比格式统一：每方案列出核心思路、优势、劣势、推荐理由

### R3: 逐段确认替代一次性确认（aion-design）
- Step 4 的 spec 确认从"展示完整 spec 一次性确认"改为按章节逐段确认
- 确认顺序：Goal → Requirements P0 → Requirements P1 → Acceptance Criteria → Constraints
- 每段确认后可立即修改，再进入下一段
- 全部确认后整合写入文件

### R4: Spec 自审门禁（aion-design）
- 在 Step 4（展示给用户）之前，新增 Step 3.8: Spec Self-Review
- 四项检查：
  1. Placeholder scan — 有无 TBD/TODO/不完整内容
  2. Internal consistency — P0 需求之间有无矛盾，与 Constraints 有无冲突
  3. Scope check — 是否一个 plan 能覆盖，过大则建议拆分
  4. Ambiguity check — 有无可被两种理解的需求，有则明确化
- 发现问题直接 inline 修复，用户看到的是审查过的版本
- 不增加用户交互，仅内部执行

### R5: Plan 自审门禁（aion-plan）
- 在 Step 4（展示给用户）之前，新增 Step 3.8: Plan Self-Review
- 三项检查：
  1. Spec coverage — 逐条对照 spec 需求，每条都有对应实现步骤，列出缺失项
  2. Step completeness — 有无跳过的边界情况、错误处理、空状态
  3. Name consistency — 后面步骤引用的文件名/函数名/变量名与前面步骤定义一致
- 发现问题直接 inline 修复
- 不增加用户交互，仅内部执行

### R6: 步骤拆分强化（aion-plan）
- 每步限定为一个文件或一个函数级别的改动
- 每步必须包含明确的验证命令（怎么确认这步做对了）
- 禁止出现："类似 Step N"、"添加适当的错误处理"、"补充测试" 等模糊描述
- 步骤格式增加 `verify` 字段：具体的验证命令或检查方法

### R7: 过渡引导强化（aion-design → aion-plan）
- design 完成后的 Next Steps 从静态提示改为主动引导
- 输出格式："Spec 已写入 `{path}`。下一步建议运行 `/project:aion-plan` 基于此 spec 生成实现方案。"
- 明确告知 plan 会自动读取刚写入的 spec，用户不需要额外指定参数

## Requirements (P1)

### R8: 问题上下文回顾
- 当提问超过 3 个时，在第 4 个问题前简要回顾已确认的决策（一行摘要），帮助用户保持全局视角

### R9: Plan 步骤模板升级
- 步骤格式从当前的 Description/Files/Dependencies/Complexity 扩展为：
  ```
  ### Step N: {Title}
  - **What**: 一句话说明做什么
  - **Files**: 创建或修改的具体文件
  - **How**: 2-3 句话说明实现要点（不写代码，但要具体到函数/方法级别）
  - **Verify**: 验证命令或检查方法
  - **Dependencies**: 依赖哪些前置步骤
  ```

## Future Work（待后续独立 spec 规划）

以下是 superpowers 对比分析中识别出的有价值能力，本次不实现，记录供后续版本规划：

### F1: Dashboard 设计协作视图（来源：superpowers visual-companion）
- aion-design 运行时将方案选项/UI mockup 推送到 Dashboard
- 用户在 Dashboard 上可视化浏览方案、点选选项，结果回传终端
- 复用现有 FastAPI + SSE 架构，预置 CSS 组件（option cards、wireframe、split view、pros/cons）
- 按问题类型决定走终端还是 Dashboard（布局→Dashboard，概念→终端）

### F2: TDD 模式集成（来源：superpowers test-driven-development）
- aion-loop 实现阶段可选强制 Red-Green-Refactor 循环
- 铁律：先写失败测试 → 确认失败 → 写最少实现 → 确认通过 → 重构
- 反模式检测表：防止"先写代码再补测试"等借口

### F3: Systematic Debug 方法论（来源：superpowers systematic-debugging）
- aion-fix 增加 `--deep` 模式，走四阶段根因分析
- 阶段：根因调查 → 模式分析 → 假设验证 → 实现修复
- 3 次修复失败后自动升级为架构级问题

### F4: Git Worktree 隔离（来源：superpowers using-git-worktrees）
- aion-loop 增加 `--worktree` 选项，在隔离工作树中执行
- 自动检测依赖并运行 setup
- 完成后提供 merge/PR/保留/丢弃四选一

### F5: 双阶段 Review（来源：superpowers subagent-driven-development）
- aion-review 拆为两轮独立审查：Spec 合规（需求覆盖）+ 代码质量（实现水平）
- 两轮可由不同子代理并行执行

### F6: Rationalization Prevention 体系（来源：superpowers 全局机制）
- 在关键命令的 Anti-Patterns 中增加"借口 vs 现实"对照表
- 明确列出 AI 可能用来绕过规则的理由及其反驳
- 重点覆盖：review（跳过审查的借口）、commit（跳过确认的借口）、plan（跳过代码阅读的借口）

### F7: Receiving Code Review 能力（来源：superpowers receiving-code-review）
- 教 AI 如何技术性地回应 review 反馈
- 禁止表演性同意（"Great point!"），要求技术评估后再行动
- 有理由时应 push back 而非盲从

## Acceptance Criteria
- aion-design 对话过程中每次只出现一个需要用户决策的问题
- aion-design 在需要用户选择方向时提供 2-3 个选项 + 推荐
- aion-design spec 展示前经过自审，无 placeholder、无矛盾、无歧义
- aion-design spec 按章节逐段确认（至少 Goal + P0 + P1 三段）
- aion-plan 展示前经过自审，spec 需求 100% 有对应步骤
- aion-plan 每步有明确的 verify 字段
- aion-plan 无模糊描述（"类似 Step N"、"适当处理"等）
- 两个命令文件均符合命令文件结构规范（style.md 规则 2）

## Constraints
- 只修改 2 个文件：`commands/aion-design.md` 和 `commands/aion-plan.md`
- 不改变命令架构（仍为独立 slash command，不自动互调）
- 不引入代码块级 plan（保持架构级）
- 单文件不超过 500 行（style.md 规则 3）
- 保留 AionCode 现有的所有独有能力（知识积累、_product.md 同步、version check、write protocol）
