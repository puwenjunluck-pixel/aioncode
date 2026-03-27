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
  { id:'what',       title:'什么是 AionCode' },
  { id:'install',    title:'安装与升级' },
  { id:'roadmap',    title:'版本路线图' },
  { id:'releaselog', title:'更新日志' },
];
const HELP_SECTIONS = [
  { id:'workflow',  title:'工作流指南' },
  { id:'commands',  title:'命令速查' },
  { id:'scenarios', title:'常见场景' },
  { id:'testing',   title:'测试最佳实践' },
  { id:'dashboard', title:'副驾驶面板' },
  { id:'faq',       title:'常见问题' },
];
function renderAboutToc() {
  document.getElementById('about-toc').innerHTML = ABOUT_SECTIONS.map(s =>
    `<div class="fnode" style="padding-left:4px;cursor:pointer" onclick="scrollAbout('${s.id}')"><span class="ico">§</span>${s.title}</div>`).join('');
}
function scrollAbout(id) {
  const el = document.getElementById('about-' + id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function renderHelpToc() {
  document.getElementById('help-toc').innerHTML = HELP_SECTIONS.map(s =>
    `<div class="fnode" style="padding-left:4px;cursor:pointer" onclick="scrollHelp('${s.id}')"><span class="ico">§</span>${s.title}</div>`).join('');
}
function scrollHelp(id) {
  const el = document.getElementById('help-' + id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function _tbl(h,r){return `<table class="key-table"><tr>${h.map(x=>'<th>'+x+'</th>').join('')}</tr>${r.map(x=>'<tr>'+x.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')}</table>`}
function _flow(s){return `<div class="flow">${s.map(x=>`<span class="flow-step">${x}</span>`).join('<span class="flow-arrow">→</span>')}</div>`}
function _faq(q,a){return `<p><strong>Q：${q}</strong></p><p>${a}</p>`}
/** 测试最佳实践板块 */
function _renderTestingGuide() {
  return `
    <h2 id="help-testing">测试最佳实践</h2>
    <p>本章是写给<strong>测试人员（QA）</strong>的完整指南。核心工具是 <code>aion-qa</code>（发现）+ <code>aion-fix</code>（修复）+ <code>aion-review</code>（质量验收）。</p>

    <h3>一、你的角色定位</h3>
    ${_tbl(['传统模式','AionCode v0.7 模式'],[
      ['手写 Selenium/Playwright 脚本','<code>aion-qa {url}</code> 自动浏览所有页面发现问题'],
      ['手动整理 Bug 报告','AI 自动生成结构化 Bug 报告到 <code>.aion/bugs/</code>'],
      ['开发修复后手工回归','<code>aion-fix</code> + <code>aion-review</code> 自动修复并验证'],
      ['测试覆盖率靠人肉检查','<code>aion-review</code> 自动发现 test gap 并生成测试'],
      ['E2E 用例用代码写','用中文 Given/When/Then Markdown 描述，存 <code>.aion/tests/e2e/</code>']
    ])}

    <h3>二、QA 流程</h3>
    <p><strong>推荐流程（先报告后修复）：</strong></p>
    ${_flow(['aion-qa --report-only {url}','审核 Bug 报告','aion-fix','aion-review','commit'])}
    <p style="margin-top:8px"><strong>全自动流程（一键测试+修复）：</strong></p>
    ${_flow(['aion-qa {url}','aion-review','commit'])}
    <p style="margin-top:6px;color:var(--text-tertiary)">推荐用"先报告后修复"，方便 QA 人员审核 Bug 报告再决定是否修复。</p>

    <h3>三、aion-qa — 浏览器 QA 测试</h3>
    <p>aion-qa 使用真实浏览器逐页测试，自动发现并分类 Bug：</p>
    ${_tbl(['参数','说明'],[
      ['<code>aion-qa {url}</code>','测试 URL，发现 Bug 后自动修复（P0/P1 优先）'],
      ['<code>aion-qa --report-only {url}</code>','只生成报告，不修改任何代码（QA 审查模式）'],
    ])}
    <p style="margin-top:8px"><strong>Bug 严重级别：</strong></p>
    ${_tbl(['级别','触发条件','示例'],[
      ['P0 Critical','崩溃 / 数据丢失 / 支付 / 认证破坏','登录后跳转死循环、支付报错'],
      ['P1 High','核心功能无法完成','表单提交无响应、列表加载失败'],
      ['P2 Medium','功能可用但有问题','按钮位置偏移、某些输入不校验'],
      ['P3 Low','UI 细节 / 文案问题','字体大小不一致、标点错误']
    ])}
    <p style="margin-top:8px"><strong>Bug 类型前缀：</strong><code>F-</code> 前端 · <code>B-</code> 后端 · <code>X-</code> 跨端。报告写入 <code>.aion/bugs/</code>，可在副驾驶「缺陷」视图查看。</p>
    <p style="margin-top:6px"><strong>浏览器后端：</strong>优先使用 gstack browse CLI（ARIA 交互，~100ms）；回退到 Playwright MCP。两者都没有时命令退出并提示安装。</p>

    <h3>四、aion-fix — 按角色修复 Bug</h3>
    <p>读取 <code>.aion/bugs/</code> 中的报告，根据当前角色过滤，逐个 atomic commit 修复：</p>
    ${_tbl(['参数','说明'],[
      ['<code>aion-fix</code>','修复所有符合当前角色的 open Bug'],
      ['<code>aion-fix -f</code>','只修复前端 Bug（F-* 前缀）'],
      ['<code>aion-fix -b</code>','只修复后端 Bug（B-* 前缀）'],
      ['<code>aion-fix {BUG-ID}</code>','只修复指定 Bug（如 F-0326-001）'],
    ])}
    <p style="margin-top:6px;color:var(--text-tertiary)">每个 Bug 独立提交（fix(bug): {ID} {title}），方便单独回滚。修复完成后自动将 Bug 状态更新为 fixed。</p>

    <h3>五、aion-review — 代码质量 + 测试缺口</h3>
    <p>一站式质量门禁，QA 阶段修复完成后运行：</p>
    ${_tbl(['检查项','说明'],[
      ['Build / Lint / Tests','先 verify，不通过则阻止 review'],
      ['代码审查','逐文件审查，评分 0-100，verdict: approved / needs_fix'],
      ['Test Gap 分析','覆盖图：已改动函数 vs 已有测试；自动生成 P0 缺口的测试'],
      ['Regression Iron Rule','已有测试的函数如有修改，测试必须同步更新'],
      ['--quick 模式','只跑 verify + 审查，跳过 test gap 分析（快速确认）']
    ])}

    <h3>六、自然语言 E2E 测试用例</h3>
    <p>测试用例存在 <code>.aion/tests/e2e/</code>，每个功能一个 <code>.md</code> 文件，aion-review 会引用它们生成测试：</p>
    <pre style="background:var(--bg-sidebar);padding:12px;border-radius:6px;font-size:12px;line-height:1.6;overflow-x:auto">---
feature: 功能名称
target_url: http://localhost:19200
---

## TC-001: 测试标题

**Given**: 在登录页，用户未登录
**When**: 输入正确账号 → 点击登录
**Then**:
  - 跳转到主页
  - 顶部显示用户名

**Edge Cases**:
  - 密码错误时显示错误提示
  - 连续失败 5 次后锁定账号</pre>
    <p style="margin-top:8px;color:var(--text-tertiary)">直接用自然语言描述操作，AI 会推断对应的浏览器操作（点击/输入/等待/截图等）。</p>

    <h3>七、与开发者协作</h3>
    ${_tbl(['QA 负责','开发者负责'],[
      ['运行 <code>aion-qa --report-only {url}</code> 发现 Bug','用 <code>aion-design</code> 写需求规格'],
      ['审核 <code>.aion/bugs/</code> 中的 Bug 报告','用 <code>aion-plan</code> 规划实现方案'],
      ['在 <code>.aion/tests/e2e/</code> 补充测试场景','用 <code>aion-fix {BUG-ID}</code> 修复 Bug'],
      ['用 <code>aion-review --quick</code> 快速验收','用 <code>aion-review</code> 全量质量检查']
    ])}
    <p style="margin-top:12px"><strong>推荐协作流程：</strong></p>
    ${_flow(['QA: qa --report-only','审核 Bug 报告','开发: fix','QA: review --quick','commit'])}

    <h3>八、快速上手</h3>
    <ol>
      <li>✅ 确认项目已执行 <code>aioncode init</code>（<code>.aion/</code> 目录存在）</li>
      <li>✅ 启动你要测试的应用（如 <code>npm run dev</code>）</li>
      <li>✅ 在 Claude Code 终端运行 <code>/project:aion-qa --report-only http://localhost:3000</code></li>
      <li>✅ 查看 <code>.aion/bugs/</code> 下生成的 Bug 报告</li>
      <li>✅ 运行 <code>/project:aion-fix</code> 修复 Bug，或指定 ID 修复单个</li>
      <li>✅ 运行 <code>/project:aion-review --quick</code> 快速验收</li>
      <li>✅（可选）在 <code>.aion/tests/e2e/</code> 添加自然语言测试用例</li>
    </ol>
  `;
}
/** 更新日志板块 */
function _renderReleaseLog() {
  return `
    <h2 id="about-releaselog">更新日志</h2>

    <h3>2026-03-25 · design-plan 合并 + init 交互式安装 (v0.6.6)</h3>
    <p><strong>design-plan 工作流合并：</strong></p>
    <ul>
      <li><code>aion-design</code> 升级为一步到位：需求分析 + 实施计划直接输出 <code>plan.md</code>，无需再单独跑 <code>aion-plan</code></li>
      <li><code>aion-plan</code> 降级为"修订实施方案"，仅用于已有 plan 的调整</li>
      <li>支持 <code>--design-only</code> 仅输出需求（不生成实施步骤）</li>
      <li>10 个命令文件更新引用，全部添加 legacy fallback 兼容旧 spec 文件</li>
    </ul>
    <p style="margin-top:8px"><strong>init 交互式安装：</strong></p>
    <ul>
      <li><code>aioncode init</code> 新增交互引导：项目类型 → 角色选择（设计师/前端/后端/测试/全栈）→ 命令推荐 → 自由增减</li>
      <li>5 种角色预设，核心命令（help/status/review/commit/learn）始终安装</li>
      <li>升级时自动清理已移除的旧命令文件，保持 <code>.claude/commands/</code> 整洁</li>
    </ul>
    <p style="margin-top:8px"><strong>其他改进：</strong></p>
    <ul>
      <li>新增 <code>.aion/refs/command-conventions.md</code> 共享约定文档</li>
      <li>11 个已完成 spec/plan 归档至 archive/，changelog 滚动归档</li>
      <li><code>architecture.md</code> 更新至 v0.6.4 基线</li>
    </ul>

    <h3>2026-03-23 · 测试体系升级 + 产品设计层</h3>
    <p><strong>测试体系三层升级：</strong></p>
    <ul>
      <li><strong>P0 — 测试自愈</strong>：<code>aion-test --heal</code> 测试失败时自动诊断根因（代码 bug / 测试过期 / 环境问题），最多 3 轮自动修复。<code>aion-verify --fix</code> 升级为"修理工"，lint 自动修复 + 测试自愈。</li>
      <li><strong>P1 — E2E 浏览器测试</strong>：<code>aion-test e2e</code> 三阶段架构（实地勘察 → 多源分析生成用例 → 执行）。支持 Playwright MCP live 模式和 gen 脚本生成模式自动降级。测试人员不需要手写用例，AI 从 spec + 源码 + UI 勘察 + API 契约 + Bug 历史自动生成，覆盖率约 90%。</li>
      <li><strong>P2 — 多代理测试管道</strong>：<code>aion-test pipeline</code> 启动 5 阶段子代理（分析师 → 规划师 → 工程师 → 哨兵 → 治疗师），哨兵有质量门禁 BLOCK 权力。</li>
    </ul>
    <p style="margin-top:8px"><strong>产品设计层（_product.md）：</strong></p>
    <ul>
      <li>新增 <code>.aion/specs/_product.md</code> 全局产品设计文档：产品定位、功能地图、核心业务流程、模块架构、技术栈</li>
      <li><code>aion-design</code> / <code>aion-plan</code> 完成后自动传播更新产品文档</li>
      <li><code>aion-scan</code> 支持浏览器探索（<code>--url</code>）+ 外部文档导入（<code>--file</code>），多源交叉分析生成产品文档</li>
      <li>所有策略支持 AI 提问补充，[INFERRED] 推断项经用户确认后升级为 [CONFIRMED]</li>
    </ul>
    <p style="margin-top:8px"><strong>外部文档导入（--file）：</strong></p>
    <ul>
      <li><code>aion-design --file 需求.docx</code> — 从 Word/PDF/PPT 导入需求，自动生成 spec</li>
      <li><code>aion-scan --file 架构设计.pdf</code> — 补充扫描上下文，提升产品文档质量</li>
      <li>支持格式：.docx / .pdf / .md / .pptx / .xlsx，通过 markitdown 工具自动转换</li>
    </ul>
    <p style="margin-top:8px"><strong>其他改进：</strong></p>
    <ul>
      <li>自然语言 E2E 测试定义格式（Given/When/Then + Edge Cases），存放在 <code>.aion/tests/e2e/*.md</code></li>
      <li>14 个中文 When 动作关键词映射到 Playwright 操作</li>
      <li>Dashboard「关于」页新增完整的"测试人员最佳实践"指南（11 个子章节）</li>
      <li>pitfalls 规则更新：Playwright 浏览器自动化仅限 <code>aion-test e2e</code> 模式</li>
      <li>ImportError 诊断拆分为"依赖未安装 [ENV_ISSUE]"和"模块改名 [TEST_FIX]"</li>
      <li>E2E 目标智能匹配：支持中文描述、spec 文件名、模块路径、交互式选择四种输入方式，测试人员无需记忆 spec 文件名</li>
    </ul>

    <h3>2026-03-23 · GitHub Token 认证支持</h3>
    <ul>
      <li><code>network.py</code> 新增 <code>_get_token()</code> / <code>_build_headers()</code> 认证辅助</li>
      <li>私有仓库 API 和 asset 下载均支持 GITHUB_TOKEN</li>
      <li>401/403/404 给出明确中文提示</li>
    </ul>

    <h3>2026-03-22 · auto 模式权限扩展 + loop 报告持久化</h3>
    <ul>
      <li>settings 模板新增 11 个 auto 模式常用权限</li>
      <li><code>aion-loop</code> 新增执行报告持久化到 <code>.aion/monitor/loop-{timestamp}.md</code></li>
    </ul>

    <h3>2026-03-22 · v0.6.0 发布</h3>
    <ul>
      <li>Skills 管理与官方市场</li>
      <li>工作流强制化（NEVER skip the workflow）</li>
      <li>并行策略优化</li>
      <li>Dashboard 版本号动态显示 + 关于页命令补全</li>
    </ul>
  `;
}
function renderHelpPage() {
  setTimeout(renderHelpToc, 0);
  return `<div class="about">
    <h1>帮助中心</h1>
    <p class="subtitle">使用指南 · 命令速查 · 最佳实践</p>

    <h2 id="help-workflow">工作流指南</h2>
    <p><strong>新功能开发：</strong></p>
    ${_flow(['design','plan','[OK→执行]','review','commit'])}
    <p style="margin-top:6px;font-size:12px;color:var(--text-tertiary)">design 内含：挑战假设 + 方案对比 + spec。plan 确认后直接执行代码。</p>
    <p style="margin-top:12px"><strong>Bug 修复：</strong></p>
    ${_flow(['qa --report-only','fix','review','commit'])}
    <p style="margin-top:6px;font-size:12px;color:var(--text-tertiary)">或：<code>aion-qa {url}</code> 一键测试+修复。</p>
    <p style="margin-top:12px"><strong>小改动（Tier 1 快速通道）：</strong></p>
    ${_flow(['直接改代码','commit -y'])}
    <p style="margin-top:6px;font-size:12px;color:var(--text-tertiary)">Tier 1 自动检测微小改动，跳过 review gate，自动提交。</p>

    <h2 id="help-commands">命令速查</h2>
    ${_tbl(['阶段','命令','说明'],[
      ['准备','<code>aion-scan</code>','扫描项目 + 浏览器探索（--url）+ 文档导入（--file）→ 产品设计文档'],
      ['设计','<code>aion-design</code>','挑战假设 + 需求分析 + 方案对比 + spec（--demo 生成原型，--file 导入文档）'],
      ['规划','<code>aion-plan</code>','技术方案 + Scope Challenge + ASCII 图，用户确认后直接执行'],
      ['质量','<code>aion-review</code>','verify + 代码审查 + test gap 一站式（--quick 只跑 verify+review）'],
      ['QA','<code>aion-qa</code>','浏览器 QA 测试 → bug 报告（--report-only 只报告不修复）'],
      ['修复','<code>aion-fix</code>','按角色修复 .aion/bugs/ 中的 bug（-f 前端 / -b 后端 / 指定 ID）'],
      ['提交','<code>aion-commit</code>','Tier 1/2/3 智能分级提交 + changelog（-y 快速提交）'],
      ['流水线','<code>aion-loop</code>','自动化流水线（full: 全流程 / fix: 修复循环 / --auto: 跳过确认）'],
      ['保存','<code>aion-save</code>','保存对话上下文到 .aion/ 和 memory'],
      ['帮助','<code>aion-help</code>','查看所有命令和工作流说明'],
    ])}
    <p style="margin-top:8px;font-size:12px;color:var(--text-tertiary)">所有命令在 Claude Code 中以 <code>/project:aion-xxx</code> 格式调用。</p>

    <h2 id="help-scenarios">常见场景</h2>
    ${_tbl(['场景','操作流程'],[
      ['加新功能','design → plan → [OK→执行] → review → commit'],
      ['修 Bug（测试报告）','qa --report-only {url} → fix → review → commit'],
      ['修 Bug（全自动）','qa {url}（自动测试+修复）→ review → commit'],
      ['小改动','直接改 → commit -y（Tier 1 自动放行）'],
      ['导入外部需求','design --file 需求.docx → 自动提取需求+生成 spec'],
      ['接手旧项目','scan → design/plan → review → commit'],
      ['补充测试','review（自动发现 test gap + 生成测试）'],
      ['全自动流水线','loop full --auto（design → plan → 执行 → review → commit）'],
    ])}

    ${_renderTestingGuide()}

    <h2 id="help-dashboard">副驾驶面板</h2>
    <p>副驾驶是 <strong>CLI 的可视化外壳</strong>。启动：<code>aioncode dashboard</code></p>
    ${_tbl(['视图','用途'],[
      ['概览','项目统计 + 最近变更历史'],
      ['文件','浏览 .aion/ 配置文件（Markdown 渲染）'],
      ['监控','SSE 实时事件流'],
      ['需求','需求规格文档（specs/）'],
      ['方案','实施计划（plans/）'],
      ['规则','项目规则（style / pitfalls / perf）'],
      ['清单','工作流检查清单'],
      ['缺陷','Bug 列表与详情（aion-qa 生成，aion-fix 消费）'],
      ['测试','测试报告（reports/）'],
      ['日志','变更日志（changelog.md）'],
      ['技能','Skill 安装管理 + 官方市场'],
      ['团队','团队成员信息'],
      ['帮助','使用指南（你正在看的这个）'],
      ['关于','产品介绍 + 版本信息'],
      ['设置','深色模式等偏好设置'],
    ])}

    <h2 id="help-faq">常见问题</h2>
    ${[
      ['支持哪些 AI 模型？','命令在 Claude Code 中执行，当前基于 Claude Sonnet/Opus。aion-review 支持多 Agent 并行 review 不同模块。'],
      ['.aion/ 要提交 Git 吗？','建议提交。rules/specs/plans/bugs 是团队共享知识。sessions.jsonl 和 monitor/ 已在 .gitignore 排除。'],
      ['如何升级？','执行 <code>aioncode upgrade</code> 更新工具，再执行 <code>aioncode init</code> 更新项目命令文件（自动清理已移除的旧命令）。'],
      ['review 不通过能提交吗？','不能（Tier 3）。aion-commit 的 Tier 3 需要 review 通过。docs-only 改动自动判定为 Tier 1，可直接提交。'],
      ['design 和 plan 有什么区别？','<code>aion-design</code> 是需求层：挑战假设 + 分析需求 + 方案对比 → spec。<code>aion-plan</code> 是实现层：技术方案 → 用户确认后直接执行代码。'],
      ['init 可以只安装部分命令吗？','可以。<code>aioncode init</code> 交互式安装根据角色（设计师/前端/后端/测试/全栈）推荐命令，你可以自由增减。'],
      ['什么是 Tier 1/2/3 提交？','Tier 1（微小改动）自动放行，Tier 2（小改动）内联轻量审查，Tier 3（大改动/安全路径）需要完整 review 通过。commit -y 强制走 Tier 1。'],
      ['--file 支持哪些格式？','支持 .docx、.pdf、.md、.pptx、.xlsx，通过 markitdown 自动转为 Markdown 后提取需求。'],
      ['aion-qa 和 aion-fix 什么关系？','aion-qa 负责"发现"：浏览器测试 → 生成 .aion/bugs/ 报告。aion-fix 负责"修复"：读 bugs 报告 → 按角色过滤 → 逐个修复 → atomic commit。'],
    ].map(([q,a])=>_faq(q,a)).join('')}
  </div>`;
}
function renderAboutPage() {
  setTimeout(renderAboutToc, 0);
  return `<div class="about">
    <h1>关于 AionCode</h1>
    <p class="subtitle">AI 原生开发智能框架 · 成都奕贝科技</p>

    <h2 id="about-what">什么是 AionCode</h2>
    <p>AionCode 是成都奕贝科技公司开发的一个 <strong>AI 辅助开发的智能框架</strong>。它为你的项目建立一套结构化的知识体系（规则、规格、计划），让 AI（Claude Code）在编码时有据可循。</p>
    <p style="margin-top:8px">核心理念：<strong>知识沉淀 → 规则驱动 → 质量可控</strong></p>
    ${_tbl(['组成','作用'],[
      ['<code>.aion/</code> 目录','项目智能数据：规则、规格、计划、日志、Bug'],
      ['<code>commands/</code>','10 个 AI 工作流命令'],
      ['<code>aioncode</code> CLI','命令行工具：初始化、升级、副驾驶'],
      ['副驾驶面板','Web 可视化界面（你正在看的这个）'],
    ])}
    <p style="margin-top:8px">使用指南请见「帮助」页面 · <a href="https://github.com/user/aioncode/releases" target="_blank">GitHub Releases</a></p>

    <h2 id="about-install">安装与升级</h2>
    <p><strong>安装：</strong>从 <a href="https://github.com/user/aioncode/releases" target="_blank">GitHub Releases</a> 下载对应平台的二进制文件：</p>
    ${_tbl(['平台','文件名','安装命令'],[
      ['macOS (Apple Silicon)','<code>aioncode-macos-arm64</code>','<code>chmod +x aioncode-macos-arm64 && sudo mv aioncode-macos-arm64 /usr/local/bin/aioncode</code>'],
      ['Linux (x64)','<code>aioncode-linux-x64</code>','<code>chmod +x aioncode-linux-x64 && sudo mv aioncode-linux-x64 /usr/local/bin/aioncode</code>'],
      ['Windows (x64)','<code>aioncode-windows-x64.exe</code>','移动到 PATH 目录并重命名为 <code>aioncode.exe</code>'],
    ])}
    <p style="margin-top:8px"><strong>初始化项目：</strong><code>aioncode init</code> — 交互式安装，自动引导选择项目类型 → 角色（设计师/前端/后端/测试/全栈）→ 推荐命令 → 自由增减，按需安装。</p>
    <p><strong>升级：</strong>执行 <code>aioncode upgrade</code> 自动下载最新版，然后在项目中执行 <code>aioncode init</code> 更新命令和模板（自动清理已移除的旧命令文件）。</p>

    <h2 id="about-roadmap">版本路线图</h2>
    <ul>
      <li><strong>v0.5</strong> — FastAPI 重构 + 副驾驶 UI + Core 层统一</li>
      <li><strong>v0.6</strong> — Skills 管理 + 工作流强制化 + init 交互式安装 + 浏览器 QA 测试</li>
      <li><strong>v0.7</strong>（当前）— 命令精简（18→10）+ QA 体系（aion-qa/fix）+ Dashboard 帮助/关于拆分</li>
      <li><strong>v0.8</strong> — 云端 MVP：意图日志管道 + 多项目统计</li>
    </ul>

    ${_renderReleaseLog()}
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
  const models = t.models || [];
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
    <div class="do-section">
      <h3 class="do-title">模型配置 (${models.length} 自定义)</h3>
      ${models.length ? models.map(m => `<div class="do-kv"><span class="do-kv-k">${esc(m.name||'')}</span><span class="do-kv-v">${esc(m.provider||'')} · ${esc(m.default_model||'')}</span></div>`).join('') : '<div class="empty">未配置自定义 Provider — <a href="#" onclick="switchView(\'settings\');return false" style="color:var(--accent-text)">前往设置</a></div>'}
    </div>
    <div class="do-section">
      <h3 class="do-title">风险关键词</h3>
      ${Object.keys(risk).length ? Object.entries(risk).map(([k,v])=>`<div class="do-kv"><span class="do-kv-k">${esc(k)}</span><span class="do-kv-v">${esc(String(v))}</span></div>`).join('') : '<div class="empty">未配置</div>'}
    </div>`;
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

