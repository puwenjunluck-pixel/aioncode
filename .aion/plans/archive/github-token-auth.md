---
status: completed
created_at: 2026-03-23
spec: github-token-auth.md
version: 1
previous_version: null
change_reason: null
author: waynepo
scope: api
current_step: 0
total_steps: 3
---

# Plan: GitHub Token 认证支持

## Architecture Decisions
- token 来源：仅 `GITHUB_TOKEN` 环境变量，读取一次缓存为模块级变量
- 下载策略：有 token 时用 asset API URL + `application/octet-stream`；无 token 时保持 `browser_download_url`
- 认证 header 统一通过 `_build_headers()` 辅助函数生成，避免散落多处
- P1 提示：在 `upgrade.py` 中 `get_latest_release()` 返回 None 时检查是否有 token，给出提示

## Implementation Steps

### Step 1: network.py — 添加认证支持
- **Description**:
  1. 新增 `_get_token()` 函数，读取 `os.environ.get("GITHUB_TOKEN")`
  2. 新增 `_build_headers()` 函数，统一构建 headers（含可选 Authorization）
  3. `_github_get()` 使用 `_build_headers()`
  4. `ReleaseInfo.__init__` 增加存储 asset API URL（`url` 字段）到 `self.api_urls` 字典
  5. `ReleaseInfo.get_binary_url()` 改为返回 `(url, is_api)` 元组，有 token 时优先返回 API URL
  6. `download_file()` 增加 `headers: dict | None` 参数，有值时合并到请求 headers
- **Files**: `aioncode/utils/network.py`
- **Dependencies**: None
- **Complexity**: medium

### Step 2: upgrade.py — 适配认证下载
- **Description**:
  1. 适配 `get_binary_url()` 新返回值
  2. 有 token 时构建认证 headers 传给 `download_file()`
  3. `get_latest_release()` 返回 None 时，检查无 token 则提示 "私有仓库需设置 GITHUB_TOKEN 环境变量"（P1）
- **Files**: `aioncode/commands/upgrade.py`
- **Dependencies**: Step 1
- **Complexity**: small

### Step 3: 手动验证
- **Description**: 设置 `GITHUB_TOKEN` 环境变量，运行 `aioncode upgrade` 验证
- **Files**: 无
- **Dependencies**: Step 1, Step 2
- **Complexity**: small

## Verification Strategy
- **Method**: manual_check + build_check
- **Coverage**: 有 token / 无 token 两种场景
- **Commands**:
  - `ruff check aioncode/utils/network.py aioncode/commands/upgrade.py`
  - `python -m pytest tests/ -x`
  - `GITHUB_TOKEN=xxx python -m aioncode upgrade`（source 模式验证 API 调通）
- **Success criteria**: lint 通过，现有测试不回归，有 token 时能获取到 release 信息

## Risks
- urllib 重定向时丢 Authorization header → 已通过 API URL + octet-stream 规避
- token 无效时 GitHub 返回 401 → 在错误提示中包含 "请检查 GITHUB_TOKEN 是否有效"
