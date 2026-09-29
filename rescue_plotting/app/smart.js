/* 智能标图：一句话 → 大模型解析为结构化指令 → 程序计算坐标 → 预览 → 确认写入。
 *
 * 大模型只负责“选符号、定参照、给方位距离”，坐标一律由本程序按参照物计算，
 * 避免模型编造经纬度。接口为 OpenAI 兼容 chat/completions：
 *   - 代理模式：页面由 server.py 提供，请求发到 /api/llm/chat（推荐，Key 不进浏览器）；
 *   - 直连模式：浏览器直接请求模型服务（需模型服务允许跨域）。
 */
(function () {
  'use strict';
  const app = window.plotApp;
  const { map, SYM, LIB } = app;
  const { escapeXml } = window.PLOT_STYLES;
  const $ = id => document.getElementById(id);
  const CFG_KEY = 'rescue-plot-llm';

  // ---------------------------------------------------------------- 配置

  const cfg = Object.assign({ mode: 'proxy', url: 'http://127.0.0.1:11434/v1', model: '', key: '' }, loadCfg());
  function loadCfg() { try { return JSON.parse(localStorage.getItem(CFG_KEY) || '{}'); } catch (e) { return {}; } }
  function saveCfg() { try { localStorage.setItem(CFG_KEY, JSON.stringify(cfg)); } catch (e) { /* 忽略 */ } }

  let proxyInfo = null;
  async function detectProxy() {
    if (!location.protocol.startsWith('http')) return null;
    try {
      const r = await fetch('/api/llm/config');
      if (r.ok) return await r.json();
    } catch (e) { /* 非 server.py 提供的页面 */ }
    return null;
  }

  async function chat(messages) {
    if (cfg.mode === 'proxy') {
      const r = await fetch('/api/llm/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages, temperature: 0.1 }),
      });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error((d.error || `HTTP ${r.status}`) + (d.detail ? `：${d.detail}` : ''));
      return d.content;
    }
    const headers = { 'Content-Type': 'application/json' };
    if (cfg.key) headers.Authorization = 'Bearer ' + cfg.key;
    const r = await fetch(cfg.url.replace(/\/$/, '') + '/chat/completions', {
      method: 'POST', headers, body: JSON.stringify({ model: cfg.model, messages, temperature: 0.1 }),
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}：${(await r.text()).slice(0, 300)}`);
    const d = await r.json();
    return d.choices[0].message.content;
  }

  // ---------------------------------------------------------------- 本地坐标（米，东为 x、北为 y，原点为视图中心）

  let origin = map.getCenter();
  const M_LAT = 110540;
  const mLng = lat => 111320 * Math.cos(lat * Math.PI / 180);
  const toXY = ll => [Math.round((ll[1] - origin.lng) * mLng(origin.lat)), Math.round((ll[0] - origin.lat) * M_LAT)];
  const toLL = ([x, y]) => [origin.lat + y / M_LAT, origin.lng + x / mLng(origin.lat)];
  const centroid = cs => [cs.reduce((s, c) => s + c[0], 0) / cs.length, cs.reduce((s, c) => s + c[1], 0) / cs.length];

  const DIRS = { 北: 0, 东北: 45, 北东: 45, 东: 90, 东南: 135, 南东: 135, 南: 180, 西南: 225, 南西: 225, 西: 270, 西北: 315, 北西: 315 };
  function bearing(dir) {
    if (dir == null || dir === '') return null;
    if (typeof dir === 'number') return dir;
    const s = String(dir).replace(/[偏方向侧面边]/g, '');
    if (s in DIRS) return DIRS[s];
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : NaN;
  }

  // ---------------------------------------------------------------- 参照物

  let refPoints = [];          // 用户放置的参考点 P1、P2…
  const refLayer = L.layerGroup().addTo(map);
  let anchors = {};            // 'F3' / 'P1' / 'O' → {ll, name, feature?}

  function featName(f) {
    const s = SYM[f.sym];
    const p = f.props || {};
    const base = s.glyph_path ? (p.label || s.name) : s.name;
    return p.note && p.note !== base ? `${p.note}·${base}` : base;
  }

  function buildAnchors() {
    origin = map.getCenter();
    anchors = { O: { ll: [origin.lat, origin.lng], name: '当前视图中心' } };
    app.features.forEach((f, i) => {
      anchors['F' + (i + 1)] = { ll: f.type === 'point' ? f.coords[0] : centroid(f.coords), name: featName(f), feature: f };
    });
    refPoints.forEach((p, i) => { anchors['P' + (i + 1)] = { ll: p, name: '参考点' }; });
    return anchors;
  }

  function anchorTable() {
    const geo = { point: '点', line: '线', polygon: '面' };
    return Object.entries(anchors).map(([k, a]) => {
      const f = a.feature;
      let extra = '';
      if (f && f.type === 'line') extra = ` 起点${JSON.stringify(toXY(f.coords[0]))} 终点${JSON.stringify(toXY(f.coords[f.coords.length - 1]))}`;
      if (f && f.type === 'polygon') {
        const xs = f.coords.map(toXY);
        const r = Math.round(Math.max(...xs.map(([x, y]) => Math.hypot(x - toXY(a.ll)[0], y - toXY(a.ll)[1]))));
        extra = ` 半径约${r}米`;
      }
      if (!f) return `${k} | 名称:${a.name} | 参考点 | 位置${JSON.stringify(toXY(a.ll))}`;
      const s = SYM[f.sym];
      const nm = s.glyph_path ? (f.props.label || s.name) : s.name;
      return `${k} | 名称:${nm} | 注记:${f.props.note || '无'} | ${geo[f.type]} ${f.sym} | 位置${JSON.stringify(toXY(a.ll))}${extra}` +
        (f.props.count ? ` | 人数:${f.props.count}` : '');
    }).join('\n');
  }

  function catalog() {
    const geo = { point: '点', line: '线', polygon: '面' };
    const skip = new Set(['building']);
    return LIB.symbols.filter(s => !skip.has(s.category))
      .map(s => `${s.id} ${s.name}[${geo[s.geometry]}]`).join('\n');
  }

  // ---------------------------------------------------------------- 提示词

  function systemPrompt() {
    return `你是抢险救援标图助手。把指挥员的口述指令转换为标图操作，只输出一个 JSON 对象，不要输出其他文字。

## 坐标约定
以米为单位的平面坐标：x 向东为正，y 向北为正，原点 O 为当前视图中心。

## 位置写法（<位置>）
- {"ref":"F3"}：就在参照物 F3 处（面、线取其中心）
- {"ref":"F3","dir":"西","dist":200}：F3 的西方 200 米。dir 取 北/东北/东/东南/南/西南/西/西北，或方位角数字（正北为 0，顺时针）；“北偏东30度”写 30，“南偏西20度”写 200，只说“北偏东”未给度数按 30
- {"ref":"F12.start"} / {"ref":"F12.end"}：线要素 F12 的起点 / 终点
- {"xy":[x,y]}：直接给平面坐标
- 线的 path 中可写 {"along":"F12"}，表示沿 F12 这条线走（展开为其全部节点）

## 操作
{"actions":[
  {"op":"add","symbol":"符号id","geometry":"point","at":<位置>,"note":"注记，如番号/单位","count":人数,"label":"国标符号的标识文字(可选)","heading":"东(可选，表示朝向，用于进攻方向、车辆等)","time":"可选，格式2026.09.29.0630"},
  {"op":"add","symbol":"符号id","geometry":"line","path":[<位置>,<位置>,...],"note":"可选"},
  {"op":"add","symbol":"符号id","geometry":"polygon","center":<位置>,"radius":半径米,"note":"可选"},
  {"op":"add","symbol":"符号id","geometry":"polygon","ring":[<位置>,<位置>,<位置>,...],"note":"可选"},
  {"op":"update","target":"F5","note":"新注记","count":新人数,"label":"新标识文字"},
  {"op":"move","target":"F5","at":<位置>},
  {"op":"delete","target":"F5"}
],
"questions":["指令中无法确定、需要指挥员补充的内容"]}

## 规则
1. symbol 必须从下方“符号目录”中原样选取，geometry 必须与目录中的[点/线/面]一致。
2. 参照物优先按名称匹配下方“参照物”列表（如“堆积区”“前指”“县道”）。找不到参照物或方位距离不明时，不要猜，写入 questions。
3. 没说距离时：“附近/旁边”按 100 米，“一侧”按 200 米。
4. 行动路线从出发位置画到目标位置；“向X搜救/推进”用 XF-6.3.18 进攻方向（heading 为推进方向）或 XF-6.3.17 预计行动路线。
5. 被困人员用 XF-6.3.22，失联用 X-A01，并填 count。
6. 已有要素的人数、状态变化用 update，不要重复新增；若原注记里写有人数等数值，update 时同时给出改写后的 note。
7. 泥石流、滑坡等灾情优先用 GB- 开头的预设符号（如 GB-A10400-泥石流）。
8. “派/调/转移”图上已有的力量或装备到某处，用 move 移动该要素，不要新增，也不要只改注记。
9. note 只写注记内容本身（番号、单位、状态、人数），不要带上符号名称；label 只用于 GB- 开头的点符号。

## 符号目录
${catalog()}`;
  }

  function userPrompt(text) {
    return `## 参照物（当前图上）\n${anchorTable()}\n\n## 指令\n${text}`;
  }

  // ---------------------------------------------------------------- 解析与坐标计算

  function extractJson(text) {
    let t = String(text).replace(/<think>[\s\S]*?<\/think>/g, '').trim();
    const fence = t.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (fence) t = fence[1];
    const a = t.indexOf('{'), b = t.lastIndexOf('}');
    if (a < 0 || b < a) throw new Error('模型没有返回 JSON');
    return JSON.parse(t.slice(a, b + 1));
  }

  function resolvePos(pos) {
    if (!pos || typeof pos !== 'object') throw new Error('位置为空');
    if (Array.isArray(pos.xy)) return toLL(pos.xy.map(Number));
    let ref = String(pos.ref || '').trim();
    let which = null;
    const m = ref.match(/^(\w+?)\.(start|end)$/);
    if (m) { ref = m[1]; which = m[2]; }
    const a = anchors[ref];
    if (!a) throw new Error(`找不到参照物 ${ref || '（未指定）'}`);
    let ll = a.ll;
    if (which) {
      if (!a.feature || a.feature.type !== 'line') throw new Error(`${ref} 不是线，不能取${which === 'start' ? '起点' : '终点'}`);
      ll = which === 'start' ? a.feature.coords[0] : a.feature.coords[a.feature.coords.length - 1];
    }
    const dist = Number(pos.dist || 0);
    if (dist) {
      const br = bearing(pos.dir);
      if (br == null || Number.isNaN(br)) throw new Error(`方位“${pos.dir}”无法识别`);
      if (dist > 50000) throw new Error(`距离 ${dist} 米过大`);
      const [x, y] = toXY(ll);
      const r = br * Math.PI / 180;
      ll = toLL([x + dist * Math.sin(r), y + dist * Math.cos(r)]);
    }
    return ll;
  }

  function resolvePath(list) {
    const out = [];
    (list || []).forEach(p => {
      if (p && p.along) {
        const a = anchors[String(p.along)];
        if (!a || !a.feature || a.feature.type !== 'line') throw new Error(`along 引用的 ${p.along} 不是线`);
        out.push(...a.feature.coords);
      } else out.push(resolvePos(p));
    });
    return out;
  }

  function circle(centerLL, radius, n = 16) {
    const [cx, cy] = toXY(centerLL);
    return Array.from({ length: n }, (_, i) => {
      const t = 2 * Math.PI * i / n;
      return toLL([cx + radius * Math.sin(t), cy + radius * Math.cos(t)]);
    });
  }

  const NAME_OP = { add: '新增', update: '修改', delete: '删除', move: '移动' };

  function plan(action) {
    const op = action.op || 'add';
    if (op === 'move') {
      const a = anchors[String(action.target)];
      if (!a || !a.feature) throw new Error(`找不到要移动的要素 ${action.target}`);
      if (a.feature.type !== 'point') throw new Error(`${action.target} 不是点，暂不支持移动线、面`);
      const ll = resolvePos(action.at || action.position);
      return { op, target: a.feature, coords: [ll], text: `移动 ${action.target}「${a.name}」到 ${describePos(action.at || action.position)}` };
    }
    if (op === 'update' || op === 'delete') {
      const a = anchors[String(action.target)];
      if (!a || !a.feature) throw new Error(`找不到要${NAME_OP[op]}的要素 ${action.target}`);
      const props = {};
      const canLabel = !!SYM[a.feature.sym].glyph_path;
      ['note', 'count', 'label', 'time'].forEach(k => {
        if (action[k] === undefined || action[k] === null || (k === 'label' && !canLabel)) return;
        props[k] = k === 'count' ? Number(action[k]) : String(action[k]);
      });
      if (op === 'update' && !Object.keys(props).length) throw new Error(`对 ${action.target} 的修改没有有效内容`);
      return { op, target: a.feature, props, text: `${NAME_OP[op]} ${action.target}「${a.name}」` + (op === 'update' ? ' → ' + JSON.stringify(props) : '') };
    }
    const s = SYM[action.symbol];
    if (!s) throw new Error(`符号 ${action.symbol} 不在符号库中`);
    const geom = s.geometry;
    let coords;
    if (geom === 'point') coords = [resolvePos(action.at || action.position)];
    else if (geom === 'line') {
      coords = resolvePath(action.path);
      if (coords.length < 2) throw new Error('线至少需要 2 个点');
    } else {
      if (action.ring) coords = resolvePath(action.ring);
      else coords = circle(resolvePos(action.center), Math.min(Math.max(Number(action.radius) || 100, 10), 20000));
      if (coords.length < 3) throw new Error('面至少需要 3 个点');
    }
    const props = {};
    if (action.note) props.note = String(action.note);
    if (action.count) props.count = Number(action.count);
    if (action.time) props.time = String(action.time);
    if (action.label && s.glyph_path) props.label = String(action.label);
    const hd = bearing(action.heading);
    if (hd != null && !Number.isNaN(hd) && geom === 'point') props.rotation = Math.round(hd - 90);  // 符号默认朝东
    const where = geom === 'point' ? describePos(action.at || action.position) : geom === 'line' ? `${coords.length} 个点` : action.ring ? `${coords.length} 边形` : `半径 ${action.radius || 100} 米`;
    return { op: 'add', sym: s.id, type: geom, coords, props, text: `新增「${s.name}」${props.note ? '（' + props.note + '）' : ''} ${where}` };
  }

  function describePos(p) {
    if (!p) return '';
    if (p.xy) return `坐标 ${JSON.stringify(p.xy)}`;
    const a = anchors[String(p.ref).split('.')[0]];
    const nm = a ? `${p.ref}「${a.name}」` : p.ref;
    const d = typeof p.dir === 'number' || /^\d/.test(String(p.dir)) ? `方位${p.dir}°` : p.dir;
    return p.dist ? `${nm} ${d} ${p.dist} 米` : `位于 ${nm}`;
  }

  // ---------------------------------------------------------------- 预览与写入

  const previewLayer = L.layerGroup().addTo(map);
  let pending = [];

  function showPreview(items, questions, raw) {
    previewLayer.clearLayers();
    items.filter(it => it.ok && it.p.op === 'add').forEach(it => {
      const { type, coords } = it.p;
      const st = { color: '#1565c0', weight: 3, dashArray: '6,5', fillOpacity: 0.1, interactive: false };
      if (type === 'point') L.circleMarker(coords[0], { ...st, radius: 14 }).addTo(previewLayer);
      else if (type === 'line') L.polyline(coords, st).addTo(previewLayer);
      else L.polygon(coords, st).addTo(previewLayer);
    });
    items.filter(it => it.ok && it.p.op === 'move').forEach(it => {
      L.polyline([it.p.target.coords[0], it.p.coords[0]], { color: '#1565c0', weight: 2, dashArray: '4,4', interactive: false }).addTo(previewLayer);
      L.circleMarker(it.p.coords[0], { color: '#1565c0', weight: 3, dashArray: '6,5', radius: 14, fillOpacity: 0.1, interactive: false }).addTo(previewLayer);
    });
    items.filter(it => it.ok && (it.p.op === 'update' || it.p.op === 'delete')).forEach(it => {
      const f = it.p.target;
      const ll = f.type === 'point' ? f.coords[0] : centroid(f.coords);
      L.circleMarker(ll, { color: it.p.op === 'delete' ? '#c62828' : '#ef6c00', weight: 3, radius: 18, fill: false, interactive: false }).addTo(previewLayer);
    });
    const html = items.map((it, i) => it.ok
      ? `<label class="sm-item"><input type="checkbox" data-i="${i}" checked> ${iconFor(it.p)}<span>${escapeXml(it.p.text)}</span></label>`
      : `<div class="sm-item err">✗ ${escapeXml(it.err)}<div class="muted">${escapeXml(JSON.stringify(it.a))}</div></div>`).join('');
    const q = (questions || []).map(q => `<div class="sm-q">？${escapeXml(q)}</div>`).join('');
    const okCount = items.filter(it => it.ok).length;
    $('sm-result').innerHTML = (html || '<div class="muted">没有可执行的操作</div>') + q +
      `<div class="pf-actions">${okCount ? '<button id="sm-apply" class="primary">写入地图</button>' : ''}<button id="sm-discard">放弃</button></div>` +
      `<details class="muted"><summary>模型原始输出</summary><pre>${escapeXml(raw)}</pre></details>`;
    const b = previewLayer.getLayers().length ? L.featureGroup(previewLayer.getLayers()).getBounds() : null;
    if (b && b.isValid() && !map.getBounds().contains(b)) map.fitBounds(b.pad(0.3));
  }

  function iconFor(p) {
    if (p.op !== 'add') return '';
    const s = SYM[p.sym];
    const svg = s.glyph_path && p.props.label ? window.PLOT_STYLES.gbPointSvg(s, p.props.label) : s.svg;
    return `<span class="sm-ic">${svg}</span>`;
  }

  function apply() {
    const chosen = [...document.querySelectorAll('#sm-result input[data-i]')].filter(c => c.checked).map(c => pending[+c.dataset.i]);
    let n = 0;
    chosen.forEach(it => {
      const p = it.p;
      if (p.op === 'add') { app.addFeature(p.sym, p.type, p.coords.map(ll => [ll[0], ll[1]]), p.props); n++; }
      else if (p.op === 'update') { Object.assign(p.target.props, p.props); n++; }
      else if (p.op === 'move') { p.target.coords = [[p.coords[0][0], p.coords[0][1]]]; n++; }
      else if (p.op === 'delete') { app.removeFeature(p.target.id); n++; }
    });
    discard();
    if (n) { app.renderAll(); app.renderProps(); app.commit(); app.hint(`已写入 ${n} 项，可 Ctrl+Z 撤销`, 2500); }
  }

  function discard() {
    pending = [];
    previewLayer.clearLayers();
    $('sm-result').innerHTML = '';
  }

  async function run() {
    const text = $('sm-input').value.trim();
    if (!text) return;
    discard();
    buildAnchors();
    const btn = $('sm-run');
    btn.disabled = true; btn.textContent = '解析中…';
    $('sm-result').innerHTML = '<div class="muted">正在请求大模型…</div>';
    let raw = '';
    try {
      raw = await chat([{ role: 'system', content: systemPrompt() }, { role: 'user', content: userPrompt(text) }]);
      const data = extractJson(raw);
      pending = (data.actions || []).map(a => {
        try { return { ok: true, a, p: plan(a) }; } catch (e) { return { ok: false, a, err: e.message }; }
      });
      showPreview(pending, data.questions, raw);
    } catch (e) {
      $('sm-result').innerHTML = `<div class="sm-item err">✗ ${escapeXml(e.message)}</div>` +
        (raw ? `<details class="muted" open><summary>模型原始输出</summary><pre>${escapeXml(raw)}</pre></details>` : '');
    } finally {
      btn.disabled = false; btn.textContent = '解析';
    }
  }

  // ---------------------------------------------------------------- 参考点

  let placingRef = false;
  function renderRefs() {
    refLayer.clearLayers();
    refPoints.forEach((p, i) => L.marker(p, {
      interactive: false,
      icon: L.divIcon({ className: 'ref-pt', iconSize: [26, 26], iconAnchor: [13, 26], html: `<div><span>P${i + 1}</span></div>` }),
    }).addTo(refLayer));
  }
  map.on('click', e => {
    if (!placingRef) return;
    refPoints.push([e.latlng.lat, e.latlng.lng]);
    renderRefs();
    placingRef = false;
    $('sm-ref').classList.remove('on');
    app.hint(`已放置 P${refPoints.length}，可在指令中说“在 P${refPoints.length} …”`, 2500);
  });

  // ---------------------------------------------------------------- 界面

  function engineLabel() {
    if (cfg.mode === 'proxy') return proxyInfo && proxyInfo.enabled ? `本地服务 · ${proxyInfo.model}` : '未连接（请用 server.py 启动，或改为直连）';
    return `直连 · ${cfg.model || '未设置模型'}`;
  }

  function renderSettings() {
    $('sm-engine').textContent = engineLabel();
    $('sm-settings').innerHTML = `
      <label class="field"><span>连接方式</span><select id="sm-mode">
        <option value="proxy"${cfg.mode === 'proxy' ? ' selected' : ''}>经 server.py 转发（推荐）</option>
        <option value="direct"${cfg.mode === 'direct' ? ' selected' : ''}>浏览器直连模型服务</option></select></label>
      <div id="sm-direct"${cfg.mode === 'direct' ? '' : ' hidden'}>
        <label class="field"><span>接口地址（OpenAI 兼容）</span><input id="sm-url" value="${escapeXml(cfg.url)}"></label>
        <label class="field"><span>模型名</span><input id="sm-model" value="${escapeXml(cfg.model)}" placeholder="如 qwen2.5:14b"></label>
        <label class="field"><span>API Key（本地模型可留空）</span><input id="sm-key" type="password" value="${escapeXml(cfg.key)}"></label>
        <p class="muted">直连需要模型服务允许跨域，例如 Ollama 设置 OLLAMA_ORIGINS=*。</p>
      </div>`;
  }

  const EXAMPLES = [
    '在前指东北方向300米设侦察组，派无人机到堆积区上空侦察',
    '二中队从集结地沿救援车辆行进路线出发，向堆积区东侧搜救，堆积区东侧新发现被困群众4人',
    '失联人员已找到，删除失联标记；划定以泥石流堆积区为中心、半径600米的事故控制区域',
  ];

  function mount() {
    const box = document.createElement('section');
    box.id = 'smart';
    box.innerHTML = `
      <h3>智能标图 <span class="sm-engine" id="sm-engine"></span></h3>
      <textarea id="sm-input" rows="3" placeholder="例：在堆积区西侧200米设前进指挥所，一中队向东搜救，发现被困群众3人"></textarea>
      <div class="sm-bar">
        <button id="sm-run" class="primary">解析</button>
        <button id="sm-ref" title="在地图上单击放置参考点 P1、P2…，指令中可引用">放参考点</button>
        <button id="sm-ref-clear" title="清除参考点">清参考点</button>
        <button id="sm-cfg-btn" title="模型连接设置">设置</button>
      </div>
      <div class="sm-examples">${EXAMPLES.map(e => `<button class="sm-ex">${escapeXml(e)}</button>`).join('')}</div>
      <div id="sm-settings" hidden></div>
      <div id="sm-result"></div>`;
    $('props').prepend(box);
    renderSettings();

    $('sm-run').onclick = run;
    $('sm-input').addEventListener('keydown', e => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) run(); });
    $('sm-ref').onclick = () => { placingRef = !placingRef; $('sm-ref').classList.toggle('on', placingRef); if (placingRef) app.hint('单击地图放置参考点', 2000); };
    $('sm-ref-clear').onclick = () => { refPoints = []; renderRefs(); };
    $('sm-cfg-btn').onclick = () => { $('sm-settings').hidden = !$('sm-settings').hidden; };
    box.addEventListener('click', e => {
      if (e.target.classList.contains('sm-ex')) { $('sm-input').value = e.target.textContent; $('sm-input').focus(); }
      if (e.target.id === 'sm-apply') apply();
      if (e.target.id === 'sm-discard') discard();
    });
    box.addEventListener('change', e => {
      if (!['sm-mode', 'sm-url', 'sm-model', 'sm-key'].includes(e.target.id)) return;
      if (e.target.id === 'sm-mode') cfg.mode = e.target.value;
      if (e.target.id === 'sm-url') cfg.url = e.target.value.trim();
      if (e.target.id === 'sm-model') cfg.model = e.target.value.trim();
      if (e.target.id === 'sm-key') cfg.key = e.target.value.trim();
      saveCfg(); renderSettings(); $('sm-settings').hidden = false;
    });
  }

  mount();
  detectProxy().then(info => { proxyInfo = info; if (info && info.enabled) cfg.mode = 'proxy'; renderSettings(); });

  // 供测试
  window.smartPlot = { buildAnchors, systemPrompt, userPrompt, extractJson, plan, resolvePos, run, apply, get pending() { return pending; }, refPoints };
})();
