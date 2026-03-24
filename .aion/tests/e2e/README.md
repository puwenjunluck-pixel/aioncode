# E2E 自然语言测试定义

本目录存放自然语言编写的 E2E 测试用例。测试人员用 Markdown 描述用户行为，`aion-test e2e` 解析并执行（或生成 Playwright 脚本）。

## 文件格式

每个 `.md` 文件对应一个 feature，使用以下结构：

### YAML Frontmatter（必填）

```yaml
---
feature: 功能名称            # 必填，feature 标识
target_url: http://localhost:19200  # 必填，测试目标 URL
viewport: [desktop, mobile]   # 可选，默认 [desktop]
preconditions:                # 可选，全局前置条件
  - 用户已登录
  - 至少存在 1 条测试数据
---
```

**viewport 预设值**：
- `desktop` → 1440×900
- `mobile` → 375×667 (iPhone SE)
- `tablet` → 768×1024 (iPad)
- 自定义 → `1920x1080`

### 测试用例结构

每个用例以 `## TC-{NNN}: {标题}` 开头：

```markdown
## TC-001: 创建新记录

**Given**: 用户已登录，在列表页
**When**: 点击"新建" → 填写表单 → 点击"保存"
**Then**:
  - 页面显示"保存成功"提示
  - 列表中出现新记录

**Edge Cases**:
  - 必填字段为空时，保存按钮禁用
  - 名称超过限制时，显示错误提示
```

### 语法规则

| 元素 | 格式 | 说明 |
|------|------|------|
| **Given** | 单行描述 | 前置状态，用"在XX页"描述位置 |
| **When** | 用 `→` 分隔步骤 | 每个 `→` 是一个用户操作 |
| **Then** | 缩进列表 | 每项是一个可验证的断言 |
| **Edge Cases** | 缩进列表 | 每项是一个边界场景（可选） |

### When 动作关键词

以下关键词帮助 AI 将自然语言映射到 Playwright 调用。**不需要精确匹配** — AI 会根据语义理解，但使用标准关键词能提高准确性。

| 关键词 | Playwright 映射 | 示例 |
|--------|----------------|------|
| 点击"XX" / 点击XX按钮 | `page.getByText('XX').click()` | 点击"保存" |
| 点击{描述}按钮（aria-label="XX"） | `page.getByLabel('XX').click()` | 点击导航栏"日志"按钮（aria-label="日志"） |
| 输入"XX"到{字段} / 填写{字段}为"XX" | `page.getByLabel('{字段}').fill('XX')` | 输入"测试"到名称字段 |
| 选择{选项} / 从下拉框选择{选项} | `page.getByRole('option').click()` | 选择分类"默认" |
| 访问{URL} / 在浏览器中访问{URL} | `page.goto('{URL}')` | 访问 http://localhost:19200 |
| 导航到{页面} / 进入{页面} | `page.goto()` 或 click nav | 导航到设置页 |
| 查看{内容} / 检查{内容} | (断言操作，非导航) | 查看侧边栏内容 |
| 等待{元素}出现 / 等待页面加载 | `page.waitForSelector()` | 等待列表加载完成 |
| 上传{文件} / 选择文件{文件名} | `page.setInputFiles(...)` | 上传 test.csv |
| 滚动到{元素} / 滚动到底部 | `element.scrollIntoViewIfNeeded()` | 滚动到页面底部 |
| 确认{操作} / 点击确认 | `page.getByRole('button', {name: '确认'}).click()` | 确认删除 |
| 取消{操作} / 点击取消 | `page.getByRole('button', {name: '取消'}).click()` | 取消删除 |
| 刷新页面 | `page.reload()` | 刷新页面 |
| 切换到{视口} | `page.setViewportSize(...)` | 切换到移动端视口 |

> **提示**：如果你的操作不在表中，直接用自然语言描述即可。AI 会根据上下文推断对应的 Playwright 操作。关键是**描述清楚你要做什么**，而非记忆关键词。

### TC-ID 编号规则

- 格式：`TC-{NNN}`，从 001 开始
- 同一文件内连续编号
- 不同文件可重用编号（按 feature 隔离）

## 最佳实践

1. **一个文件一个 feature** — 不要在一个文件里混合多个不相关功能
2. **步骤要具体可执行** — "填写表单"太模糊，改为"输入名称'测试'到名称字段 → 选择分类'默认'"
3. **Then 要可验证** — "页面正确显示"太模糊，改为"页面显示'保存成功'提示"
4. **Edge Cases 写典型场景** — 空值、超长、特殊字符、并发、网络断开
5. **前置条件写在 frontmatter** — 全局前置条件（如"已登录"）写在 preconditions，不要每个 TC 重复

## 与 aion-test e2e 的集成

```bash
# 仅生成 Playwright 脚本（无需 MCP）
/project:aion-test e2e

# 通过 Playwright MCP 实时执行
/project:aion-test e2e    # 自动检测 MCP，有则 live，无则 gen

# 针对特定 feature
/project:aion-test e2e dashboard

# 生成 + 自愈
/project:aion-test e2e --heal
```

## 参考

- 格式灵感来源：Gherkin (Given/When/Then) + Markdown
- 执行引擎：Playwright MCP (live) 或 Playwright Test (gen)
- 报告输出：`.aion/tests/reports/{feature}-e2e.md`
