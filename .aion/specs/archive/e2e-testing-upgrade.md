# 测试体系升级设计规格

> 版本：A（初版）
> 日期：2026-03-23
> 状态：Draft — 待用户审批

## 背景

基于 2026-03-23 的行业调研（OpenObserve 多代理管道、Shipyard TDD 模式、Quinn AI QA 工程师、TestDino Playwright Skill），AionCode 的 `aion-test` 和 `aion-verify` 命令需要从"生成+报告"升级为"生成+执行+自愈+E2E"的闭环测试体系。

### 调研关键发现

| 来源 | 核心能力 | 效果 |
|------|---------|------|
| OpenObserve | 8 子代理测试管道 | 分析提速 6-10x，flaky 减少 85% |
| Shipyard | Claude Code + Cypress TDD | 一次 run 生成 4 个完整测试并通过 |
| alexop.dev | Quinn AI QA + Playwright MCP | PR 自动黑盒测试，回贴 Markdown 报告 |
| TestDino | Playwright Skill | 1 分钟生成 82 个测试，7 个文件 |
| firstloophq | 自然语言测试运行器 | JSON 定义步骤，AI 自动执行 |

### 当前缺口

1. **无自愈能力** — verify 失败只报告，不修复
2. **无真实 E2E** — 明确禁止 Playwright 浏览器自动化
3. **无自然语言测试** — 测试人员必须理解代码才能参与
4. **单代理模型** — 一个 prompt 承担所有测试职责

---

## 设计方案：三层递进架构

### 第一层：测试自愈闭环（优先级 P0）

#### 1.1 `aion-test --heal` 模式

**目标**：测试失败时不停下来，而是自动诊断 + 修复 + 重试。

**工作流**：

```
aion-test [feature] --heal
    │
    ├─ Step 1-4: 正常生成测试（现有逻辑不变）
    │
    ├─ Step 5 (NEW): 执行测试
    │   └─ 运行 pytest / vitest / go test
    │
    ├─ Step 6 (NEW): 自愈循环（最多 3 轮）
    │   ├─ 读取失败日志（Traceback / Error output）
    │   ├─ 对比 .aion/specs/ 判断根因：
    │   │   ├─ "代码 bug" → 修复源代码，标记 [CODE_FIX]
    │   │   ├─ "测试过期" → 更新测试用例，标记 [TEST_FIX]
    │   │   └─ "环境问题" → 报告 [ENV_ISSUE]，停止自愈
    │   ├─ 应用修复补丁
    │   └─ 重新运行测试
    │
    └─ Step 7: 输出自愈报告
        ├─ 每轮修复的内容和理由
        ├─ 最终测试通过/失败状态
        └─ 未解决的问题（如有）
```

**自愈判断逻辑**：

| 信号 | 判定 | 动作 |
|------|------|------|
| `AssertionError` + spec 中有对应验收标准 | 代码未满足 spec | 修复源代码 |
| `AttributeError` / `ImportError` / 选择器失效 | 代码重构后测试过期 | 更新测试 |
| `ConnectionRefusedError` / `TimeoutError` | 环境问题 | 停止自愈，报告 |
| 测试逻辑与 spec 矛盾 | 测试写错了 | 修复测试 |
| spec 不存在 + 测试失败 | 无法判断谁对 | 报告 [NEEDS_HUMAN]，不自动修复 |

**安全护栏**：
- 最多 3 轮自愈（防止无限循环）
- 每轮修改不超过 3 个文件
- 修改源代码前必须确认 spec 支持该行为
- 所有修复以 `[HEAL]` 前缀标记在 changelog 中
- 如果自愈循环全部失败，输出完整诊断报告而非静默放弃

#### 1.2 `aion-verify` 升级为"修理工"

**目标**：verify 从"检查员"变成"检查员 + 修理工"。

**新增 `--fix` 选项**：

```
aion-verify --fix
```

**工作流变化**：

```
原来：
  Build FAIL → 报告 → 停止
  Lint FAIL  → 报告 → 停止
  Test FAIL  → 报告 → 停止

升级后（--fix 模式）：
  Build FAIL → 分析错误 → 尝试修复 → 重新 build → 报告
  Lint FAIL  → 运行 auto-fix（ruff --fix / eslint --fix）→ 报告
  Test FAIL  → 触发自愈循环（复用 aion-test --heal 逻辑）→ 报告
```

**关键约束**：
- `--fix` 是 opt-in，默认 verify 行为不变（纯报告）
- Lint auto-fix 直接运行工具自带的 `--fix` 命令
- Build/Test 失败的修复通过 AI 分析 + 补丁实现
- 每个修复步骤可审计（输出修改了什么、为什么）

---

### 第二层：E2E 浏览器测试（优先级 P1）

#### 2.1 `aion-test e2e` 模式

**目标**：通过 Playwright MCP 控制真实浏览器，执行 E2E 测试。

**前置条件检测**：

