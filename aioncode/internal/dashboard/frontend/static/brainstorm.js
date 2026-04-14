/* AionCode Dashboard — Brainstorm collaboration view */

let _bsPollTimer = null;
let _bsLastScreen = null;
let _bsPollInterval = 1500;
const _BS_ACTIVE_INTERVAL = 1500;
const _BS_IDLE_INTERVAL = 10000;
const _BS_MAX_BACKOFF = 30000;

function loadBrainstorm() {
  const el = document.getElementById('detail-brainstorm');
  if (!el) return;
  el.innerHTML = '<div class="bs-loading">加载中...</div>';
  _bsLastScreen = null;
  _bsPollInterval = _BS_ACTIVE_INTERVAL;
  _bsStopPoll();
  _bsFetchScreen().then(() => _bsStartPoll());
}

async function _bsFetchScreen() {
  const el = document.getElementById('detail-brainstorm');
  if (!el) { _bsStopPoll(); return; }

  let d;
  try {
    d = await api(`/api/projects/${curEncoded}/brainstorm/screen`);
  } catch {
    _bsPollInterval = Math.min(_bsPollInterval * 2, _BS_MAX_BACKOFF);
    _bsStartPoll();
    return;
  }

  if (!d.ok) {
    el.innerHTML = '<div class="bs-error">读取失败</div>';
    return;
  }

  _bsPollInterval = d.active ? _BS_ACTIVE_INTERVAL : _BS_IDLE_INTERVAL;

  const badge = document.getElementById('b-brainstorm');
  if (badge) {
    if (d.active) { badge.style.display = ''; badge.textContent = '●'; }
    else { badge.style.display = 'none'; }
  }

  if (!d.active || !d.screen) {
    el.innerHTML = _bsRenderEmpty();
    _bsLastScreen = null;
    return;
  }

  const screenStr = JSON.stringify(d.screen);
  if (screenStr === _bsLastScreen) return;
  _bsLastScreen = screenStr;

  const s = d.screen;
  switch (s.type) {
    case 'options': el.innerHTML = _bsRenderOptions(s); break;
    case 'compare': el.innerHTML = _bsRenderCompare(s); break;
    case 'info':    el.innerHTML = _bsRenderInfo(s); break;
    case 'html':    el.innerHTML = _bsRenderHtmlPlaceholder(); break;
    default:        el.innerHTML = `<div class="bs-error">未知类型: ${esc(s.type)}</div>`;
  }
}

function _bsStartPoll() {
  _bsStopPoll();
  _bsPollTimer = setInterval(_bsFetchScreen, _bsPollInterval);
}

function _bsStopPoll() {
  if (_bsPollTimer) { clearInterval(_bsPollTimer); _bsPollTimer = null; }
}

function _bsRenderEmpty() {
  return `<div class="bs-empty">
    <div class="bs-empty-icon">💬</div>
    <div class="bs-empty-title">当前无设计协作会话</div>
    <div class="bs-empty-hint">运行 <code>/project:aion-think</code> 开始讨论，方案选项将在此展示。</div>
  </div>`;
}

function _bsRenderOptions(s) {
  const multi = s.multiselect ? 'data-multi' : '';
  let html = `<div class="bs-screen">
    <h2 class="bs-title">${esc(s.title)}</h2>
    ${s.description ? `<p class="bs-desc">${esc(s.description)}</p>` : ''}
    <div class="bs-options" ${multi}>`;

  for (const item of (s.items || [])) {
    const rec = item.recommended ? '<span class="bs-rec">推荐</span>' : '';
    const pros = (item.pros || []).map(p => `<li class="bs-pro">${esc(p)}</li>`).join('');
    const cons = (item.cons || []).map(c => `<li class="bs-con">${esc(c)}</li>`).join('');
    html += `<div class="bs-card" data-key="${esc(item.key)}" onclick="bsSelect(this)">
      <div class="bs-card-head">
        <span class="bs-card-key">${esc(item.key.toUpperCase())}</span>
        <span class="bs-card-title">${esc(item.title)}</span>
        ${rec}
      </div>
      ${item.body ? `<p class="bs-card-body">${esc(item.body)}</p>` : ''}
      ${pros || cons ? `<div class="bs-pros-cons">
        ${pros ? `<ul class="bs-pros">${pros}</ul>` : ''}
        ${cons ? `<ul class="bs-cons">${cons}</ul>` : ''}
      </div>` : ''}
    </div>`;
  }

  html += `</div>
    <div class="bs-hint" id="bs-hint">点击选择方案，然后回到终端继续</div>
  </div>`;
  return html;
}

function _bsRenderCompare(s) {
  const dims = s.dimensions || [];
  const items = s.items || [];

  let thead = '<th></th>' + items.map(i => `<th>${esc(i.title)}</th>`).join('');
  let tbody = '';
  for (const dim of dims) {
    tbody += `<tr><td class="bs-dim">${esc(dim)}</td>`;
    for (const item of items) {
      const val = (item.scores || {})[dim] || '';
      tbody += `<td>${esc(val)}</td>`;
    }
    tbody += '</tr>';
  }

  let html = `<div class="bs-screen">
    <h2 class="bs-title">${esc(s.title)}</h2>
    <table class="bs-compare"><thead><tr>${thead}</tr></thead><tbody>${tbody}</tbody></table>
    <div class="bs-options">`;

  for (const item of items) {
    html += `<button class="bs-choose-btn" data-key="${esc(item.key)}" onclick="bsSelect(this)">
      选择 ${esc(item.title)}
    </button>`;
  }

  html += `</div>
    <div class="bs-hint" id="bs-hint">点击选择方案，然后回到终端继续</div>
  </div>`;
  return html;
}

function _bsRenderInfo(s) {
  return `<div class="bs-info">
    <div class="bs-info-icon">ℹ️</div>
    <div class="bs-info-title">${esc(s.title || '')}</div>
    ${s.description ? `<div class="bs-info-desc">${esc(s.description)}</div>` : ''}
  </div>`;
}

function _bsRenderHtmlPlaceholder() {
  return `<div class="bs-info">
    <div class="bs-info-icon">🔮</div>
    <div class="bs-info-title">HTML 渲染即将支持</div>
    <div class="bs-info-desc">自由 HTML 内容（mockup、wireframe）将在后续版本中支持。</div>
  </div>`;
}

async function bsSelect(el) {
  const key = el.dataset.key;
  if (!key) return;

  /* Visual feedback */
  const container = el.closest('.bs-options');
  if (container && !container.hasAttribute('data-multi')) {
    container.querySelectorAll('.bs-card, .bs-choose-btn').forEach(c => c.classList.remove('bs-selected'));
  }
  el.classList.add('bs-selected');

  /* Post event to backend */
  await api(`/api/projects/${curEncoded}/brainstorm/event`, {
    method: 'POST', body: { type: 'click', choice: key }
  });

  /* Update hint */
  const hint = document.getElementById('bs-hint');
  if (hint) {
    hint.textContent = `已选择 ${key.toUpperCase()}，请回到终端继续`;
    hint.classList.add('bs-hint-done');
  }
}
