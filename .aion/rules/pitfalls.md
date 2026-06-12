---
category: pitfalls
rule_count: 5
last_updated: 2026-06-12
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
Rules with no citations in 60+ days are flagged as "stale" by `bash scripts/rules-status.sh`（机械扫描）.
-->

- **plugin.json 不要声明标准自动加载位置（skills/、hooks/hooks.json）** (review, 2026-06-12) [cite_count: 1, last_cited: 2026-06-12]
  Claude Code 自动发现 `skills/` 与自动加载 `hooks/hooks.json`。在 plugin.json 的 `skills`/`hooks` 字段里再显式声明它们会触发运行时「Duplicate hooks file detected」并使**整个插件加载失败**。manifest 只应是元数据 + 指向**额外**（非标准位置）的文件。**关键教训：`claude plugin validate` 只校验 manifest schema 合法性，不模拟运行时加载——validate 通过 ≠ 插件能装**。v0.8.0 因此发布即坏，第一次真人 `/plugin install` 才暴露（`claude plugin list` 显示 `failed to load`）。对照标准：superpowers 的 plugin.json 只有元数据，零 skills/hooks 字段。验收新插件必须以 `claude plugin list` 状态为准，不能只信 validate。

- **uninstall.sh 命令列表必须与 profiles.py 同步** (scan, 2026-03-21, updated 2026-03-26) [cite_count: 0, last_cited: 2026-03-26, status: archived]
  `uninstall.sh` 硬编码命令名用于删除，增删命令时必须同步更新删除列表，否则卸载后残留命令文件。当前核心命令（v0.7 架构）：aion-scan, aion-think, aion-plan, aion-review, aion-qa, aion-fix, aion-commit, aion-loop, aion-save, aion-help。每次命令体系变更后检查 `uninstall.sh`。v0.8 插件化后 `uninstall.sh` 与 `profiles.py` 均已删除，该规则归档。

- **命令 rename 必须跨层扫描七件套** (review, 2026-04-14, updated 2026-06-12) [cite_count: 2, last_cited: 2026-06-12]
  rename 一个 `aion:*` 命令时,grep 需覆盖 7 层(插件形态),少一层就会留下死引用:(1) `skills/*/SKILL.md` 与各自 `references/`;(2) `skills/init/references/claude-md-section.md` 命令表;(3) `README.md` 命令表;(4) `MIGRATION.md` 映射表;(5) `.claude-plugin/` 清单;(6) CI 的死引用 grep 清单;(7) `.aion/` 本仓库工件。Verify:`grep -rn "aion:{旧名}" skills/ README.md MIGRATION.md` 必须为 0。v0.7.6 surgical fusion 第一轮 review 只查了 `.aion/` 和 `commands/`,漏掉 6 层,Iron Law 2 反面教材。

- **dashboard.py 路由匹配顺序敏感** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21, status: archived]
  v0.5 迁移至 FastAPI，旧 `dashboard.py`（4,749 行）于 v0.7.4 删除。此规则已归档。

