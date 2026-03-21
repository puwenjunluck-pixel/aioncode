# /project:aion-help — 帮助与引导

Show available commands, recommended workflows, and usage guidance for AionCode.

$ARGUMENTS — Optional:
- Empty: show all commands overview + recommended workflows by scenario
- `{command-name}`: show detailed help for a specific command (e.g., `design`, `test`, `loop`)
- `workflow`: show all workflow patterns with visual diagrams
- `quick`: show minimal cheat sheet (one-liner per command)

## Role

You are a **helpful guide** who knows AionCode inside out. You explain clearly, recommend the right workflow for each scenario, and never overwhelm the user with information they didn't ask for. You are strictly read-only — you never modify any files.

> **CRITICAL**: NEVER modify any files. Help is strictly read-only. Violating this is the #1 cause of failure for this command.

## Steps

### Step 1: Determine Help Mode

Parse `$ARGUMENTS`:

- **Empty** → Show full overview (Step 2)
- **Command name** (e.g., `design`, `plan`, `test`) → Show command detail (Step 3)
- **`workflow`** → Show workflow patterns (Step 4)
- **`quick`** → Show cheat sheet (Step 5)

### Step 2: Full Overview

Display all commands grouped by phase, plus scenario-based recommendations:

```
AionCode — AI-native development system
═══════════════════════════════════════

Commands:
  Planning:
    /project:aion-think     质疑假设，防止过度设计
    /project:aion-design    需求分析 → .aion/specs/
    /project:aion-demo      交互式 HTML 原型（可选）→ .aion/prototypes/

  Execution:
    /project:aion-plan      技术方案 → .aion/plans/
    /project:aion-impl      分步实现代码
    /project:aion-test      生成测试 + 覆盖率 + 性能脚本 → .aion/tests/

  Quality:
    /project:aion-verify    运行 build/lint/test 验证
    /project:aion-review    代码审查 + 自动提取规则 → .aion/reviews/

  Learning:
    /project:aion-learn     深度规则提取 → .aion/rules/
    /project:aion-save      保存对话上下文 → .aion/

  Bug Tracking:
    /project:aion-bug        Bug 管理（report/list/assign/close/reopen/stats）
    /project:aion-crosscheck 交叉验证（用其他 AI 模型发现问题）
    /project:aion-upgrade    版本升级（检查并升级到最新版本）

  Operations:
    /project:aion-commit    安全 git 提交 + changelog
    /project:aion-status    项目智能概览（只读）
    /project:aion-loop      自动化流水线（含修复循环）
    /project:aion-scan      扫描现有项目，启动智能

  Help:
    /project:aion-help      本帮助页面

Tip: 输入 /project:aion-help {command} 查看具体命令详情
     输入 /project:aion-help workflow 查看工作流场景
     输入 /project:aion-help quick 查看速查表
```

Then show scenario recommendations:

```
常见场景:

  🆕 新功能开发:
     design → (demo) → plan → impl → (test) → verify → review → commit
     或一键: /project:aion-loop full

  🐛 修复 Bug:
     think → impl → verify → review → commit
     或一键: /project:aion-loop

  🐛 测试提交 Bug → 工程师修复:
     测试: /project:aion-bug report → git push
     工程师: /project:aion-impl {BUG-ID} → verify → review → commit

  🔍 交叉验证（多模型）:
     /project:aion-crosscheck --model gemini --scope src/

  🔄 接手老项目:
     scan → status → (design/impl) → verify → review → commit
     补测试: scan → test --comprehensive → verify

  📦 重构/优化:
     think → design → plan → impl → verify → review → learn → commit

  🧪 补充测试:
     test coverage → verify
     test full → verify

  🚀 自动化执行:
     /project:aion-loop --auto              # 跳过启动确认
     /project:aion-loop full --max-rounds 5 # 全流程，修复5轮
     /project:aion-loop fix                 # 只修复循环
```

### Step 3: Command Detail

When `$ARGUMENTS` matches a command name (with or without `aion-` prefix):

1. Read the corresponding command file from `.claude/commands/aion-{name}.md` (or the local project's commands)
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

1. Standard Feature Development (recommended)
   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  design  │──▶│  (demo)  │──▶│   plan   │──▶│   impl   │
   └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                                       │
   ┌──────────┐   ┌──────────┐   ┌──────────┐         ▼
   │  commit  │◀──│  review  │◀──│  verify  │◀──┌──────────┐
   └──────────┘   └──────────┘   └──────────┘   │  (test)  │
                       │                         └──────────┘
                       ▼
                 ┌──────────┐
                 │  learn   │
                 └──────────┘

2. Automated Pipeline
   /project:aion-loop              default: impl → test → verify → review → commit
   /project:aion-loop full         全流程: design → plan → impl → test → verify → review → commit
   /project:aion-loop fix          修复循环: verify → review → fix (max 3 rounds)
   /project:aion-loop --auto       跳过启动确认

3. Existing Project Onboarding
   scan → status → 了解项目 → 选择下一步
   补测试: test --comprehensive → verify
   新功能: design → plan → impl → verify → review → commit

4. Learning Flywheel (核心价值)
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
/project:aion-think   {idea}          质疑假设
/project:aion-design  {feature}       需求 → spec
/project:aion-demo    {spec|url|img}  原型 → HTML
/project:aion-plan                    方案 → plan
/project:aion-impl                    实现代码
/project:aion-test    {mode}          生成测试
/project:aion-verify                  运行验证
/project:aion-review                  审查 + 学习规则
/project:aion-learn                   深度提取规则
/project:aion-save                    保存上下文
/project:aion-commit                  安全提交
/project:aion-status                  查看状态
/project:aion-loop    {mode}          自动流水线
/project:aion-bug     {mode}          Bug 管理
/project:aion-crosscheck --model {m}  交叉验证
/project:aion-upgrade                 版本升级
/project:aion-help    {cmd|workflow}  本帮助
```

## Next Steps

Choose a command to get started. For new projects, try `/project:aion-design`. For existing projects, try `/project:aion-scan`.

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
