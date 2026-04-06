# AionCode

**AI 原生开发智能框架** — 让 Claude Code 有章可循、越用越聪明。

> AionCode 不是另一个 AI 编码工具。它是运行在 Claude Code 内部的技能包，为 AI 编程添加方法论、项目记忆和团队协作能力。

## 核心理念

每次 AI 编码都从零开始。Claude 不记得你上周踩过的坑、团队约定的代码规范、还是性能优化的经验教训。

**AionCode 用学习飞轮解决这个问题：**

```
编写代码 → 审查 → 提取规则 → 下次自动加载规则
    ↑                                    ↓
    └──── AI 自动避免过去的错误 ←────────┘
```

## 前提条件

- [Claude Code CLI](https://claude.ai/download) — AionCode 的 11 个技能命令在 Claude Code 中运行
- Git — 项目需要是 Git 仓库

## 安装

### macOS (Apple Silicon)

```bash
# 1. 下载
curl -L -o aioncode https://github.com/puwenjunluck-pixel/aioncode/releases/latest/download/aioncode-macos-arm64

# 2. 添加执行权限
chmod +x aioncode

# 3. 移到系统 PATH
sudo mv aioncode /usr/local/bin/

# 4. 解除 macOS 安全限制（首次需要）
xattr -d com.apple.quarantine /usr/local/bin/aioncode

# 5. 验证
aioncode version
```

**如果 curl 下载到 HTML 而非二进制**，改用浏览器直接下载：
1. 打开 [Releases 页面](https://github.com/puwenjunluck-pixel/aioncode/releases/latest)
2. 下载 `aioncode-macos-arm64`
3. 终端执行步骤 2-5

### Windows

```powershell
# 1. 下载（PowerShell）
Invoke-WebRequest -Uri "https://github.com/puwenjunluck-pixel/aioncode/releases/latest/download/aioncode-windows-x64.exe" -OutFile "$env:USERPROFILE\aioncode.exe"

# 2. 移到 PATH 目录（需要管理员权限）
Move-Item "$env:USERPROFILE\aioncode.exe" "C:\Windows\aioncode.exe"

# 3. 验证
aioncode version
```

**或者手动安装：**
1. 打开 [Releases 页面](https://github.com/puwenjunluck-pixel/aioncode/releases/latest)
2. 下载 `aioncode-windows-x64.exe`
3. 重命名为 `aioncode.exe`
4. 放到任意在 PATH 中的目录（如 `C:\Windows\` 或自定义目录）
5. 打开命令提示符，运行 `aioncode version`

### Linux

```bash
# 1. 下载
curl -L -o aioncode https://github.com/puwenjunluck-pixel/aioncode/releases/latest/download/aioncode-linux-x64

# 2. 添加执行权限并移到 PATH
chmod +x aioncode
sudo mv aioncode /usr/local/bin/

# 3. 验证
aioncode version
```

### 从源码安装（开发者）

```bash
git clone https://github.com/puwenjunluck-pixel/aioncode.git
cd aioncode
pip install -e .
aioncode version
```

## 快速开始

### 初始化项目

```bash
cd /path/to/your/project
aioncode init
```

这会创建：
- `.claude/commands/` — 11 个 AI 技能命令
- `.claude/CLAUDE.md` — 项目索引（Claude 每次启动自动加载）
- `.aion/` — 项目智能数据目录（建议提交到 Git）

### 使用命令

在 Claude Code 中打开你的项目，输入命令：

```
/project:aion-scan      扫描现有项目，建立初始规则
/project:aion-design    需求分析 → .aion/specs/
/project:aion-plan      技术方案 → 确认后自动执行
/project:aion-review    代码审查 + 自动提取规则
/project:aion-qa        浏览器 QA 测试 → bug 报告
/project:aion-fix       按角色修复 bug
/project:aion-audit     安全 + 性能审计
/project:aion-commit    安全提交（需 review 通过）
/project:aion-loop      自动化流水线
/project:aion-save      保存上下文到 .aion/
/project:aion-help      查看所有命令和工作流
```

**推荐工作流：**
```
design → plan（自动执行）→ review → commit
```

### 副驾驶面板

```bash
aioncode dashboard
# 打开 http://localhost:19200
```

16 个可视化视图：概览、文件、监控、协作、需求、方案、规则、清单、缺陷、测试、日志、技能、团队、帮助、关于、设置。

## 三大支柱

### 1. 开发方法论
11 个技能命令覆盖完整生命周期：扫描 → 设计 → 规划 → 审查 → QA → 修复 → 审计 → 提交。每个阶段有最佳实践内置。

### 2. 项目智能（核心差异化）
`.aion/rules/` 自动积累项目知识：
- **pitfalls.md** — 项目特有的坑和陷阱
- **style.md** — 团队约定的编码规范
- **perf.md** — 从实践中学到的性能经验

规则在审查时自动提取，每次 Claude 会话自动加载。

### 3. 团队协作
通过 `.aion/` 文件驱动协作：
- 设计师放原型到 `.aion/prototypes/` → 开发者自动读取
- 后端写接口契约到 `.aion/contracts/` → 前端自动遵循
- `/project:aion-save` 保存上下文 → 下一个人自动继承

## 项目结构

```
your-project/
├── .claude/
│   ├── commands/        # 11 个 AionCode 技能命令
│   └── CLAUDE.md        # 项目索引（自动加载）
├── .aion/               # 项目智能数据（建议 git tracked）
│   ├── rules/           # 自动学习的规则
│   ├── specs/           # 需求规格
│   ├── plans/           # 实施方案
│   ├── reviews/         # 审查结果
│   ├── bugs/            # Bug 报告
│   ├── changelog.md     # 工作日志
│   └── team.yml         # 团队配置
└── ...
```

## 学习飞轮

```
第 1 周:  0 条规则  → Claude 犯常见错误
第 2 周:  5 条规则  → Claude 避免同样的错误
第 4 周:  15 条规则 → Claude 了解项目的特殊性
第 8 周:  25 条规则 → Claude 像资深团队成员一样编码
```

## 其他命令

```bash
aioncode dashboard          # 启动副驾驶面板
aioncode dashboard --dev    # 开发模式（含 API 文档）
aioncode upgrade            # 升级到最新版本
aioncode doctor             # 环境诊断
aioncode uninstall          # 卸载（保留 .aion/ 数据）
```

## 卸载

```bash
# 从项目移除命令和配置（保留 .aion/ 数据）
cd /path/to/your/project
aioncode uninstall

# 从系统移除二进制
rm /usr/local/bin/aioncode          # macOS/Linux
del C:\Windows\aioncode.exe         # Windows
```

## License

MIT
