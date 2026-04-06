---
category: pitfalls
rule_count: 11
last_updated: 2026-04-07
---

# Pitfalls — Known gotchas and traps

<!-- Rules are auto-extracted by /aion-review (auto-learn runs in every review).
Format:
- **{Title}** ({source}, {date}) [cite_count: {N}, last_cited: {date}]
  {1-2 sentence description with a concrete example from this project}

Each rule entry tracks:
  - cite_count: how many times this rule was referenced during reviews/learns
  - last_cited: the last date this rule was referenced
  - status: active | deprecated | archived (default: active)
Rules with no citations in 60+ days are flagged as "stale" by aion-status.
-->

- **uninstall.sh 命令列表必须与 profiles.py 同步** (scan, 2026-03-21, updated 2026-03-26) [cite_count: 0, last_cited: 2026-03-26]
  `uninstall.sh` 硬编码命令名用于删除，增删命令时必须同步更新删除列表，否则卸载后残留命令文件。当前核心命令（v0.7 架构）：aion-scan, aion-design, aion-plan, aion-review, aion-qa, aion-fix, aion-commit, aion-loop, aion-save, aion-help。每次命令体系变更后检查 `uninstall.sh`。

- **dashboard.py 路由匹配顺序敏感** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21, status: archived]
  v0.5 迁移至 FastAPI，旧 `dashboard.py`（4,749 行）于 v0.7.4 删除。此规则已归档。

- **NEVER 反向同步 .aion/ → templates/** (discussion, 2026-03-21) [cite_count: 0, last_cited: 2026-03-22]
  禁止将 `.aion/` 下的任何文件复制回 `templates/`。`templates/` 是产品模板（给所有用户的），`.aion/` 是本项目运行时数据（仅给自己的），数据流只能单向：`templates/` → `.aion/`。违反会导致所有新安装的用户继承 AionCode 自身的项目规则。**此规则无例外，无豁免，无 override。**

- **NEVER 同步 commands/ → .claude/commands/** (discussion, 2026-03-22) [cite_count: 1, last_cited: 2026-03-22]
  禁止执行任何将 `commands/*.md` 复制到 `.claude/commands/` 的操作（包括 `cp`、`rsync`、`shutil.copy` 等一切形式）。`commands/` 是源码，`.claude/commands/` 是运行版，二者必须隔离。违反此规则会导致 AI 工作流立刻失效。同步只能由用户自行执行。**此规则无例外，无豁免，无 override。**

- **NEVER 手动编辑 embedded.py** (save, 2026-03-22) [cite_count: 2, last_cited: 2026-03-26]
  `aioncode/internal/dashboard/embedded.py` 是由 `build_frontend.py` 从 `static/` 目录自动生成的文件。手动编辑会在下次构建时被覆盖。`ruff` 配置已 exclude 此文件。前端修改必须在 `static/` 目录中进行，然后运行构建脚本。

- **NEVER 忘记同步模板 config.yml 版本号** (save, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  `aioncode/internal/templates/aion/config.yml` 和 `templates/aion/config.yml` 的 `version` 字段必须与 `pyproject.toml` 和 `__init__.py` 同步更新。遗漏会导致新用户安装时拿到旧版本号，且 upgrade 逻辑无法正确检测版本差异。v0.5 曾因此遗留 version: "0.3"。

- **NEVER 在非 qa/scan-url 模式下调用浏览器自动化** (design, 2026-03-23, updated 2026-03-26) [cite_count: 1, last_cited: 2026-03-26]
  浏览器自动化仅允许在 `aion-qa` 和 `aion-scan --url` 两种模式下使用。支持两种后端：gstack browse CLI（优先，通过 Bash 调用）和 Playwright MCP（fallback）。在其他命令中触发浏览器操作会消耗大量 token 且超出作用域。**此规则无例外。**

- **commands/ + profiles.py ALL_COMMANDS 必须同步** (bugfix, 2026-03-26) [cite_count: 0, last_cited: 2026-03-26]
  增删命令时，`commands/` 源目录和 `aioncode/core/profiles.py` 的 `ALL_COMMANDS` + `ROLE_PRESETS` 必须同步更新。否则 `aioncode init` 会从 `commands/` 安装已废弃的命令文件，或 `profiles.py` 推荐不存在的命令。v0.6.8 曾因 `profiles.py` 未清理导致 `aion-learn`/`aion-status` 被 init 重装。

- **PyInstaller CI 构建必须显式安装 certifi** (bugfix, 2026-03-25) [cite_count: 0, last_cited: 2026-03-25]
  GitHub Actions CI 环境中 `certifi` 不在默认依赖中，`ssl.get_default_verify_paths().cafile` 在 Linux CI 上可能返回 `None`，导致 `aioncode.spec` 中 `(None, "certifi")` 元组使 PyInstaller 构建失败。`release.yml` 的 pip install 步骤必须包含 `certifi`。`aioncode.spec` 和 `network.py` 已加系统 CA 路径 fallback 防护。

- **写入 ~/.claude/settings.json 必须保留现有字段** (review, 2026-03-28) [cite_count: 0, last_cited: 2026-03-28]
  `switch_model()` 读取完整 settings.json → 修改目标字段 → 写回全量 JSON。绝不能只写入部分字段，否则会丢失用户的 permissions、hooks、statusLine 等配置。写入时使用 `json.dumps(data, indent=2)` 保持格式。

- **CC 第三方模型必须同时设置所有 model-family env vars** (bugfix, 2026-03-29) [cite_count: 0, last_cited: 2026-03-29]
  切换到第三方 Provider 时，仅设 `ANTHROPIC_MODEL` 会触发 CC 内置模型名白名单校验并报错"There's an issue with the selected model"。必须同时设置 `ANTHROPIC_SMALL_FAST_MODEL`、`ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_DEFAULT_OPUS_MODEL`、`ANTHROPIC_DEFAULT_HAIKU_MODEL` 五个 vars，CC 才会跳过校验直接使用。参考：cc-switch 最佳实践。

- **CC hot-reload 无法 unset env vars，清除需用空字符串** (bugfix, 2026-03-29) [cite_count: 0, last_cited: 2026-03-29]
  切回官方 Anthropic 时不能用 `pop()` 删除 env 字段——运行中的 CC 进程已将 env var 注入进程环境，从 settings.json 中删除字段只影响下次启动，无法影响当前进程。需将字段设为 `""` 空字符串；CC JS 层以 falsy 判断（`if (baseUrl)`），空字符串等效未设置，无需重启立即生效。

- **CC daemon 将 env vars 广播给所有会话，settings.local.json 无法项目级隔离** (bugfix, 2026-03-29) [cite_count: 0, last_cited: 2026-03-29]
  Claude Code 所有打开的会话共用同一 daemon 进程。任何项目的 `.claude/settings.local.json` 中 env 变化都会立即广播给所有已连接会话——包括其他项目的终端窗口。模型切换不存在"只影响当前项目"的运行时隔离，应使用全局 `~/.claude/settings.json`，并在 UI 上说明切换是全局生效。

- **upgrade 路径必须从 config 恢复完整 profile（含 platform）** (review, 2026-04-07) [cite_count: 0, last_cited: 2026-04-07]
  `init.py` upgrade 分支在无新命令时曾跳过 profile 构建，导致 `project.py` 使用 DEFAULT_PLATFORM 默认值。Antigravity 用户升级时命令会错误安装到 `.claude/commands/`。修复：始终从 `read_profile()` 结果构建 InitProfile，即使命令列表未变化。
