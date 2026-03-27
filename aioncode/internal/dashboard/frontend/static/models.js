/* AionCode Copilot — Model Configuration: provider cards, model switching, add/edit/delete */

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

/** Get brand color for a provider. */
function getProviderColor(provider) {
  const c = { anthropic: '#d97706', openai: '#10a37f', google: '#4285f4', deepseek: '#536dfe' };
  return c[provider] || c[Object.keys(c).find(k => (provider||'').includes(k))] || '#6b7280';
}

/** Determine active provider and model from current-model API response. */
function resolveActive(cur, providers) {
  if (!cur.base_url) return { provider: '__official__', model: cur.model || 'opus' };
  const match = providers.find(p => cur.base_url === p.endpoint);
  if (match) return { provider: match.name, model: cur.anthropic_model || '' };
  return { provider: '__custom__', model: cur.anthropic_model || '' };
}

/** Main model config renderer. */
async function showModelConfig() {
  const el = document.getElementById('detail-settings');
  if (!el) return;
  el.innerHTML = '<div class="model-config"><div class="empty">加载中...</div></div>';

  const [curRes, teamData] = await Promise.all([
    api(`/api/projects/${curEncoded}/team/current-model`),
    window._team ? Promise.resolve(window._team) : api(`/api/projects/${curEncoded}/team`)
  ]);
  if (!window._team && teamData.ok !== false) window._team = teamData;

  const cur = curRes.ok ? curRes : { model: '', base_url: '', anthropic_model: '' };
  const providers = (window._team?.models) || [];
  const active = resolveActive(cur, providers);

  let envStatus = {};
  const envNames = providers.map(p => p.api_key_env).filter(Boolean);
  if (envNames.length) {
    const envRes = await api(`/api/projects/${curEncoded}/team/check-env`, { method: 'POST', body: { names: envNames } });
    if (envRes.ok) envStatus = envRes.env_status || {};
  }

  const badge = document.getElementById('b-models');
  if (badge) badge.textContent = providers.length ? String(providers.length + 1) : '1';

  el.innerHTML = `<div class="model-config">
    <div class="model-config-header">
      <span class="model-config-title">模型配置</span>
      <button class="model-add-btn" onclick="showAddProviderDialog()">+ 添加 Provider</button>
    </div>
    <div class="model-cards">
      ${renderOfficialCard(active)}
      ${providers.map((p, i) => renderProviderCard(p, i, envStatus, active)).join('')}
    </div>
    <div id="model-form-area"></div>
  </div>`;
}

/** Render built-in Anthropic official card. */
function renderOfficialCard(active) {
  const isActive = active.provider === '__official__';
  return `<div class="model-card${isActive ? ' active-provider' : ''}">
    <div class="model-card-accent" style="background:${OFFICIAL_PROVIDER.color}"></div>
    <div class="model-card-body">
      <div class="model-card-header">
        <span class="model-card-name">Anthropic 官方</span>
        <span class="tag">内置</span>
        ${isActive ? '<span class="tag active-tag">当前</span>' : ''}
      </div>
      <div class="model-card-row">
        <span class="model-card-label">模式</span>
        <span class="model-card-value">官方订阅</span>
      </div>
      <div class="model-card-row">
        <span class="model-card-label">模型</span>
        <div class="model-chips">
          ${OFFICIAL_PROVIDER.models.map(m =>
            `<button class="model-chip${isActive && active.model === m ? ' active' : ''}" onclick="doSwitch('__official__','${m}')">${esc(m)}</button>`
          ).join('')}
        </div>
      </div>
    </div>
  </div>`;
}

