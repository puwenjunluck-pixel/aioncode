---
status: completed
created_at: 2026-03-22
version: 1
scope: web
---

# Dashboard 细节完善：版本号 + 关于页更新

## Goal
底栏显示动态版本号，关于页命令列表补全。

## Requirements (P0)
1. 底栏右下角 "AionCode" 改为 "AionCode v{version}"，版本号从后端 API 动态获取
2. 关于页命令速查表补全缺失的 4 个命令：aion-loop、aion-status、aion-upgrade、aion-learn

## Acceptance Criteria
- 底栏显示真实版本号（如 "AionCode v0.5.0"），不是硬编码
- 关于页命令表包含全部 18 个命令
- 切换项目后版本号保持正确

## Constraints
- 版本号来源：后端 DASHBOARD_VERSION（读自 aioncode.__version__）
- 不新增独立 API 端点，复用现有 stats API 附带返回
