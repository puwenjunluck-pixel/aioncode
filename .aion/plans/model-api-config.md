# 模型 API 可视化配置功能

## Context

用户需要一个类似 cc-switch 的可视化模型管理功能，集成在 AionCode Dashboard 设置页中。核心需求：
- 配置 Provider 时包含模型列表，支持一键切换
- **Anthropic 官方订阅**作为内置卡片始终置顶、不可删除
- 自定义 Provider（OpenAI、DeepSeek 等）可增删改
- 切换后自动更新 `~/.claude/settings.json`
- 切换回官方模式时清除所有自定义 env

当前问题：后端 `team.py` 的 models 解析器有 bug（list-of-objects 当 flat dict），前端无配置 UI。

---

## 数据模型

### team.yml models 结构

```yaml
models:
  - name: openai
    provider: openai-compatible
    endpoint: https://api.openai.com/v1
    api_key_env: OPENAI_API_KEY
    models: [gpt-4o, gpt-4-turbo, gpt-4o-mini]
    default_model: gpt-4o

  - name: deepseek
    provider: openai-compatible
    endpoint: https://api.deepseek.com/v1
    api_key_env: DEEPSEEK_API_KEY
    models: [deepseek-chat, deepseek-reasoner]
    default_model: deepseek-chat
```

> 注意：Anthropic 官方不存储在 team.yml，它是前端内置的。team.yml 仅存自定义 Provider。

### 切换机制 — 写入 `~/.claude/settings.json`

| 操作 | settings.json 变更 |
|------|-------------------|
| 切换到**官方** opus/sonnet/haiku | `model` = 选中别名；**删除** `env.ANTHROPIC_BASE_URL` 和 `env.ANTHROPIC_MODEL` |
| 切换到**自定义** Provider 的某模型 | `env.ANTHROPIC_BASE_URL` = endpoint；`env.ANTHROPIC_MODEL` = 模型名；`model` 保持不变 |

API Key 通过用户 shell 环境变量或 UI inline 输入提供；inline 输入的 key 写入全局 settings.json 的 `env.ANTHROPIC_AUTH_TOKEN`（非 ANTHROPIC_API_KEY）。

> **Amendment (2026-03-29)**：
> - 切换目标由 `{project}/.claude/settings.local.json` → `~/.claude/settings.json`（全局）。原因：CC daemon 将 settings.local.json 的 env 广播给所有会话，项目级隔离不可达，改全局更透明。
> - 第三方模型切换需同时设置五个 model-family vars（ANTHROPIC_MODEL + SMALL_FAST + DEFAULT_SONNET/OPUS/HAIKU），否则 CC 校验报错。
> - 切回官方时，env vars 改为设空字符串 `""` 而非删除，支持热重载无重启生效。

---

## 实施步骤

### Step 1: 修复并升级后端 models 解析器

**文件**: `aioncode/internal/dashboard/services/team.py`

**1a — `read_team_config()`**:
- `models` 默认值 `{}` → `[]`
- 新增 `current_model: dict | None = None` 状态变量
- models section 改为 list-of-objects 解析：
  - `- name:` 开始新对象
  - 后续 `key: value` 追加到 current_model
  - 支持 `models: [a, b, c]` 数组值
- section 切换和循环结束时 flush current_model

**1b — `write_team_config()`**:
- models 序列化改为 list-of-objects 格式（与 team section 写法一致）
- 支持写出 `models: [a, b, c]` 数组字段

### Step 2: 新增 API 端点

**文件**: `aioncode/internal/dashboard/routers/team.py`

**2a — `POST /api/projects/{encoded}/team/check-env`**
- 接收 env var names 列表，返回每个是否已设置的 boolean（不暴露值）

**2b — `POST /api/projects/{encoded}/team/switch-model`**
- 接收 `{ provider_name: str | "__official__", model_name: str }`
- 若 `provider_name == "__official__"`：
  - 设置 settings.json `model` = model_name
  - 删除 `env.ANTHROPIC_BASE_URL`、`env.ANTHROPIC_MODEL`
- 若自定义 Provider：
  - 从 team.yml 查找 Provider
  - 设置 `env.ANTHROPIC_BASE_URL` = endpoint
  - 设置 `env.ANTHROPIC_MODEL` = model_name
