---
category: template
kind: spec
last_updated: 2026-04-14
---

# Spec Template — AionCode 设计文档标准结构

<!-- 本模板综合 AionCode 现有 spec 格式 + superpowers:brainstorming 的 design 章节结构。
     See .aion/CREDITS.md
     使用方: aion-think 的 Phase 7 "写设计文档并提交" 按此结构生成 `.aion/specs/{feature}.md`
-->

## 通用原则

1. **每段按复杂度 scale** — 一句话能说清的不要写一段;有 nuance 的段落允许 200-300 字
2. **为隔离和清晰而设计** — 每个单元一个明确目的,接口清晰,可独立理解和测试
3. **YAGNI 狠心** — 删掉所有不必要的功能;P0 要真的是 must-have
4. **显式 out-of-scope** — 把不做什么写出来,和做什么一样重要
5. **verification-driven** — 每条 P0 都要对应一条可测验收标准

## Frontmatter

```yaml
---
status: completed              # draft | in_review | completed | archived
created_at: {YYYY-MM-DD}
version: 1
author: {current user from team.yml, or "unknown"}
scope: {api|web|mobile|infra|full}
change_reason: null            # v2+ 必填,v1 为 null
---
```

## 文档主体结构

```markdown
# {Feature Name}

## 1. Goal (目标)

One sentence. 明确这个 feature 要解决什么问题。

## 2. Context (背景)

为什么要做?(2-5 句)
- 当前状态是什么(what's broken / missing)
- 业务/技术驱动(谁要它/哪个指标/哪个合规)
- 若不做会怎样

## 3. Requirements

### P0 (必须有)
- {需求 1 — 具体,可测}
- {需求 2}

### P1 (锦上添花,本期可延)
- {需求}

> ⚠️ P0/P1 区分是**承诺级别**,不是"优先级排序"。P0 一条都不能少。

## 4. Acceptance Criteria (验收标准)

每条必须**可测**(能写成自动化测试或明确的手动复现步骤)。

- [ ] {AC 1 — "当 X 时,系统应 Y,此时用户看到 Z"}
- [ ] {AC 2}

## 5. Architecture (架构)

按复杂度 scale。简单功能 2-3 句即可;复杂功能分子段:

- **组件**:涉及哪些模块/文件/服务
- **数据流**:输入 → 处理 → 输出
- **接口**:和外部/上下游的契约(如有,引用 `.aion/contracts/`)
- **状态管理**:持久化/缓存/会话
- **隔离边界**:什么是这个 feature 的内部细节,什么是公开接口

## 6. Error Handling (错误处理)

- 输入非法时行为
- 依赖不可用时行为(超时/降级/重试)
- 用户可见的错误提示

## 7. Testing Strategy (测试策略)

- 单元测试覆盖哪些核心逻辑
- 集成/E2E 测试覆盖哪些用户路径
- 性能/安全/兼容性测试(如适用)
- 测试资产位置(`.aion/tests/e2e/*.md` 等)

## 8. Constraints (约束)

- 技术约束(必须兼容 X / 不能引入 Y 依赖)
- 业务约束(预算 / 时间窗)
- 性能预算(响应时间/资源占用)

## 9. Out of Scope (明确不做什么)

- {非目标 1 — 说明这次不做,避免 scope creep}
- {非目标 2}

## 10. References

- Related specs: `.aion/specs/{other}.md`
- Contracts: `.aion/contracts/{name}.md` (if applicable)
- Prototypes: `.aion/prototypes/{name}.html`
- External refs: `.aion/refs/{doc}.md`
- Product landscape: `.aion/specs/_product.md`
```

## Self-Review Checklist (aion-think Phase 8 使用)

写完 spec 后,用"新鲜眼睛"检查 4 个维度,有问题**就地修,不要回头重看**:

| 维度 | 检查项 |
|---|---|
| **定位 (Positioning)** | Spec 是否准确回应了 Phase 2 澄清出来的真实需求?有没有跑题? |
| **一致性 (Consistency)** | P0 之间有无矛盾?需求与 Constraints 有无冲突?和 `_product.md` 有无冲突? |
| **范围 (Scope)** | 能被单个 plan 覆盖吗?还是跨了多个独立子系统(需要拆分)? |
| **歧义 (Ambiguity)** | 任何一条需求是否可能被两种方式理解?如果是,挑一种写明确。 |

## 禁忌

- ❌ 占位符:"TBD" / "TODO" / "待定" / 空 section
- ❌ 抽象形容词:"better" / "fast" / "user-friendly"(不可测)
- ❌ 把实现细节塞进 Requirements("用 Redux 存 state"是实现,不是需求)
- ❌ 合并 P0 P1(级别混乱 → 后续 plan 无法分批)
- ❌ 省略 Out of Scope(scope creep 就是这样开始的)
