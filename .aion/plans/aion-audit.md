---
status: completed
created_at: 2026-04-06
spec: aion-audit.md
version: 1
previous_version: null
change_reason: null
author: wayne
scope: full
current_step: 3
total_steps: 3
---

# Plan: aion-audit — 安全+性能审计

## Architecture Decisions
- 纯 prompt 命令（.md 文件），Python 仅 profiles.py 注册
- 报告存放 `.aion/audits/{date}.md`，独立于 `.aion/reviews/`
- 评分体系：Security (0-100) + Performance (0-100) + Overall (加权 60/40)
- uninstall.sh 使用动态 find，无需手动同步

## Implementation Steps

### Step 1: 创建 commands/aion-audit.md
- **What**: 编写完整的 aion-audit 命令文件
- **Files**: 新建 `commands/aion-audit.md`
- **How**: 统一命令结构，5 步流程（上下文→扫描→评分→基线对比→规则联动→写报告），安全 5 维度（S1-S5）+ 性能 5 维度（P1-P5），Rationalization Prevention 表
- **Verify**: `wc -l` < 500，包含全部结构段落
- **Dependencies**: None
- **Complexity**: large
- **Status**: Done

### Step 2: 更新 profiles.py
- **What**: 注册 aion-audit 到 ALL_COMMANDS 和 ROLE_PRESETS
- **Files**: `aioncode/core/profiles.py`
- **How**: ALL_COMMANDS 末尾新增 CommandInfo，backend/fullstack ROLE_PRESETS 增加 aion-audit
- **Verify**: `python3.11 -c "from aioncode.core.profiles import ALL_COMMANDS; print(len(ALL_COMMANDS))"` 输出 11
- **Dependencies**: None
- **Complexity**: small
- **Status**: Done

### Step 3: 验证完整性
- **What**: 端到端检查
- **Files**: 无新增修改
- **How**: 确认行数 < 500，ALL_COMMANDS = 11，命令文件结构完整
- **Verify**: 三项检查全部通过
- **Dependencies**: Steps 1, 2
- **Complexity**: small
- **Status**: Done

## Verification Strategy
- **Method**: manual_check
- **Coverage**: 命令文件结构、行数上限、profiles 注册
- **Commands**: `wc -l commands/aion-audit.md` + `python3.11 -c "from aioncode.core.profiles import ALL_COMMANDS; print(len(ALL_COMMANDS))"`
- **Success criteria**: 278 行 < 500，ALL_COMMANDS = 11

## Risks
- 行数：278 行，远低于 500 上限，无风险
