# 从 AionCode CLI（≤ v0.7.6）迁移到 Aion 插件

v0.8.0 起，AionCode 从「CLI 二进制 + Dashboard」收缩为纯 Claude Code 插件 **Aion**。旧形态封存于 tag `v0.7.6-final` / branch `archive/v0.7-cli`，不再维护。

## 迁移步骤（每个项目约 2 分钟）

1. **安装插件**：
   ```
   /plugin marketplace add puwenjunluck-pixel/aioncode
   /plugin install aion@aion-marketplace
   ```
2. **删除旧命令文件**（避免与插件命令重复出现）：
   ```bash
   rm -f .claude/commands/aion-*.md
   ```
3. **在项目里跑 `/aion:init`**：幂等升级——元认知规则装进 `.claude/rules/`、CLAUDE.md 的 AionCode 段落更新为新命令名。
4. **卸载旧二进制**（所有项目迁移完后）：
   ```bash
   rm /usr/local/bin/aioncode        # macOS/Linux
   del C:\Windows\aioncode.exe       # Windows
   ```

## 你的数据不受影响

`.aion/` 目录（rules/specs/plans/reviews/bugs/changelog）**格式完全兼容**，插件直接继续使用。规则的引用计数、spec 版本归档历史全部保留。

## 命令名映射

| 旧（≤ v0.7.6） | 新（v0.8+） |
|---|---|
| `/project:aion-think` | `/aion:think` |
| `/project:aion-plan` | `/aion:plan` |
| `/project:aion-scan` | `/aion:scan` |
| `/project:aion-review` | `/aion:review` |
| `/project:aion-audit` | `/aion:review --deep`（并入） |
| `/project:aion-qa` | `/aion:qa` |
| `/project:aion-fix` | `/aion:fix` |
| `/project:aion-commit` | `/aion:commit` |
| `/project:aion-save` | `/aion:save`（仅工件落盘；记忆交给原生 memory） |
| `/project:aion-help` | 移除 — 用原生 `/help`（插件命令自动列出） |
| `/project:aion-loop` | 移除 — 用原生 background tasks / agent teams |
| `aioncode init`（CLI） | `/aion:init` |
| `aioncode dashboard` | 移除 — `.aion/` 是纯 markdown，编辑器/GitHub 直接看 |
| `aioncode upgrade` | `/plugin update aion@aion-marketplace` |

## 新增能力（旧版没有的）

- **提交门禁 hook**：无 approved review 覆盖的 `git commit` 被机械 deny（旧版只是 prompt 约定）
- **安全 hook**：`rm -rf /`、force push 等危险命令被拦截
- **review 报告新 frontmatter**：`reviewed_files` + `base_commit`（门禁 hook 消费；旧 review 文件不受影响，但新提交需要新格式的 review）
