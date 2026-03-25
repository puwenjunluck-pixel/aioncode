---
status: completed
created_at: 2026-03-21
version: 1
author: waynepo
scope: full
change_reason: null
---

# AionCode v0.4 — Python 统一 CLI 重写

## Goal
将 install.sh / uninstall.sh / dashboard.py / upgrade 合并为跨平台（Windows/Mac/Linux）统一 Python CLI 工具 `aioncode`，通过 PyInstaller 打包为单文件自包含二进制分发。

## 架构设计

### 包结构
```
aioncode/
├── __main__.py          # python -m aioncode 入口
├── main.py              # CLI 调度（argparse + match/case）
├── commands/
│   ├── install.py       # 全局安装（二进制 → PATH，shell 补全）
│   ├── init.py          # 项目初始化（.aion/ 脚手架）
│   ├── upgrade.py       # 在线更新（GitHub Releases）
│   ├── uninstall.py     # 全局卸载
│   ├── doctor.py        # 环境诊断
│   ├── version.py       # 版本 + 自举状态
│   ├── dashboard.py     # 启动 Web UI（懒加载 internal）
│   └── clean.py         # 清理 .aion/ 临时文件
├── internal/
│   ├── dashboard.py     # 现有 dashboard.py 原样迁入
│   └── templates/       # 现有 templates/ 迁入（打包时 bundle）
├── utils/
│   ├── platform.py      # 跨平台：权限提升、路径、长路径、编码
│   ├── console.py       # rich 封装：颜色、进度条、表格
│   ├── integrity.py     # MD5 反向同步检测 + fingerprint
│   └── network.py       # GitHub API 版本检查 + 下载
└── pyproject.toml        # 构建配置（entry_points, dependencies）
```

### 子命令设计

#### Admin 维度（全局/环境级）

| 命令 | 说明 | 对标 |
|------|------|------|
| `aioncode install` | 将自身复制到系统 PATH，安装 shell 补全，检查全局依赖 | 新增 |
| `aioncode upgrade` | 从 GitHub Releases 下载最新版本替换自身 | install.sh --upgrade |
| `aioncode uninstall` | 从 PATH 移除，清理全局配置 | uninstall.sh |
| `aioncode doctor` | 环境诊断：Python 版本、协议完整性、spec 冲突、API 连通性 | install.sh --check |
| `aioncode version` | 显示版本号 + 模板版本 + 模型后端 | 新增 |

#### Project 维度（项目/目录级）

| 命令 | 说明 | 对标 |
|------|------|------|
| `aioncode init` | 在当前目录创建 .aion/ + .claude/ 脚手架，复制模板 | install.sh |
| `aioncode dashboard` | 启动 Web UI (localhost:19200) | python dashboard.py |
| `aioncode clean` | 清理 .aion/ 下过期计划、临时文件、PK 残留 | 新增 |

### 关键技术决策

#### 1. 依赖约束（更新）
- **开发态**：允许引入成熟第三方库（rich, requests, PyInstaller）
- **分发物**：必须是单文件自包含二进制（.exe / Unix executable）
- **用户无需预装 Python 或任何库**

