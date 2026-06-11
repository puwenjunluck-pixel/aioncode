# Product Template — `_product.md` 产品全景文档结构

<!-- 使用方: /aion:think Phase 10.1 与 /aion:scan。
     _product.md 是项目唯一的产品全景文档，由 think/scan 自动维护，人工确认的内容标 [CONFIRMED]。 -->

## Frontmatter

```yaml
---
product: {产品名}
updated_at: {YYYY-MM-DD}
generation_method: scan | spec-propagation
confidence: high | medium | low
sources:
  - code-scan | spec:{name}.md | user-confirmed
---
```

## 文档主体结构

```markdown
# 产品设计文档

## 一、产品定位
- **目标用户**：{谁} [CONFIRMED 或 from:spec/from:code]
- **核心价值**：{解决什么问题}
- **产品形态**：{CLI / Web / 插件 / ...}
- **商业模式**：{如适用}

## 二、功能地图
| 模块 | 功能 | 用户场景 | 状态 | 对应 spec |
|------|------|---------|------|-----------|
| {模块} | {一句话} | {场景} | 已实现/计划中 | {spec 文件名 或 [from:code]} |

## 三、核心业务流程
### 流程 N: {名称}
{角色} → {步骤链} [CONFIRMED 或 from:spec]
```

## 维护规则

1. **标注来源**：每条内容标 `[CONFIRMED]`（用户确认）/ `[from:spec]` / `[from:code]`
2. **增量更新**：新 spec 落盘后追加功能地图行（带对应 spec 列）与业务流程（若暗示新用户旅程）
3. **NEVER 覆盖 `[CONFIRMED]` 项** — 用户确认的内容只能由用户改
4. **每次更新刷新 `updated_at`** 并汇报增量（"功能地图 +N 项"）
