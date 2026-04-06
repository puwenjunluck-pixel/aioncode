/* AionCode Copilot — Core: view switching, data loading, SSE, palette, theme */

let curProject = null, curEncoded = null, sse = null, curView = 'overview';

const api = async (p, o = {}) => {
  const r = await fetch(p, { headers: {'Content-Type':'application/json'}, ...o, body: o.body ? JSON.stringify(o.body) : undefined });
  return r.json();
};
const enc = p => btoa(p).replace(/\+/g,'-').replace(/\//g,'_').replace(/=/g,'');
const esc = s => s ? s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') : '';
const fmtSz = b => b<1024?b+'B':b<1048576?(b/1024).toFixed(1)+'K':(b/1048576).toFixed(1)+'M';
const fmtTs = d => d ? new Date(d).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'}) : '';

document.addEventListener('DOMContentLoaded', () => { loadProjects(); setupKeys(); });

// ══════════════════════════════════════
//  View Switching
// ══════════════════════════════════════
function switchView(view) {
  curView = view;
  document.querySelectorAll('.rail-btn[data-view]').forEach(b =>
    b.classList.toggle('active', b.dataset.view === view));
  document.querySelectorAll('.view-sidebar').forEach(el =>
    el.classList.toggle('hidden', el.id !== 'vs-' + view));
  if (typeof ensureViewData === 'function') ensureViewData(view);
  showViewDetail(view);
}

function showViewDetail(view) {
  const d = document.getElementById('detail');
  switch (view) {
    case 'overview':
      d.innerHTML = '<div class="detail-overview" id="detail-overview"></div>';
      loadOverviewDetail(); break;
    case 'files':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">◇</div>
        <div class="welcome-title">选择文件查看内容</div>
        <div class="welcome-hint">点击左侧文件树中的文件</div></div>`; break;
    case 'monitor':
      d.innerHTML = '<div class="detail-monitor" id="detail-monitor"></div>';
      loadMonitorDetail(); break;
    case 'bugs':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">●</div>
        <div class="welcome-title">选择缺陷查看详情</div>
        <div class="welcome-hint">点击左侧缺陷列表中的条目</div></div>`; break;
    case 'team':
      d.innerHTML = '<div class="detail-team" id="detail-team"></div>';
      loadTeamDetail(); break;
    case 'help':
      d.innerHTML = renderHelpPage(); break;
    case 'about':
      d.innerHTML = renderAboutPage(); break;
    case 'specs':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">📋</div>
        <div class="welcome-title">选择需求文档查看详情</div>
        <div class="welcome-hint">点击左侧列表中的条目</div></div>`; break;
    case 'plans':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">📊</div>
        <div class="welcome-title">选择方案查看详情</div>
        <div class="welcome-hint">点击左侧列表中的条目</div></div>`; break;
    case 'rules':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">🛡</div>
        <div class="welcome-title">选择规则文件查看详情</div>
        <div class="welcome-hint">点击左侧列表中的条目</div></div>`; break;
    case 'checklists':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">✓</div>
        <div class="welcome-title">选择清单查看详情</div>
        <div class="welcome-hint">点击左侧列表中的条目</div></div>`; break;
    case 'test':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">⚡</div>
        <div class="welcome-title">选择测试文件查看内容</div>
        <div class="welcome-hint">点击左侧列表中的条目</div></div>`; break;
    case 'changelog':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">⏱</div>
        <div class="welcome-title">选择日志条目查看详情</div>
        <div class="welcome-hint">点击左侧变更日志列表</div></div>`; break;
    case 'brainstorm':
      d.innerHTML = '<div class="detail-brainstorm" id="detail-brainstorm"></div>';
      if (typeof loadBrainstorm === 'function') loadBrainstorm(); break;
    case 'skills':
      d.innerHTML = `<div class="detail-welcome"><div class="welcome-icon">◆</div>
        <div class="welcome-title">选择技能查看详情</div>
        <div class="welcome-hint">点击左侧技能列表中的条目</div></div>`; break;
    case 'settings':
      d.innerHTML = '<div class="detail-settings" id="detail-settings"></div>';
      if (typeof showModelConfig === 'function') showModelConfig();
      break;
  }
}

// ══════════════════════════════════════
//  Projects
// ══════════════════════════════════════
async function loadProjects() {
  const list = await api('/api/projects');
  const sel = document.getElementById('proj-sel');
  sel.innerHTML = '';
  if (!list.length) { sel.innerHTML = '<option>无项目</option>'; return; }
  list.forEach(p => {
    const o = document.createElement('option');
    o.value = p.path; o.textContent = p.name + (p.has_aion ? '' : ' ⚠');
    sel.appendChild(o);
  });
  switchProject(list[0].path);
}

async function switchProject(path) {
  if (!path) return;
  curProject = path; curEncoded = enc(path);
  document.getElementById('proj-path').textContent = path;
  document.getElementById('s-proj').textContent = path.split('/').pop();
  if (typeof resetViewsCache === 'function') resetViewsCache();
  await Promise.all([loadStats(), loadFiles(), loadEvents(), loadBugs(), loadTeam()]);
  switchView(curView);
  startSSE();
}

// ══════════════════════════════════════
//  Overview (sidebar stats)
// ══════════════════════════════════════
async function loadStats() {
  const d = await api(`/api/projects/${curEncoded}/stats`);
  if (!d.ok) return;
  window._stats = d;
  if (d.aioncode_version) document.getElementById('s-version').textContent = `AionCode v${d.aioncode_version}`;
  const items = [
    { v: d.rules?.total??0, l: '规则' }, { v: d.specs??0, l: '需求' },
    { v: d.plans??0, l: '方案' }, { v: d.reviews??0, l: '审查' },
    { v: d.bugs??0, l: '缺陷' }, { v: d.commands??0, l: '命令' },
  ];
  document.getElementById('stats').innerHTML = items.map(s =>
    `<div class="stat"><div class="stat-val">${s.v}</div><div class="stat-lbl">${s.l}</div></div>`
  ).join('');
}

// ══════════════════════════════════════
//  Files
// ══════════════════════════════════════
async function loadFiles() {
  const d = await api(`/api/projects/${curEncoded}/files`);
  if (!d.ok) return;
  window._fileTree = d.tree || [];
  document.getElementById('ftree').innerHTML = buildTree(d.tree, 0);
}

function buildTree(items, depth) {
  if (!items?.length) return '<div class="empty">空目录</div>';
  return items.map(n => {
    const pad = `padding-left:${4+depth*14}px`;
    if (n.type === 'dir') {
      return `<div class="fnode dir" style="${pad}" onclick="this.nextElementSibling.classList.toggle('closed')">
        <span class="ico">▸</span>${esc(n.name)}/
      </div><div class="fnode-children${depth>0?' closed':''}">${buildTree(n.children,depth+1)}</div>`;
    }
    return `<div class="fnode" style="${pad}" onclick="viewFile(this,'${esc(n.path)}')" title="${esc(n.path)}">
      <span class="ico">·</span>${esc(n.name)}<span class="sz">${fmtSz(n.size)}</span>
    </div>`;
  }).join('');
}

async function viewFile(el, path) {
  document.querySelectorAll('.fnode.active').forEach(n => n.classList.remove('active'));
  el.classList.add('active');
  const d = await api(`/api/projects/${curEncoded}/file?path=${encodeURIComponent(path)}`);
  if (!d.ok) return;
  const fname = path.split('/').pop();
  document.getElementById('detail').innerHTML = `
    <div class="detail-file">
      <div class="detail-file-header">
        <span class="fname">${esc(fname)}</span>
        <span class="fpath">${esc(path)}</span>
        <span class="spacer"></span>
        <button class="close-btn" onclick="switchView('files')">✕</button>
      </div>
      <pre>${esc(d.content)}</pre>
    </div>`;
}

// ══════════════════════════════════════
//  Monitor (sidebar events)
// ══════════════════════════════════════
async function loadEvents() {
  const d = await api(`/api/projects/${curEncoded}/events/recent?limit=30`);
  if (!d.ok) return;
  window._events = d.events || [];
  renderEventsSidebar(window._events);
}

function renderEventsSidebar(evts) {
  document.getElementById('b-events').textContent = evts.length || '—';
  const el = document.getElementById('events');
  if (!evts.length) { el.innerHTML = '<div class="empty">暂无事件</div>'; return; }
  el.innerHTML = evts.slice(0, 20).map(e =>
    `<div class="evt"><span class="evt-ts">${fmtTs(e.ts)}</span><span class="evt-msg">${esc(e.summary)}</span></div>`
  ).join('');
  if (evts[0]?.ts) document.getElementById('s-last').textContent = fmtTs(evts[0].ts);
}

function startSSE() {
  if (sse) sse.close();
  sse = new EventSource(`/api/projects/${curEncoded}/events/stream`);
  const dot = document.getElementById('live-dot');
  sse.onmessage = e => {
    try {
      const evt = JSON.parse(e.data);
      const data = evt.data || evt;
      const tool = data.tool_name || data.tool || data.hook_event_name || 'event';
      const now = fmtTs(new Date());
      const el = document.getElementById('events');
      const empty = el.querySelector('.empty'); if (empty) empty.remove();
      const div = document.createElement('div');
      div.className = 'evt';
      div.innerHTML = `<span class="evt-ts">${now}</span><span class="evt-msg">${esc(tool)}</span>`;
      el.prepend(div);
      while (el.children.length > 20) el.lastChild.remove();
      document.getElementById('s-last').textContent = now;
      dot.style.display = 'inline-block';
    } catch(_){}
  };
  document.getElementById('s-dot').className = 'status-dot';
  sse.onerror = () => { document.getElementById('s-dot').className = 'status-dot err'; dot.style.display='none'; };
}

// ══════════════════════════════════════
//  Bugs (sidebar)
// ══════════════════════════════════════
async function loadBugs() {
  const d = await api(`/api/projects/${curEncoded}/bugs`);
  if (!d.ok) return;
  window._bugs = d.bugs || [];
  const badge = document.getElementById('b-bugs');
  badge.textContent = window._bugs.length || '—';
  badge.className = 'sw-badge' + (window._bugs.length > 0 ? ' warn' : '');
  const el = document.getElementById('bugs');
  if (!window._bugs.length) { el.innerHTML = '<div class="empty">无缺陷 ✓</div>'; return; }
  el.innerHTML = window._bugs.map((b, i) =>
    `<div class="bug" onclick="viewBug(${i})">
      <span class="bug-dot ${b.severity||'medium'}"></span>
      <span class="bug-id">${esc(b.id)}</span>
      <span class="bug-title">${esc(b.title)}</span>
      <span class="tag">${b.status||'open'}</span>
    </div>`
  ).join('');
}

// ══════════════════════════════════════
//  Team (sidebar)
// ══════════════════════════════════════
async function loadTeam() {
  const d = await api(`/api/projects/${curEncoded}/team`);
  if (!d.ok) return;
  window._team = d;
  const members = d.team || [];
  const el = document.getElementById('team');
  if (!members.length) { el.innerHTML = '<div class="empty">未配置团队</div>'; return; }
  el.innerHTML = members.map(m =>
    `<div class="member">
      <div class="avatar">${(m.name||'?')[0].toUpperCase()}</div>
      <div><div class="member-name">${esc(m.name)}</div><div class="member-role">${esc(m.role||'member')}</div></div>
    </div>`
  ).join('');
}

// ══════════════════════════════════════
//  Keyboard & Actions
// ══════════════════════════════════════
function setupKeys() {}
async function addProject() {
  const p = prompt('输入项目路径:');
  if (!p) return;
  const d = await api('/api/projects/add', { method:'POST', body:{path:p} });
  d.ok ? loadProjects() : alert(d.message);
}

// ══════════════════════════════════════
//  Theme
// ══════════════════════════════════════
function toggleThemeSwitch() {
  const sw = document.getElementById('theme-switch');
  const theme = sw.checked ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('aioncode-theme', theme);
}
function _syncThemeSwitch(theme) {
  const sw = document.getElementById('theme-switch');
  if (sw) sw.checked = theme === 'dark';
}

(function() {
  const saved = localStorage.getItem('aioncode-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  document.addEventListener('DOMContentLoaded', () => _syncThemeSwitch(saved));
})();