#### 2. 跨平台处理（utils/platform.py）
- **权限提升**：Windows 用 `ctypes.windll.shell32.ShellExecuteW` 请求 UAC；Unix 用 `os.geteuid()` 检测 + sudo 提示
- **路径统一**：全部使用 `pathlib.Path`，终结 `\` vs `/`
- **长路径支持**：Windows 自动启用 `\\?\` 前缀（注册表检测 `LongPathsEnabled`）
- **编码强制**：所有 `open()` 强制 `encoding='utf-8'`，启动时设置 `PYTHONUTF8=1`

#### 3. 反向同步保护（utils/integrity.py）
- `aioncode init` 执行时，对每个模板文件计算 MD5
- 升级时比对本地 .aion/ 文件与内置模板的 MD5：
  - 匹配 → 安全覆盖
  - 不匹配 → 提示："检测到模板被手动改动，是否保留？"
- 与 Write Protocol 的 Regenerable 类型对齐

#### 4. dashboard.py 处理
- 原样迁入 `aioncode/internal/dashboard.py`
- 懒加载导入，不重构内部代码
- `aioncode dashboard` 调用 `dashboard.run_server()`
- 内部重构（拆 HTML、路由注册表）推迟到 v0.5

#### 5. 分发方式
- PyInstaller 打包为单文件：`aioncode`（Unix）/ `aioncode.exe`（Win）
- GitHub Actions CI 矩阵构建：macOS-arm64、macOS-x64、Linux-x64、Windows-x64
- 通过 GitHub Releases 分发
- 安装流程：下载 → `./aioncode install` → 完成

#### 6. doctor 检查项
- 环境：Python 版本（if 源码运行）、系统信息
- 协议：.aion/refs/write-protocol.md 存在且完好
- 冲突：多 author 在同一 spec 上的并发修改检测
- 连通性：GitHub API 可达（升级用）
- 输出：rich 渲染的 ✅/❌ 清单

#### 7. version 输出
- aioncode 二进制版本（v0.4.x）
- 内置模板版本
- 当前项目 .aion/config.yml 版本（如果在项目目录内）
- 检测是否有新版本可用

#### 8. clean 策略
- 清理 `.aion/plans/*.v*.md` 中超过 30 天的归档版本
- 清理 `.aion/monitor/events.jsonl` 超过 1MB 的部分（保留最近 200KB）
- 清理孤立的临时文件（`tmp_*`, `*.bak`）
- 交互确认后执行，显示将清理的文件列表和预计释放空间

## Requirements (P0)
- Python 3.10+ 开发，使用 match/case 语法
- 跨平台支持：Windows 10+、macOS 12+、Linux（glibc 2.31+）
- 单文件自包含二进制分发（PyInstaller）
- `aioncode init` 实现完整的项目初始化（替代 install.sh 的项目级功能）
- `aioncode install` 实现全局安装（自身 → PATH）
- `aioncode dashboard` 启动 Web UI
- `aioncode upgrade` 在线更新
- `aioncode uninstall` 安全卸载
- 反向同步保护（MD5 检测模板修改）
- UTF-8 编码强制
- Windows 长路径支持
- CLAUDE.md marker 合并策略保持不变

## Requirements (P1)
- `aioncode doctor` 环境诊断
- `aioncode version` 版本 + 自举状态
- `aioncode clean` 清理临时文件
- Shell 补全（bash, zsh, fish）
- rich 终端渲染（进度条、彩色表格、✅/❌ 清单）
- GitHub Actions CI 自动构建四平台二进制

## Acceptance Criteria
- 在 Windows 11、macOS 14、Ubuntu 22.04 上分别验证 `aioncode init` + `aioncode dashboard` 正常运行
- 打包后二进制为单文件，体积 < 100MB
- `aioncode init` 创建的 .aion/ 结构与现有 install.sh 创建的完全一致
- `aioncode upgrade` 能从 GitHub Releases 检测并下载新版本
- 中文文件名和内容在 Windows GBK 环境下无乱码
- MD5 检测能正确识别模板被用户修改的情况

## Constraints
- 不重构 dashboard.py 内部代码（v0.5 再做）
- install.sh 保留在仓库但标注 deprecated，不再维护
- 命令文件（commands/*.md）仍然是 Markdown，不变
- templates/ 迁入包内后，源码仓库中保留副本用于开发调试

## 废弃清单
| 文件 | 处置 |
|------|------|
| install.sh | 标注 deprecated，仓库保留不维护 |
| uninstall.sh | 标注 deprecated，仓库保留不维护 |
| dashboard.py（根目录） | 迁入 aioncode/internal/，根目录保留软链或删除 |

## References
- .aion/refs/write-protocol.md — 反向同步保护对齐 Regenerable 策略
- .aion/refs/architecture.md — 现有架构（将被本 spec 取代）
- .aion/specs/refactor-targets.md — dashboard.py 已知技术债（v0.5 处理）
- .aion/rules/pitfalls.md — "Dogfooding 禁止反向同步" 规则
