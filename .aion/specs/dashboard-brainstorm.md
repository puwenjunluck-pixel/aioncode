---
status: completed
created_at: 2026-04-06
version: 1
author: wayne
scope: web
change_reason: null
---

# Dashboard 设计协作视图

## Goal
在 Dashboard 新增「协作」视图，通过文件中转机制实现 aion-design 与用户的可视化交互——终端写入结构化内容，Dashboard 实时展示方案选项，用户点选后结果回传终端。

## Requirements (P0)

### R1: 文件中转协议
- aion-design 写入 `.aion/brainstorm/screen.json`（当前展示内容）
- 用户点选后 Dashboard 追加事件到 `.aion/brainstorm/events.jsonl`（一行一事件）
- aion-design 读取 events.jsonl 获取用户选择
- 每次新 screen 写入时清空 events.jsonl（新问题新事件流）
- 无 brainstorm 活动时 `.aion/brainstorm/` 目录可不存在

### R2: 结构化内容格式（screen.json）
- `type: "options"` — 方案选择（A/B/C 卡片）
  ```json
  {
    "type": "options",
    "title": "模型切换方案",
    "description": "选择实现方式",
    "items": [
      {"key": "a", "title": "方案 A", "body": "描述...", "pros": ["优势1"], "cons": ["劣势1"], "recommended": true},
      {"key": "b", "title": "方案 B", "body": "描述...", "pros": ["优势1"], "cons": ["劣势1"]}
    ],
    "multiselect": false
  }
  ```
- `type: "compare"` — 对比表格（多维度对比）
  ```json
  {
    "type": "compare",
    "title": "方案对比",
    "dimensions": ["复杂度", "性能", "可维护性"],
    "items": [
      {"key": "a", "title": "方案 A", "scores": {"复杂度": "低", "性能": "高", "可维护性": "中"}},
      {"key": "b", "title": "方案 B", "scores": {"复杂度": "中", "性能": "中", "可维护性": "高"}}
    ]
  }
  ```
- `type: "info"` — 纯展示（等待态、进度提示）
- 预留 `type: "html"` 字段（P1 扩展，P0 不实现）

### R3: 事件格式（events.jsonl）
- 每行一个 JSON 事件：`{"type": "click", "choice": "a", "timestamp": 1706000101}`
- 多选模式：多次 click 事件，最终选择集合由 aion-design 自行聚合

### R4: Dashboard「协作」视图
- 侧边栏新增「协作」入口（图标 + badge 显示活跃状态）
- 视图轮询 `.aion/brainstorm/screen.json`（间隔 1-2 秒）
- 根据 `type` 渲染对应 CSS 组件（option cards、compare table、info panel）
- 用户点选后写入 events.jsonl 并显示"已选择 X，请回到终端继续"提示
- 无 brainstorm 数据时显示空态："当前无设计协作会话。运行 /project:aion-design 开始。"

### R5: aion-design 命令集成
- Step 1.5（方案探索）和 Step 2（澄清问题）中，检测 Dashboard 是否运行
- 如果 Dashboard 运行中：同时在终端输出文本 + 写 screen.json 推送到 Dashboard
- 如果 Dashboard 未运行：仅终端输出，行为不变（向后兼容）
- 检测方式：检查 `.aion/brainstorm/` 是否可写，或 curl Dashboard health endpoint

### R6: 后端 API
- `GET /api/projects/{encoded}/brainstorm/screen` — 读取 screen.json 内容
- `POST /api/projects/{encoded}/brainstorm/event` — 追加事件到 events.jsonl
- `GET /api/projects/{encoded}/brainstorm/status` — 返回是否有活跃的 brainstorm 会话

## Requirements (P1)

### R7: HTML 自由内容（预留扩展）
- `type: "html"` — aion-design 写入原始 HTML，Dashboard 在沙箱 iframe 中渲染
- CSS 隔离：iframe sandbox 属性限制脚本执行
- 适用场景：UI mockup、wireframe、交互原型

### R8: 预置 CSS 组件库
- option cards（选择卡片，支持推荐标记和高亮）
- pros/cons 对比列（绿/红色列表）
- compare table（多维度对比表格，支持高亮最优项）
- mockup container（P1，配合 type: html 使用）
- split view（左右对比布局）

### R9: 会话生命周期
- aion-design 结束后写入 screen.json 为 `{"type": "info", "title": "设计会话已结束"}`
- Dashboard 检测到结束态后显示摘要 + "开始新会话"提示
- `.aion/brainstorm/` 历史文件可选保留（不自动清理）

## Acceptance Criteria
- aion-design 写入 screen.json 后，Dashboard 协作视图在 2 秒内展示内容
- 用户在 Dashboard 点选方案后，events.jsonl 中出现对应事件
- aion-design 读取 events.jsonl 获得用户选择，继续下一步
- Dashboard 未运行时 aion-design 行为不变（纯终端，向后兼容）
- `type: options` 和 `type: compare` 两种内容类型正确渲染
- 无 brainstorm 数据时显示空态提示
- 协作视图侧边栏入口正常显示，有活跃会话时 badge 亮起

## Constraints
- 前端无构建工具（Vanilla JS），修改 static/ 后需运行 build_frontend.py 生成 embedded.py（pitfalls 规则 5）
- 轮询方式获取 screen.json（非 WebSocket/SSE），保持架构简单一致
- aion-design 检测 Dashboard 仅用文件系统检查，不引入 HTTP 依赖到 prompt 层
- type: html 在 P0 阶段仅预留字段，前端遇到此类型显示"HTML 渲染即将支持"占位
- 不修改现有 SSE 监控机制，协作视图独立运行
