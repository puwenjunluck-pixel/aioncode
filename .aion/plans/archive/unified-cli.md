---
status: completed
created_at: 2026-03-21
spec: unified-cli.md
version: 1
previous_version: null
change_reason: null
author: waynepo
scope: full
current_step: 0
total_steps: 10
---

# Plan: AionCode v0.4 — Python 统一 CLI 重写

## Architecture Decisions

1. **包结构使用标准 Python 包布局**：`aioncode/` 作为顶级包，`pyproject.toml` 声明 entry_points，开发态用 `pip install -e .`
2. **utils 层先行**：platform/console/integrity/network 是所有命令的基础，必须最先实现
3. **init 命令是核心**：它替代 install.sh 的项目级功能，包含最复杂的逻辑（marker 合并、模板复制、反向同步检测），必须最早实现和验证
4. **dashboard 原样迁入**：不修改 dashboard.py 内部代码，仅调整 imports 和入口适配
5. **templates 打包策略**：用 `importlib.resources` 读取打包内的模板文件，PyInstaller 通过 `--add-data` 包含
6. **argparse 而非 click**：保持依赖最小化，argparse + match/case 足够处理 8 个子命令

## Implementation Steps

### Step 1: 项目脚手架
- **Description**: 创建 Python 包结构、pyproject.toml、__init__.py、__main__.py
- **Files**:
  - 新建 `aioncode/__init__.py`（版本常量）
  - 新建 `aioncode/__main__.py`（`python -m aioncode` 入口）
  - 新建 `aioncode/commands/__init__.py`
  - 新建 `aioncode/utils/__init__.py`
  - 新建 `aioncode/internal/__init__.py`
  - 新建 `pyproject.toml`（entry_points, dependencies: rich, requests）
- **Dependencies**: None
- **Complexity**: small
- **Status**: Not started

### Step 2: Utils 层 — 跨平台基础
- **Description**: 实现四个工具模块
  - `platform.py`：路径统一（pathlib）、权限检测（Unix euid / Windows UAC ctypes）、长路径支持（Windows \\?\）、编码强制（UTF-8）、系统信息
  - `console.py`：rich Console 封装、进度条、状态表格（✅/❌）、彩色输出、确认提示
  - `integrity.py`：MD5 计算、fingerprint 读取/写入、模板对比（匹配/不匹配/无指纹）、CLAUDE.md marker 合并（移植 install.sh L346-384 逻辑）
  - `network.py`：GitHub Releases API 查询最新版本、下载二进制、进度回调
- **Files**:
  - 新建 `aioncode/utils/platform.py`
  - 新建 `aioncode/utils/console.py`
  - 新建 `aioncode/utils/integrity.py`
  - 新建 `aioncode/utils/network.py`
- **Dependencies**: Step 1
- **Complexity**: large
- **关键移植**:
  - `integrity.py` 的 marker 合并逻辑移植自 `install.sh:346-384`
  - `platform.py` 的权限提升需要 Windows ctypes 和 Unix os.geteuid() 双路径
- **Status**: Not started

### Step 3: init 命令 — 项目初始化
- **Description**: 替代 install.sh 的项目级功能。实现：
  - 模板复制（.aion/ 脚手架，跳过已存在文件）
  - 命令复制（commands/*.md → .claude/commands/，无条件覆盖）
  - CLAUDE.md marker 合并（调用 integrity.py）
  - hooks.json / settings.local.json（仅在不存在时创建）
  - 脚手架空目录创建（refs, prototypes, specs, plans, reviews, contracts, monitor, tests, bugs）
  - 反向同步保护（MD5 检测模板修改）
  - 版本写入 .aion/config.yml
  - .gitignore 检查和补充
  - 安装报告输出（rich 渲染）
- **Files**:
  - 新建 `aioncode/commands/init.py`
  - 迁入 `templates/` → `aioncode/internal/templates/`（保留源码仓库副本）
- **Dependencies**: Step 2
- **Complexity**: large
- **关键移植**:
  - install.sh L262-282 的模板分级复制策略
  - install.sh L115-169 的项目类型检测
  - install.sh L30-41 的版本检查逻辑
- **Pitfall 注意**: "Dogfooding 禁止反向同步" — init 只能从内置模板复制到项目，不能反向
- **Status**: Not started

### Step 4: dashboard 命令 — Web UI
- **Description**: 将 dashboard.py 原样迁入 internal/，创建 dashboard 子命令的懒加载入口
  - 迁入时调整 PROJECTS_FILE 和 SCRIPT_DIR 的路径解析逻辑
  - 添加 CLI 参数：`--port`（默认 19200）、`--host`（默认 0.0.0.0）
  - 懒加载：`from aioncode.internal import dashboard`
- **Files**:
  - 迁入 `dashboard.py` → `aioncode/internal/dashboard.py`（微调路径逻辑）
  - 新建 `aioncode/commands/dashboard.py`（薄封装层）
- **Dependencies**: Step 1
- **Complexity**: medium
- **关键调整**:
  - dashboard.py 中 `SCRIPT_DIR` 的计算方式需适配包内运行
  - `PROJECTS_FILE` 路径需要独立于安装位置（用 ~/.aioncode/projects.json 或 XDG 标准）
- **Status**: Not started

### Step 5: install 命令 — 全局安装
- **Description**: 将 aioncode 二进制安装到系统 PATH
  - 检测操作系统，选择安装位置：
    - macOS/Linux：`/usr/local/bin/aioncode` 或 `~/.local/bin/aioncode`
    - Windows：`%LOCALAPPDATA%\AionCode\aioncode.exe`，自动添加到用户 PATH
  - 安装 shell 补全脚本（bash/zsh/fish）
  - 权限提升（sudo / UAC）
  - 幂等：已安装则提示版本信息
- **Files**: 新建 `aioncode/commands/install.py`
- **Dependencies**: Step 2
- **Complexity**: medium
- **Status**: Not started

### Step 6: uninstall 命令
- **Description**: 移植 uninstall.sh 的逻辑到 Python
  - 从 PATH 移除 aioncode 二进制
  - 清理全局配置（shell 补全）
  - 项目级卸载：动态扫描 .claude/commands/aion-*.md 并删除
  - CLAUDE.md marker 感知删除（调用 integrity.py）
  - hooks.json / settings.local.json 备份后删除
  - .aion/ 永不删除
  - 确认机制（输入 "aioncode"）
  - --dry-run 支持
  - rich 渲染卸载报告
- **Files**: 新建 `aioncode/commands/uninstall.py`
- **Dependencies**: Step 2
- **Complexity**: medium
- **关键移植**: uninstall.sh 的四步流程（扫描 → 确认 → 执行 → 报告）
- **Status**: Not started

### Step 7: upgrade 命令
- **Description**: 在线更新机制
  - 调用 network.py 查询 GitHub Releases 最新版本
  - 对比当前版本（aioncode.__version__）
  - 下载对应平台的二进制（macOS-arm64/x64、Linux-x64、Windows-x64）
  - 替换自身（Unix: 原子 rename；Windows: 延迟替换批处理）
  - 进度条显示下载进度
  - 回滚：下载失败不覆盖旧版本
- **Files**: 新建 `aioncode/commands/upgrade.py`
- **Dependencies**: Step 2 (network.py)
- **Complexity**: medium
- **Status**: Not started

### Step 8: doctor / version / clean 命令 (P1)
- **Description**: 三个辅助命令
  - `doctor`：环境诊断（协议完整性、spec 冲突、GitHub 连通性），rich 渲染 ✅/❌ 清单
  - `version`：版本号 + 内置模板版本 + 项目 config.yml 版本 + 新版本检测
  - `clean`：清理 .aion/ 下过期归档（>30天 .v*.md）、events.jsonl 截断、tmp_*/*.bak 文件，交互确认
