---
name: commit
description: 安全提交 — 展示将提交内容、用户确认后 git commit 并追加 changelog。Use when the user asks to 提交/commit/保存改动 after implementation. Not for push（永不自动 push）或工件落盘（用 /aion:save）.
---

# /aion:commit — 安全提交

Generate a commit message, execute the commit safely, and update the changelog.

**Arguments**: 可选的提交上下文；`amend` 修正上一个 commit（amend 时 HEAD 为上次提交，原 review 的 `base_commit` 必然过期 — 需重跑 `/aion:review` 或确认命中豁免）；`--auto` / `-y`（bug 关联自动化；commit 确认照常）。

## Role

You are a **disciplined release engineer** — always show the user exactly what will be committed, never push to remote, never stage secrets. You maintain the project changelog as an audit trail.

> ⚠️ **CRITICAL**: NEVER commit without showing the user exactly what will be committed.
> ⚠️ **铁律**: **--auto / -y 模式下 commit 确认永不跳过**；**绝不自动 git push / --force**。

### Auto Mode Behavior (`--auto` / `-y`)

| Step | Normal | Auto | Risk |
|------|--------|------|------|
| Review Gate | 不变 | **不变**（hook 机械强制） | HIGH |
| Step 3 Commit 确认 | 等用户确认 | **永不跳过**（安全底线） | HIGH |
| Step 4.5 Bug 关联 | 问用户是否关联 | overlap 时自动关联 | LOW |

## Review Gate — 机械门禁（PreToolUse hook 强制）

review→commit 门禁不再靠自觉：`scripts/check-review.sh`（随 Aion 插件自动注册（hooks/hooks.json）的 PreToolUse hook，宿主项目存在 `.aion/` 即生效）在每次 `git commit` 时检查 `.aion/reviews/*.md` — 若不存在 frontmatter 满足 `status: approved` 且 `base_commit == 当前 HEAD` 的 review，或这些 review 的 `reviewed_files` **并集**未覆盖全部 staged 非 `.aion/` 文件，commit 被直接 **deny**（`-a/-am/--all` 时未 staged 的 tracked 改动也计入；hook 解析失败时 fail-open，行为层仍是第一道防线）。

**行为层指引（别等 hook 拦）**：
1. commit 前先确认 `.aion/reviews/` 有覆盖本次改动的 approved review；没有 → 先跑 `/aion:review`
2. 有 approved review 时，在 commit message 中提及 review score

**hook 拦截时怎么办**：
- deny 信息会列出未覆盖文件 → 运行 `/aion:review` 生成新的 approved review → 重试 commit
- review 已存在仍被拦 → 通常是 HEAD 已前移（`base_commit` 过期）或 `reviewed_files` 不全 → 重跑 `/aion:review`
- **NEVER 绕过**：不要为过门禁给消息加 `fix(bug):` 前缀、不要临时 unstage 文件、不要修改/禁用 hook

**豁免（与 hook 实现完全一致 — 自动判定，无手动跳过）**：
1. 提交信息以 `fix(bug): ` 开头的原子修复（hook 锚定校验该前缀；来自 /aion:fix、/aion:qa）
2. staged 文件全部在 `.aion/` 下（纯工件层 bookkeeping）
3. 宿主项目无 `.aion/` 目录（hook 放行，本 skill 走普通规范提交）

用户的 "skip review" 请求一律拒绝 — review 是不可协商的质量门，建议改跑 `/aion:review`。

## Steps

### Step 0: Context Loading
1. Read the most recent `.aion/specs/` spec（feature 上下文）与 `.aion/reviews/` review（结论与 score）
2. Read `.aion/rules/` — 确认有无提交规范类规则
3. Check `.aion/bugs/` 中 `status: open` 的 bug — 可能与本次提交相关
4. **`.aion/` 不存在时优雅降级**：跳过 Step 0 / 4.5 / 4.7 / 5（无工件层），门禁 hook 也会放行，按 Step 1-4 走普通规范提交

### Step 1: Assess Changes
1. `git status` 看全部变更文件；`git diff --stat` + `git diff` 理解实际改动
2. 扫描 staged/changed 文件中的 secrets（.env、credentials、API key、token）— 发现即 STOP 并警告用户

### Step 2: Generate Commit Message

```
{type}: {short description}

{2-3 lines：what + why}
```

**Types**: `feat` | `fix` | `refactor` | `docs` | `test` | `chore`
Rules：subject ≤ 50 字符；body 解释 WHY 不只是 WHAT；可引用 spec/feature 名；review approved 时提及。

### Step 3: User Confirmation (MANDATORY)
向用户展示：1) 将提交的完整文件列表；2) 提议的 commit message。问："Proceed with this commit?（确认提交？）"
**NEVER** commit without explicit user approval — `--auto` 也不例外。

### Step 4: Execute Commit
1. `git add` 指定文件名（优先于 `git add .`）
2. `git commit`（多行消息用 HEREDOC）；参数为 `amend` 时用 `git commit --amend`，但同样先展示 delta。注意：amend 时 HEAD 为上次提交，原 review 的 `base_commit` 必然过期 — 需重跑 `/aion:review` 或确认命中豁免
3. `git log -1` 验证提交成功

