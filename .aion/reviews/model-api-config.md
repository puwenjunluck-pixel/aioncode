---
status: approved
score: 88
verdict: approved
issues_found: 2
rules_extracted: 1
reviewed_at: 2026-03-28
---

# Review: Dashboard 模型 API 可视化配置

## Score: 88/100
**Verdict**: approved

### Dimension Scores
- Code Quality: 35/40
- Security: 28/30
- Architecture Compliance: 25/30

## Passed
- models 解析器正确实现 list-of-objects 格式，修复了原有 flat dict bug
- section 切换时正确 flush current_member/current_model，无数据丢失
- write_team_config 正确序列化 list-of-objects + 数组字段
- switch_model 逻辑清晰：official 模式清除 env，custom 模式设置 env
- check_env_vars 仅返回 boolean，不暴露环境变量值
- API 端点使用 Pydantic BaseModel 做请求体验证
- 前端所有用户输入经 esc() 转义，无 XSS 风险
- CSS 使用项目标准 var() 变量，与现有风格完全一致
- 模型配置独立为 models.js，符合关注点分离和 500 行限制
- embedded.py 通过 build_frontend.py 重新生成，未手动编辑
- team.yml 模板注释已更新，体现 models 数组字段
- ruff lint 全部通过
- Dashboard app 可正常加载

## Issues
- **[minor]** services/team.py:11 — CLAUDE_SETTINGS_PATH 模块级计算 Path.home()，daemon 模式下 HOME 变更可能不正确。Phase 1 local 无风险。
- **[minor]** models.js:147 — toast._timer 使用 DOM expando property，功能正确但非标准。

## Rules Extracted
- Added to `rules/pitfalls.md`: settings.json 写入需保留现有字段

## Style Patterns Learned
- 无新 pattern（本次变更延续了现有 CSS var + vanilla JS + custom YAML parser 模式）
