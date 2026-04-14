---
last_updated: 2026-04-14
---

# AionCode Credits

AionCode 的纪律层(元认知 / spec 模板 / plan 模板 / 10-phase think / Verification Gate / 4-phase debugging)部分内容
**基于** [Obra Works 的 superpowers 项目](https://github.com/obra/superpowers) 改编并本地化(中文化 + `.aion/` 路径注入 + AionCode 工作流对齐)。

superpowers 采用 **MIT License**,允许本项目借鉴其设计和内容,我们在此声明来源以示尊重。

## 借鉴对照表

| AionCode 资产 | 借鉴自 superpowers | 改编内容 |
|---|---|---|
| `.aion/rules/metacognition.md` | `using-superpowers` + `verification-before-completion` | Iron Laws / Red Flags / Rationalization Prevention — 中文化,关键英文打断语言保留;加入 AionCode 专属红旗 |
| `.aion/rules/spec-template.md` | `brainstorming`(design 输出章节结构) | 融合 AionCode 原 spec 格式(P0/P1/scope/frontmatter)+ superpowers 的 Architecture/Error Handling/Testing Strategy 段 |
| `.aion/rules/plan-template.md` | `writing-plans`(bite-sized task 模板) | 融合 AionCode 原 plan 格式(frontmatter/current_step)+ superpowers 的 TDD 节奏、code-in-every-step、No Placeholders 禁忌 |
| `commands/aion-think.md` 10-phase 工作流 | `brainstorming` 9-step checklist | 保留原 9 step + 新增 Phase 5 "挑战"(AionCode 独有);TodoWrite 驱动明确化 |
| `commands/aion-review.md` Iron Law + Verification Gate | `verification-before-completion` | "Evidence before claims" 精神注入 Step 2.8;对照表本地化 |
| `commands/aion-fix.md` Iron Law + 4-phase debugging | `systematic-debugging` | AionCode 原 `--deep` 模式本来就已经对齐 4-phase;此次强化 Iron Law + 默认推荐 `--deep` + 红-绿回归验证 |

## 未借鉴的部分(明确不搬)

| superpowers 资产 | 不搬理由 |
|---|---|
| `test-driven-development` | 和 AionCode `.aion/tests/e2e/*.md`(AI 多源生成 Given/When/Then 格式)的测试哲学冲突 |
| `writing-plans` 作为独立 skill | 已内嵌进 `aion-plan` 命令和 `.aion/rules/plan-template.md` |
| `brainstorming` 作为独立 skill | 已内嵌进 `commands/aion-think.md` 10-phase |
| `subagent-driven-development` | AionCode 已有 Agent 工具并行规则(见 `.claude/CLAUDE.md`) |
| `using-git-worktrees` | 本项目 solo + master 工作流,不需要 |
| `requesting-code-review` / `receiving-code-review` | `aion-review` 已是双向闭环 |
| `using-superpowers` 的 skill check 元规则 | AionCode 靠 `.aion/rules/` + CLAUDE.md MANDATORY 段达成等效 |

## 升级策略

superpowers 升级(目前追踪版本:**5.0.7**)时,**不自动同步**。需要人工 diff 对比:

1. 对比 `/Users/.../superpowers/{new_version}/skills/` 和本文件"借鉴对照表"列出的 AionCode 资产
2. 评估是否有新内容值得本地化
3. 有则更新对应 AionCode 资产,同步更新本文件"借鉴对照表"和 `last_updated`

**不强求追新** — 我们只取精华,不跟全部。

## License

AionCode 本身的 License 见项目 `LICENSE` 文件。superpowers 借鉴部分继承其 MIT License 的开放性。
