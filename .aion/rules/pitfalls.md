---
category: pitfalls
rule_count: 4
last_updated: 2026-03-22
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

- **dashboard.py 路由匹配顺序敏感** (scan, 2026-03-21) [cite_count: 0, last_cited: 2026-03-21]
  `do_GET()`/`do_POST()` 使用 `path.startswith()` 前缀匹配路由。具体路由（如 `/api/projects/{id}/bugs/stats`）必须在通用路由（如 `/api/projects/{id}/stats`）之前检查，否则通用路由会"吃掉"请求。新增 API 端点时必须注意插入位置。

- **NEVER 反向同步 .aion/ → templates/** (discussion, 2026-03-21) [cite_count: 0, last_cited: 2026-03-22]
  禁止将 `.aion/` 下的任何文件复制回 `templates/`。`templates/` 是产品模板（给所有用户的），`.aion/` 是本项目运行时数据（仅给自己的），数据流只能单向：`templates/` → `.aion/`。违反会导致所有新安装的用户继承 AionCode 自身的项目规则。**此规则无例外，无豁免，无 override。**

- **NEVER 同步 commands/ → .claude/commands/** (discussion, 2026-03-22) [cite_count: 0, last_cited: 2026-03-22]
  禁止执行任何将 `commands/*.md` 复制到 `.claude/commands/` 的操作（包括 `cp`、`rsync`、`shutil.copy` 等一切形式）。`commands/` 是源码，`.claude/commands/` 是运行版，二者必须隔离。违反此规则会导致 AI 工作流立刻失效。同步只能由用户自行执行。**此规则无例外，无豁免，无 override。**
