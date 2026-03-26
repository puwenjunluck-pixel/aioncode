# /project:aion-help — 帮助与引导

Show available commands, recommended workflows, and usage guidance for AionCode.

$ARGUMENTS — Optional:
- Empty: show all commands overview + recommended workflows by scenario
- `{command-name}`: show detailed help for a specific command (e.g., `design`, `review`, `qa`)
- `workflow`: show all workflow patterns with visual diagrams
- `quick`: show minimal cheat sheet (one-liner per command)

## Role

You are a **helpful guide** who knows AionCode inside out. You explain clearly, recommend the right workflow for each scenario, and never overwhelm the user with information they didn't ask for. You are strictly read-only — you never modify any files.

> **CRITICAL**: NEVER modify any files. Help is strictly read-only. Violating this is the #1 cause of failure for this command.

## Steps

### Step 1: Determine Help Mode

Parse `$ARGUMENTS`:

- **Empty** → Show full overview (Step 2)
- **Command name** (e.g., `design`, `plan`, `review`) → Show command detail (Step 3)
- **`workflow`** → Show workflow patterns (Step 4)
- **`quick`** → Show cheat sheet (Step 5)

### Step 2: Full Overview

Display all commands grouped by role, plus scenario-based recommendations:

```
AionCode — AI-native development system
═══════════════════════════════════════

Core Commands (8):
  Discovery:
    /project:aion-scan      扫描项目 → .aion/ 知识库冷启动

  Design & Planning:
    /project:aion-design    挑战假设 + 需求设计 + 方案对比 + (--demo 原型)
    /project:aion-plan      技术规划 + 用户确认后直接执行

  Quality:
    /project:aion-review    verify + 代码审查 + test gap 一站式

  Bug Workflow:
    /project:aion-qa        浏览器 QA 测试 → bug 报告 (+ 自动修复)
    /project:aion-fix       按角色修复 .aion/bugs/ 中的 bug

  Release:
    /project:aion-commit    Tier 1/2/3 智能分级提交 + changelog

  Utilities:
    /project:aion-loop      自动化流水线（含修复循环）
    /project:aion-save      保存对话上下文 → .aion/
    /project:aion-help      本帮助页面

Tip: 输入 /project:aion-help {command} 查看命令详情
     输入 /project:aion-help workflow 查看工作流场景
     输入 /project:aion-help quick 查看速查表
```

Then show scenario recommendations:

```
常见场景:

  🆕 新功能开发（复杂任务）:
     design → plan → [OK → 直接执行] → review → commit
     或一键: /project:aion-loop full

  ⚡ 小改动（Tier 1 快速通道）:
     [直接改] → commit -y（Tier 1 自动提交，跳过 review）
     中等改动: commit（Tier 2 内联审查）

  🐛 发现 + 报告 Bug（测试角色）:
     /project:aion-qa --report-only {url}

  🔧 修复 Bug（开发角色）:
     /project:aion-fix（按角色过滤）→ review → commit

  🐛 QA + 自动修复（全流程）:
     /project:aion-qa {url} → review → commit

  🔄 接手老项目:
     scan → design/plan → review → commit
     补测试: scan → review（test gap 自动发现 + 生成）

  📦 重构/优化:
     design --skip-challenge → plan → review → commit

  🚀 自动化执行:
     /project:aion-loop --auto              # 跳过启动确认
     /project:aion-loop full --max-rounds 5 # 全流程，修复5轮
     /project:aion-loop fix                 # 只修复循环
```

### Step 3: Command Detail

When `$ARGUMENTS` matches a command name (with or without `aion-` prefix):

1. Read the corresponding command file from `.claude/commands/aion-{name}.md`
2. Extract and display:
   - **Purpose** — one-line description
   - **Arguments** — what inputs it accepts
   - **What it does** — numbered step summary (3-5 steps)
   - **Examples** — 2-3 common usage examples
   - **Output** — what files it produces
   - **Tips** — 1-2 practical tips for best results
   - **Related commands** — what to run before/after

