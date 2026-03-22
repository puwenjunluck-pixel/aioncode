/* AionCode Copilot — View renderers + data views */
function parseFrontmatter(content) {
  const m = content.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!m) return { meta: {}, body: content };
  const meta = {};
  m[1].split('\n').forEach(line => {
    const kv = line.match(/^(\w[\w_-]*)\s*:\s*(.+)$/);
    if (kv) meta[kv[1]] = kv[2].replace(/^["']|["']$/g, '').trim();
  });
  return { meta, body: m[2] };
}
function applyInline(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
}
function renderMarkdown(text) {
  let html = '';
  let inCode = false, inList = false, listType = '';
  const lines = text.split('\n');
  for (const raw of lines) {
    if (raw.trimStart().startsWith('```')) {
      if (inCode) { html += '</code></pre>'; inCode = false; }
      else { html += '<pre><code>'; inCode = true; }
      continue;
    }
    if (inCode) { html += esc(raw) + '\n'; continue; }
    let line = esc(raw);
    if (inList && !line.match(/^(\s*[-*]\s|^\s*\d+\.\s|^\s*- \[[ x]\])/)) {
      html += listType === 'ul' ? '</ul>' : '</ol>'; inList = false;
    }
    if (line.match(/^### /)) { html += '<h3>' + line.slice(4) + '</h3>'; continue; }
    if (line.match(/^## /)) { html += '<h2>' + line.slice(3) + '</h2>'; continue; }
    if (line.match(/^# /)) { html += '<h1>' + line.slice(2) + '</h1>'; continue; }
    if (line.match(/^-{3,}$/)) { html += '<hr>'; continue; }
    if (line.match(/^- \[x\] /)) {
      if (!inList) { html += '<ul style="list-style:none;padding-left:4px">'; inList = true; listType = 'ul'; }
      html += '<li><div class="check-row"><span class="check-box checked">✓</span>' + applyInline(line.slice(6)) + '</div></li>';
      continue;
    }
    if (line.match(/^- \[ \] /)) {
      if (!inList) { html += '<ul style="list-style:none;padding-left:4px">'; inList = true; listType = 'ul'; }
      html += '<li><div class="check-row"><span class="check-box"></span>' + applyInline(line.slice(6)) + '</div></li>';
      continue;
    }
    if (line.match(/^\s*[-*]\s/)) {
      if (!inList) { html += '<ul>'; inList = true; listType = 'ul'; }
      html += '<li>' + applyInline(line.replace(/^\s*[-*]\s/, '')) + '</li>';
      continue;
    }
    if (line.match(/^\s*\d+\.\s/)) {
      if (!inList) { html += '<ol>'; inList = true; listType = 'ol'; }
      html += '<li>' + applyInline(line.replace(/^\s*\d+\.\s/, '')) + '</li>';
      continue;
    }
    if (line.match(/^\|/)) {
      if (line.match(/^\|[\s-:|]+\|$/)) continue;
      const cells = line.split('|').filter(c => c.trim());
      if (!html.includes('<table>') || html.endsWith('</table>')) {
        html += '<table><tr>' + cells.map(c => '<th>' + applyInline(c.trim()) + '</th>').join('') + '</tr>';
      } else {
        html += '<tr>' + cells.map(c => '<td>' + applyInline(c.trim()) + '</td>').join('') + '</tr>';
      }
      continue;
    }
    if (html.includes('<table>') && !html.endsWith('</table>') && !line.match(/^\|/)) {
      html += '</table>';
    }
    if (!line.trim()) { html += '<br>'; continue; }
    html += '<p>' + applyInline(line) + '</p>';
  }
  if (inCode) html += '</code></pre>';
  if (inList) html += listType === 'ul' ? '</ul>' : '</ol>';
  if (html.includes('<table>') && !html.endsWith('</table>')) html += '</table>';
  return html;
}
function renderFrontmatterTable(meta) {
  if (!meta || !Object.keys(meta).length) return '';
  const statusBadge = v => {
    const cls = ['completed','active','in_progress','deprecated','pending'].find(s => v.includes(s));
    return cls ? `<span class="fm-badge ${cls}">${esc(v)}</span>` : esc(v);
  };
  const rows = Object.entries(meta).map(([k, v]) => {
    const val = k === 'status' ? statusBadge(v) : esc(v);
    return `<tr><td>${esc(k)}</td><td>${val}</td></tr>`;
  }).join('');
  return `<table class="fm-table">${rows}</table>`;
}
async function loadDirFiles(subdir) {
  if (!window._fileTree) {
    const d = await api(`/api/projects/${curEncoded}/files`);
    if (!d.ok) return [];
    window._fileTree = d.tree || [];
  }
  const dir = window._fileTree.find(n => n.name === subdir && n.type === 'dir');
  return dir ? (dir.children || []).filter(f => f.type === 'file') : [];
}
async function loadFileContent(path) {
  const d = await api(`/api/projects/${curEncoded}/file?path=${encodeURIComponent(path)}`);
  if (!d.ok) return null;
  return { ...parseFrontmatter(d.content), raw: d.content, path: d.path };
}
const viewsLoaded = new Set();
function ensureViewData(view) {
  if (viewsLoaded.has(view)) return;
  viewsLoaded.add(view);
  switch(view) {
    case 'specs': loadSpecs(); break;
    case 'plans': loadPlans(); break;
    case 'rules': loadRules(); break;
    case 'checklists': loadChecklists(); break;
    case 'test': loadTests(); break;
    case 'changelog': loadChangelog(); break;
    case 'skills': loadSkills(); break;
  }
}
function resetViewsCache() {
  viewsLoaded.clear();
  window._fileTree = null;
  window._clEntries = null;
}
async function _loadDataView(dir, listId, badgeId, emptyMsg, renderItem) {
  const files = await loadDirFiles(dir);
  const el = document.getElementById(listId);
  document.getElementById(badgeId).textContent = files.length || '—';
  if (!files.length) { el.innerHTML = `<div class="empty">${emptyMsg}</div>`; return; }
  const items = [];
  for (const f of files) {
    const data = await loadFileContent(f.path);
    const title = data?.meta?.title || data?.body?.match(/^#\s+(.+)/m)?.[1] || f.name.replace('.md','');
    items.push({ path: f.path, title, status: data?.meta?.status||'', meta: data?.meta||{} });
  }
  el.innerHTML = items.map(renderItem).join('');
}
async function loadSpecs() {
  await _loadDataView('specs','specs-list','b-specs','暂无需求文档', it =>
    `<div class="data-item" onclick="viewDataItem('${esc(it.path)}')"><div class="data-item-title">${esc(it.title)}</div><div class="data-item-meta">${it.status?`<span class="fm-badge ${it.status}">${esc(it.status)}</span>`:''}${it.meta.created_at?`<span>${esc(it.meta.created_at)}</span>`:''}</div></div>`);
}
async function loadPlans() {
  await _loadDataView('plans','plans-list','b-plans','暂无实施方案', it => {
    const cur=parseInt(it.meta.current_step)||0, total=parseInt(it.meta.total_steps)||0, pct=total?Math.round(cur/total*100):0;
    return `<div class="data-item" onclick="viewDataItem('${esc(it.path)}')"><div class="data-item-title">${esc(it.title)}</div><div class="data-item-meta">${it.status?`<span class="fm-badge ${it.status}">${esc(it.status)}</span>`:''}${total?`<span>${cur}/${total}</span><div class="check-progress"><div class="check-progress-fill" style="width:${pct}%"></div></div>`:''}</div></div>`;
  });
}
async function loadRules() {
  const files = await loadDirFiles('rules');
  const el = document.getElementById('rules-list');
  if (!files.length) { el.innerHTML = '<div class="empty">暂无规则</div>'; document.getElementById('b-rules').textContent = '—'; return; }
  let totalRules = 0;
  let html = '';
  for (const f of files) {
    const data = await loadFileContent(f.path);
    const category = data?.meta?.category || f.name.replace('.md','');
    const count = parseInt(data?.meta?.rule_count) || 0;
    totalRules += count;
    html += `<div class="rule-group-header">${esc(category)} (${count})</div>`;
    html += `<div class="data-item" onclick="viewDataItem('rules/${esc(f.name)}')">
      <div class="data-item-title">${esc(f.name)}</div>
      <div class="data-item-meta"><span>${count} 条规则</span></div>
    </div>`;
  }
  document.getElementById('b-rules').textContent = totalRules || '—';
  el.innerHTML = html;
}
async function loadChecklists() {
  const files = await loadDirFiles('checklists'), el = document.getElementById('checklists-list');
  document.getElementById('b-checklists').textContent = files.length || '—';
  if (!files.length) { el.innerHTML = '<div class="empty">暂无清单</div>'; return; }
  const items = [];
  for (const f of files) {
    const data = await loadFileContent(f.path), body = data?.body||data?.raw||'';
    const total = (body.match(/- \[[ x]\]/g)||[]).length, done = (body.match(/- \[x\]/g)||[]).length;
    items.push({ path: f.path, name: f.name.replace('.md',''), done, total, pct: total?Math.round(done/total*100):0 });
  }
  el.innerHTML = items.map(it => `<div class="data-item" onclick="viewDataItem('${esc(it.path)}')"><div class="data-item-title">${esc(it.name)}</div><div class="data-item-meta"><span>${it.done}/${it.total}</span><div class="check-progress"><div class="check-progress-fill" style="width:${it.pct}%"></div></div></div></div>`).join('');
}
async function loadTests() {
  const el = document.getElementById('test-list');
  if (!window._fileTree) { const d = await api(`/api/projects/${curEncoded}/files`); if (d.ok) window._fileTree = d.tree || []; }
  const dir = (window._fileTree||[]).find(n => n.name === 'tests' && n.type === 'dir');
  if (!dir?.children?.length) { el.innerHTML = '<div class="empty">暂无测试报告</div>'; document.getElementById('b-test').textContent = '—'; return; }
  let total = 0, html = '';
  for (const c of dir.children) {
    if (c.type === 'dir') {
      const sf = c.children||[]; total += sf.length;
      html += `<div class="rule-group-header">${esc(c.name)}/ (${sf.length})</div>`;
      sf.forEach(f => { html += `<div class="data-item" onclick="viewDataItem('tests/${esc(c.name)}/${esc(f.name)}')"><div class="data-item-title">${esc(f.name)}</div><div class="data-item-meta"><span>${fmtSz(f.size)}</span></div></div>`; });
    } else { total++; html += `<div class="data-item" onclick="viewDataItem('tests/${esc(c.name)}')"><div class="data-item-title">${esc(c.name)}</div><div class="data-item-meta"><span>${fmtSz(c.size)}</span></div></div>`; }
  }
  document.getElementById('b-test').textContent = total || '—'; el.innerHTML = html;
}
async function loadChangelog() {
  const d = await api(`/api/projects/${curEncoded}/changelog?limit=50`);
  window._clEntries = d.entries || []; const el = document.getElementById('changelog-list');
  document.getElementById('b-changelog').textContent = window._clEntries.length || '—';
  if (!window._clEntries.length) { el.innerHTML = '<div class="empty">暂无变更记录</div>'; return; }
  el.innerHTML = window._clEntries.map((e, i) => { const p=e.header.split('|'); return `<div class="cl-entry" onclick="viewChangelogEntry(${i})"><div class="cl-entry-date">${esc(p[0]?.trim()||'')}</div><div class="cl-entry-title">${esc(p[1]?.trim()||e.header)}</div></div>`; }).join('');
}
function viewChangelogEntry(idx) {
  const e = window._clEntries?.[idx]; if (!e) return;
  document.querySelectorAll('.cl-entry').forEach((el,i)=>el.classList.toggle('active',i===idx));
  const p=e.header.split('|'), date=p[0]?.trim()||'', title=p[1]?.trim()||e.header;
  document.getElementById('detail').innerHTML = `<div class="md-content"><h1>${esc(title)}</h1><p style="color:var(--text-tertiary);font-size:11px;margin-bottom:16px">${esc(date)}</p>${renderMarkdown(e.body)}</div>`;
}
async function viewDataItem(path) {
  document.querySelectorAll('.data-item').forEach(el => el.classList.remove('active'));
  event?.target?.closest('.data-item')?.classList.add('active');
  const data = await loadFileContent(path);
  if (!data) { document.getElementById('detail').innerHTML = '<div class="detail-welcome"><div class="welcome-title">文件加载失败</div></div>'; return; }
  document.getElementById('detail').innerHTML = `<div class="md-content"><div style="display:flex;align-items:center;gap:8px;margin-bottom:12px"><h1 style="margin:0;flex:1">${esc(path.split('/').pop())}</h1></div>${renderFrontmatterTable(data.meta)}${renderMarkdown(data.body)}</div>`;
}
const ABOUT_SECTIONS = [
  { id:'what',      title:'什么是 AionCode' },
  { id:'install',   title:'安装与初始化' },
  { id:'workflow',  title:'工作流指南' },
  { id:'commands',  title:'命令速查' },
  { id:'scenarios', title:'常见场景' },
  { id:'dashboard', title:'副驾驶面板' },
  { id:'faq',       title:'常见问题' },
  { id:'roadmap',   title:'版本路线图' },
];
function renderAboutToc() {
  document.getElementById('about-toc').innerHTML = ABOUT_SECTIONS.map(s =>
    `<div class="fnode" style="padding-left:4px;cursor:pointer" onclick="scrollAbout('${s.id}')">
      <span class="ico">§</span>${s.title}
    </div>`
  ).join('');
}
function scrollAbout(id) {
  const el = document.getElementById('about-' + id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function _tbl(h,r){return `<table class="key-table"><tr>${h.map(x=>'<th>'+x+'</th>').join('')}</tr>${r.map(x=>'<tr>'+x.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')}</table>`}
function _flow(s){return `<div class="flow">${s.map(x=>`<span class="flow-step">${x}</span>`).join('<span class="flow-arrow">→</span>')}</div>`}
function _faq(q,a){return `<p><strong>Q：${q}</strong></p><p>${a}</p>`}
function renderAboutPage() {
  setTimeout(renderAboutToc, 0);
  const cmds = [
    ['准备','<code>aion-scan</code>','扫描已有项目，建立初始智能数据'],
    ['','<code>aion-think</code>','质疑假设，在开始前暴露盲点'],
    ['','<code>aion-help</code>','查看所有命令和工作流说明'],
    ['设计','<code>aion-design</code>','将想法转化为结构化需求规格'],
    ['','<code>aion-demo</code>','生成交互式 HTML 原型（可选）'],
    ['','<code>aion-plan</code>','创建分步实施计划'],
    ['实施','<code>aion-impl</code>','按计划编写代码（自动遵守规则）'],
    ['','<code>aion-test</code>','生成测试、分析覆盖率'],
    ['质量','<code>aion-verify</code>','运行构建、测试、lint、类型检查'],
    ['','<code>aion-review</code>','代码审查 + 自动提取规则'],
    ['管理','<code>aion-commit</code>','安全提交（需 review 通过）'],
    ['','<code>aion-save</code>','保存对话上下文到 .aion/ 和 memory'],
    ['','<code>aion-bug</code>','Bug 管理：报告/列表/分配/关闭'],
    ['','<code>aion-crosscheck</code>','用其他 AI 模型交叉验证代码'],
    ['运维','<code>aion-loop</code>','自动化流水线（设计→实现→验证→审查）'],
    ['','<code>aion-status</code>','项目状态总览'],['','<code>aion-upgrade</code>','版本升级'],['','<code>aion-learn</code>','从审查中提取规则'],
  ];
  return `<div class="about">
    <h1>AionCode 使用指南</h1>
    <p class="subtitle">AI 原生开发智能框架 · 让 AI 编程有章可循</p>
    <h2 id="about-what">什么是 AionCode</h2>
    <p>AionCode 是成都奕贝科技公司开发的一个 <strong>AI 辅助开发的智能框架</strong>。它为你的项目建立一套结构化的知识体系（规则、规格、计划），让 AI（Claude Code）在编码时有据可循。</p>
    <p style="margin-top:8px">核心理念：<strong>知识沉淀 → 规则驱动 → 质量可控</strong></p>
    ${_tbl(['组成','作用'],[['<code>.aion/</code> 目录','项目智能数据：规则、规格、计划、日志、Bug'],['<code>commands/</code>','18 个 AI 工作流命令'],['<code>aioncode</code> CLI','命令行工具：初始化、升级、副驾驶'],['副驾驶面板','Web 可视化界面（你正在看的这个）']])}
    <h2 id="about-install">安装与初始化</h2>
    <p>在项目根目录执行 <code>aioncode init</code>，然后（可选）运行 <code>/project:aion-scan</code> 自动提取规则。</p>
    ${_tbl(['目录','用途'],[['<code>.aion/rules/</code>','编码规则'],['<code>.aion/specs/</code>','需求文档'],['<code>.aion/plans/</code>','实施计划'],['<code>.aion/bugs/</code>','Bug 报告'],['<code>.claude/commands/</code>','AI 工作流命令']])}
    <h2 id="about-workflow">工作流指南</h2>
    <p><strong>新项目：</strong></p>${_flow(['think','design','plan','impl','verify','review','commit'])}
    <p style="margin-top:12px"><strong>已有项目：</strong></p>${_flow(['scan','impl/design','verify','review','commit'])}
    <p style="margin-top:12px"><strong>Bug 修复：</strong></p>${_flow(['bug report','impl {BUG-ID}','verify','review','commit'])}
    <p style="margin-top:8px">所有命令在 Claude Code 终端中以 <code>/project:aion-xxx</code> 格式调用。</p>
    <h2 id="about-commands">命令速查</h2>
    <table class="key-table"><tr><th>阶段</th><th>命令</th><th>说明</th></tr>${cmds.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')}</table>
    <h2 id="about-scenarios">常见场景</h2>
    ${_tbl(['场景','操作流程'],[['加新功能','design → plan → impl → verify → review → commit'],['修 Bug','bug report → impl {BUG-ID} → verify → commit'],['交叉验证','crosscheck --model gemini → 自动生成 Bug 报告'],['接手项目','aioncode init → aion-scan → 自动建立智能数据']])}
    <h2 id="about-dashboard">副驾驶面板</h2>
    <p>副驾驶是 <strong>CLI 的可视化外壳</strong>。启动：<code>aioncode dashboard</code></p>
    ${_tbl(['视图','用途'],[['◈ 概览','项目统计 + 变更历史'],['◇ 文件','浏览 .aion/ 配置文件'],['◎ 监控','SSE 实时事件流'],['● 缺陷','Bug 列表与详情'],['⚡ 技能','Skill 管理与市场']])}
    <h2 id="about-faq">常见问题</h2>
    ${[['支持哪些 AI 模型？','命令在 Claude Code 中执行。crosscheck 可调用 Gemini 等做交叉验证。'],['.aion/ 要提交 Git 吗？','建议提交。rules/specs/plans 是团队共享知识。sessions.jsonl 和 monitor/ 已排除。'],['如何升级？','运行 <code>aioncode upgrade</code>，只更新命令和工具，不覆盖数据。'],['review 不通过能提交吗？','不能。aion-commit 要求 review 通过（docs-only 可豁免）。']].map(([q,a])=>_faq(q,a)).join('')}
    <h2 id="about-roadmap">版本路线图</h2>
    <ul>
      <li><strong>v0.5</strong>（当前）— FastAPI 重构 + 副驾驶 UI + Core 层统一</li>
      <li><strong>v0.6</strong> — 云端 MVP：意图日志管道 + 多项目统计</li>
      <li><strong>v0.7</strong> — 云端完整：团队管理 + Bug 看板 + 规则共享</li>
    </ul>
  </div>`;
}
async function loadOverviewDetail() {
  const el = document.getElementById('detail-overview');
  if (!el || !curEncoded) return;
  const s = window._stats || {};
  const cl = await api(`/api/projects/${curEncoded}/changelog?limit=5`);
  const entries = cl.entries || [];
  const se = await api(`/api/projects/${curEncoded}/sessions?limit=5`);
  const sessions = se.sessions || [];
  el.innerHTML = `
    <div class="do-section">
      <h3 class="do-title">项目统计</h3>
      <div class="do-grid">
        ${[['style','代码风格',s.rules?.style],['pitfalls','已知陷阱',s.rules?.pitfalls],['perf','性能规则',s.rules?.perf],['cmds','命令数',s.commands],['specs','需求文档',s.specs],['plans','实施方案',s.plans]].map(([,l,v])=>`<div class="do-card"><div class="do-card-val">${v??0}</div><div class="do-card-lbl">${l}</div></div>`).join('')}
      </div>
    </div>
    <div class="do-section">
      <h3 class="do-title">变更历史</h3>
      ${entries.length ? entries.map(e => `
        <div class="do-entry">
          <div class="do-entry-head">${esc(e.header)}</div>
          <div class="do-entry-body">${esc(e.body).substring(0, 200)}</div>
        </div>`).join('') : '<div class="empty">暂无记录</div>'}
    </div>
    <div class="do-section">
      <h3 class="do-title">最近会话</h3>
      ${sessions.length ? sessions.map(s => `
        <div class="do-session">
          <span class="do-session-ts">${esc(s.started_at || s.ts || '')}</span>
          <span class="do-session-info">工具 ${Object.keys(s.tools_used||{}).length} 种 · 文件 ${(s.files_changed||[]).length} 个</span>
        </div>`).join('') : '<div class="empty">暂无会话</div>'}
    </div>`;
}
async function loadMonitorDetail() {
  const el = document.getElementById('detail-monitor');
  if (!el || !curEncoded) return;
  const state = await api(`/api/monitor/${curEncoded}/state`);
  if (!state.ok) return;
  const tools = state.tools || {};
  const files = state.files_changed || [];
  const toolEntries = Object.entries(tools).sort((a,b) => b[1]-a[1]);
  const maxCount = toolEntries.length ? toolEntries[0][1] : 1;
  el.innerHTML = `
    <div class="do-section">
      <h3 class="do-title">会话状态</h3>
      <div class="do-grid">
        ${[['总事件',state.total_events],['工具种类',toolEntries.length],['文件变更',files.length],['子代理',(state.agents||[]).length]].map(([l,v])=>`<div class="do-card"><div class="do-card-val">${v}</div><div class="do-card-lbl">${l}</div></div>`).join('')}
      </div>
    </div>
    <div class="do-section">
      <h3 class="do-title">工具使用分布</h3>
      ${toolEntries.length ? toolEntries.map(([name, count]) => `
        <div class="do-bar-row">
          <span class="do-bar-label">${esc(name)}</span>
          <div class="do-bar-track"><div class="do-bar-fill" style="width:${(count/maxCount*100).toFixed(0)}%"></div></div>
          <span class="do-bar-val">${count}</span>
        </div>`).join('') : '<div class="empty">暂无数据</div>'}
    </div>
    <div class="do-section">
      <h3 class="do-title">变更文件</h3>
      ${files.length ? files.map(f => `<div class="do-file-item">→ ${esc(f.split('/').slice(-2).join('/'))}</div>`).join('') : '<div class="empty">暂无文件变更</div>'}
    </div>`;
}
function viewBug(idx) {
  const b = window._bugs[idx];
  if (!b) return;
  document.getElementById('detail').innerHTML = `
    <div class="detail-bug">
      <h2>${esc(b.title)}</h2>
      <div class="meta">
        <span class="tag">${esc(b.id)}</span>
        <span class="tag">${esc(b.severity||'medium')}</span>
        <span class="tag">${esc(b.status||'open')}</span>
        ${b.assignee ? `<span class="tag">→ ${esc(b.assignee)}</span>` : ''}
      </div>
      <div class="body">${esc(b.body||'无描述')}</div>
    </div>`;
}
async function loadTeamDetail() {
  const el = document.getElementById('detail-team');
  if (!el) return;
  const t = window._team || {};
  const members = t.team || [];
  const models = t.models || {};
  const risk = t.risk_keywords || {};
  el.innerHTML = `
    <div class="do-section">
      <h3 class="do-title">成员 (${members.length})</h3>
      ${members.length ? members.map(m => `
        <div class="do-member-card">
          <div class="avatar" style="width:32px;height:32px;font-size:14px;border-radius:6px">${(m.name||'?')[0].toUpperCase()}</div>
          <div>
            <div style="font-weight:600;font-size:13px">${esc(m.name)}</div>
            <div style="font-size:11px;color:var(--text-tertiary)">${esc(m.role||'member')}${m.git_email ? ' · '+esc(m.git_email) : ''}</div>
            ${m.expertise ? `<div style="font-size:10px;color:var(--text-tertiary);margin-top:2px">专长: ${esc(Array.isArray(m.expertise)?m.expertise.join(', '):m.expertise)}</div>` : ''}
          </div>
        </div>`).join('') : '<div class="empty">未配置成员</div>'}
    </div>
    ${[['模型配置',models],['风险关键词',risk]].map(([t,d])=>`<div class="do-section"><h3 class="do-title">${t}</h3>${Object.keys(d).length?Object.entries(d).map(([k,v])=>`<div class="do-kv"><span class="do-kv-k">${esc(k)}</span><span class="do-kv-v">${esc(v)}</span></div>`).join(''):'<div class="empty">未配置</div>'}</div>`).join('')}`;
}

// ══════════════════════════════════════
//  Skills
// ══════════════════════════════════════
async function loadSkills() {
  const d = await api('/api/skills');
  if (!d.ok) return;
  window._skills = d.skills || [];
  document.getElementById('b-skills').textContent = window._skills.length || '--';
  renderSkillsSidebar(window._skills);
}

function renderSkillsSidebar(skills) {
  const el = document.getElementById('skills-list');
  if (!skills.length) { el.innerHTML = '<div class="empty">暂无已安装技能</div><div class="skill-hint">运行 <code>/find-skills</code> 搜索技能</div>'; return; }
  const groups = { user: [], agent: [] }, labels = { user: '用户技能', agent: '代理技能' };
  skills.forEach(s => (groups[s.source] || groups.user).push(s));
  let html = '';
  for (const [type, items] of Object.entries(groups)) {
    if (!items.length) continue;
    html += `<div class="rule-group-header">${labels[type]||type} (${items.length})</div>`;
    items.forEach(s => {
      const desc = (s.description||'').substring(0, 60);
      html += `<div class="data-item" onclick="viewSkill('${esc(s.dir_name)}')"><div class="data-item-title">${esc(s.name)}</div><div class="data-item-meta"><span class="tag">${esc(type)}</span><span>${esc(desc)}${desc.length>=60?'...':''}</span></div></div>`;
    });
  }
  el.innerHTML = html;
}

async function switchSkillTab(tab) {
  document.querySelectorAll('.skill-tab').forEach(b =>
    b.classList.toggle('active', (tab === 'installed' && b.textContent === '已安装') || (tab === 'marketplace' && b.textContent === '官方市场')));
  if (tab === 'installed') {
    renderSkillsSidebar(window._skills || []);
  } else {
    const el = document.getElementById('skills-list');
    el.innerHTML = '<div class="empty">加载中...</div>';
    const d = await api('/api/skills/marketplace');
    if (!d.ok) { el.innerHTML = '<div class="empty">加载失败</div>'; return; }
    window._marketplacePlugins = d.plugins || [];
    renderMarketplaceSidebar(window._marketplacePlugins);
  }
}

function renderMarketplaceSidebar(plugins) {
  const el = document.getElementById('skills-list');
  if (!plugins.length) {
    el.innerHTML = '<div class="empty">暂无可用插件</div>';
    return;
  }
  el.innerHTML = plugins.map(p =>
    `<div class="data-item" onclick="viewMarketplacePlugin('${esc(p.name)}')">
      <div class="data-item-title">${esc(p.name)} ${p.installed ? '<span class="fm-badge completed">已安装</span>' : ''}</div>
      <div class="data-item-meta"><span>${esc((p.description || '').substring(0, 80))}</span></div>
    </div>`
  ).join('');
}

async function viewSkill(dirName) {
  document.querySelectorAll('#skills-list .data-item').forEach(el => el.classList.remove('active'));
  if (event?.target) event.target.closest('.data-item')?.classList.add('active');
  const d = await api(`/api/skills/${encodeURIComponent(dirName)}`);
  if (!d.ok) {
    document.getElementById('detail').innerHTML = '<div class="detail-welcome"><div class="welcome-title">技能加载失败</div></div>';
    return;
  }
  const meta = d.meta || {};
  const files = d.files || [];
  document.getElementById('detail').innerHTML = `<div class="md-content">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
      <h1 style="margin:0;flex:1">${esc(meta.name || dirName)}</h1>
      <button class="skill-action-btn danger" onclick="uninstallSkill('${esc(dirName)}')">卸载</button>
    </div>
    ${renderFrontmatterTable(meta)}
    ${files.length ? `<div style="margin:12px 0"><strong>文件结构:</strong><div style="margin-top:4px;display:flex;flex-wrap:wrap;gap:4px">${files.map(f => '<code style="font-size:11px;padding:1px 6px;background:var(--bg);border-radius:3px">' + esc(f) + '</code>').join('')}</div></div>` : ''}
    ${renderMarkdown(d.body || '')}
  </div>`;
}

function viewMarketplacePlugin(name) {
  document.querySelectorAll('#skills-list .data-item').forEach(el => el.classList.remove('active'));
  if (event?.target) event.target.closest('.data-item')?.classList.add('active');
  const plugin = (window._marketplacePlugins || []).find(p => p.name === name) || {};
  const authorStr = plugin.author ? (typeof plugin.author === 'object' ? (plugin.author.name || '') : plugin.author) : '';
  document.getElementById('detail').innerHTML = `<div class="md-content">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px">
      <h1 style="margin:0;flex:1">${esc(name)}</h1>
      ${plugin.installed
        ? '<span class="fm-badge completed">已安装</span>'
        : `<button class="skill-action-btn primary" onclick="installPlugin('${esc(name)}')">安装</button>`}
    </div>
    ${plugin.description ? `<p>${esc(typeof plugin.description === 'object' ? JSON.stringify(plugin.description) : plugin.description)}</p>` : ''}
    ${authorStr ? `<p style="font-size:12px;color:var(--text-tertiary)">作者: ${esc(authorStr)}</p>` : ''}
  </div>`;
}

async function uninstallSkill(dirName) {
  if (!confirm(`确定卸载技能 "${dirName}"？`)) return;
  const btn = document.querySelector('.skill-action-btn.danger');
  if (btn) { btn.disabled = true; btn.textContent = '卸载中...'; }
  const d = await api(`/api/skills/${encodeURIComponent(dirName)}`, { method: 'DELETE' });
  if (d.ok) { viewsLoaded.delete('skills'); loadSkills(); showViewDetail('skills'); }
  else { alert('卸载失败: ' + (d.message||'')); if (btn) { btn.disabled = false; btn.textContent = '卸载'; } }
}
async function installPlugin(name) {
  const btn = event?.target;
  if (btn) { btn.disabled = true; btn.textContent = '安装中...'; }
  const d = await api('/api/skills/marketplace/install', { method: 'POST', body: { name } });
  if (d.ok) { if (btn) { btn.textContent = '已安装'; btn.className = 'skill-action-btn'; } const md = await api('/api/skills/marketplace'); if (md.ok) window._marketplacePlugins = md.plugins || []; }
  else { alert('安装失败: ' + (d.message||'')); if (btn) { btn.disabled = false; btn.textContent = '安装'; } }
}
