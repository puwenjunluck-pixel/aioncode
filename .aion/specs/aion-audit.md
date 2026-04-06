---
status: completed
created_at: 2026-04-06
version: 1
author: wayne
scope: full
change_reason: null
---

# aion-audit — 安全+性能审计

## Goal
新增 aion-audit 命令，对整个代码库进行项目级安全 + 性能静态审计，输出持久化报告并追踪改进趋势。

## Requirements (P0)

### R1: 安全审计维度
- 依赖漏洞扫描：检查 requirements.txt / pyproject.toml / package.json 中已知漏洞依赖
- 密钥泄露检测：扫描代码和配置文件中的硬编码 key、token、password（正则模式匹配）
- 注入模式：SQL 拼接、命令注入（subprocess + 字符串拼接）、XSS（未转义输出）
- 认证/授权缺陷：无鉴权的 API 端点、硬编码 admin 判断、token 过期未校验
- OWASP Top 10 逐项检查（静态可检测的项）

### R2: 性能审计维度
- N+1 查询模式：循环内数据库/API 调用
- 大 O 嗅探：嵌套循环对大数据集的操作、未分页的全量查询
- 内存泄漏模式：未关闭的文件句柄/连接、无限增长的缓存/列表
- 阻塞操作：同步 I/O 在异步上下文中、大文件一次性读入内存
- 重复计算：循环内重复调用相同函数、缺少缓存的昂贵操作

### R3: 报告生成
- 输出到 `.aion/audits/{YYYY-MM-DD}.md`，格式含 frontmatter（date, scope, score）
- 每条发现包含：severity（critical/high/medium/low）、类型（security/perf）、file:line、描述、建议修复
- 汇总评分：Security Score (0-100) + Performance Score (0-100) + Overall Score

### R4: 基线对比
- 扫描前读取最近一次 audit 报告（如有），扫描后输出 delta：新增/已修复/仍存在
- 趋势指示：Overall Score 上升/下降/持平

### R5: 命令格式
- 默认全量扫描，`--focus security` 或 `--focus perf` 可选聚焦单维度
- 遵循统一命令文件结构（Header → Role → Steps → Checklist → Anti-Patterns → Output → Exit Status）

## Requirements (P1)

### R6: 规则联动
- 审计发现中重复出现（≥2 次）的模式自动提取为 `.aion/rules/security.md` 或 `.aion/rules/perf.md` 规则
- 与 aion-review 共享规则：review 时加载 security/perf 规则作为检查项

### R7: 忽略机制
- 支持 `--ignore {pattern}` 跳过特定文件/目录（如 vendor/、node_modules/、生成文件）
- 支持行内注释 `# audit:ignore` 标记已知误报，审计时跳过该行

## Acceptance Criteria
- 运行 `aion-audit` 输出 `.aion/audits/{date}.md` 报告文件
- 报告包含 Security Score + Performance Score + Overall Score
- 每条发现标注 severity、类型、file:line、描述、建议修复
- 有历史 audit 时输出 delta（新增/已修复/仍存在）和趋势
- `--focus security` 仅输出安全维度，`--focus perf` 仅输出性能维度
- 命令文件符合统一结构规范（style.md 规则 2）
- 命令文件不超过 500 行（style.md 规则 3）

## Constraints
- 纯静态分析，不运行代码、不启动服务、不做 runtime profiling
- 新增 1 个文件：`commands/aion-audit.md`
- 命令总数 10→11，需同步更新 `profiles.py` ALL_COMMANDS 和 `uninstall.sh`（pitfalls 规则 1、8）
- 不重复 aion-review 的变更级审查职责——audit 是项目级，review 是 diff 级