Format as a concise, scannable reference card — NOT the full command specification.

### Step 4: Workflow Patterns

Show detailed workflow diagrams for each scenario:

```
Workflow Patterns
═══════════════════════════════════════

1. New Feature (recommended)
   ┌──────────┐   ┌──────────┐   ┌─────────────┐   ┌──────────┐
   │  design  │──▶│   plan   │──▶│  [OK→execute]│──▶│  review  │
   └──────────┘   └──────────┘   └─────────────┘   └────┬─────┘
     内含: 挑战假设                内含: 直接执行              │
     方案对比 + spec               + TDD                    ▼
     (--demo 可选)                                    ┌──────────┐
                                                      │  commit  │
                                                      └──────────┘

2. Bug Fix Workflow
   ┌────────────────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │ qa --report-only   │──▶│   fix    │──▶│  review  │──▶│  commit  │
   └────────────────────┘   └──────────┘   └──────────┘   └──────────┘
   (or: qa {url} → auto-fix in one step)

3. Quick Change (Tier 1)
   [直接改代码] → commit -y  ← Tier 1 自动判断，无需 review

4. Automated Pipeline
   /project:aion-loop              default: plan execute → review → commit
   /project:aion-loop full         全流程: design → plan → execute → review → commit
   /project:aion-loop fix          修复循环: verify → review → fix (max 3 rounds)
   /project:aion-loop --auto       跳过启动确认

5. Existing Project Onboarding
   scan → 了解项目 → 选择下一步
   新功能: design → plan → review → commit
   测试补全: review（自动 test gap 分析）

6. Learning Flywheel (核心价值)
   Write Code → Review → Extract Rules → Rules Loaded Next Time
        ↑                                        ↓
        └──── AI avoids past mistakes ←──────────┘
```

### Step 5: Cheat Sheet

Minimal one-liner per command:

```
AionCode Cheat Sheet
═══════════════════════════════════════
/project:aion-scan                    扫描项目，初始化智能
/project:aion-design  {feature}       挑战假设 + 需求 + 方案对比 → spec
/project:aion-design  --demo          同上 + 生成 HTML 原型
/project:aion-plan                    技术规划 → plan → 用户 OK → 直接执行
/project:aion-review                  verify + 审查 + test gap 一站式
/project:aion-review  --quick         只 verify + 审查（跳过 test gap）
/project:aion-qa      {url}           浏览器 QA → 发现 bug → 自动修复
/project:aion-qa      --report-only   只报告 bug，不改代码
/project:aion-fix                     按角色修复所有 open bug
/project:aion-fix     {BUG-ID}        修复指定 bug
/project:aion-commit                  智能分级提交（Tier 1/2/3）
/project:aion-commit  -y              Tier 1 快速提交（跳过确认）
/project:aion-loop    full            全流程自动化流水线
/project:aion-save                    保存上下文
/project:aion-help    {cmd|workflow}  本帮助
```

## Next Steps

Choose a command to get started. For new projects, try `/project:aion-scan`. For new features, try `/project:aion-design`.

## Checklist
- [ ] Help mode correctly determined from arguments
- [ ] No files modified (read-only operation)
- [ ] Output is concise and scannable
- [ ] Scenario recommendations match user's likely intent

## Anti-Patterns
| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| Modifying any files | Help is read-only; side effects break trust | CRITICAL |
| Showing the full command specification instead of a summary | Users want quick reference, not a manual | HIGH |
| Not showing examples | Examples are the fastest way to understand a command | MEDIUM |
| Dumping all information at once when user asked about one command | Overwhelming the user defeats the purpose of help | MEDIUM |

## Output Format

Depends on mode — see Steps 2-5 for each format.

## Exit Status
- `DONE` — Always. Help is a read-only operation that always succeeds.
