# Changelog

<!-- AionCode auto-appends entries here. Do not remove this file. -->

## 2026-03-21 22:00 | feat: Write Protocol + Dashboard 日志/帮助中心 + 升级机制重构

### Summary
- 设计并实现 Write Protocol 统一写入保护协议（四类文件分级保护 + Refusal Condition + Fingerprint + Scope 冲突检测）
- 修复 aion-learn 边界问题（Evidence Gate：证据源全空时返回 BLOCKED，不越界做全量扫描）
- 修复 aion-scan（FIRST_SCAN/RE_SCAN 双模式 + Delta Report）
- 修复 aion-design（新增 Step 3.5 版本检查 + scope 冲突）
- 修复 aion-test（Regenerable fingerprint 保护）
- 重写 uninstall.sh（动态扫描命令、CLAUDE.md 只删标记区域、hooks/settings 备份、防误卸载确认）
- Dashboard 新增日志中心（Changelog/Sessions/Events 三源聚合）
- Dashboard 新增帮助中心（使用说明 + 更新日志）
- 最佳实践页面重构为角色/场景导向，去命令化
- 升级机制：dashboard.py + uninstall.sh 纳入 .aion/bin/ 统一管理
- 版本升至 v0.3

### Key Decisions
- Write Protocol 四类文件：Accumulative / Versioned / Regenerable / Unique-by-ID
- learn 的范围严格限定为增量经验，全量扫描是 scan 的职责
- Versioned 文件必须声明 scope（api/web/mobile/infra/full），不同 scope 同名文件强制换名
- Regenerable 文件用 MD5 fingerprint 检测用户修改
- uninstall.sh 需输入"aioncode"确认，防误操作
- .aion/bin/ 作为工具目录，安装/升级时无条件覆盖
- 仓库将公开，通过 GitHub Releases 分发 tarball
- v0.4 目标：Python 重写脚本实现跨平台（Windows 支持）

### Files Changed
- 新增: templates/aion/refs/write-protocol.md
- 修改: commands/aion-learn.md, aion-scan.md, aion-design.md, aion-test.md, aion-plan.md, aion-save.md
- 修改: dashboard.py（日志中心 + 帮助中心 + 最佳实践重构 + changelog API）
- 重写: uninstall.sh（安全卸载）
- 修改: install.sh（.aion/bin/ 复制 + Dashboard 提示）
- 修改: README.md（路径更新）
- 修改: templates/aion/config.yml（v0.2 → v0.3）
- 新增: .aion/refs/architecture.md, api-inventory.md（scan 产物）
- 新增: .aion/specs/refactor-targets.md（scan 产物）
- 新增: .aion/rules/ 初始规则（2 style + 3 pitfalls）

### Pending
- 创建 GitHub 公开仓库，首次提交
- 编写 build.sh / install-remote.sh / upgrade.sh（远程安装/升级）
- v0.4: Python 重写 install/upgrade/uninstall 实现 Windows 支持

---

## 2026-03-21 20:30 | enhance: aion-save 完成后提醒执行 aion-learn

### Summary
- 讨论了在何处提醒用户执行 /aion-learn 以避免遗忘
- 评估了 review/commit/verify/save 等多个触发时机
- 决定在 aion-save 完成后添加条件性提示

### Key Conclusions
- aion-save 是最自然的触发点：用户已在做"沉淀"动作，心智负担最小
- 条件性提示（涉及代码变更时才建议），避免提醒疲劳

### Files Changed
- commands/aion-save.md — Next Steps 末尾新增 learn 提示语

---

## 2026-03-21 17:00 | feat: Bug 追踪系统 + 交叉验证 + 版本升级

### Summary
- 设计并实现了完整的 Bug 追踪与团队协作系统
- 新增 3 个命令：aion-bug、aion-crosscheck、aion-upgrade
- 增强 6 个命令：aion-save（三层持久化）、aion-impl/verify/commit/status/help
- 实现版本升级机制（install.sh --upgrade + Dashboard UI + /aion-upgrade）
- 重写 install.sh：预检 + CLAUDE.md marker 合并 + 安装报告
- Dashboard 新增 Bug 看板页面、团队管理页面、7 个新 API

### Key Decisions
- Bug ID 格式：`{F|B|X}-{MMDD}-{SEQ}`，分类即分配
- git blame + team.yml 自动识别 Bug 责任人
- 交叉验证（/aion-crosscheck）与 Bug 管理（/aion-bug）完全解耦
- aion-save 三层持久化：.aion/ + CLAUDE.md + Claude memory
- CLAUDE.md 使用 markers 合并，永不覆盖用户内容
- 版本号从 0.1 升至 0.2

### Files Changed
- 新增: commands/aion-bug.md, aion-crosscheck.md, aion-upgrade.md
- 新增: templates/aion/team.yml
- 修改: commands/aion-save.md, aion-impl.md, aion-verify.md, aion-commit.md, aion-status.md, aion-help.md
- 修改: templates/CLAUDE.md.tpl, templates/aion/config.yml
- 修改: install.sh (重写), dashboard.py (Bug 看板+团队管理+升级)
- 修改: docs/aion-design.md, docs/commands.md
- 命令总数: 15 → 18

### Pending
- 在实际项目中验证 Bug 工作流（report → assign → impl → close）
- 交叉验证需配置第三方模型 API key 才能测试
- 云端部署方案待后续讨论
