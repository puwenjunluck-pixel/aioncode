# Spec Template — 设计文档标准结构

<!-- 使用方: /aion:think Phase 7 按此结构生成 .aion/specs/{feature}.md。
     宿主项目若存在 .aion/rules/spec-template.md（项目自定义版），以宿主版为准。 -->

## 通用原则

1. **每段按复杂度 scale** — 一句话能说清的不要写一段；有 nuance 的段落允许 200-300 字
2. **为隔离和清晰而设计** — 每个单元一个明确目的，接口清晰，可独立理解和测试
3. **YAGNI 狠心** — 删掉所有不必要的功能；P0 要真的是 must-have
4. **显式 out-of-scope** — 把不做什么写出来，和做什么一样重要
5. **verification-driven** — 每条 P0 都要对应一条可测验收标准

## Frontmatter

```yaml
---
status: in_review              # draft | in_review | completed | archived — Phase 9 用户批准后改为 completed
created_at: {YYYY-MM-DD}
version: 1
author: {current user, or "unknown"}
scope: {api|web|mobile|infra|full}
change_reason: null            # v2+ 必填，v1 为 null
---
```

## 文档主体结构

```markdown
# {Feature Name}

## 1. Goal (目标)
One sentence. 明确这个 feature 要解决什么问题。

## 2. Context (背景)
为什么要做？(2-5 句)：当前状态（what's broken/missing）、业务/技术驱动、若不做会怎样。

## 3. Requirements
### P0 (必须有)
- {需求 — 具体，可测}
### P1 (锦上添花，本期可延)
- {需求}
> ⚠️ P0/P1 是**承诺级别**，不是优先级排序。P0 一条都不能少。

## 4. Acceptance Criteria (验收标准)
每条必须**可测**（能写成自动化测试或明确的手动复现步骤）。
- [ ] {AC — "当 X 时，系统应 Y，此时用户看到 Z"}

## 5. Architecture (架构)
按复杂度 scale。简单功能 2-3 句；复杂功能分子段：组件 / 数据流 / 接口 / 状态管理 / 隔离边界。

## 6. Error Handling (错误处理)
输入非法时行为；依赖不可用时行为（超时/降级/重试）；用户可见的错误提示。

## 7. Testing Strategy (测试策略)
单元测试覆盖哪些核心逻辑；集成/E2E 覆盖哪些用户路径；性能/安全/兼容性（如适用）。

## 8. Constraints (约束)
技术约束 / 业务约束 / 性能预算。

## 9. Out of Scope (明确不做什么)
- {非目标 — 说明这次不做，避免 scope creep}

## 10. References
Related specs / contracts / prototypes / external refs / `.aion/specs/_product.md`
```

## Self-Review Checklist（Phase 8 使用）

| 维度 | 检查项 |
|---|---|
| **定位** | 准确回应澄清出来的真实需求？有没有跑题？ |
| **一致性** | P0 之间矛盾？需求与 Constraints 冲突？与 `_product.md` 冲突？ |
| **范围** | 能被单个 plan 覆盖？还是需要拆分？ |
| **歧义** | 任一需求可被两种方式理解？挑一种写明确。 |

## 禁忌

- ❌ 占位符："TBD" / "TODO" / "待定" / 空 section
- ❌ 抽象形容词："better" / "fast" / "user-friendly"（不可测）
- ❌ 把实现细节塞进 Requirements（"用 Redux 存 state"是实现，不是需求）
- ❌ 合并 P0 P1（级别混乱 → plan 无法分批）
- ❌ 省略 Out of Scope（scope creep 就是这样开始的）
