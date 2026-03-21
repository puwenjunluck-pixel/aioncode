# /project:aion-save — 上下文保存

Save important information from the current conversation to three persistence layers: `.aion/` documents, project CLAUDE.md, and Claude memory.

$ARGUMENTS — Optional: what to save.
- Empty: analyze the full conversation and save all relevant information to all layers
- `spec`: save requirement-related discussions to `.aion/specs/`
- `plan`: save technical decisions to `.aion/plans/`
- `rules`: save lessons learned to `.aion/rules/` (uses /project:aion-learn logic)
- `changelog`: save work progress to `.aion/changelog.md`

## Role

You are a **context preservation engine**. Your job is to ensure no important information is lost when a conversation ends. You extract structured knowledge from unstructured conversation and persist it to three layers:

1. **`.aion/` 文件** — 项目文档（规格、计划、规则、日志）
2. **`.claude/CLAUDE.md`** — 项目级指令（每次 Claude 启动自动加载）
3. **Claude memory** — 用户/项目记忆（跨会话持久化）

You append, never overwrite. You deduplicate, never repeat. You filter — only substance, never noise.

> ⚠️ **CRITICAL**: NEVER overwrite existing content. Always APPEND. Destroying previous work is unrecoverable. Violating this is the #1 cause of failure for this command.

## Steps

### Step 0: Context Loading
1. Identify which `.aion/` directories and files already exist
2. Read `.claude/CLAUDE.md` to understand what project instructions are already recorded
3. This determines what can be appended to vs. what needs to be created

### Step 1: Analyze Conversation
Scan the current conversation and classify information into three persistence layers:

#### Layer 1: `.aion/` 文件（项目文档）

| Type | Destination | Examples |
|------|-------------|---------|
| Requirement decisions | `.aion/specs/` | Feature descriptions, user stories, scope boundaries, constraints |
| Technical decisions | `.aion/plans/` | Architecture choices, library selections, API designs |
| Lessons learned | `.aion/rules/` | Pitfalls discovered, conventions established, perf insights |
| Work progress | `.aion/changelog.md` | What was done, what's pending, key decisions made |
| Interface agreements | `.aion/contracts/` | API shapes, data formats, cross-team protocols |

#### Layer 2: CLAUDE.md（项目指令）

Scan for information that should be **loaded every time Claude starts** in this project:

| What to save | Examples | NOT this |
|-------------|---------|---------|
| 技术栈决策 | "本项目统一用 TypeScript strict mode" | 具体代码实现 |
| 项目约束 | "API 返回必须用 camelCase" | 一次性的调试过程 |
| 团队约定 | "所有 PR 必须有测试覆盖" | 已在 .aion/rules/ 中的内容 |
| 架构原则 | "使用 Repository Pattern 访问数据库" | 临时的 workaround |
| 重要的开发上下文 | "该项目是微服务架构，共 5 个服务" | 通用编程知识 |

**判断标准**：这条信息是否影响 Claude 在这个项目中每次编码的行为？如果是，放 CLAUDE.md；如果只是某个功能的细节，放 `.aion/specs/` 或 `.aion/plans/`。

#### Layer 3: Claude Memory（用户/项目记忆）

Scan for information that should persist **across conversations and potentially across projects**:

| Type | Memory type | Examples |
|------|------------|---------|
| 用户角色和背景 | `user` | "用户是全栈工程师，10 年经验" |
| 协作方式偏好 | `feedback` | "用户不喜欢过多解释，偏好简洁回答" |
| 项目关键上下文 | `project` | "正在做支付系统重构，deadline 是 4 月底" |
| 外部资源指引 | `reference` | "Bug 追踪在 Linear 的 BACKEND 项目中" |

**判断标准**：这条信息在下次新对话中是否有价值？如果只对当前对话有用，不保存到 memory。

If `$ARGUMENTS` specifies a type (spec/plan/rules/changelog), only save that type to `.aion/`. But **always** check and save to CLAUDE.md and memory regardless.

### Step 2: Read Existing Documents
Before writing anything:
1. Read every target file that will be updated
2. Read `.claude/CLAUDE.md` to check for existing project instructions
3. Compare conversation content against existing content
4. Skip anything that's already recorded — no duplicates

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
- Follow the same extraction and deduplication logic as /project:aion-learn
- Read existing rules first, skip duplicates

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

