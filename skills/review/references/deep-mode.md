# Deep Mode（`--deep`）— 全项目安全+性能审计

由 SKILL.md Step 0 分发至此：`--deep` 时按本文件执行，替代常规 diff-scope 流程（Step 1-3 / 5 / 5.5）；规则提取与引用维护按下方第 6 条 + SKILL.md Step 4c 执行。

默认 review 是**改动级**（diff scope）；`--deep` 是**项目级**：扫整个代码库，read-only 分析，审计中不修改任何代码。

1. **范围**：全部源文件；排除 `node_modules/`、`vendor/`、`__pycache__/`、`.git/`、`dist/`、`build/` 及 `rules/style.md` 豁免的生成文件；尊重行级 `# audit:ignore` 标记；支持 `--focus security|perf`、`--ignore {pattern}`
2. **Security（S1-S5）**：依赖漏洞（已知 CVE / 未 pin 版本）；硬编码 secrets（`sk-`/`AKIA`/`ghp_`/`Bearer `/`password=`/PRIVATE KEY，含被 git 跟踪的 `.env`）；注入（SQL 拼接、命令执行、XSS、路径穿越）；认证与访问控制（无鉴权端点 / 硬编码角色 / token 无过期 / `allow_origins=["*"]`）；其余 OWASP 静态可查项（弱哈希、prod debug 模式、日志泄敏感数据）
3. **Performance（P1-P5）**：循环内 DB/API 调用（N+1）；算法复杂度（≥3 层嵌套循环、线性查找、无分页）；资源泄漏（无 `with`、连接不还池、无界缓存）；阻塞操作（async 中同步 I/O、整文件读入内存）；冗余计算（热循环内重复昂贵操作、缺 cache）
4. **评分**：Security 与 Performance 各 0-100，按 finding 扣分（critical −20 / high −10 / medium −5 / low −2，floor 0）；Overall = Security×0.6 + Performance×0.4（`--focus` 时聚焦维度 100%）
5. **基线对比**：读 `.aion/reviews/` 中最近的 `audit-*.md`，逐条标 NEW / FIXED / PERSISTENT / REGRESSED，输出 Δ 与分数趋势；无基线则标 "First audit"
6. **规则提取**：跨 ≥2 个文件复发的模式 → `rules/security.md` / `rules/perf.md`（Accumulative 纪律 + Step 4c 引用维护与退役扫描同样执行）
7. **报告**：写入 `.aion/reviews/audit-{YYYY-MM-DD}.md`，frontmatter 含 `date / scope / security_score / performance_score / overall_score / total_findings / critical / high / medium / low`。每条 finding 格式：`- **[severity]** [S2] \`file:line\` — 描述` + `Fix: 具体建议`。**注意**：audit 报告不含 `reviewed_files` / `base_commit`，不解锁 commit 门禁 — 修复审计问题后仍需常规 `/aion:review`。

## Deep Mode Checklist（替代 SKILL.md Checklist 中的 diff-scope 项）

- [ ] 全库扫描完成（非 diff）— 排除项均为内置排除或显式 `--ignore`，无静默抽样
- [ ] 基线对比执行（或标 "First audit"）
- [ ] 报告写入 `audit-{YYYY-MM-DD}.md`（不含门禁字段，不解锁 commit）
- [ ] 规则提取 + Step 4c 引用维护与退役扫描执行

## Deep Mode Anti-Patterns

| Violation | Why it fails | Severity |
|-----------|-------------|----------|
| `--deep` 只扫 diff | 审计是项目级 — 改动级是默认模式的职责 | CRITICAL |
| 审计中修改代码 | audit 是 read-only 分析 — 修复走后续流程 | HIGH |

### Rationalization Prevention

| 借口 | 真相 |
|--------|---------|
| "代码库太大，--deep 抽几个文件看看" | 审计 = 全量扫描。用 `--ignore` 显式排除，不要静默抽样 |
