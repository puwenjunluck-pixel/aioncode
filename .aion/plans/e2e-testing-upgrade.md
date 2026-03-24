---
status: completed
created_at: 2026-03-23
spec: e2e-testing-upgrade.md
version: 1
previous_version: null
change_reason: null
author: waynepo
scope: full
current_step: 8
total_steps: 8
---

# Plan: 测试体系升级 — 自愈 + E2E + 多代理管道

## Architecture Decisions

1. **aion-test.md 保持单文件** — 三层新模式（`--heal`、`e2e`、`pipeline`）作为新 Step 追加到现有命令中，而非拆分为多个命令。理由：用户已习惯 `aion-test` 入口，多模式是现有模式的自然延伸。
2. **自愈逻辑作为可复用模块** — `--heal` 的核心诊断+修复循环写成独立 Section，`aion-verify --fix` 和 `pipeline` 中的治疗师代理均引用此 Section，避免三处重复定义。
3. **与 aion-loop fix loop 对齐** — `aion-loop` 已有 fix loop（`aion-loop.md:79-98`），其 Step 3 处理 verify/review 失败的循环。新增的 `--heal` 聚焦于**测试级别**的自愈（Traceback 分析+spec 对比），而 loop 的 fix loop 聚焦于**管道级别**的修复。两者互补不冲突。
4. **E2E 双模式降级** — `e2e-live`（需 Playwright MCP）和 `e2e-gen`（纯脚本生成）共用同一入口 `e2e`，通过环境检测自动切换。
5. **自然语言测试定义为 Regenerable 产物** — `.aion/tests/e2e/*.md` 遵循 Write Protocol 的 Regenerable 类别（用户可修改，写前检查指纹）。但用户手写的测试定义不加指纹（它们是源文件，不是生成物）。定义文件本身归类为**用户维护文件**，不受 Write Protocol 管辖。
6. **pipeline 模式使用 Agent 子代理** — 每个阶段用 `Agent` 工具启动独立子代理，通过中间文件 `.aion/tests/pipeline/{feature}/` 传递上下文。

## Implementation Steps

### Step 1: aion-test.md — 新增自愈核心逻辑 Section

- **Description**: 在 `aion-test.md` 现有 Step 4（UI）和 Step 5（Report）之间插入两个新 Step：
  - **Step 5 (NEW): Execute Tests** — 运行测试套件，捕获输出
  - **Step 6 (NEW): Self-Healing Loop** — 失败诊断 + spec 对比 + 修复 + 重试（最多 3 轮）
  - 原 Step 5（Report）变为 Step 7
  - 在 `$ARGUMENTS` 区域追加 `--heal` 选项说明
  - 在 Anti-Patterns 表追加自愈相关反模式
  - 在 Output Format 追加自愈报告段
  - 在 Checklist 追加自愈检查项
- **Files**: `commands/aion-test.md`
- **Dependencies**: None
- **Complexity**: large

### Step 2: aion-test.md — 新增 E2E 测试模式

- **Description**: 追加 `e2e` 模式到 `aion-test.md`：
  - 在 `$ARGUMENTS` 区域追加 `e2e` 模式说明
  - 在 Step 0.5（Detect Test Infrastructure）追加 Playwright MCP 检测逻辑
  - 新增 **Step 4.5: E2E Testing** — 包含 e2e-gen（脚本生成）和 e2e-live（MCP 执行）两个子模式
  - 新增自然语言测试定义解析逻辑（读取 `.aion/tests/e2e/*.md`，解析 Given/When/Then）
  - 在 Anti-Patterns 表更新 Playwright 规则（从全面禁止改为条件允许）
- **Files**: `commands/aion-test.md`
- **Dependencies**: Step 1（Step 编号依赖）
- **Complexity**: large

### Step 3: aion-test.md — 新增多代理管道模式

- **Description**: 追加 `pipeline` 模式到 `aion-test.md`：
  - 在 `$ARGUMENTS` 区域追加 `pipeline` 模式说明
  - 新增 **Step 8: Multi-Agent Pipeline** — 定义 5 阶段（分析师→规划师→工程师→哨兵→治疗师）的子代理编排
  - 每阶段定义：代理 prompt 摘要、输入/输出、使用的 Agent 子代理类型和工具限制
  - 哨兵质量门禁 BLOCK/WARN 表
  - 代理间上下文链式传递规则
  - 中间产物存储路径
- **Files**: `commands/aion-test.md`
- **Dependencies**: Step 1, Step 2（Step 编号依赖）
- **Complexity**: large

### Step 4: aion-verify.md — 新增 --fix 自动修复模式

- **Description**: 在 `aion-verify.md` 中追加 `--fix` 模式：
  - 在 `$ARGUMENTS` 区域追加 `--fix` 选项说明
  - Step 3（Lint Check）：`--fix` 时自动运行 `ruff check --fix` / `eslint --fix`，然后重新检查
  - Step 4（Test Suite）：`--fix` 时触发自愈循环（引用 `aion-test --heal` 的核心逻辑）
  - Step 1（Build Check）：`--fix` 时分析 build 错误并尝试修复（缺失 import、类型错误等常见问题）
  - 新增 Step 5.5: Fix Summary — 输出所有自动修复的汇总
  - 在 Output Format 追加 fix 模式的输出段
  - 在 Anti-Patterns 表追加 fix 相关反模式