- 写回 `~/.claude/settings.json`，保留其余字段不变
- 返回 `{ ok, active_provider, active_model }`

**2c — `GET /api/projects/{encoded}/team/current-model`**
- 读取 `~/.claude/settings.json`
- 返回 `{ model, base_url, anthropic_model }` 供前端判断当前激活状态

**新增 service 函数** — `aioncode/internal/dashboard/services/team.py`:
- `read_claude_settings()` → 读取 `~/.claude/settings.json`
- `write_claude_settings(data)` → 写入 `~/.claude/settings.json`（保留格式）

### Step 3: 前端 HTML

**文件**: `aioncode/internal/dashboard/frontend/static/index.html`

在 `#settings-list`（设置侧边栏）的深色模式开关后添加：
```html
<div class="settings-item">
  <div class="settings-row" onclick="showModelConfig()" style="cursor:pointer">
    <span class="settings-label">模型配置</span>
    <span class="sw-badge" id="b-models">—</span>
  </div>
</div>
```

### Step 4: 前端 JS — app.js

**文件**: `aioncode/internal/dashboard/frontend/static/app.js`

更新 `showViewDetail('settings')` case：
```javascript
case 'settings':
  d.innerHTML = '<div class="detail-settings" id="detail-settings"></div>';
  showModelConfig();
  break;
```

### Step 5: 前端 JS — views.js 核心逻辑

**文件**: `aioncode/internal/dashboard/frontend/static/views.js`

新增内容（追加在文件末尾，skills section 之后）：

**常量**:
```javascript
const OFFICIAL_PROVIDER = {
  name: '__official__', provider: 'anthropic',
  endpoint: 'https://api.anthropic.com/v1',
  models: ['opus', 'sonnet', 'haiku'],
  default_model: 'opus', color: '#d97706', builtin: true
};

const MODEL_PRESETS = {
  openai: { name: 'openai', provider: 'openai-compatible', endpoint: 'https://api.openai.com/v1', api_key_env: 'OPENAI_API_KEY', models: ['gpt-4o', 'gpt-4-turbo', 'gpt-4o-mini'], default_model: 'gpt-4o', color: '#10a37f' },
  google: { name: 'gemini', provider: 'google', endpoint: 'https://generativelanguage.googleapis.com/v1beta', api_key_env: 'GEMINI_API_KEY', models: ['gemini-2.5-pro', 'gemini-2.0-flash'], default_model: 'gemini-2.5-pro', color: '#4285f4' },
  deepseek: { name: 'deepseek', provider: 'openai-compatible', endpoint: 'https://api.deepseek.com/v1', api_key_env: 'DEEPSEEK_API_KEY', models: ['deepseek-chat', 'deepseek-reasoner'], default_model: 'deepseek-chat', color: '#536dfe' },
  custom: { name: '', provider: '', endpoint: '', api_key_env: '', models: [], default_model: '', color: '#6b7280' }
};
```

**主要函数**:

| 函数 | 功能 |
|------|------|
| `showModelConfig()` | 主渲染：查询 current-model + check-env → 渲染官方卡片 + 自定义 Provider 卡片 + 添加按钮 |
| `renderOfficialCard(currentModel)` | 内置 Anthropic 官方卡片：始终置顶、无删除/编辑端点按钮、显示 opus/sonnet/haiku 模型芯片 |
| `renderProviderCard(provider, i, envStatus, currentModel)` | 自定义 Provider 卡片：色带 + 端点 + Key 状态 + 模型芯片 + 编辑/删除按钮 |
| `renderModelChips(models, providerName, currentModel)` | 模型芯片列表渲染，当前激活的高亮为 active |
| `switchModel(providerName, modelName)` | 调用 switch-model API → 刷新 UI 高亮 |
| `showAddProviderDialog()` | 内联表单：预设选择器 + 5 字段 + 模型列表编辑 + 保存/取消 |
| `editProvider(index)` | 将卡片替换为编辑表单 |
| `deleteProvider(index)` | confirm() 后删除 |
| `saveProviders()` | POST /team → 刷新视图 |

**判断当前激活逻辑**:
```
GET /team/current-model → { model, base_url, anthropic_model }
若 base_url 为空 → 当前是官方模式，激活模型 = model 字段
若 base_url 非空 → 当前是自定义 Provider，匹配 endpoint 找到 Provider，激活模型 = anthropic_model
```

