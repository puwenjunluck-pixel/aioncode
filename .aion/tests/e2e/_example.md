---
feature: AionCode Dashboard
target_url: http://127.0.0.1:19200
viewport: [desktop]
preconditions:
  - Dashboard 已启动 (aioncode dashboard --dev)
  - 当前目录为已初始化的 AionCode 项目（含 .aion/ 目录）
---

# E2E: AionCode Dashboard

## TC-001: 访问 Dashboard 首页

**Given**: Dashboard 服务已启动
**When**: 在浏览器中访问 http://127.0.0.1:19200
**Then**:
  - 页面标题为"AionCode — 副驾驶"
  - 左侧导航栏（rail）包含"概览"、"文件"、"监控"等按钮
  - "概览"按钮默认处于激活状态（class 包含 active）
  - 状态栏（statusbar）底部显示"AionCode"版本信息

**Edge Cases**:
  - 服务未启动时，浏览器显示连接拒绝错误

## TC-002: 查看项目概览

**Given**: 用户在 Dashboard 首页，"概览"视图已激活
**When**: 查看侧边栏内容
**Then**:
  - 侧边栏标题显示"项目概览"
  - 显示统计区域（id="stats"），包含项目基本数据
  - 显示"最近活动"标题
  - 最近活动区域（id="changelog"）列出最新变更记录

**Edge Cases**:
  - 项目无 changelog 时，最近活动区域显示空状态提示

## TC-003: 查看变更日志

**Given**: 用户在 Dashboard 首页
**When**: 点击左侧导航栏"日志"按钮（aria-label="日志"）
**Then**:
  - 侧边栏标题切换为"变更日志"
  - 显示 changelog 条目列表
  - 条目按时间倒序排列（最新在上）

**Edge Cases**:
  - changelog.md 为空时，显示空状态提示

## TC-004: 查看项目规则

**Given**: 用户在 Dashboard 首页
**When**: 点击左侧导航栏"规则"按钮（aria-label="规则"）
**Then**:
  - 侧边栏标题切换为"项目规则"
  - 显示规则分类列表（style、pitfalls、perf）
  - 每个分类旁显示规则数量（badge）
  - 点击某条规则后，右侧详情区域（id="detail"）显示规则内容

## TC-005: 查看关于页面

**Given**: 用户在 Dashboard 任意页面
**When**: 点击左侧导航栏"关于"按钮（aria-label="关于"）
**Then**:
  - 侧边栏标题切换为"使用指南"
  - 侧边栏显示目录导航（id="about-toc"）
  - 右侧详情区域显示 AionCode 项目信息
  - 页面内容包含"成都奕贝科技"公司信息

## TC-006: 视图切换联动

**Given**: 用户在"概览"视图
**When**: 依次点击"需求"按钮 → 点击"方案"按钮 → 点击"概览"按钮
**Then**:
  - 每次点击后，对应按钮变为激活状态（active class）
  - 之前激活的按钮恢复非激活状态
  - 侧边栏内容切换为对应视图的内容
  - "需求"视图显示"需求文档"标题
  - "方案"视图显示"实施方案"标题
  - 回到"概览"后恢复"项目概览"标题
