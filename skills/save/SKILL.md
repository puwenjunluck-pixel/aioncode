---
name: save
description: 会话工件落盘 — 把会话决策与未落盘增量沉淀到 .aion/。Use when 会话要结束、上下文要交接、或用户说 保存/save/存档. Not for 提交代码（用 /aion:commit）或跨会话 memory（原生负责）.
---

# /aion:save — 会话工件落盘

**分工**：跨会话记忆交给原生 memory；本命令只做 `.aion/` 工件落盘。

**Arguments**: 可选，限定保存类型：`changelog` | `spec` | `plan` | `rules`。为空时全量扫描本次会话。

## Role

你是**工件落盘器**：从对话和实际代码变更中提取有实质价值的结论，按 Write Protocol 持久化到 `.aion/`。只存实质，过滤寒暄与过程性噪音。Append, never overwrite。

所有写入遵循 `../think/references/write-protocol.md`（changelog/rules = Accumulative；specs/plans = Versioned）。

## Steps

### Step 0 — 前置检查

`.aion/` 不存在 → 建议先跑 `/aion:init`。用户拒绝 → 不写任何文件，把本应落盘的内容以 markdown 摘要形式输出到对话，标 `DONE_WITH_CONCERNS` 退出。

### Step 1 — 收集候选

扫描本次会话，分三类收集：

1. **关键决策 / 工作进展** → `.aion/changelog.md`
2. **讨论中产生但未落盘的需求/方案增量** → `.aion/specs/{name}.md` / `.aion/plans/{name}.md`
3. **新发现的坑 / 新约定** → `.aion/rules/`（如 pitfalls.md）

跑 `git diff --stat` 佐证实际变更 — changelog 写做过的事实，不写空谈。`$ARGUMENTS` 指定类型时只收集该类。

### Step 2 — 确认清单（硬 gate）

落盘前向用户列出「将要写什么到哪」清单：

```
1. .aion/changelog.md      [Accumulative] {一行摘要}
2. .aion/specs/foo.md      [Versioned]    {一行摘要}
3. .aion/rules/pitfalls.md [Accumulative] {一行摘要} ← 需逐条确认
```

等用户确认（可剔除条目）后才执行。rules 条目敏感度最高，必须逐条获得明确同意。

### Step 3 — 执行写入

Follow `../think/references/write-protocol.md`（changelog/rules: Accumulative；specs/plans: Versioned）——未读先写 = 写入 INVALID。**Refusal Condition**：Accumulative 目标未读做 dedup 就追加 = 写入 INVALID。本 skill 特有约定：

- **changelog**：条目格式 `## {YYYY-MM-DD HH:MM} | Context Save`，含 Summary / Key Conclusions / Pending 三段；即使其他类型无内容，changelog 条目也总是追加。
- **specs / plans**：不存在同名文件时，仅当对话材料足够支撑才新建（半生不熟的 spec 比没有更糟）。
- **rules**：条目格式 `- **{Title}** ({source}, {date}) [cite_count: 0, last_cited: {date}]`。

### Step 4 — 报告

按"写入 / 跳过（重复）/ 无变化"三栏简要汇报，列出每个文件和增量内容。

## Checklist

- [ ] 写前读过每个目标文件（去重 / diff 依据）
- [ ] Step 2 清单已获用户确认
- [ ] changelog 条目已追加
- [ ] 寒暄与过程性内容已过滤
- [ ] 未写入任何 memory / CLAUDE.md

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 未读目标文件就追加 | Write Protocol 违规（Accumulative 必须先读后写、去重） | CRITICAL |
| 覆盖已有内容而非追加/归档 | 摧毁先前沉淀，不可恢复 | CRITICAL |
| 跳过 Step 2 确认清单直接落盘 | 用户失去对项目记忆的控制权 | CRITICAL |
| 把跨会话记忆写进 .aion/ 或手动写 memory | 与原生 memory 职能重叠，双写导致混乱 | HIGH |
| 保存寒暄 / 过程性噪音 | 工件被噪音稀释后失去检索价值 | HIGH |
| 对话材料不足硬造 spec | 半生不熟的 spec 会误导后续 plan | MEDIUM |

## Exit Status

- `DONE` — 清单确认 + 全部写入完成
- `DONE_WITH_CONCERNS` — 已保存但部分归属/内容存疑；或 `.aion/` 缺失仅输出了对话摘要
- `BLOCKED` — 会话中无实质内容可存
- `NEEDS_CONTEXT` — 无法判断某讨论归属哪个 spec/plan，需用户指认
