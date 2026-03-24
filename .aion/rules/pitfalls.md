---
category: pitfalls
rule_count: 7
last_updated: 2026-03-24
---

# Pitfalls — Known gotchas and traps

<!-- Rules are auto-extracted by /aion-learn and /aion-review.
Format:
- **{Title}** ({source}, {date}) [cite_count: {N}, last_cited: {date}]
  {1-2 sentence description with a concrete example from this project}

Each rule entry tracks:
  - cite_count: how many times this rule was referenced during reviews/learns
  - last_cited: the last date this rule was referenced
  - status: active | deprecated | archived (default: active)
Rules with no citations in 60+ days are flagged as "stale" by aion-status.
-->

- **uninstall.sh 命令列表不完整** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21]
  `uninstall.sh` 硬编码了 11 个命令名用于删除，但实际已有 18 个命令。新增命令时必须同步更新 `uninstall.sh` 的删除列表，否则卸载后残留命令文件。缺失：aion-scan, aion-demo, aion-test, aion-bug, aion-crosscheck, aion-upgrade, aion-help。

- **dashboard.py 路由匹配顺序敏感** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21, status: deprecated]
  ~~v0.5 已迁移至 FastAPI 路径参数，此问题不再存在。旧 `dashboard.py` 已删除。~~

- **NEVER 反向同步 .aion/ → templates/** (discussion, 2026-03-21) [cite_count: 0, last_cited: 2026-03-22]
  禁止将 `.aion/` 下的任何文件复制回 `templates/`。`templates/` 是产品模板（给所有用户的），`.aion/` 是本项目运行时数据（仅给自己的），数据流只能单向：`templates/` → `.aion/`。违反会导致所有新安装的用户继承 AionCode 自身的项目规则。**此规则无例外，无豁免，无 override。**

- **NEVER 同步 commands/ → .claude/commands/** (discussion, 2026-03-22) [cite_count: 1, last_cited: 2026-03-22]
  禁止执行任何将 `commands/*.md` 复制到 `.claude/commands/` 的操作（包括 `cp`、`rsync`、`shutil.copy` 等一切形式）。`commands/` 是源码，`.claude/commands/` 是运行版，二者必须隔离。违反此规则会导致 AI 工作流立刻失效。同步只能由用户自行执行。**此规则无例外，无豁免，无 override。**

- **NEVER 手动编辑 embedded.py** (save, 2026-03-22) [cite_count: 1, last_cited: 2026-03-24]
  `aioncode/internal/dashboard/embedded.py` 是由 `build_frontend.py` 从 `static/` 目录自动生成的文件。手动编辑会在下次构建时被覆盖。`ruff` 配置已 exclude 此文件。前端修改必须在 `static/` 目录中进行，然后运行构建脚本。

- **NEVER 忘记同步模板 config.yml 版本号** (save, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  `aioncode/internal/templates/aion/config.yml` 和 `templates/aion/config.yml` 的 `version` 字段必须与 `pyproject.toml` 和 `__init__.py` 同步更新。遗漏会导致新用户安装时拿到旧版本号，且 upgrade 逻辑无法正确检测版本差异。v0.5 曾因此遗留 version: "0.3"。

- **NEVER 在非 e2e/scan-url 模式下调用 Playwright 浏览器自动化** (design, 2026-03-23) [cite_count: 1, last_cited: 2026-03-24]
  Playwright 浏览器自动化仅允许在 `aion-test e2e` 和 `aion-scan --url` 两种模式下使用，且必须通过 Playwright MCP 控制（非直接 subprocess 调用）。在其他模式（unit/coverage/perf/ui）中触发浏览器操作会消耗大量 token 且超出作用域。MCP 提供安全代理层和超时保护。**此规则无例外。**
