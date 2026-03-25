---
version: 1
author: waynepo
scope: full
change_reason: null
created_at: 2026-03-23
---

# 产品设计层规格：`_product.md` + `--file` 输入

## 背景

AionCode 当前工作流存在架构断层：
- **spec** → "做什么"（需求、验收标准）
- **plan** → "怎么做"（实现步骤、文件变更）
- **缺失** → "做成什么样"（产品全景、逻辑流转、模块边界、客户画像）

此断层导致：
1. E2E 测试缺少全局功能地图，只能逐 spec 看局部
2. 新人无法快速理解系统整体
3. AI 实现时不知道改动在产品全局中的位置
4. 跨模块设计决策无处记录

## 设计方案

### 1. 新增 `_product.md` — 产品设计全景文档

**位置**：`.aion/specs/_product.md`

**归类**：Versioned 产物（遵循 Write Protocol），但不是普通 feature spec，而是全局唯一的产品全景。

**文档结构**：

```markdown
---
product: 产品名称
updated_at: {YYYY-MM-DD}
generation_method: {scan+explore | design-aggregation | manual | file-import}
confidence: {high | medium | low}
sources:
  - {列出生成时使用的信息源}
---

# 产品设计文档

## 一、产品定位
- **目标用户**：{谁在用这个产品，用户画像}
- **核心价值**：{解决什么问题，价值主张}
- **产品形态**：{Web / App / CLI / API / 混合}
- **商业模式**：{如何变现（如适用）}

## 二、功能地图
| 模块 | 功能 | 用户场景 | 状态 | 对应 spec |
|------|------|---------|------|-----------|
| {模块名} | {功能描述} | {用户做什么} | {已实现/规划中} | {spec 文件名} |

## 三、核心业务流程
### 流程 1: {流程名}
{角色} → {操作1} → {系统响应} → {操作2} → {结果}

### 流程 2: {流程名}
...

## 四、模块架构
| 模块 | 职责 | 对外接口 | 依赖 | 解耦方式 |
|------|------|---------|------|---------|
| {模块名} | {单一职责描述} | {API/事件/共享状态} | {依赖哪些模块} | {HTTP/MQ/文件} |

## 五、技术栈
| 层 | 选型 | 版本 | 选型理由 |
|----|------|------|---------|
| 前端 | {框架} | {版本} | {为什么选这个} |
| 后端 | {框架} | {版本} | |
| 数据库 | {类型} | {版本} | |
| 部署 | {方式} | | |

## 六、数据模型（核心实体）
| 实体 | 字段概要 | 关系 | 对应表/集合 |
|------|---------|------|-----------|
| {实体名} | {关键字段} | {1:N/N:N} | {表名} |

## 七、部署与环境
- **生产环境**：{描述}
- **开发环境**：{描述}
- **测试环境**：{描述}

## 八、已知约束与限制
- {约束1}
- {约束2}
```

**标记机制**：
- `[CONFIRMED]` — 用户确认的信息
- `[INFERRED]` — AI 从代码/UI 推断的信息，待确认
- `[from:spec]` `[from:code]` `[from:explore]` `[from:file]` `[from:user]` — 信息来源

### 2. 三种生成策略

#### 策略 1：Design 聚合（新项目）

**触发**：`aion-design` 完成时

**流程**：
1. `aion-design` 完成 feature spec
2. 检测 `_product.md` 是否存在
   - 不存在 → 从当前 spec 初始化骨架，标记 confidence: low
   - 已存在 → 提取本次 spec 的新功能/模块/用户场景
3. 合并到 `_product.md` 对应章节（功能地图、业务流程）
4. 随着 spec 积累，confidence 从 low → medium → high

**`--file` 支持**：
```
aion-design --file 产品需求.docx
aion-design --file requirements/
```
- 使用 markitdown 工具将 docx/pdf 转换为 markdown
- 从转换后的内容提取需求 → 生成 feature specs
- 同时更新 `_product.md`（功能地图、用户场景、业务流程）
- 如果是目录，批量扫描所有 .docx/.pdf/.md 文件

#### 策略 2：浏览器探索（已有项目 + 能跑起来）

**触发**：`aion-scan`（检测到 Playwright MCP 且服务可达）

**流程**：
```
Phase A: 代码扫描（现有 scan 逻辑）
  → 技术栈、目录结构、模块依赖、API 清单

Phase B: 浏览器探索（需 Playwright MCP + 服务运行中）
  1. 打开 target_url，截图首页
  2. 识别导航结构 → 功能地图骨架
  3. 逐页面探索：
     - 页面标题、核心元素 → 功能描述
     - 表单/按钮 → 用户操作
     - 数据列表 → 业务实体
     - 空状态/loading/error → 状态处理
     - 截图存档 → .aion/refs/screenshots/
  4. 登录处理（如需要）：
     - 检测是否有登录页
     - 提示用户提供测试账号（或手动登录后继续）
  5. 输出：UI 功能发现报告

Phase C: 交叉分析
  - 代码模块 ↔ UI 页面映射
  - API 路由 ↔ 前端调用映射
  - 数据库模型 ↔ UI 数据展示映射
  - 推断：用户角色、核心流程、模块边界

Phase D: AI 提问补充
  - 展示推断结果，向用户提问：
    "我从代码和 UI 中推断了以下产品结构，请确认或纠正：
     1. 这个系统的目标用户是 ___？
     2. 核心业务流程是 ___？
     3. 模块 X 和模块 Y 的关系是 ___？"
  - 用户回答后更新 [INFERRED] → [CONFIRMED]

输出：_product.md（generation_method: scan+explore, confidence: medium→high）
```