/** Render a custom provider card. */
function renderProviderCard(provider, index, envStatus, active) {
  const color = provider.color || getProviderColor(provider.provider);
  const isActive = active.provider === provider.name;
  const models = Array.isArray(provider.models) ? provider.models : [];
  const envSet = envStatus[provider.api_key_env];
  return `<div class="model-card${isActive ? ' active-provider' : ''}">
    <div class="model-card-accent" style="background:${color}"></div>
    <div class="model-card-body">
      <div class="model-card-header">
        <span class="model-card-name">${esc(provider.name)}</span>
        <span class="tag">${esc(provider.provider || 'custom')}</span>
        ${isActive ? '<span class="tag active-tag">当前</span>' : ''}
        <span style="margin-left:auto;display:flex;gap:4px">
          <button class="model-btn" onclick="editProvider(${index})" title="编辑">✎</button>
          <button class="model-btn danger" onclick="deleteProvider(${index})" title="删除">✕</button>
        </span>
      </div>
      <div class="model-card-row">
        <span class="model-card-label">端点</span>
        <span class="model-card-value">${esc(provider.endpoint || '')}</span>
      </div>
      <div class="model-card-row">
        <span class="model-card-label">API Key</span>
        <span class="model-card-value">${esc(provider.api_key_env || '')} <span class="env-dot ${envSet ? 'set' : 'unset'}"></span> <span class="env-hint">${envSet ? '已配置' : '未设置'}</span></span>
      </div>
      <div class="model-card-row">
        <span class="model-card-label">模型</span>
        <div class="model-chips">
          ${models.map(m =>
            `<button class="model-chip${isActive && active.model === m ? ' active' : ''}" onclick="doSwitch('${esc(provider.name)}','${esc(m)}')">${esc(m)}</button>`
          ).join('')}
          ${!models.length ? '<span class="env-hint">未配置模型</span>' : ''}
        </div>
      </div>
    </div>
  </div>`;
}

/** Show a toast notification that auto-fades. */
function showModelToast(msg) {
  let toast = document.getElementById('model-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'model-toast';
    toast.className = 'model-toast';
    const container = document.querySelector('.model-config');
    if (container) container.insertBefore(toast, container.children[1]);
  }
  toast.textContent = msg;
  toast.classList.add('visible');
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove('visible'), 5000);
}

/** Switch model via API. */
async function doSwitch(providerName, modelName) {
  const chips = document.querySelectorAll('.model-chip');
  chips.forEach(c => c.disabled = true);
  const d = await api(`/api/projects/${curEncoded}/team/switch-model`, {
    method: 'POST', body: { provider_name: providerName, model_name: modelName }
  });
  if (d.ok) {
    await showModelConfig();
    const label = providerName === '__official__' ? 'Anthropic 官方' : providerName;
    showModelToast(`已切换到 ${label} / ${modelName}，重启 Claude Code 会话后生效`);
  } else {
    alert('切换失败: ' + (d.message || ''));
    chips.forEach(c => c.disabled = false);
  }
}

/** Render provider form (add or edit). */
function renderProviderForm(provider, isEdit, editIndex) {
  const title = isEdit ? '编辑 Provider' : '添加 Provider';
  const models = Array.isArray(provider.models) ? provider.models.join(', ') : '';
  return `<div class="model-form" id="provider-form">
    <div class="model-form-title">${title}</div>
    ${!isEdit ? `<div class="model-presets">
      ${Object.entries(MODEL_PRESETS).map(([k]) =>
        `<button class="model-preset" onclick="applyPreset('${k}')">${k === 'custom' ? '自定义' : esc(k)}</button>`
      ).join('')}
    </div>` : ''}
    <div class="model-field">
      <label>名称</label>
      <input id="mf-name" value="${esc(provider.name || '')}" placeholder="e.g. openai">
    </div>
    <div class="model-field">
      <label>Provider 类型</label>
      <input id="mf-provider" value="${esc(provider.provider || '')}" placeholder="e.g. openai-compatible">
    </div>
    <div class="model-field">
      <label>端点 URL</label>
      <input id="mf-endpoint" value="${esc(provider.endpoint || '')}" placeholder="https://api.openai.com/v1">
    </div>
    <div class="model-field">
      <label>API Key 环境变量名</label>
      <input id="mf-apikey" value="${esc(provider.api_key_env || '')}" placeholder="OPENAI_API_KEY">
    </div>
    <div class="model-field">
      <label>模型列表（逗号分隔）</label>
      <input id="mf-models" value="${esc(models)}" placeholder="gpt-4o, gpt-4-turbo">
    </div>
    <div class="model-field">
      <label>默认模型</label>
      <input id="mf-default" value="${esc(provider.default_model || '')}" placeholder="gpt-4o">
    </div>
    <div class="model-form-actions">
      <button class="model-save-btn" onclick="saveProviderForm(${isEdit ? editIndex : -1})">${isEdit ? '更新' : '保存'}</button>
      <button class="model-cancel-btn" onclick="showModelConfig()">取消</button>
    </div>
  </div>`;
}