- **NEVER 反向同步 .aion/ → templates/** (discussion, 2026-03-21) [cite_count: 0, last_cited: 2026-03-22, status: archived]
  禁止将 `.aion/` 下的任何文件复制回 `templates/`。`templates/` 是产品模板（给所有用户的），`.aion/` 是本项目运行时数据（仅给自己的），数据流只能单向：`templates/` → `.aion/`。违反会导致所有新安装的用户继承 AionCode 自身的项目规则。**此规则无例外，无豁免，无 override。** v0.8 插件化后 templates/ 目录已删除，该规则归档。

- **NEVER 同步 commands/ → .claude/commands/** (discussion, 2026-03-22) [cite_count: 1, last_cited: 2026-03-22, status: archived]
  禁止执行任何将 `commands/*.md` 复制到 `.claude/commands/` 的操作（包括 `cp`、`rsync`、`shutil.copy` 等一切形式）。`commands/` 是源码，`.claude/commands/` 是运行版，二者必须隔离。违反此规则会导致 AI 工作流立刻失效。同步只能由用户自行执行。**此规则无例外，无豁免，无 override。** v0.8 插件化后 `commands/` 与 `.claude/commands/` 安装机制均已删除，该规则归档。

- **NEVER 手动编辑 embedded.py** (save, 2026-03-22) [cite_count: 2, last_cited: 2026-03-26, status: archived]
  `aioncode/internal/dashboard/embedded.py` 是由 `build_frontend.py` 从 `static/` 目录自动生成的文件。手动编辑会在下次构建时被覆盖。`ruff` 配置已 exclude 此文件。前端修改必须在 `static/` 目录中进行，然后运行构建脚本。v0.8 插件化后 Dashboard 与 embedded.py 已删除，该规则归档。

- **NEVER 忘记同步模板 config.yml 版本号** (save, 2026-03-22, updated 2026-04-14) [cite_count: 2, last_cited: 2026-04-14, status: archived]
  `aioncode/internal/templates/aion/config.yml` 的 `version` 字段必须与 `pyproject.toml` 和 `__init__.py` 同步更新。遗漏会导致新用户安装时拿到旧版本号,且 upgrade 逻辑无法正确检测版本差异。v0.5 曾因此遗留 version: "0.3";v0.7.6 bump 时同一坑再次触发(templates 留在 0.7.5),是 dogfood 运行 `aioncode init` 自我升级时才抓到。**bump 版本 checklist**:pyproject.toml + aioncode/__init__.py + aioncode/internal/templates/aion/config.yml 三处必须一次性改完。注:v0.7.6 同时删除了根目录废弃的 `templates/`(与真实包漂移严重),后续只需维护 `aioncode/internal/templates/`。v0.8 插件化后 templates 已删除，版本号唯一来源为 `.claude-plugin/plugin.json`，该规则归档。

- **NEVER 在非 qa/scan-url 模式下调用浏览器自动化** (design, 2026-03-23, updated 2026-06-12) [cite_count: 2, last_cited: 2026-06-12]
  浏览器自动化仅允许在 `/aion:qa` 与 `/aion:scan --url` 两种模式下使用。支持两种后端：gstack browse CLI（优先，通过 Bash 调用）和 Playwright MCP（fallback）。在其他命令中触发浏览器操作会消耗大量 token 且超出作用域。**此规则无例外。**

- **commands/ + profiles.py ALL_COMMANDS 必须同步** (bugfix, 2026-03-26) [cite_count: 0, last_cited: 2026-03-26, status: archived]
  增删命令时，`commands/` 源目录和 `aioncode/core/profiles.py` 的 `ALL_COMMANDS` + `ROLE_PRESETS` 必须同步更新。否则 `aioncode init` 会从 `commands/` 安装已废弃的命令文件，或 `profiles.py` 推荐不存在的命令。v0.6.8 曾因 `profiles.py` 未清理导致 `aion-learn`/`aion-status` 被 init 重装。v0.8 插件化后 `commands/` 与 `profiles.py` 均已删除，该规则归档。

- **PyInstaller CI 构建必须显式安装 certifi** (bugfix, 2026-03-25) [cite_count: 0, last_cited: 2026-03-25, status: archived]
  GitHub Actions CI 环境中 `certifi` 不在默认依赖中，`ssl.get_default_verify_paths().cafile` 在 Linux CI 上可能返回 `None`，导致 `aioncode.spec` 中 `(None, "certifi")` 元组使 PyInstaller 构建失败。`release.yml` 的 pip install 步骤必须包含 `certifi`。`aioncode.spec` 和 `network.py` 已加系统 CA 路径 fallback 防护。v0.8 插件化后已无 PyInstaller 二进制分发，该规则归档。

- **写入 ~/.claude/settings.json 必须保留现有字段** (review, 2026-03-28) [cite_count: 0, last_cited: 2026-03-28, status: archived]
  `switch_model()` 读取完整 settings.json → 修改目标字段 → 写回全量 JSON。绝不能只写入部分字段，否则会丢失用户的 permissions、hooks、statusLine 等配置。写入时使用 `json.dumps(data, indent=2)` 保持格式。v0.8 插件化后 Dashboard 及其 settings.json 写入逻辑已删除，该规则归档。

- **CC 第三方模型必须同时设置所有 model-family env vars** (bugfix, 2026-03-29) [cite_count: 0, last_cited: 2026-03-29, status: archived]
  切换到第三方 Provider 时，仅设 `ANTHROPIC_MODEL` 会触发 CC 内置模型名白名单校验并报错"There's an issue with the selected model"。必须同时设置 `ANTHROPIC_SMALL_FAST_MODEL`、`ANTHROPIC_DEFAULT_SONNET_MODEL`、`ANTHROPIC_DEFAULT_OPUS_MODEL`、`ANTHROPIC_DEFAULT_HAIKU_MODEL` 五个 vars，CC 才会跳过校验直接使用。参考：cc-switch 最佳实践。v0.8 插件化后模型切换功能已删除，该规则归档。

- **CC hot-reload 无法 unset env vars，清除需用空字符串** (bugfix, 2026-03-29) [cite_count: 0, last_cited: 2026-03-29, status: archived]
  切回官方 Anthropic 时不能用 `pop()` 删除 env 字段——运行中的 CC 进程已将 env var 注入进程环境，从 settings.json 中删除字段只影响下次启动，无法影响当前进程。需将字段设为 `""` 空字符串；CC JS 层以 falsy 判断（`if (baseUrl)`），空字符串等效未设置，无需重启立即生效。v0.8 插件化后模型切换功能已删除，该规则归档。

- **CC daemon 将 env vars 广播给所有会话，settings.local.json 无法项目级隔离** (bugfix, 2026-03-29) [cite_count: 0, last_cited: 2026-03-29, status: archived]
  Claude Code 所有打开的会话共用同一 daemon 进程。任何项目的 `.claude/settings.local.json` 中 env 变化都会立即广播给所有已连接会话——包括其他项目的终端窗口。模型切换不存在"只影响当前项目"的运行时隔离，应使用全局 `~/.claude/settings.json`，并在 UI 上说明切换是全局生效。v0.8 插件化后模型切换功能已删除，该规则归档。

- **发布前必须扫查 docs/ 与非打包目录的过时引用** (save, 2026-04-14, updated 2026-06-12) [cite_count: 1, last_cited: 2026-06-12]
  命令体系演进后,`README.md` / `MIGRATION.md` / `CHANGELOG.md` / `CREDITS.md` 等面向用户的文档层容易被漏改 —— 因为它们不影响 skill 加载与 CI 测试,自动化检查不一定发现。v0.7.6 差点带着 4 个仍写 `/project:aion-design` 的 docs 文件 tag 发布。**发布 checklist**:tag 前执行 `grep -rn "aion:{旧命令名}" README.md MIGRATION.md CHANGELOG.md CREDITS.md` 必须为 0。

- **upgrade 路径必须从 config 恢复完整 profile（含 platform）** (review, 2026-04-07) [cite_count: 0, last_cited: 2026-04-07, status: archived]
  `init.py` upgrade 分支在无新命令时曾跳过 profile 构建，导致 `project.py` 使用 DEFAULT_PLATFORM 默认值。Antigravity 用户升级时命令会错误安装到 `.claude/commands/`。修复：始终从 `read_profile()` 结果构建 InitProfile，即使命令列表未变化。v0.8 插件化后 upgrade 路径与 init 安装器已删除，该规则归档。

- **hook 脚本的对抗面必须用变体用例测试** (review, 2026-06-12) [cite_count: 1, last_cited: 2026-06-12]
  红队实测发现 `fix(bug):` 子串豁免、双空格 `git  commit`、`-va` 捆绑旗标、`rm -fr` 旗标反序等绕过,全部存在于教科书用例全过的测试套件之外。hook 类脚本的测试必须包含四类对抗用例:旗标反序、旗标捆绑、空白变体、prose 误杀。
