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
  { id:'testing',   title:'测试人员最佳实践' },
  { id:'dashboard', title:'副驾驶面板' },
  { id:'faq',       title:'常见问题' },
  { id:'roadmap',   title:'版本路线图' },
  { id:'releaselog',title:'更新日志' },
];
function renderAboutToc() {
  document.getElementById('about-toc').innerHTML = ABOUT_SECTIONS.map(s =>
    `<div class="fnode" style="padding-left:4px;cursor:pointer" onclick="scrollAbout('${s.id}')"><span class="ico">§</span>${s.title}</div>`).join('');
}
function scrollAbout(id) {
  const el = document.getElementById('about-' + id);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
function _tbl(h,r){return `<table class="key-table"><tr>${h.map(x=>'<th>'+x+'</th>').join('')}</tr>${r.map(x=>'<tr>'+x.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')}</table>`}
function _flow(s){return `<div class="flow">${s.map(x=>`<span class="flow-step">${x}</span>`).join('<span class="flow-arrow">→</span>')}</div>`}
function _faq(q,a){return `<p><strong>Q：${q}</strong></p><p>${a}</p>`}
/** 测试人员最佳实践板块 */
function _renderTestingGuide() {
  return `
    <h2 id="about-testing">测试人员最佳实践</h2>
    <p>本章是写给<strong>测试人员（QA）</strong>的完整指南。你不需要写代码——只需用自然语言描述测试场景，AionCode 会帮你生成、执行、修复测试。</p>

    <h3>一、你的角色定位</h3>
    <p>在 AionCode 体系中，测试人员的核心职责从"手写脚本"转变为<strong>设计测试策略 + 编写测试剧本 + 审查 AI 输出</strong>。</p>
    ${_tbl(['传统模式','AionCode 模式'],[
      ['手写 Selenium/Playwright 脚本','用中文 Markdown 描述测试用例，AI 生成脚本'],
      ['手动维护选择器','AI 自动适应 UI 变化，选择器失效时自动修复'],
      ['测试失败后手动排查','<code>--heal</code> 自愈模式自动诊断并修复'],
      ['覆盖率靠人肉检查','<code>coverage</code> 模式自动分析缺口并补充测试'],
      ['测试报告手写','自动生成结构化报告到 <code>.aion/tests/reports/</code>']
    ])}

    <h3>二、完整测试流程</h3>
    <p>以下是测试人员参与一个完整项目的推荐流程：</p>
    ${_flow(['运行 aion-test e2e','审核生成的用例','再次运行执行测试','查看报告','反馈 Bug'])}
    <p style="margin-top:12px"><strong>详细步骤：</strong></p>
    <ol>
      <li><strong>运行 E2E 测试命令</strong>：在 Claude Code 终端输入 <code>/project:aion-test e2e</code>。你有多种方式指定测试目标：
        ${_tbl(['输入方式','示例','说明'],[
          ['不填（推荐）','<code>aion-test e2e</code>','列出所有可用 spec，交互式选择'],
          ['中文描述','<code>aion-test e2e "登录功能"</code>','AI 模糊匹配最相关的 spec'],
          ['spec 文件名','<code>aion-test e2e github-token-auth</code>','精确匹配'],
          ['模块路径','<code>aion-test e2e src/auth/</code>','从代码反查关联 spec']
        ])}
        <p style="margin-top:4px">选定目标后，AI 自动完成：</p>
        <ul style="margin:4px 0 4px 16px">
          <li><strong>实地勘察</strong>：通过 Playwright MCP 浏览系统界面，记录页面、元素、状态</li>
          <li><strong>多源分析</strong>：从 spec（验收标准）+ 源码（错误路径）+ 勘察结果（UI 细节）+ API 契约 + Bug 历史自动生成测试用例</li>
          <li>输出到 <code>.aion/tests/e2e/{feature}.md</code>，每个用例标注来源</li>
        </ul>
      </li>
      <li><strong>审核测试用例</strong>：打开生成的 <code>.md</code> 文件，检查是否覆盖了你关心的场景，补充额外的边界 case。</li>
      <li><strong>执行测试</strong>：再次运行 <code>/project:aion-test e2e {feature}</code>，AI 检测到用例已存在，直接执行。也可以用 <code>--now</code> 跳过审核直接执行。</li>
      <li><strong>查看报告</strong>：打开副驾驶「测试」视图，或读 <code>.aion/tests/reports/{feature}-e2e.md</code>。</li>
      <li><strong>提交 Bug</strong>：发现问题后运行 <code>/project:aion-bug</code>，AI 自动生成格式化的 Bug 报告。</li>
    </ol>
    <p style="margin-top:8px;color:var(--fg-muted)">注意：测试人员<strong>不需要手写测试用例</strong>。AI 从多个信息源自动生成，你只需审核和补充。</p>

    <h3>三、编写自然语言测试用例</h3>
    <p>测试用例存放在 <code>.aion/tests/e2e/</code> 目录，每个功能一个 <code>.md</code> 文件。</p>
    <p><strong>文件结构：</strong></p>
    <pre style="background:var(--bg-sidebar);padding:12px;border-radius:6px;font-size:12px;line-height:1.6;overflow-x:auto">---
feature: 功能名称
target_url: http://localhost:19200
viewport: [desktop, mobile]
preconditions:
  - 用户已登录
---

# E2E: 功能名称

## TC-001: 测试标题

**Given**: 前置状态描述
**When**: 操作步骤1 → 操作步骤2 → 操作步骤3
**Then**:
  - 预期结果1
  - 预期结果2

**Edge Cases**:
  - 边界场景1
  - 边界场景2</pre>
    <p style="margin-top:8px"><strong>关键语法：</strong></p>
    ${_tbl(['元素','格式','说明'],[
      ['Given','单行','前置状态，用"在XX页"描述当前位置'],
      ['When','用 → 分隔步骤','每个 → 是一个用户操作'],
      ['Then','缩进列表','每项必须是<strong>可验证</strong>的断言'],
      ['Edge Cases','缩进列表','边界场景：空值、超长、特殊字符、网络异常']
    ])}
    <p style="margin-top:8px"><strong>常用操作关键词：</strong></p>
    ${_tbl(['你写的','AI 理解为'],[
      ['点击"保存"','点击包含"保存"文本的按钮'],
      ['输入"测试"到名称字段','在"名称"输入框中填写"测试"'],
      ['访问 http://localhost:19200','在浏览器中打开该 URL'],
      ['等待列表加载完成','等待列表元素出现在页面上'],
      ['确认删除','点击确认按钮'],
      ['切换到移动端视口','将浏览器窗口调整为 375×667']
    ])}
    <p style="margin-top:8px;color:var(--fg-muted)">提示：你不需要记忆关键词，直接用自然语言描述操作即可。AI 会根据语义推断对应的浏览器操作。</p>

    <h3>四、测试模式一览</h3>
    <p>AionCode 的 <code>aion-test</code> 命令提供多种模式，覆盖从单元测试到 E2E 的完整测试需求：</p>
    ${_tbl(['命令','适用场景','谁来用'],[
      ['<code>aion-test</code>','为最近实现的代码自动生成单元/集成测试','开发者 / QA'],
      ['<code>aion-test coverage</code>','分析测试覆盖率缺口，自动补充测试','QA'],
      ['<code>aion-test e2e</code>','智能匹配目标（中文/spec名/模块路径/交互选择）→ 勘察 → 多源生成 → 执行','<strong>QA 首选</strong>'],
      ['<code>aion-test e2e --heal</code>','E2E 测试 + 失败自动修复','QA'],
      ['<code>aion-test perf</code>','生成性能/负载测试脚本（k6/locust）','QA / 性能测试'],
      ['<code>aion-test ui</code>','UI 测试清单 + 可访问性审计','QA / 前端'],
      ['<code>aion-test pipeline</code>','多代理测试管道（5 阶段全自动）','复杂功能'],
      ['<code>aion-test full</code>','依次执行所有模式','发布前全量测试']
    ])}

    <h3>五、E2E 测试的两种运行模式</h3>
    <p>当你运行 <code>/project:aion-test e2e</code> 时，系统会自动检测环境并选择模式：</p>
    ${_tbl(['模式','条件','行为'],[
      ['<strong>e2e-live</strong>','已安装 Playwright MCP','<strong>真实浏览器执行</strong>：AI 控制浏览器点击、输入、截图，实时验证每个 TC'],
      ['<strong>e2e-gen</strong>','未安装 Playwright MCP','<strong>生成脚本</strong>：输出 Playwright 测试代码，需手动运行或交给开发者']
    ])}
    <p style="margin-top:8px"><strong>推荐：安装 Playwright MCP 以启用 live 模式</strong>（效果最佳）：</p>
    <pre style="background:var(--bg-sidebar);padding:8px 12px;border-radius:6px;font-size:12px">npx @anthropic-ai/playwright-mcp</pre>
    <p style="margin-top:4px">然后在 Claude Code 设置中添加 MCP server 配置即可。</p>

    <h3>六、自愈能力（--heal）</h3>
    <p>这是 AionCode 测试体系的核心差异化能力。当测试失败时，<code>--heal</code> 不会只报错，而是<strong>自动诊断根因并修复</strong>。</p>
    <p><strong>工作原理：</strong></p>
    <ol>
      <li>运行测试，捕获失败日志（Traceback）</li>
      <li>对比 <code>.aion/specs/</code> 中的验收标准，判断"是代码写错了"还是"测试用例过期了"</li>
      <li>自动应用修复补丁（修代码或修测试）</li>
      <li>重新运行，最多循环 3 轮</li>
    </ol>
    <p style="margin-top:8px"><strong>诊断决策表：</strong></p>
    ${_tbl(['失败信号','AI 判断','自动动作'],[
      ['断言失败 + spec 有对应标准','代码没满足需求','修复源代码 <code>[CODE_FIX]</code>'],
      ['导入错误（模块改名）','代码重构后测试过期','更新测试引用 <code>[TEST_FIX]</code>'],
      ['导入错误（依赖未安装）','环境问题','停止自愈，提示安装 <code>[ENV_ISSUE]</code>'],
      ['连接超时/拒绝','服务未启动','停止自愈，报告 <code>[ENV_ISSUE]</code>'],
      ['选择器失效（E2E）','UI 变更了','更新选择器 <code>[TEST_FIX]</code>'],
      ['无 spec + 失败原因不明','无法判断谁对','标记 <code>[NEEDS_HUMAN]</code>，等待人工']
    ])}
    <p style="margin-top:8px"><strong>安全护栏：</strong>最多 3 轮修复 · 每轮最多改 3 个文件 · 无进展立即停止 · 修复源代码前必须确认 spec 支持</p>

    <h3>七、多代理测试管道（pipeline）</h3>
    <p>对于复杂功能（5+ 用户流程），使用 <code>/project:aion-test pipeline</code> 启动全自动 5 阶段管道：</p>
    ${_flow(['分析师','规划师','工程师','哨兵','治疗师'])}
    ${_tbl(['阶段','代理','职责'],[
      ['Stage 1','分析师','从 spec 和源码中提取所有测试点、用户流程、边界 case'],
      ['Stage 2','规划师','按 P0/P1/P2 优先级编排测试计划'],
      ['Stage 3','工程师','编写测试代码（遵循项目约定）'],
      ['Stage 4','哨兵','<strong>质量门禁</strong>：审计测试质量，有权阻止（BLOCK）管道'],
      ['Stage 5','治疗师','运行测试并自动修复失败（复用 --heal 逻辑）']
    ])}
    <p style="margin-top:8px">管道产物保存在 <code>.aion/tests/pipeline/{feature}/</code>，每阶段一个报告文件。</p>

    <h3>八、验证与修复（verify --fix）</h3>
    <p>测试完成后，运行 <code>/project:aion-verify --fix</code> 做全面检查并<strong>自动修复</strong>：</p>
    ${_tbl(['检查项','默认行为','--fix 行为'],[
      ['Build','报告 PASS/FAIL','失败时分析错误并尝试修复'],
      ['Lint','报告警告和错误','自动运行 <code>ruff --fix</code> 等工具修复'],
      ['Tests','报告通过/失败','触发自愈循环（同 --heal）'],
      ['Debug','检测调试语句','仅报告（不自动删除）']
    ])}
    <p style="margin-top:8px">默认的 <code>aion-verify</code>（不带 --fix）只报告不修复，适合最终确认。</p>

    <h3>九、测试报告</h3>
    <p>所有测试报告自动生成到 <code>.aion/tests/reports/</code>，可在副驾驶的「测试」视图中查看。</p>
    <p><strong>报告内容包括：</strong></p>
    <ul>
      <li>生成的测试数量（单元/集成/E2E）和文件列表</li>
      <li>覆盖率变化（before → after）</li>
      <li>E2E 测试结果（每个 TC 的 PASS/FAIL + 截图路径）</li>
      <li>自愈日志（每轮修复了什么、改了哪些文件）</li>
      <li>未解决问题（<code>[NEEDS_HUMAN]</code> 标记的项需人工处理）</li>
    </ul>

    <h3>十、与开发者协作</h3>
    <p>测试人员和开发者在 AionCode 中的协作模式：</p>
    ${_tbl(['测试人员做','开发者做'],[
      ['在 <code>.aion/specs/</code> 中确认验收标准','编写需求规格（aion-design / --file 导入）'],
      ['审核 AI 生成的 E2E 用例，补充边界 case','实现功能代码（aion-impl）'],
      ['运行 <code>aion-test e2e</code> 执行测试','运行 <code>aion-test</code> 生成单元测试'],
      ['发现问题用 <code>aion-bug</code> 提 Bug','通过 <code>aion-impl {BUG-ID}</code> 修复'],
      ['用 <code>aion-verify</code> 做最终验收','用 <code>aion-review</code> + <code>aion-commit</code> 提交']
    ])}
    <p style="margin-top:12px"><strong>推荐协作流程：</strong></p>
    ${_flow(['QA 写 E2E 用例','开发实现功能','QA 运行 e2e','提 Bug','开发修复','QA 回归验证'])}

    <h3>十一、快速上手检查清单</h3>
    <p>如果你是第一次使用 AionCode 做测试，按这个顺序操作：</p>
    <ol>
      <li>✅ 确认项目已执行 <code>aioncode init</code>（<code>.aion/</code> 目录存在）</li>
      <li>✅ 阅读 <code>.aion/tests/e2e/README.md</code> 了解用例格式</li>
      <li>✅ 参考 <code>.aion/tests/e2e/_example.md</code> 编写你的第一个测试文件</li>
      <li>✅ 在 Claude Code 终端运行 <code>/project:aion-test e2e</code></li>
      <li>✅ 查看 <code>.aion/tests/reports/</code> 下的测试报告</li>
      <li>✅（可选）安装 Playwright MCP 启用 live 模式获得最佳体验</li>
      <li>✅（可选）运行 <code>/project:aion-test e2e --heal</code> 体验自愈能力</li>
    </ol>
  `;
}
/** 更新日志板块 */
function _renderReleaseLog() {
  return `
    <h2 id="about-releaselog">更新日志</h2>

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
function renderAboutPage() {
  setTimeout(renderAboutToc, 0);
  const cmds = [
    ['准备','<code>aion-scan</code>','扫描项目 + 浏览器探索（--url）+ 导入文档（--file）→ 生成产品设计文档'],
    ['','<code>aion-think</code>','质疑假设，在开始前暴露盲点'],
    ['','<code>aion-help</code>','查看所有命令和工作流说明'],
    ['设计','<code>aion-design</code>','需求分析 + 导入外部文档（--file .docx/.pdf）→ 生成 spec + 更新产品文档'],
    ['','<code>aion-demo</code>','生成交互式 HTML 原型（可选）'],
    ['','<code>aion-plan</code>','创建分步实施计划 → 自动传播模块/技术栈变更到产品文档'],
    ['实施','<code>aion-impl</code>','按计划编写代码（自动遵守规则）'],
    ['','<code>aion-test</code>','生成测试 + E2E 三阶段（勘察→多源生成→执行）+ 自愈（--heal）+ 多代理管道（pipeline）'],
    ['质量','<code>aion-verify</code>','运行构建/测试/lint 检查 + 自动修复（--fix）'],
    ['','<code>aion-review</code>','代码审查 + 自动提取规则'],
    ['管理','<code>aion-commit</code>','安全提交（需 review 通过）'],
    ['','<code>aion-save</code>','保存对话上下文到 .aion/ 和 memory'],
    ['','<code>aion-bug</code>','Bug 管理：报告/列表/分配/关闭'],
    ['','<code>aion-crosscheck</code>','用其他 AI 模型交叉验证代码'],
    ['运维','<code>aion-loop</code>','自动化流水线（设计→实现→验证→审查→提交）'],
    ['','<code>aion-status</code>','项目状态总览'],['','<code>aion-upgrade</code>','版本升级'],['','<code>aion-learn</code>','从审查中提取规则'],
  ];
  return `<div class="about">
    <h1>AionCode 使用指南</h1>
    <p class="subtitle">AI 原生开发智能框架 · 让 AI 编程有章可循</p>
    <h2 id="about-what">什么是 AionCode</h2>
    <p>AionCode 是成都奕贝科技公司开发的一个 <strong>AI 辅助开发的智能框架</strong>。它为你的项目建立一套结构化的知识体系（规则、规格、计划），让 AI（Claude Code）在编码时有据可循。</p>
    <p style="margin-top:8px">核心理念：<strong>知识沉淀 → 规则驱动 → 质量可控</strong></p>
    ${_tbl(['组成','作用'],[['<code>.aion/</code> 目录','项目智能数据：规则、规格、计划、日志、Bug'],['<code>commands/</code>','18 个 AI 工作流命令'],['<code>aioncode</code> CLI','命令行工具：初始化、升级、副驾驶'],['副驾驶面板','Web 可视化界面（你正在看的这个）']])}
    <h2 id="about-install">安装与升级</h2>
    <p><strong>安装：</strong>从 <a href="https://github.com/user/aioncode/releases" target="_blank">GitHub Releases</a> 下载对应平台的二进制文件：</p>
    ${_tbl(['平台','文件名','安装命令'],[['macOS (Apple Silicon)','<code>aioncode-macos-arm64</code>','<code>chmod +x aioncode-macos-arm64 && sudo mv aioncode-macos-arm64 /usr/local/bin/aioncode</code>'],['Linux (x64)','<code>aioncode-linux-x64</code>','<code>chmod +x aioncode-linux-x64 && sudo mv aioncode-linux-x64 /usr/local/bin/aioncode</code>'],['Windows (x64)','<code>aioncode-windows-x64.exe</code>','移动到 PATH 目录并重命名为 <code>aioncode.exe</code>']])}
    <p style="margin-top:8px"><strong>初始化项目：</strong><code>aioncode init</code>，然后（可选）<code>/project:aion-scan</code> 自动提取规则。</p>
    <p><strong>升级：</strong>执行 <code>aioncode upgrade</code> 自动下载最新版，然后在项目中执行 <code>aioncode init</code> 更新命令和模板。</p>
    <h2 id="about-workflow">工作流指南</h2>
    <p><strong>新项目：</strong></p>${_flow(['think','design','plan','impl','verify','review','commit'])}
    <p style="margin-top:12px"><strong>已有项目：</strong></p>${_flow(['scan','impl/design','verify','review','commit'])}
    <p style="margin-top:12px"><strong>Bug 修复：</strong></p>${_flow(['bug report','impl {BUG-ID}','verify','review','commit'])}
    <p style="margin-top:8px">所有命令在 Claude Code 终端中以 <code>/project:aion-xxx</code> 格式调用。</p>
    <h2 id="about-commands">命令速查</h2>
    <table class="key-table"><tr><th>阶段</th><th>命令</th><th>说明</th></tr>${cmds.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')}</table>
    <h2 id="about-scenarios">常见场景</h2>
    ${_tbl(['场景','操作流程'],[['加新功能','design → plan → impl → verify → review → commit'],['修 Bug','bug report → impl {BUG-ID} → verify → commit'],['E2E 测试','aion-test e2e → 自动勘察+多源生成用例 → 审核 → 执行'],['导入外部需求','aion-design --file 需求.docx → 自动提取需求生成 spec'],['接手旧项目','aion-scan --url http://localhost:3000 → 浏览器探索+代码扫描 → 产品设计文档'],['交叉验证','crosscheck --model gemini → 自动生成 Bug 报告']])}
    ${_renderTestingGuide()}
    <h2 id="about-dashboard">副驾驶面板</h2>
    <p>副驾驶是 <strong>CLI 的可视化外壳</strong>。启动：<code>aioncode dashboard</code></p>
    ${_tbl(['视图','用途'],[['概览','项目统计 + 最近变更历史'],['文件','浏览 .aion/ 配置文件（Markdown 渲染）'],['监控','SSE 实时事件流'],['需求','需求规格文档（specs/）'],['方案','实施计划（plans/）'],['规则','项目规则（style / pitfalls / perf）'],['清单','工作流检查清单'],['缺陷','Bug 列表与详情'],['测试','测试报告（reports/）'],['日志','变更日志（changelog.md）'],['技能','Skill 安装管理 + 官方市场'],['团队','团队成员信息'],['关于','使用指南（你正在看的这个）'],['设置','深色模式等偏好设置']])}
    <h2 id="about-faq">常见问题</h2>
    ${[['支持哪些 AI 模型？','命令在 Claude Code 中执行。crosscheck 可调用 Gemini 等做交叉验证。'],['.aion/ 要提交 Git 吗？','建议提交。rules/specs/plans 是团队共享知识。sessions.jsonl 和 monitor/ 已排除。'],['如何升级？','执行 <code>aioncode upgrade</code> 自动更新工具，再执行 <code>aioncode init</code> 更新项目命令。'],['review 不通过能提交吗？','不能。aion-commit 要求 review 通过（docs-only 可豁免）。'],['测试人员需要会写代码吗？','不需要。E2E 测试用例由 AI 从多源（spec + 源码 + UI 勘察）自动生成，测试人员只需审核和补充边界 case。'],['什么是产品设计文档（_product.md）？','位于 <code>.aion/specs/_product.md</code>，是项目的全局产品全景（目标用户、功能地图、模块架构）。由 aion-scan 或 aion-design 自动生成和维护。'],['--file 支持哪些文件格式？','支持 .docx、.pdf、.md、.pptx、.xlsx。通过 markitdown 工具自动转换为 Markdown 后提取内容。'],['E2E 测试一定需要 Playwright MCP 吗？','不一定。没有 MCP 时自动降级为 gen 模式（生成 Playwright 脚本），有 MCP 时使用 live 模式（真实浏览器执行）。']].map(([q,a])=>_faq(q,a)).join('')}
    <h2 id="about-roadmap">版本路线图</h2>
    <ul>
      <li><strong>v0.5</strong> — FastAPI 重构 + 副驾驶 UI + Core 层统一</li>
      <li><strong>v0.6</strong>（当前）— Skills 管理 + 工作流强制化 + 测试体系升级（自愈/E2E/多代理管道）+ 产品设计层（_product.md）+ 外部文档导入（--file）</li>
      <li><strong>v0.7</strong> — 云端 MVP：意图日志管道 + 多项目统计</li>
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
