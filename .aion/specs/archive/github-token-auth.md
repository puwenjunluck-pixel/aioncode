---
status: completed
created_at: 2026-03-23
version: 1
author: waynepo
scope: api
change_reason: null
---

# GitHub Token 认证支持

## Goal
让 `aioncode upgrade` 在私有仓库下正常工作，通过 `GITHUB_TOKEN` 环境变量认证 GitHub API。

## Requirements (P0)
- `_github_get()` 读取 `GITHUB_TOKEN` 环境变量，有值时添加 `Authorization: token {TOKEN}` header
- `ReleaseInfo` 同时存储 asset 的 API URL（`url` 字段），不仅仅是 `browser_download_url`
- `download_file()` 支持传入自定义 headers（用于认证）
- 有 token 时用 API URL + `Accept: application/octet-stream` 下载（避免重定向丢 header）
- 无 token 时行为不变（兼容公开仓库）

## Requirements (P1)
- 无 token 且 API 返回 401/403 时，提示用户设置 `GITHUB_TOKEN`

## Acceptance Criteria
- 设置 `GITHUB_TOKEN` 后，`aioncode upgrade` 能正确获取私有仓库 release 信息
- 设置 `GITHUB_TOKEN` 后，能正确下载私有仓库 release assets
- 不设置 `GITHUB_TOKEN` 时，公开仓库行为不变
- 无 token 访问私有仓库时，给出明确提示而非静默失败

## Constraints
- 只改 `aioncode/utils/network.py` 和 `aioncode/commands/upgrade.py`
- 不引入新依赖，继续使用 stdlib `urllib`
- token 只从环境变量读取，不持久化存储

## References
- 无