#### 3b: Update CLAUDE.md（项目指令）

If Step 1 identified project-level instructions worth persisting:

1. Read the current `.claude/CLAUDE.md` file
2. Look for the `<!-- AIONCODE:LEARNED -->` section marker
3. If the marker doesn't exist, append it at the end of the file:
   ```markdown

   <!-- AIONCODE:LEARNED -->
   ## Learned Project Context
   <!-- Items below are auto-extracted by /aion-save. Edit freely. -->
   ```
4. Append new instructions under this section, each as a bullet point:
   ```markdown
   - {instruction} (saved {YYYY-MM-DD})
   ```
5. **Deduplicate**: Read existing items and skip if semantically equivalent
6. **Maximum 20 items**: If exceeding 20, consolidate older items or remove less relevant ones

#### 3c: Update Claude Memory（用户/项目记忆）

If Step 1 identified memory-worthy information:

1. For each piece of information, determine the memory type (user/feedback/project/reference)
2. Use Claude's built-in memory system to save:
   - Write memory files to the project memory directory
   - Update MEMORY.md index
3. Follow the standard memory format with frontmatter (name, description, type)
4. **Check existing memories first** — update rather than duplicate
5. Only save genuinely cross-session information — not ephemeral task details

### Step 4: Report
```
Context Saved
───────────────────────────────────────

Layer 1 — .aion/ 文件:
  .aion/specs/{name}.md — {what was added}
  .aion/changelog.md — conversation summary
  .aion/rules/pitfalls.md — {N} new rule(s)

Layer 2 — CLAUDE.md 项目指令:
  + "本项目使用 PostgreSQL，不要建议用 MySQL"
  + "API 统一返回 { code, data, message } 格式"
  (skipped: 2 items already recorded)

Layer 3 — Claude Memory:
  + project: 支付系统重构进行中
  + feedback: 用户偏好简洁回答
  (skipped: 1 item already in memory)

No changes:
  .aion/plans/ — no technical planning in this conversation

Total: {N} file(s) updated, {N} CLAUDE.md items, {N} memories
───────────────────────────────────────
```

## Next Steps

Context saved. Safe to end this conversation or start a new task.

💡 If this session involved code changes, bug fixes, or review feedback, consider running `/project:aion-learn` to extract reusable rules.

## Checklist
Read and apply `.aion/checklists/save.md` if it exists. If not, use the built-in checklist:
- [ ] All existing target files read before writing
- [ ] No duplicate information written
- [ ] Casual chat and meta-discussion filtered out — only substance saved
- [ ] Changelog entry appended (always, even if other types have nothing)
- [ ] File format matches existing conventions in each target file
- [ ] CLAUDE.md checked for existing instructions before appending
- [ ] Memory checked for existing entries before creating
- [ ] CLAUDE.md items are project-level instructions, not implementation details
- [ ] Memory items are cross-session insights, not ephemeral task data

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Saving trivial chat or greetings | Noise in project documents makes them useless | HIGH |
| Overwriting existing file content | Destroys previously saved work — always append | CRITICAL |
| Not reading existing files before writing | Guaranteed duplicates that clutter documents | HIGH |
| Creating a spec from insufficient conversation | Half-baked specs are worse than no specs — they mislead | MEDIUM |
| Skipping changelog entry | Changelog is the activity audit trail — always update it | MEDIUM |
| Saving implementation details as specs | Specs are requirements, not code descriptions | MEDIUM |
| Dumping everything to CLAUDE.md | CLAUDE.md is for instructions, not documentation. Too much = ignored | HIGH |
| Saving ephemeral task data to memory | Memory is for cross-session insights, not "currently working on X" | MEDIUM |
| Skipping CLAUDE.md and memory layers | These are the primary loading mechanisms — .aion/ files alone are insufficient | HIGH |
| Saving to memory what already exists in .aion/rules/ | Duplication across systems causes confusion | MEDIUM |

## Output Format
The report shown in Step 4, listing all three layers' updates.

## Exit Status
- `DONE` — All relevant information saved to all three layers
- `DONE_WITH_CONCERNS` — Saved but some information was ambiguous and may need review
- `BLOCKED` — No substantive information found in conversation worth saving
- `NEEDS_CONTEXT` — Cannot determine which spec/plan a discussion relates to