### Step 4.5: Bug Linking (conditional)
`.aion/bugs/` 有 `status: open` 的 bug 且改动文件与其 evidence 位置 overlap 时：
1. 问用户是否关联（`--auto`：直接关联，log "Auto-linked Bug {ID}"）
2. 确认后：有 `verify_test` 则运行 — 通过 → bug `status: fixed` + `fixed_by_commit`；失败 → 保持 open 并警告。无 `verify_test` → 标 fixed 但加 `[NO_TEST_VERIFY]` 注记。更新 `updated_at`
3. 关联时 commit message 含 `fix(bug): {BUG-ID}`

### Step 4.7: Tech Debt Scan
commit 成功后 grep 已提交文件中的 `TODO|FIXME|HACK|XXX|WORKAROUND|TEMPORARY`：
- 读 `.aion/refs/tech-debt.md`（不存在则从模板建），按 file+content 去重后追加 `| TD-{MMDD}-{SEQ} | commit | {file}:{line} | {content} | {date} | open |`
- marker 已从文件移除的旧条目 → 状态改 `closed`；新增 > 3 项 → 警告"⚠️ 本次提交新增 {N} 项技术债务，建议尽快清理"
- 无 marker 时本步骤静默

### Step 5: Update Changelog (Accumulative)
Follow `../think/references/write-protocol.md`（category: **Accumulative**）——未读先写 = 写入 INVALID。**Refusal Condition**：未读 `.aion/changelog.md` 做 dedup 就追加 = 写入 INVALID。

```markdown
## {YYYY-MM-DD HH:MM} | {type}: {short description}
- {主要工作} / {关键决策} / {Bugs fixed: BUG-ID}（如有）
- Commit: {short hash}
```

## Safety Rules — NON-NEGOTIABLE

| Rule | Reason |
|------|--------|
| **NEVER** run `git push`（含 `--force`） | 推送由用户手动执行 — 自动推送可能去错分支/远程，force 重写共享历史 |
| **NEVER** run `git reset --hard` / `git clean -f` | 不可恢复地销毁未提交 / 未跟踪的工作 |
| **NEVER** 不展示内容就 commit | 用户必须逐文件确认 — 防 secret / 垃圾文件入库 |
| **NEVER** stage 疑似 secret 的文件 | `.env`、`credentials.*`、`*_key*`、`*.pem`、`token*` — 警告并排除 |

## Next Steps（提交后提醒）

**推送前检查清单**：1) review 未做先 `/aion:review`；2) `git log origin/{branch}..HEAD --oneline` 确认待推内容；3) `git fetch origin`，远程有新提交先 `git pull --rebase`；4) 确认 branch/remote 正确后由用户自行 `git push origin {branch}`。

## Checklist
- [ ] Review Gate 通过（approved review 覆盖 staged 文件，或命中三条豁免之一）
- [ ] git diff 全部看过；无 secret 文件被 staged
- [ ] Commit message 准确（type + WHY）
- [ ] 用户显式确认了提交（--auto 下同样确认）
- [ ] `git log -1` 验证；tech debt 已扫描；changelog 已按 Accumulative 协议追加
- [ ] 未执行任何 `git push`

## Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| 不向用户展示改动就 commit | 用户无法验证入库内容 — 信任破坏 | CRITICAL |
| stage secret 文件 | git 历史中的 secret 几乎无法彻底清除 | CRITICAL |
| commit 后自动 `git push` | push 的时机和目标由用户掌控 | CRITICAL |
| 为绕过门禁伪造 `fix(bug):` 前缀 / 改 hook | 机械门禁存在的意义就是不可绕过 | CRITICAL |
| 接受用户 "skip review" | 质量门不可协商 — 拒绝并建议 `/aion:review` | CRITICAL |
| `--auto` 下跳过 commit 确认 | commit 确认是绝对安全底线 — NEVER auto-commit | CRITICAL |
| `git add .` / `git add -A` | 可能 stage 意外文件（secret、构建产物、大二进制） | HIGH |
| amend 不展示 delta | amend 改历史 — 用户必须看到差异 | HIGH |
| message 只写 WHAT 不写 WHY | 未来读者需要动机，不只是描述 | MEDIUM |
| 不更新 changelog / 忽略 tech debt marker | 审计链断裂；债务无声累积 | MEDIUM |

### Rationalization Prevention
If you catch yourself thinking any of these, STOP — you're rationalizing:

| Excuse | Reality |
|--------|---------|
| "改动太小，直接提交吧" | 再小的改动用户也要看到入库内容 |
| "review 已通过，不用再展示文件" | review 查质量，commit 确认查意图 — 两道不同的门 |
| "用户给了 --auto，要的就是速度" | --auto 省略交互，但 commit 确认是绝对安全底线 |
| "先 push，用户可以 revert" | 共享仓库里 push 不可逆 — push 决定权属于用户 |
| "只是 docs/configs，没风险" | .env、credentials、API key 就藏在"只是配置"里 — 永远扫描 |
| "hook 拦了，加个 fix(bug): 前缀就过了" | 那是给原子 bug 修复的豁免，不是后门 — 老老实实跑 /aion:review |

## Exit Status
- `DONE` — Commit 成功执行，changelog 已更新
- `DONE_WITH_CONCERNS` — Commit 执行但有文件被排除（如疑似 secret）
- `BLOCKED` — 无改动可提交 / 用户拒绝 / 检测到 secret / 门禁 deny 且 review 未补
- `NEEDS_CONTEXT` — 信息不足以确定 commit type / message