```
aion-test e2e [feature]
    │
    ├─ 检查 Playwright MCP 是否已配置
    │   ├─ 已配置 → 进入 e2e-live 模式（真实浏览器）
    │   └─ 未配置 → 进入 e2e-gen 模式（仅生成脚本）
    │
    ├─ e2e-gen：生成 Playwright 测试脚本（不执行）
    │   ├─ 读取 .aion/specs/ 和 .aion/tests/e2e/*.md（自然语言用例）
    │   ├─ 生成 Page Object Model 结构
    │   ├─ 输出到 tests/e2e/ 或项目约定目录
    │   └─ 建议：安装 Playwright MCP 以启用实时执行
    │
    └─ e2e-live：通过 MCP 控制浏览器执行测试
        ├─ 读取自然语言测试定义
        ├─ 逐步执行（导航、点击、输入、截图、断言）
        ├─ 自动适应 UI 变化（不依赖硬编码选择器）
        ├─ 失败时触发自愈（healer 逻辑）
        └─ 生成带截图的测试报告
```

#### 2.2 自然语言测试定义格式

**位置**：`.aion/tests/e2e/{feature-name}.md`

**格式规范**：

```markdown
---
feature: Prompt 游乐场
target_url: http://localhost:19200
viewport: [desktop, mobile]
preconditions:
  - 商家已登录云端 WEB
  - 至少存在 1 个已创建的 Prompt
---

# E2E: Prompt 游乐场

## TC-001: 创建新 Prompt

**Given**: 商家已登录，在 Dashboard 首页
**When**: 点击侧边栏"Prompt 游乐场" → 点击"新建 Prompt" → 输入名称"测试指令" → 填写系统提示词 → 点击"保存"
**Then**:
  - 页面显示"保存成功"提示
  - Prompt 列表中出现"测试指令"
  - 详情页显示正确的系统提示词

**Edge Cases**:
  - 名称为空时，保存按钮应禁用
  - 名称超过 100 字时，显示长度限制提示
  - 网络断开时，显示离线提示而非静默失败

## TC-002: 编辑已有 Prompt

**Given**: 已存在名为"测试指令"的 Prompt
**When**: 点击该 Prompt → 修改系统提示词 → 点击"保存"
**Then**:
  - 显示"更新成功"提示
  - 修改后的内容立即生效

## TC-003: 删除 Prompt

**Given**: 已存在名为"测试指令"的 Prompt
**When**: 点击该 Prompt → 点击"删除" → 确认删除
**Then**:
  - Prompt 从列表中消失
  - 再次访问列表页不包含该 Prompt

**Edge Cases**:
  - 取消删除确认后，Prompt 仍存在
```

**设计原则**：
- **Markdown 即文档又是剧本** — 测试人员写 Markdown，AionCode 解析并执行
- **Given/When/Then 结构** — 明确的前置条件、操作步骤、预期结果
- **Edge Cases 节** — 鼓励测试人员主动思考边界
- **Frontmatter 元数据** — target_url、viewport 等执行参数
- **不要求代码知识** — 测试人员只需描述用户行为

#### 2.3 Playwright MCP 集成方式

**检测逻辑**（加入 Step 0.5）：

```
检测 MCP 配置：
  1. 读取 .claude/settings.json 或 mcp.json
  2. 查找 playwright 相关 MCP server 配置
  3. 如果存在 → 标记 HAS_PLAYWRIGHT_MCP = true
  4. 如果不存在 → HAS_PLAYWRIGHT_MCP = false，输出安装指引
```

**安装指引输出**（当未检测到时）：

```markdown
## Playwright MCP 未检测到

E2E live 模式需要 Playwright MCP。安装方式：

npm install -g @anthropic-ai/playwright-mcp

然后在 Claude Code 设置中添加 MCP server 配置。

当前已切换为 e2e-gen 模式（仅生成测试脚本，不执行）。
```

#### 2.4 修改 NEVER Playwright 规则

**原规则**：
> Running Playwright or full browser automation | Too heavy, too many tokens, breaks constraints | HIGH

**新规则**：
> Running Playwright browser automation WITHOUT MCP or in non-e2e mode | Browser automation only allowed in `aion-test e2e` mode with Playwright MCP configured | HIGH

**理由**：MCP 提供了安全的浏览器控制代理层，不再是"直接跑浏览器"，而是通过协议控制。在 e2e 模式下有明确的作用域和超时保护。

---

### 第三层：多代理测试管道（优先级 P2）

#### 3.1 子代理架构

**触发条件**：`aion-test pipeline [feature]` 或 `aion-test full --pipeline`

**5 阶段管道**：

```
                    ┌──────────────────────────────────────────────┐
                    │           aion-test pipeline                 │
                    │              (编排器)                         │
                    └──────┬───────┬───────┬───────┬───────┬──────┘
                           │       │       │       │       │
                    Stage 1│Stage 2│Stage 3│Stage 4│Stage 5│
                           ▼       ▼       ▼       ▼       ▼
                    ┌──────┐┌─────┐┌──────┐┌─────┐┌──────┐
                    │分析师 ││规划师││工程师 ││哨兵  ││治疗师 │
                    └──────┘└─────┘└──────┘└─────┘└──────┘
```

