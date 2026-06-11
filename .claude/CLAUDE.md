# Aion Plugin — Project Intelligence (dogfood)

## 本仓库是什么
Aion 插件源码仓库（dogfooding 自身）。产品本体 = `skills/` + `hooks/` + `scripts/`。
旧形态（Python CLI + Dashboard + 多平台 init）已于 2026-06-12 封存：tag `v0.7.6-final` / branch `archive/v0.7-cli`。战略决策见 `.aion/specs/contraction-to-plugin.md`。

## Rules (MANDATORY)
NEVER write or edit any file without first reading ALL rules in `.aion/rules/`. This is non-negotiable.

**`.aion/rules/metacognition.md` 是元规则** — 元认知 / 反合理化 / Verification Gate / Iron Laws。每次动作前生效。

## Source layout
- `skills/<name>/SKILL.md` — 9 个命令源（这就是产品；`skills/think/SKILL.md` 是格式范本）
- `skills/*/references/` — 随 skill 分发的模板与协议（spec/plan/write-protocol/metacognition）
- `hooks/hooks.json` + `scripts/*.sh` — 安全 hook + commit 门禁 hook
- `.claude-plugin/` — 插件与 marketplace 清单
- `.aion/` — 本仓库自身的工件层（specs/plans/reviews/bugs/changelog）

## Key rules
- NEVER commit without a review file in `.aion/reviews/`（frontmatter 必含 `reviewed_files` + `base_commit`）— 本仓库 hooks 已机械强制
- 验证三件套，改动后必跑：`bash tests/hook/test_check_review.sh && bash tests/hook/test_safety_check.sh && claude plugin validate .`
- 死引用断言：`grep -rn "PLATFORM:\|/project:\|aion-help\|aion-loop\|aion-audit" skills/` 必须 0 命中
- 3+ 文件改动先对齐获批（spec/plan 或用户明示）再实现
- skill 文案中文为主；frontmatter description 必含触发条件 + 负面范围（"Not for…"）
