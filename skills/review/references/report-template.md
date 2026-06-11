# Review 报告模板

写入 `.aion/reviews/{feature-name}.md`。必填字段与 hook 契约（为什么必填、门禁三条件、豁免清单）见 SKILL.md Step 5 — 本文件只是完整模板。

```markdown
---
status: {approved | needs_fix}
score: {N}
issues_found: {N}
rules_extracted: {N}
reviewed_at: {YYYY-MM-DD}
review_rounds: {N}
reviewed_files:
  - {repo 相对路径，与 `git diff --name-only` 输出一致，逐文件一行}
base_commit: {`git rev-parse --short HEAD` 的输出}
---

# Review: {Feature Name}
## Score: {N}/100
**Verdict**: {approved | needs_fix}（展示用 — frontmatter `status` 为唯一机读权威，hook 只读 status）
### Dimension Scores
- Code Quality: {N}/40
- Security: {N}/30
- Spec Compliance: {N}/30
## Verification
| 验证项 | 命令 | 结果 |
## Issues
- **[critical|major|minor]** {描述} — {建议修复}
## Rules Extracted / Retired
- Added to `rules/{category}.md`: {title}；建议归档：{list 或 none}
```

注意：Dimension Scores 三个维度名必须与 SKILL.md Step 3 完全一致（Code Quality / Security / Spec Compliance）— 命名错位会让评分不可对照。
