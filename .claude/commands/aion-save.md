# /project:aion-save — 上下文保存

Save important information from the current conversation to three persistence layers: `.aion/` documents, `.claude/CLAUDE.md` (first-layer memory), and Claude memory.

$ARGUMENTS — Optional: what to save.
- Empty: analyze the full conversation and save all relevant information to all layers
- `spec`: save requirement-related discussions to `.aion/specs/`
- `plan`: save technical decisions to `.aion/plans/`
- `rules`: save lessons learned to `.aion/rules/` (uses the same extraction and deduplication logic as aion-review's Auto-Learn step)
- `changelog`: save work progress to `.aion/changelog.md`

## Role

You are a **context preservation engine**. Your job is to ensure no important information is lost when a conversation ends. You extract structured knowledge from both conversation AND actual code changes, and persist it to three layers:

1. **`.aion/` 文件** — 项目文档（规格、计划、规则、日志）
2. **`.claude/CLAUDE.md`** — 第一层记忆（每次对话最先加载的项目索引）
3. **Claude memory** — 用户/项目记忆（跨会话持久化）

You append, never overwrite. You deduplicate, never repeat. You filter — only substance, never noise.

> ⚠️ **CRITICAL**: NEVER overwrite existing content. Always APPEND. Destroying previous work is unrecoverable. Violating this is the #1 cause of failure for this command.

> ⚠️ **CRITICAL**: `.claude/CLAUDE.md` 是项目第一层记忆。save 可以在 `<!-- AIONCODE:END -->` 标记之后追加或更新项目级上下文，但 NEVER 修改标记区域内的内容（由 init/upgrade 管理）。保持简约索引风格——一行一条，不写详细说明。标记外 Project Notes 区域不超过 10 行。

## Steps

### Step 0: Context Loading
1. Identify which `.aion/` directories and files already exist
2. This determines what can be appended to vs. what needs to be created

### Step 1: Analyze Conversation
Scan the current conversation and classify information into two persistence layers:

#### Layer 1: `.aion/` 文件（项目文档）

| Type | Destination | Examples |
|------|-------------|---------|
| Requirement decisions | `.aion/specs/` | Feature descriptions, user stories, scope boundaries, constraints |
| Technical decisions | `.aion/plans/` | Architecture choices, library selections, API designs |
| Lessons learned | `.aion/rules/` | Pitfalls discovered, conventions established, perf insights |
| Work progress | `.aion/changelog.md` | What was done, what's pending, key decisions made |
| Interface agreements | `.aion/contracts/` | API shapes, data formats, cross-team protocols |

**Routing guide for learned knowledge** (previously went to CLAUDE.md LEARNED section):
- 项目约束/规则 → `.aion/rules/pitfalls.md` or `.aion/rules/style.md`
- 技术栈决策 → `.aion/rules/style.md`
- 架构原则 → `.aion/specs/` or `.aion/plans/`
- 开发上下文 → Claude memory (project type)

#### Layer 2: Claude Memory（用户/项目记忆）

Scan for information that should persist **across conversations and potentially across projects**:

| Type | Memory type | Examples |
|------|------------|---------|
| 用户角色和背景 | `user` | "用户是全栈工程师，10 年经验" |
| 协作方式偏好 | `feedback` | "用户不喜欢过多解释，偏好简洁回答" |
| 项目关键上下文 | `project` | "正在做支付系统重构，deadline 是 4 月底" |
| 外部资源指引 | `reference` | "Bug 追踪在 Linear 的 BACKEND 项目中" |

**判断标准**：这条信息在下次新对话中是否有价值？如果只对当前对话有用，不保存到 memory。

If `$ARGUMENTS` specifies a type (spec/plan/rules/changelog), only save that type to `.aion/`. But **always** check and save to memory regardless.

### Step 1.5: Code Change Audit（代码变更审计）

Run `git diff --stat` and `git diff --name-only` to detect actual code changes in this session.

1. **分类变更文件**：commands/ (命令), aioncode/ (核心代码), templates/ (模板), .aion/ (文档)
2. **对比现有文档**：对每个重要功能变更，检查 `.aion/specs/` 和 `.aion/plans/` 是否有对应文档
3. **Gap 处理**：
   - 功能已实现但无 spec → Step 3a 中创建追溯性 spec，frontmatter 加 `source: retroactive-save`
   - 功能已实现但无 plan → Step 3a 中创建追溯性 plan summary
   - 追溯文档基于实际代码变更（读 diff），不是对话文本

### Step 2: Read Existing Documents
Before writing anything:
1. Read every target file that will be updated
2. Compare conversation content against existing content
3. Skip anything that's already recorded — no duplicates

### Step 3: Write Updates

Follow Write Protocol (`.aion/refs/write-protocol.md`): Versioned for specs/plans, Accumulative for rules/changelog.

#### 3a: Write to `.aion/` files

**For specs** (`.aion/specs/{name}.md`):
- If a spec file for this feature exists, append new sections (don't overwrite)
- If no spec exists, create one with the standard format (see /project:aion-design)
- Only write substantive requirement information, not casual discussion

**For plans** (`.aion/plans/{name}.md`):
- If a plan exists, update with new decisions or step changes
- If no plan exists, create one only if there's enough technical detail

**For rules** (`.aion/rules/*.md`):
- Follow the same extraction and deduplication logic used in aion-review's Auto-Learn step (Step 6)
- Read existing rules first, skip duplicates
- Use the standard rule format: `- **{Title}** ({source}, {date}) [cite_count: 0, last_cited: {date}]`

**For changelog** (`.aion/changelog.md`):
- Always append an entry for this conversation
- Format:
```markdown
## {YYYY-MM-DD HH:MM} | Context Save

### Summary
- {What was discussed}
- {Key decisions made}

### Key Conclusions
- {Most important outcomes, 1-3 items}

### Pending
- {What still needs to be done} (if any)
```

**For contracts** (`.aion/contracts/{name}.md`):
- Only if API or interface agreements were discussed
- Write in a format both backend and frontend can reference

#### 3b: Update Claude Memory（用户/项目记忆）

If Step 1 identified memory-worthy information:

1. For each piece of information, determine the memory type (user/feedback/project/reference)
2. Use Claude's built-in memory system to save:
   - Write memory files to the project memory directory
   - Update MEMORY.md index
3. Follow the standard memory format with frontmatter (name, description, type)
4. **Check existing memories first** — update rather than duplicate
5. Only save genuinely cross-session information — not ephemeral task details

#### 3c: CLAUDE.md 智能更新（第一层记忆）

读取 `.claude/CLAUDE.md`，检查是否有本次变更需要反映：

1. **标记区域内**（`<!-- AIONCODE:START/END -->` 之间）：
   - NEVER 直接修改
   - 如内容过时（如新增命令未列出），在报告中提示用户运行 `aioncode init --upgrade`

2. **标记区域外**（`<!-- AIONCODE:END -->` 之后）：
   - 使用 `## Project Notes` 区域
   - 每条一行，索引风格
   - 总量不超过 10 行，超过时合并或删除过时条目
   - 只放通过"删掉这条，Claude 会犯错吗？"测试的信息
   - 先去重：已存在则跳过

### Step 4: Report
```
Context Saved
───────────────────────────────────────

Layer 0 — CLAUDE.md (第一层记忆):
  + Project Notes: {N} entries added/updated
  (或: no updates needed)
  (或: ⚠ marker section outdated — run `aioncode init --upgrade`)

Layer 1 — .aion/ 文件:
  .aion/specs/{name}.md — {what was added}
  .aion/changelog.md — conversation summary
  .aion/rules/pitfalls.md — {N} new rule(s)

Layer 2 — Claude Memory:
  + project: 支付系统重构进行中
  + feedback: 用户偏好简洁回答
  (skipped: 1 item already in memory)

No changes:
  .aion/plans/ — no technical planning in this conversation

Total: {N} file(s) updated, {N} memories
───────────────────────────────────────
```

## Next Steps

Context saved. Safe to end this conversation or start a new task.

## Checklist
Read and apply `.aion/checklists/save.md` if it exists. If not, use the built-in checklist:
- [ ] All existing target files read before writing
- [ ] No duplicate information written
- [ ] Casual chat and meta-discussion filtered out — only substance saved
- [ ] Changelog entry appended (always, even if other types have nothing)
- [ ] File format matches existing conventions in each target file
- [ ] Code changes audited via git diff
- [ ] Spec/plan gaps identified and retroactively documented
- [ ] CLAUDE.md: only wrote OUTSIDE markers, kept index style, ≤10 lines
- [ ] Memory checked for existing entries before creating
- [ ] Memory items are cross-session insights, not ephemeral task data

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Modifying CLAUDE.md marker section (AIONCODE:START/END 之间) | 标记区域由 init/upgrade 管理，手动修改会被覆盖 | **CRITICAL** |
| Writing detailed content to CLAUDE.md | CLAUDE.md 是索引不是文档，详细内容属于 .aion/ | HIGH |
| Skipping git diff audit | 遗漏已实现但未文档化的功能 | HIGH |
| Only analyzing conversation without checking code changes | 跳过 design/plan 直接实现时，对话文本中没有需求/方案信息 | HIGH |
| Saving trivial chat or greetings | Noise in project documents makes them useless | HIGH |
| Overwriting existing file content | Destroys previously saved work — always append | CRITICAL |
| Not reading existing files before writing | Guaranteed duplicates that clutter documents | HIGH |
| Creating a spec from insufficient conversation | Half-baked specs are worse than no specs — they mislead | MEDIUM |
| Skipping changelog entry | Changelog is the activity audit trail — always update it | MEDIUM |
| Saving implementation details as specs | Specs are requirements, not code descriptions | MEDIUM |
| Saving ephemeral task data to memory | Memory is for cross-session insights, not "currently working on X" | MEDIUM |
| Saving to memory what already exists in .aion/rules/ | Duplication across systems causes confusion | MEDIUM |

## Output Format
The report shown in Step 4, listing both layers' updates.

## Exit Status
- `DONE` — All relevant information saved to both layers
- `DONE_WITH_CONCERNS` — Saved but some information was ambiguous and may need review
- `BLOCKED` — No substantive information found in conversation worth saving
- `NEEDS_CONTEXT` — Cannot determine which spec/plan a discussion relates to