- **Files**:
  - 新建 `aioncode/commands/doctor.py`
  - 新建 `aioncode/commands/version.py`
  - 新建 `aioncode/commands/clean.py`
- **Dependencies**: Step 2
- **Complexity**: small (each)
- **Status**: Not started

### Step 9: main.py — CLI 调度器
- **Description**: argparse 子命令注册 + match/case 调度
  - 8 个子命令：install, init, upgrade, uninstall, doctor, version, dashboard, clean
  - 全局选项：`--verbose`, `--no-color`, `--version`
  - 无子命令时显示帮助
  - UTF-8 编码初始化（PYTHONUTF8=1）
- **Files**: 新建 `aioncode/main.py`
- **Dependencies**: Step 3-8 (所有命令)
- **Complexity**: small
- **Status**: Not started

### Step 10: 打包与分发
- **Description**: PyInstaller 配置 + GitHub Actions CI
  - `aioncode.spec`：PyInstaller 配置文件，`--onefile --add-data templates`
  - `.github/workflows/release.yml`：矩阵构建（macOS-arm64, macOS-x64, Linux-x64, Windows-x64）
  - 触发条件：tag push（v*）
  - 自动上传 artifacts 到 GitHub Releases
  - 标记 install.sh / uninstall.sh / 根目录 dashboard.py 为 deprecated
- **Files**:
  - 新建 `aioncode.spec`（PyInstaller）
  - 新建 `.github/workflows/release.yml`
  - 修改 `install.sh`（顶部添加 deprecated 注释）
  - 修改 `uninstall.sh`（顶部添加 deprecated 注释）
- **Dependencies**: Step 9
- **Complexity**: medium
- **Status**: Not started

## Verification Strategy
- **Method**: manual_check + build_check
- **Coverage**:
  1. `aioncode init` 在空目录执行，验证 .aion/ 结构与 install.sh 创建的一致
  2. `aioncode init` 在已有 .aion/ 的目录执行，验证幂等性（不覆盖用户文件）
  3. `aioncode dashboard` 启动后访问 localhost:19200 正常
  4. `aioncode version` 显示正确版本号
  5. `aioncode doctor` 输出诊断清单
  6. PyInstaller 打包后二进制在 macOS 上可运行
  7. 中文路径和内容无乱码
- **Commands**:
  ```bash
  pip install -e .
  aioncode init /tmp/test-project
  aioncode dashboard
  aioncode version
  aioncode doctor
  pyinstaller aioncode.spec
  ./dist/aioncode version
  ./dist/aioncode init /tmp/test-project-2
  ```
- **Success criteria**:
  - init 创建的文件列表与 install.sh 输出一致
  - dashboard Web UI 正常访问
  - 打包后二进制 < 100MB
  - 无 Python traceback 错误

## Risks
- **PyInstaller 打包体积**：rich 可能使二进制超 100MB。缓解：使用 `--exclude-module` 排除不需要的 rich 子模块
- **dashboard.py 路径依赖**：迁入包内后 `SCRIPT_DIR` 和 `PROJECTS_FILE` 路径可能失效。缓解：Step 4 中显式处理
- **Windows 测试覆盖**：开发环境是 macOS，Windows 特性（UAC、长路径、GBK）难以本地验证。缓解：GitHub Actions CI 在 Windows runner 上跑 smoke test
- **self-update 的原子性**：upgrade 命令替换自身二进制时，Windows 不允许覆盖正在运行的 .exe。缓解：使用批处理延迟替换策略
