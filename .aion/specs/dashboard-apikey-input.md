---
status: completed
created_at: 2026-03-29
version: 1
author: unknown
scope: web
change_reason: null
---

# Dashboard — 内联 API Key 输入

## Goal
模型配置页切换第三方 Provider 时，若 API Key 环境变量未设置，允许用户直接在界面输入 Key 完成切换，无需回终端设置环境变量。

## Requirements (P0)
- 点击 model chip 且 env var 未设置 → 原地展开 key 输入框（非 alert/prompt）
- 用户输入 key 确认后，key 随 switch-model 请求传给后端（api_key_override 字段）
- 后端 switch_model 接受可选 api_key_override，优先于 os.environ 读取
- key 写入 {project}/.claude/settings.local.json，不写 team.yml
- 已设置 env var 时点击 chip → 直接切换，行为不变
- toast 提示"已切换到 xxx"，不提"重启"

## Requirements (P1)
- 输入框默认 type=password，支持显示/隐藏切换
- 显示提示：key 仅保存在本项目 settings.local.json，不会上传或提交 git

## Acceptance Criteria
- env 未设置时点击 chip → 出现输入框，不报错
- 输入 key 提交 → 切换成功，settings.local.json 包含 ANTHROPIC_API_KEY
- env 已设置时 → 直接切换成功
- team.yml 始终不含裸 key

## Constraints
- key 不存 localStorage / sessionStorage
- 仅涉及 3 个文件：services/team.py、routers/team.py、models.js