/** Show add provider dialog. */
function showAddProviderDialog() {
  const area = document.getElementById('model-form-area');
  if (!area) return;
  area.innerHTML = renderProviderForm({}, false, -1);
  area.scrollIntoView({ behavior: 'smooth' });
}

/** Apply a preset to the form. */
function applyPreset(key) {
  const p = MODEL_PRESETS[key];
  if (!p) return;
  document.querySelectorAll('.model-preset').forEach(b => b.classList.remove('active'));
  if (event?.target) event.target.classList.add('active');
  document.getElementById('mf-name').value = p.name || '';
  document.getElementById('mf-provider').value = p.provider || '';
  document.getElementById('mf-endpoint').value = p.endpoint || '';
  document.getElementById('mf-apikey').value = p.api_key_env || '';
  document.getElementById('mf-models').value = (p.models || []).join(', ');
  document.getElementById('mf-default').value = p.default_model || '';
}

/** Edit provider inline. */
function editProvider(index) {
  const providers = (window._team?.models) || [];
  const p = providers[index];
  if (!p) return;
  const area = document.getElementById('model-form-area');
  if (!area) return;
  area.innerHTML = renderProviderForm(p, true, index);
  area.scrollIntoView({ behavior: 'smooth' });
}

/** Delete provider with confirmation. */
async function deleteProvider(index) {
  const providers = (window._team?.models) || [];
  const p = providers[index];
  if (!p || !confirm(`确定删除 Provider "${p.name}"？`)) return;
  providers.splice(index, 1);
  await saveProviders();
}

/** Save provider form data. */
async function saveProviderForm(editIndex) {
  const name = document.getElementById('mf-name').value.trim();
  const provider = document.getElementById('mf-provider').value.trim();
  const endpoint = document.getElementById('mf-endpoint').value.trim();
  const apiKey = document.getElementById('mf-apikey').value.trim();
  const modelsStr = document.getElementById('mf-models').value.trim();
  const defaultModel = document.getElementById('mf-default').value.trim();

  if (!name || !endpoint) { alert('名称和端点为必填项'); return; }

  const models = modelsStr ? modelsStr.split(',').map(s => s.trim()).filter(Boolean) : [];
  const obj = { name, provider, endpoint, api_key_env: apiKey, models, default_model: defaultModel };

  if (!window._team) window._team = { team: [], models: [], risk_keywords: {} };
  if (!Array.isArray(window._team.models)) window._team.models = [];

  if (editIndex >= 0) {
    window._team.models[editIndex] = obj;
  } else {
    window._team.models.push(obj);
  }
  await saveProviders();
}

/** Persist providers to backend. */
async function saveProviders() {
  const config = {
    team: window._team?.team || [],
    models: window._team?.models || [],
    risk_keywords: window._team?.risk_keywords || {}
  };
  const d = await api(`/api/projects/${curEncoded}/team`, { method: 'POST', body: config });
  if (d.ok) {
    showModelConfig();
  } else {
    alert('保存失败: ' + (d.message || ''));
  }
}