- **Files**: `commands/aion-verify.md`
- **Dependencies**: Step 1（引用自愈逻辑）
- **Complexity**: medium

### Step 5: 更新 pitfalls.md — 修改 Playwright 规则

- **Description**: 修改 `.aion/rules/pitfalls.md` 中的 Playwright 相关 Anti-Pattern 规则：
  - 原规则："Running Playwright or full browser automation" → NEVER
  - 新规则："Running Playwright browser automation WITHOUT MCP or outside `aion-test e2e` mode" → NEVER
  - 追加新规则：**NEVER 在非 e2e 模式下调用 Playwright MCP** — 浏览器自动化仅限于 `aion-test e2e` 模式
  - 遵循 Accumulative 写入协议：先读取现有内容去重，再追加/更新
- **Files**: `.aion/rules/pitfalls.md`
- **Dependencies**: Step 2（E2E 模式定义完成后才能更新规则）
- **Complexity**: small

### Step 6: 更新 test.md 检查清单

- **Description**: 扩展 `.aion/checklists/test.md`，新增三个 Section：
  - **Self-Healing** — 自愈前确认 spec 存在、自愈后验证修复不引入新问题
  - **E2E Testing** — 自然语言测试定义已解析、Playwright MCP 检测完成、截图已保存
  - **Pipeline** — 各阶段代理输出完整、哨兵审计通过、中间产物已存储
  - 遵循 Regenerable 写入协议：检查指纹后写入
- **Files**: `.aion/checklists/test.md`
- **Dependencies**: None
- **Complexity**: small

### Step 7: 创建 .aion/tests/e2e/README.md — 格式规范

- **Description**: 创建自然语言测试定义的格式说明文档：
  - YAML Frontmatter 规范（feature、target_url、viewport、preconditions）
  - Given/When/Then 语法说明
  - Edge Cases 节的用法
  - TC-ID 编号规则（TC-001, TC-002...）
  - 最佳实践（一个文件一个 feature、步骤要具体可执行、Then 要可验证）
  - 与 `aion-test e2e` 的集成说明
- **Files**: `.aion/tests/e2e/README.md`（新建）
- **Dependencies**: None
- **Complexity**: small

### Step 8: 创建 .aion/tests/e2e/_example.md — 示例测试

- **Description**: 创建一个完整的示例测试定义文件，以 AionCode Dashboard 为例：
  - 覆盖 Dashboard 的核心用户流程（访问首页、查看项目状态、切换视图）
  - 展示 Frontmatter、Given/When/Then、Edge Cases 的完整用法
  - 包含多 viewport 场景（desktop、mobile）
  - 作为测试人员的起步模板
- **Files**: `.aion/tests/e2e/_example.md`（新建）
- **Dependencies**: Step 7（格式规范先行）
- **Complexity**: small

## Verification Strategy

- **Method**: `manual_check`
- **Coverage**:
  - 所有命令文件语法正确、结构完整（Header → Arguments → Role → Steps → Checklist → Anti-Patterns → Output → Exit Status）
  - `aion-test.md` 的 `--heal`、`e2e`、`pipeline` 三个模式的 Step 编号连贯，无跳号或冲突
  - `aion-verify.md` 的 `--fix` 模式不影响默认行为（默认路径无变化）
  - `pitfalls.md` 规则更新遵循 Accumulative 协议
  - `test.md` 检查清单覆盖三层能力
  - `.aion/tests/e2e/README.md` 格式说明清晰，与 `_example.md` 一致
- **Commands**:
  - `wc -l commands/aion-test.md commands/aion-verify.md` — 确认文件未超预期
  - `grep -c "### Step" commands/aion-test.md` — 确认 Step 编号完整
  - `grep "NEVER" .aion/rules/pitfalls.md` — 确认规则更新
- **Success criteria**: 所有文件可被 Claude Code 正确加载和执行，无语法错误或结构缺失

## Risks

| 风险 | 缓解 |
|------|------|
| `aion-test.md` 过长（当前 357 行 + 三层新增估计 400+ 行） | 各模式 Step 尽量引用共享逻辑（如自愈 Section），避免重复。如超 800 行再考虑拆分 |
| 自愈循环与 aion-loop fix loop 职责模糊 | 明确分工：`--heal` 是测试级自愈（单次 Traceback 修复），loop fix 是管道级修复（跨 verify+review）|
| pipeline 子代理 token 消耗 | pipeline 模式 opt-in，默认不触发。每个子代理只给必要上下文 |
| 修改 Playwright 规则后可能被滥用 | 新规则严格限定在 `aion-test e2e` 模式 + Playwright MCP 已配置双条件下 |
