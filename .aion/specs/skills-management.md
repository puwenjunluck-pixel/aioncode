---
title: Skills 管理视图
status: completed
source: retroactive-save
created_at: 2026-03-22
---

# Skills 管理视图

> 追溯性 spec — 功能已实现，此文档基于实际代码变更生成。

## 功能概述

Dashboard 新增「技能」视图，提供 Claude Code skill 的可视化管理能力。

## 核心能力

1. **已安装 skill 浏览** — 读取 `~/.claude/skills/` 解析 SKILL.md frontmatter，按来源分组（用户/代理）
2. **官方市场浏览** — 读取 `~/.claude/plugins/marketplaces/` 的 plugin.json，标记已安装状态
3. **一键卸载** — 已安装 skill 详情页标题右侧卸载按钮（`DELETE /api/skills/{name}`）
4. **一键安装** — 官方市场未安装插件标题右侧安装按钮（`POST /api/skills/marketplace/install`，调用 `claude plugin add`）

## 内置 Skill 打包

`aioncode init` 自动安装两个基础 skill 到 `~/.claude/skills/`（绝不覆盖已有）：
- **find-skills** — 原样复制第三方版，包装 `npx skills find/add`
- **aion-skill-creator** — 自研轻量版，交互式问答 → SKILL.md 脚手架生成 → 编写指南

## 技术实现

- Backend: `services/skills.py` + `routers/skills.py`（全局路由，非项目级）
- Frontend: rail 按钮 + sidebar（已安装/官方市场 tab 切换）+ detail 面板
- Init: `core/project.py` 步骤 2.5，从 `templates/skills/` 复制到 `~/.claude/skills/`

## 设计决策

- 不绑定特定第三方 skill，做平台不做集合
- 放弃 skills.sh 对接（用户决定）
- skill-creator 自研轻量版，不含 eval/benchmark 重量级功能
