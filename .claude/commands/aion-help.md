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
    /project:aion-scan      扫描现有项目，启动智能
    /project:aion-design    需求分析 → .aion/specs/
    /project:aion-plan      技术方案 → .aion/plans/

  Quality:
    /project:aion-review    代码审查 + 自动提取规则 → .aion/reviews/
    /project:aion-fix       Bug 修复
    /project:aion-qa        浏览器 QA 测试

  Operations:
    /project:aion-commit    安全 git 提交 + changelog
    /project:aion-loop      自动化流水线（含修复循环）
    /project:aion-save      保存对话上下文 → .aion/

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
     design → plan → /project:aion-loop → commit
     手动: design → plan → 实现 → review → commit

  🐛 修复 Bug:
     /project:aion-fix → review → commit
     或一键: /project:aion-loop fix

  🔄 接手老项目:
     scan → design → plan → 实现 → review → commit

  📦 重构/优化:
     design → plan → 实现 → review → commit

  🧪 浏览器 QA:
     /project:aion-qa {url}

  🚀 自动化执行（--auto 模式）:
     /project:aion-loop --auto              # 全自动（commit 仍需确认）
     /project:aion-loop fix --max-rounds 5  # 修复循环，最多5轮
     /project:aion-fix --auto               # 自动修复所有 bug
     /project:aion-qa {url} --auto          # 自动测试+修复
     /project:aion-review --auto            # 机械修复自动应用

  ⚠️ 安全底线: --auto 永不跳过 commit 确认、>5 严重问题仍 STOP
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
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │  design  │──▶│   plan   │──▶│   实现    │
   └──────────┘   └──────────┘   └──────────┘
                                       │
   ┌──────────┐   ┌──────────┐         ▼
   │  commit  │◀──│  review  │◀────────┘
   └──────────┘   └──────────┘

2. Automated Pipeline
   /project:aion-loop              default: 实现 → verify → review → commit
   /project:aion-loop fix          修复循环: verify → review → fix (max 3 rounds)
   /project:aion-loop --auto       全自动（commit 仍需确认）
   /project:aion-loop verify-only  仅验证

3. Existing Project Onboarding
   scan → 了解项目 → 选择下一步
   新功能: design → plan → 实现 → review → commit

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
/project:aion-scan     {--file}       扫描项目，初始化智能
/project:aion-design   {feature}      需求 → spec
/project:aion-plan                    方案 → plan
/project:aion-fix      {BUG-ID}       Bug 修复             --auto ✓
/project:aion-qa       {url}          浏览器 QA 测试        --auto ✓
/project:aion-review                  审查 + 学习规则       --auto ✓
/project:aion-commit                  安全提交              --auto ✓
/project:aion-loop     {mode}         自动流水线            --auto ✓
/project:aion-save                    保存上下文
/project:aion-help     {cmd|workflow} 本帮助

⚠️ --auto 安全底线: commit 确认永不跳过 | >5 严重问题仍 STOP
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
