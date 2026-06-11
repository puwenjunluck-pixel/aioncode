---
category: template
kind: plan
last_updated: 2026-06-12
---

# Plan Template — AionCode 实现计划标准结构

<!-- 使用方: /aion:plan 流程（含 /aion:think Phase 10 主动衔接），按此结构生成 `.aion/plans/{feature}.md`。
     宿主项目若有 `.aion/rules/plan-template.md`，以宿主版为准。 -->

## Core Principles

1. **假设执行者零上下文** — 写 plan 时假设执行这个 plan 的工程师是**熟练但不了解我们代码库/工具链/问题域**的人。所有细节写出来。
2. **Bite-sized steps (2-5 min/step)** — 每个 step 是**一个动作**,不是"一个功能模块"。"Write the failing test" 是一个 step,"Implement auth" 不是。
3. **完整代码,不是占位符** — 如果一个 step 会改代码,把完整代码块写出来。读者可能乱序读,不能让他们靠猜。
4. **精确路径和命令** — 每个 step 写清 `exact/path/to/file.py:123` 和 `pytest tests/xxx::test_name -v`,不要"相关文件"。
5. **DRY. YAGNI. TDD. 频繁 commit.** — 每个 task 结束一次 commit。
6. **Verify = evidence** — 每个 step 有 `Verify` 字段,给出命令和预期输出。没有 Verify 的 step 是残次品。

## Frontmatter

```yaml
---
status: draft                  # draft | in_review | completed | archived
created_at: {YYYY-MM-DD}
spec: {spec filename, e.g. feature-xyz.md}
version: {N}
previous_version: {N-1 or null}
change_reason: "{reason for this version, or null for v1}"
author: {current user from team.yml, or "unknown"}
scope: {api|web|mobile|infra|full}
current_step: 0
total_steps: {N}
---
```

## 文档主体结构

```markdown
# Plan: {Feature Name}

> **For agentic workers:** 用 subagent 逐 task 执行（推荐）或在当前会话逐 task 执行
> （也可用 /aion:loop 自动流水线）。Steps 使用 `- [ ]` checkbox 跟踪。

**Goal:** {One sentence describing what this builds}

**Architecture:** {2-3 sentences about approach}

**Tech Stack:** {Key technologies/libraries}

**Spec:** `.aion/specs/{feature}.md`

---

## Architecture Decisions

- {Key technical choice 1 + rationale,引用 file:line 证据}
- {Key technical choice 2 + rationale}

## File Structure (Files Touched)

在定义 tasks 之前,先列出所有会被创建/修改的文件 + 每个文件的职责。这是 decomposition 决策锁定的地方。

| 文件 | 动作 | 职责 |
|---|---|---|
| `src/foo/bar.py` | Create | 处理 X 逻辑 |
| `src/foo/baz.py:123-145` | Modify | 扩展 Y 行为 |
| `tests/test_bar.py` | Create | 覆盖 bar 单元测试 |

- 设计有清晰边界的单元。每个文件一个清晰职责。
- Files that change together should live together. Split by responsibility, not technical layer.
- 在既有代码库中,follow established patterns。

## Implementation Tasks

### Task N: {Component Name}

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

  ```python
  def test_specific_behavior():
      result = function(input)
      assert result == expected
  ```

- [ ] **Step 2: Run test to verify it fails**

  Run: `pytest tests/path/test.py::test_name -v`
  Expected: `FAIL with "function not defined"`

- [ ] **Step 3: Write minimal implementation**

  ```python
  def function(input):
      return expected
  ```

- [ ] **Step 4: Run test to verify it passes**

  Run: `pytest tests/path/test.py::test_name -v`
  Expected: `PASS`

- [ ] **Step 5: Commit**

  ```bash
  git add tests/path/test.py src/path/file.py
  git commit -m "feat: {concise message}"
  ```

### Task N+1: ...

## Verification Strategy (overall)

- **Method**: `unit_test | integration_test | e2e_test | manual_check | build_check`
- **Coverage**: 覆盖哪些 P0 要求
- **Commands**: 完整验证命令
- **Success criteria**: 通过的定义(exit 0 / N passed / 视觉一致)

## Risks

- {已知风险 + 缓解措施}
```

## No Placeholders — 绝对禁忌

以下是 **plan failures**,发现即删除/填充:

| ❌ 禁忌 | ✅ 替换为 |
|---|---|
| "TBD" / "TODO" / "implement later" / "fill in details" | 具体代码/路径/命令 |
| "Add appropriate error handling" / "handle edge cases" | 明确列出哪些错误、如何处理 |
| "Write tests for the above"(没有测试代码) | 完整 test 函数代码 |
| "Similar to Task N"(不重复细节) | 重复写出来——执行者可能乱序读 |
| Steps that describe what without showing how | code block required if code changes |
| References to undefined types / functions / methods | 先在某个 task 里定义 |

## Self-Review (plan 生成后、呈现给用户前必做)

三维度检查,有问题**就地修**,不要回头重审。自审在落盘前完成 — 用户看到的必须是已审版本:

| 维度 | 检查 |
|---|---|
| **1. Spec Coverage** | 过一遍 spec 每条 P0 / AC。每条能指向实现它的 task(s) 吗?缺失的补上。 |
| **2. Placeholder Scan** | 搜索上方 "No Placeholders" 表里的红旗 pattern。找到就修。 |
| **3. Name Consistency** | 后续 task 用的 types / method signatures / property names 和前面 task 定义的一致吗?一个 `clearLayers()` 在 Task 3 / `clearFullLayers()` 在 Task 7 是 bug。 |

## Execution Handoff (用户确认 + 落盘后)

保存到 `.aion/plans/{feature-name}.md` 后,向用户提供执行选项:

> Plan 已保存到 `.aion/plans/{filename}.md`。如何执行?
>
> **(a) Subagent-Driven (推荐)** — 每个 task 派一个新 subagent,task 间 review,快速迭代
> **(b) Inline** — 本会话内逐 task 执行,每 task 完成后 pause 供 review
> **(c) 暂不执行** — 保留 plan,后续再触发

若选 (a):用 Agent 工具逐 task 派发,或 `/aion:loop` 自动流水线。
若选 (b):在当前会话逐 task 执行,按每个 step 的 Verify 验证,checkpoint 分批 review。
若选 (c):退出,plan 保留供后续触发。

## 禁忌

- ❌ 步骤过大(> 10 分钟 / 覆盖多文件)— 拆细
- ❌ 没有 Verify — 无法确认 step 做对了
- ❌ 占位符 — 见上表
- ❌ 不引用 spec 就写 plan — plan 必须 trace 回 spec 的 AC
- ❌ 忽略 `.aion/rules/` / `.aion/contracts/` — 知道的坑不能再掉
