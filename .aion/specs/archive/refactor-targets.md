---
status: completed
created_at: 2026-03-21
version: 1
author: unknown
scope: full
change_reason: null
---

# Refactor Targets

## Code Smells Detected

### dashboard.py — 4437 lines, single file
- **Embedded HTML** (~3000 lines): `HTML_PAGE` 和 `MONITOR_HTML` 字符串常量占文件 2/3 以上。可提取为独立 `.html` 文件，运行时读取。
- **路由匹配缺乏抽象**: `do_GET()` 中 17 个 `if path.startswith()` 链式判断，新增端点需小心插入位置。可考虑简单的路由注册表。
- **手写 YAML 解析器**: `read_team_config()` + `write_team_config()` 约 100 行，仅支持扁平结构。如果 team.yml 结构扩展会很脆弱。

### uninstall.sh — 硬编码不完整
- 只删除 11 个命令文件，实际 18 个。每次新增命令都需手动维护列表。可改为动态扫描 `.claude/commands/aion-*.md`。

## Dependency Issues
- 无外部依赖（零依赖约束），无此类问题

## Performance Concerns
- **events.jsonl 增长**: 已有尾部读取优化（>1MB 只读最后 200KB），但文件本身无轮转机制
- **SSE 轮询间隔**: 固定 2 秒，高频场景可能不够响应

<!-- aion:fingerprint:1a93f1c55ed0ca2798f81fcaac5846fc -->
