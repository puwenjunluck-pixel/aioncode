# Credits

Aion 的纪律层（元认知 / spec 模板 / plan 模板 / 10-phase think / Verification Gate / 4-phase debugging）部分内容**基于 [Obra Works 的 superpowers 项目](https://github.com/obra/superpowers) 改编**并本地化（中文化 + `.aion/` 工件层注入 + Aion 工作流对齐）。

superpowers 采用 **MIT License**，允许本项目借鉴其设计和内容，我们在此声明来源以示尊重。

## 借鉴对照表

| Aion 资产 | 借鉴自 superpowers | 改编内容 |
|---|---|---|
| `skills/init/references/metacognition.md` | `using-superpowers` + `verification-before-completion` | Iron Laws / Red Flags / 合理化阻断表 — 中文化，关键英文打断语保留 |
| `skills/think/references/spec-template.md` | `brainstorming`（design 输出章节结构） | 融合 Aion 原 spec 格式（P0/P1/scope/frontmatter） |
| `skills/plan/references/plan-template.md` | `writing-plans`（bite-sized task 模板） | 融合 Aion 原 plan 格式 + TDD 节奏、No Placeholders 禁忌 |
| `skills/think` 10-phase 工作流 | `brainstorming` 9-step checklist | 新增 Phase 5「挑战」（Aion 独有）+ TodoWrite 驱动明确化 |
| `skills/review` Verification Gate | `verification-before-completion` | "Evidence before claims" + 声明→证据对照表本地化 |
| `skills/fix` 4-phase debugging | `systematic-debugging` | 复现→根因→修复→回归验证 + 红→绿证据强制化 |

## Aion 在此之上的原创增量

- **机械化提交门禁**（PreToolUse hook + `reviewed_files`/`base_commit` 集合校验）— prompt 约定升级为不可绕过的拦截
- **`.aion/` 工件闭环**（specs/plans/reviews/bugs/changelog 的版本化与 Write Protocol）
- **学习飞轮**（review 时提取规则 + cite_count 引用计数 + 60 天 stale 归档出口）
- **中文优先的完整方法论表述**
