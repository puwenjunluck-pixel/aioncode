# Changelog

## 0.8.1 (2026-06-12)

### Fixed
- **插件加载失败（发布即坏）**：plugin.json 误声明了 `skills` 与 `hooks` 字段——二者是 Claude Code 标准自动加载位置，显式声明触发运行时「Duplicate hooks file detected」使整个插件 `failed to load`。改为纯元数据 manifest（对齐 superpowers 惯例）。`claude plugin validate` 只校验 schema 不模拟加载，故未提前抓到；第一次真人 `/plugin install` 暴露。

## 0.8.0 (2026-06-12)

**形态重生：CLI → Claude Code 插件。** 战略背景见 `.aion/specs/contraction-to-plugin.md`。

### Added
- 9 个 skills：`/aion:init` `/aion:scan` `/aion:think` `/aion:plan` `/aion:fix` `/aion:qa` `/aion:review` `/aion:commit` `/aion:save`
- **提交门禁 hook**（`scripts/check-review.sh`）：无 approved review 覆盖（`reviewed_files` ⊇ staged 且 `base_commit` == HEAD）的 `git commit` 被机械 deny；豁免 `fix(bug):` 原子修复、纯 `.aion/` 提交、非 Aion 项目；fail-open 设计
- **安全 hook**（`scripts/safety-check.sh`）：拦截 `rm -rf /`、force push、`git reset --hard` 等危险命令
- `/aion:init`：替代 CLI init——创建 `.aion/`、安装元认知规则到 `.claude/rules/`、标记式合并 CLAUDE.md（幂等）
- review 报告 frontmatter 新增 `reviewed_files` + `base_commit`（供门禁机械校验）
- 学习飞轮出口：cite_count 为 0 且 60 天未引用的规则在 review 时建议归档

### Changed
- `aion-audit` 并入 `/aion:review --deep`（全项目安全+性能审计）
- `/aion:scan` 蒸馏：与原生 `/init` 重叠的冷启动部分移除，保留产品全景 / 规则种子 / E2E 定义
- `/aion:save` 蒸馏为工件落盘薄壳（跨会话记忆交给原生 auto memory）
- `/aion:plan` 修复内部矛盾：统一 bite-sized 格式（完整代码块 + Verify），落盘后 Handoff 询问执行方式
- 纪律层文件（metacognition / spec-template / plan-template / write-protocol）随插件分发（旧版漏分发）

### Removed（BREAKING）
- Python CLI 二进制（init/upgrade/doctor/dashboard/install/uninstall/clean）与三平台发布
- Web Dashboard 全栈
- Google Antigravity 多平台支持与 `<!-- PLATFORM -->` 裁剪机制
- `aion-help`（原生 `/help` 接管）、`aion-loop`（原生 background tasks / agent teams 接管）

旧形态完整封存：tag `v0.7.6-final` / branch `archive/v0.7-cli`。迁移指南：[MIGRATION.md](MIGRATION.md)。

---

更早版本（v0.4–v0.7.6，CLI 时代）的历史见 `.aion/changelog.md` 与 `archive/v0.7-cli` 分支。