**同时更新 `loadTeamDetail()`**: models 从 flat k:v 改为 list-of-objects 只读摘要。

### Step 6: 前端 CSS

**文件**: `aioncode/internal/dashboard/frontend/static/views.css`

新增样式（遵循现有 CSS 变量和命名规范）：

- **布局**: `.model-config`, `.model-cards` — padding + grid 布局
- **卡片**: `.model-card`, `.model-card-accent`, `.model-card-body`, `.model-card.builtin` — 卡片 + 色带 + 内置标记
- **内容**: `.model-card-header`, `.model-card-row`, `.model-card-label`, `.model-card-value`
- **模型芯片**: `.model-chip`, `.model-chip.active`, `.model-chip:hover` — 可点击切换
- **状态**: `.env-dot.set`, `.env-dot.unset` — 绿/红环境变量指示器
- **按钮**: `.model-btn`, `.model-btn.danger`, `.model-add-btn`
- **表单**: `.model-form`, `.model-presets`, `.model-preset`, `.model-field`, `.model-tags-input`
- **操作**: `.model-save-btn`, `.model-cancel-btn`

### Step 7: 更新 team.yml 模板

**文件**: `aioncode/internal/templates/aion/team.yml`

更新 models 注释示例，体现 `models` 数组字段。

### Step 8: 重新构建 embedded.py

```bash
cd aioncode/internal/dashboard/frontend && python build_frontend.py
```

---

## UI 卡片布局

```
┌─ Anthropic 官方 ────────────── 内置 ──┐
│ ▌(琥珀色带)                            │
│  当前模式: 官方订阅                     │
│                                        │
│  模型:                                 │
│  [● opus]  [sonnet]  [haiku]           │  ← 可点击，● = 当前激活
│                                        │
└────────────────────────────────────────┘

┌─ OpenAI ──────────────── 自定义 ✎  ✕ ─┐
│ ▌(绿色带)                              │
│  端点   https://api.openai.com/v1      │
│  Key    OPENAI_API_KEY  🟢 已配置      │
│                                        │
│  模型:                                 │
│  [gpt-4o]  [gpt-4-turbo]  [gpt-4o-mini]│
│                                        │
└────────────────────────────────────────┘

         [ + 添加 Provider ]
```

## 安全

- API Key **永不存储**在 team.yml — 仅存环境变量名
- `/check-env` 仅返回 boolean
- settings.json 切换时仅写 URL/MODEL，**不写 API Key**
- 官方模式切换时主动清除 env 中的 BASE_URL/MODEL

## 涉及文件

| 文件 | 变更类型 |
|------|----------|
| `aioncode/internal/dashboard/services/team.py` | 修复 models 解析 + 新增 settings.json 读写 |
| `aioncode/internal/dashboard/routers/team.py` | 新增 3 个端点 |
| `aioncode/internal/dashboard/frontend/static/index.html` | 设置侧边栏入口 |
| `aioncode/internal/dashboard/frontend/static/app.js` | settings 视图切换 |
| `aioncode/internal/dashboard/frontend/static/views.js` | 模型配置核心 JS |
| `aioncode/internal/dashboard/frontend/static/views.css` | 卡片/芯片/表单样式 |
| `aioncode/internal/templates/aion/team.yml` | 模板注释更新 |
| `aioncode/internal/dashboard/frontend/embedded.py` | 自动重新生成 |

## 验证

1. 启动 Dashboard dev：`python3.11 -c "from aioncode.internal.dashboard.app import create_app; import uvicorn; uvicorn.run(create_app(dev=True), host='127.0.0.1', port=19200)"`
2. 打开设置 → 模型配置 → 验证官方卡片置顶且不可删除
3. 点击官方卡片 "sonnet" → 验证 `~/.claude/settings.json` 的 `model` 变为 `"sonnet"`
4. 添加 OpenAI Provider（预设填充） → 验证 team.yml 写入
5. 点击 OpenAI "gpt-4o" → 验证 settings.json 的 `env.ANTHROPIC_BASE_URL` 和 `env.ANTHROPIC_MODEL` 设置正确
6. 切回官方 "opus" → 验证 env 中 BASE_URL/MODEL 被清除
7. 编辑/删除自定义 Provider → 验证持久化
8. 环境变量状态指示器（绿/红）正确显示