**`--file` 支持**：
```
aion-scan --file 架构设计.pdf
aion-scan --file docs/
```
- 外部文档作为代码扫描的辅助输入
- 提升 `_product.md`、`architecture.md`、`contracts/` 的质量
- 特别有效的场景：有 API 文档但代码注释少、有 PPT 架构图但无代码文档

#### 策略 3：纯代码（跑不起来的旧项目）

**触发**：`aion-scan`（无 Playwright MCP 或服务未启动）

**流程**：
```
Phase A: 代码扫描（同上）

Phase B: 深度静态分析（替代浏览器探索）
  - 读 HTML/JSX/Vue 模板 → 推断页面结构和功能
  - 读路由配置 → 推断导航结构和 URL 地图
  - 读 API 控制器 → 推断业务端点
  - 读数据库迁移/模型 → 推断业务实体

Phase C: --file 补充（如提供）
  - 导入外部文档弥补代码推断不足

Phase D: AI 提问（兜底）
  - 标记所有 [INFERRED] 项
  - 向用户提问不确定的部分
  - 用户回答后更新

输出：_product.md（generation_method: scan, confidence: low→medium）
```

### 3. 自动传播机制

| 触发时机 | 检查内容 | 更新 `_product.md` 的章节 |
|---------|---------|------------------------|
| `aion-design` 完成 | 新 spec 有新功能/模块/用户场景 | 功能地图、业务流程 |
| `aion-plan` 完成 | plan 有新模块/新依赖/架构变更 | 模块架构、技术栈 |
| `aion-scan` 完成 | 全量重建或增量更新 | 整个文档 |
| `aion-impl` 完成 | 不触发（实现不改产品设计） | — |
| `aion-test e2e` Phase 0 | 勘察发现了新页面/新功能 | 功能地图（追加 [from:explore]）|

**传播规则**：
- 只追加/更新，不删除已有内容
- 用户 [CONFIRMED] 的内容不被自动覆盖
- [INFERRED] 的内容可被后续更准确的信息覆盖
- 每次更新记录 `updated_at` 和变更的 source

### 4. `--file` 输入规范

**支持格式**：docx, pdf, md, txt, pptx, xlsx（通过 markitdown 工具转换）

**处理流程**：
```
--file input
    │
    ├─ 单文件 → markitdown 转换 → markdown 内容
    ├─ 目录   → 扫描所有支持格式 → 逐文件转换
    │
    ├─ 内容分类：
    │   ├─ 需求类（PRD、用户故事、功能清单）→ 生成 feature specs + 更新 _product.md
    │   ├─ 架构类（系统设计、模块图、部署图）→ 更新 architecture.md + _product.md
    │   ├─ 接口类（API 文档、Swagger、协议）→ 生成 contracts/ + 更新 _product.md
    │   └─ 混合类 → 按内容段落分别处理
    │
    └─ 输出：处理报告（导入了什么、生成了什么、跳过了什么）
```

**安全约束**：
- `--file` 的文件路径必须存在，不存在则报错
- 大文件（>10MB）警告用户，确认后继续
- 转换失败时降级为纯文本读取

### 5. 与其他系统的集成

| 消费方 | 如何使用 `_product.md` |
|--------|----------------------|
| `aion-test e2e` | Phase 1 多源分析时读取，作为全局功能上下文 |
| `aion-plan` | 实现规划时参考模块边界和技术栈 |
| `aion-impl` | 实现时了解改动在产品全局中的位置 |
| `aion-review` | 审查时检查是否与产品设计一致 |
| `aion-help` | 向新人介绍项目时引用 |
| Dashboard 关于页 | 可嵌入展示产品全景 |

## 文件变更清单

### 修改文件

| 文件 | 变更内容 |
|------|---------|
| `commands/aion-design.md` | 新增 `--file` 参数、完成后更新 `_product.md` 逻辑 |
| `commands/aion-scan.md` | 新增 Phase B（浏览器探索）、`--file` 参数、生成 `_product.md` |
| `commands/aion-plan.md` | 完成后检查并更新 `_product.md` 的模块/技术栈章节 |
| `commands/aion-test.md` | E2E Phase 1 多源分析时读取 `_product.md` |

### 新增文件

| 文件 | 内容 |
|------|------|
| `.aion/specs/_product.md` | 产品设计全景文档（按项目自动生成） |

## 验收标准

- [ ] `aion-design` 完成后自动检查并更新 `_product.md`
- [ ] `aion-design --file xx.docx` 能正确导入外部文档并生成 specs
- [ ] `aion-scan` 在有 Playwright MCP 时执行浏览器探索
- [ ] `aion-scan` 无 MCP 时降级为深度静态分析 + AI 提问
- [ ] `aion-scan --file xx.pdf` 能作为辅助输入提升产出质量
- [ ] `aion-plan` 完成后检查模块/技术栈变更并传播到 `_product.md`
- [ ] `_product.md` 的 [INFERRED] 标记经用户确认后升级为 [CONFIRMED]
- [ ] 所有策略最后都支持 AI 提问补充
- [ ] `aion-test e2e` Phase 1 读取 `_product.md` 作为全局上下文

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 浏览器探索需要登录但无测试账号 | 提示用户手动登录或提供 credentials |
| `--file` 导入的文档质量参差不齐 | markitdown 转换 + AI 过滤噪音 |
| `_product.md` 过度膨胀 | 模块架构和功能地图用表格保持简洁 |
| [INFERRED] 内容可能误导后续命令 | 低置信度内容明确标记，关键决策前提示用户确认 |
| 多人协作时 `_product.md` 冲突 | 追加式更新 + [CONFIRMED] 内容不被自动覆盖 |