| 阶段 | 代理 | 输入 | 输出 | 工具 |
|------|------|------|------|------|
| 1 | **分析师** | specs + 源码 + prototypes | 测试点清单 + 用户流程图 + 边界case 列表 | Read, Grep, Glob |
| 2 | **规划师** | 分析师输出 | P0/P1/P2 优先级测试计划 | Read, Write |
| 3 | **工程师** | 规划师输出 + 测试基础设施信息 | Playwright/pytest 测试代码 | Read, Write, Edit, Bash |
| 4 | **哨兵** | 工程师输出 | 质量审计报告（PASS/BLOCK） | Read, Grep, Glob |
| 5 | **治疗师** | 哨兵 PASS 后的测试代码 + 运行结果 | 修复后的测试代码 | Read, Write, Edit, Bash |

#### 3.2 代理间通信

**上下文链式传递**：每个代理接收前序所有阶段的输出（非仅上一个）。

```
分析师输出 → 规划师（接收：分析师输出）
           → 工程师（接收：分析师输出 + 规划师输出）
           → 哨兵  （接收：分析师输出 + 规划师输出 + 工程师输出）
           → 治疗师（接收：全部 + 测试运行日志）
```

**中间产物存储**：`.aion/tests/pipeline/{feature-name}/{stage}.md`

#### 3.3 哨兵质量门禁

哨兵是管道中唯一有**硬阻止权**的代理：

| 检查项 | 阻止级别 |
|--------|---------|
| 测试代码不遵循项目约定（框架/目录/命名） | BLOCK |
| 测试硬编码了环境值（URL、路径、token） | BLOCK |
| 测试验证实现细节而非行为 | BLOCK |
| 覆盖率低于 spec 要求的验收标准 | WARN |
| 缺少 edge case 测试 | WARN |

**BLOCK 时**：管道回退到工程师阶段，附带哨兵的审计意见，工程师修复后再次提交。最多回退 2 次，超过则 FAIL 退出。

#### 3.4 治疗师自愈循环

复用第一层 `--heal` 的核心逻辑，但独立为子代理运行：

1. 运行测试套件
2. 收集失败日志
3. 分析根因（代码 bug / 测试过期 / 环境问题）
4. 应用修复
5. 重试（最多 3 轮）
6. 输出治疗报告

---

## 文件变更清单

### 修改文件

| 文件 | 变更内容 |
|------|---------|
| `commands/aion-test.md` | 新增 `--heal`、`e2e`、`pipeline` 模式 |
| `commands/aion-verify.md` | 新增 `--fix` 选项和自动修复逻辑 |
| `.aion/checklists/test.md` | 新增 E2E 和自愈相关检查项 |
| `.aion/rules/pitfalls.md` | 修改 Playwright 规则为条件允许 |

### 新增文件

| 文件 | 内容 |
|------|------|
| `.aion/specs/e2e-testing-upgrade.md` | 本文档 |
| `.aion/tests/e2e/README.md` | 自然语言测试定义格式说明 + 模板 |
| `.aion/tests/e2e/_example.md` | 示例测试用例（展示格式） |

### 不变文件

| 文件 | 理由 |
|------|------|
| `aioncode/` 下所有 Python 代码 | 本次改动仅涉及 Claude Code 命令 prompt，不改 CLI 代码 |
| `.claude/commands/` | 遵守 NEVER 同步规则，用户自行同步 |
| `templates/` | 遵守 NEVER 反向同步规则 |

---

## 验收标准

### 第一层（P0）
- [ ] `aion-test {feature} --heal` 能在测试失败时自动诊断并尝试修复
- [ ] 自愈循环最多 3 轮，有明确的退出条件
- [ ] 自愈报告记录每轮修复内容和理由
- [ ] `aion-verify --fix` 能自动修复 lint 问题和尝试修复测试失败
- [ ] `--fix` 不改变默认 verify 行为（纯报告模式不变）

### 第二层（P1）
- [ ] `aion-test e2e` 在无 Playwright MCP 时生成脚本（e2e-gen）
- [ ] `aion-test e2e` 在有 Playwright MCP 时控制浏览器执行（e2e-live）
- [ ] 自然语言测试定义格式文档完整，含示例
- [ ] Given/When/Then + Edge Cases 结构清晰
- [ ] Playwright MCP 检测 + 安装指引正确输出

### 第三层（P2）
- [ ] `aion-test pipeline` 依次调用 5 个子代理
- [ ] 代理间上下文链式传递
- [ ] 哨兵有 BLOCK 权力，能回退管道
- [ ] 治疗师自愈循环正常工作
- [ ] 中间产物存储在 `.aion/tests/pipeline/`

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| 自愈循环误修改正确代码 | spec 对比 + 最多 3 轮 + 每轮限 3 文件 |
| Playwright MCP 不稳定 | 双模式降级（live → gen） |
| 多代理管道 token 消耗大 | pipeline 模式 opt-in，非默认 |
| 自然语言测试定义歧义 | 严格 Given/When/Then 格式 + 解析验证 |
