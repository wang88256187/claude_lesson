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
      anchors['F' + (i + 1)] = {
        ll: f.type === 'point' ? f.coords[0] : centroid(f.coords), name: featName(f), feature: f,
        chains: f.type === 'line' ? [f.coords] : null,
      };
    });
    refPoints.forEach((p, i) => { anchors['P' + (i + 1)] = { ll: p, name: '参考点' }; });
    gazInView().forEach((g, i) => {
      anchors['G' + (i + 1)] = { ll: g.ll, name: g.name, kind: g.kind, chains: g.chains || null, gaz: g };
    });
    return anchors;
  }

  // ---------------------------------------------------------------- 地名参照（OSM）

  let gazetteer = [];          // {name, kind, ll, chains?}
  const gazLayer = L.layerGroup();
  const PLACE_KIND = { city: '城市', town: '镇', village: '村', hamlet: '自然村', suburb: '城区', neighbourhood: '社区', locality: '地名', isolated_dwelling: '居民点' };
  const ROAD_KIND = { motorway: '高速', trunk: '国道/干线', primary: '省道/主干道', secondary: '县道/次干道', tertiary: '乡道', unclassified: '村道', residential: '街巷', track: '机耕道' };
  const AMENITY_KIND = { school: '学校', kindergarten: '幼儿园', hospital: '医院', clinic: '卫生院', townhall: '政府', police: '派出所', fire_station: '消防站' };

  function roadKind(t) {
    const ref = t.ref || '';
    if (/^G\d/.test(ref)) return '国道';
    if (/^S\d/.test(ref)) return '省道';
    if (/^X\d/.test(ref)) return '县道';
    if (/^Y\d/.test(ref)) return '乡道';
    return ROAD_KIND[t.highway] || '道路';
  }

  // 把同名路段按公共端点拼接成连续折线
  function joinChains(segs) {
    const key = ll => ll[0].toFixed(6) + ',' + ll[1].toFixed(6);
    const chains = segs.map(s => s.slice());
    let merged = true;
    while (merged) {
      merged = false;
      outer: for (let i = 0; i < chains.length; i++) {
        for (let j = i + 1; j < chains.length; j++) {
          const a = chains[i], b = chains[j];
          const a0 = key(a[0]), a1 = key(a[a.length - 1]), b0 = key(b[0]), b1 = key(b[b.length - 1]);
          let c = null;
          if (a1 === b0) c = a.concat(b.slice(1));
          else if (a1 === b1) c = a.concat(b.slice(0, -1).reverse());
          else if (a0 === b1) c = b.concat(a.slice(1));
          else if (a0 === b0) c = b.slice().reverse().concat(a.slice(1));
          if (c) { chains[i] = c; chains.splice(j, 1); merged = true; break outer; }
        }
      }
    }
    return chains;
  }

  function chainLength(c) {
    let d = 0;
    for (let i = 1; i < c.length; i++) d += map.distance(c[i - 1], c[i]);
    return d;
  }

  function processOverpass(data) {
    const pts = [], lines = new Map();
    (data.elements || []).forEach(e => {
      const t = e.tags || {};
      const name = t['name:zh'] || t.name;
      if (t.highway || t.waterway) {
        if (!e.geometry) return;
        const label = t.highway ? (name && t.ref ? `${name}(${t.ref})` : name || t.ref) : name;
        if (!label) return;
        const kind = t.highway ? roadKind(t) : (t.waterway === 'river' ? '河流' : '沟/溪');
        const k = (t.highway ? 'R:' : 'W:') + (t.ref || name);
        if (!lines.has(k)) lines.set(k, { name: label, kind, segs: [] });
        lines.get(k).segs.push(e.geometry.map(g => [g.lat, g.lon]));
        return;
      }
      if (!name) return;
      let ll = e.lat != null ? [e.lat, e.lon] : e.center ? [e.center.lat, e.center.lon]
        : e.geometry ? centroid(e.geometry.map(g => [g.lat, g.lon])) : null;
      if (!ll) return;
      const kind = t.place ? PLACE_KIND[t.place] || '地名' : t.amenity ? AMENITY_KIND[t.amenity] || '设施'
        : t.natural === 'peak' ? '山峰' : t.natural === 'valley' ? '沟谷' : t.bridge ? '桥' : '地物';
      pts.push({ name, kind, ll });
    });
    const out = pts.filter((p, i) => pts.findIndex(q => q.name === p.name && q.kind === p.kind) === i);
    lines.forEach(v => {
      const chains = joinChains(v.segs).sort((a, b) => chainLength(b) - chainLength(a));
      // 代表位置：离当前视图中心最近的节点（长河流、长道路的中点可能远在视野外）
      const c = map.getCenter();
      const ll = chains.flat().reduce((b, p) => (map.distance(p, c) < map.distance(b, c) ? p : b));
      out.push({ name: v.name.replace(/;/g, '/'), kind: v.kind, chains, ll });
    });
    return out;
  }

  async function loadGazetteer() {
    const b = map.getBounds();
    const km = map.distance(b.getSouthWest(), b.getNorthEast()) / 1000;
    if (km > 40) return app.hint('视野过大，请放大到 40 公里范围内再载入地名', 3000);
    const bb = [b.getSouth(), b.getWest(), b.getNorth(), b.getEast()].map(v => v.toFixed(5)).join(',');
    const query = `[out:json][timeout:60];(
node["place"]["name"](${bb});
way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|track)$"]["name"](${bb});
way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]["ref"](${bb});
way["waterway"~"^(river|stream)$"]["name"](${bb});
nwr["amenity"~"^(school|kindergarten|hospital|clinic|townhall|police|fire_station)$"]["name"](${bb});
nwr["natural"~"^(peak|valley)$"]["name"](${bb});
way["bridge"="yes"]["name"](${bb});
);out geom qt;`;
    const btn = $('sm-gaz');
    btn.disabled = true; btn.textContent = '载入中…';
    try {
      let data;
      if (location.protocol.startsWith('http')) {
        const r = await fetch('/api/osm/overpass', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query }) });
        data = await r.json();
        if (!r.ok) throw new Error(data.error || r.status);
      } else {
        const r = await fetch('https://overpass-api.de/api/interpreter', { method: 'POST', body: new URLSearchParams({ data: query }) });
        data = await r.json();
      }
      const got = processOverpass(data);
      // 合并：同名同类的以新数据为准
      const keyOf = g => g.kind + '|' + g.name;
      const m = new Map(gazetteer.map(g => [keyOf(g), g]));
      got.forEach(g => m.set(keyOf(g), g));
      gazetteer = [...m.values()];
      saveGaz(); renderGaz();
      $('sm-gaz-show').checked = true; map.addLayer(gazLayer);
      app.hint(`已载入 ${got.length} 个地名（村镇、道路、河流、设施）`, 3000);
    } catch (e) {
      app.hint('地名载入失败：' + e.message, 4000);
    } finally {
      btn.disabled = false; btn.textContent = '载入地名';
    }
  }

  function gazInView() {
    // 取视野（外扩一半）内的地名；点最多 60 个、线最多 25 条，离视图中心近的优先
    const b = map.getBounds().pad(0.5), c = map.getCenter();
    const inb = g => g.chains ? g.chains.some(ch => ch.some(ll => b.contains(ll))) : b.contains(g.ll);
    const d = g => map.distance(c, g.ll);
    const vis = gazetteer.filter(inb).sort((a, x) => d(a) - d(x));
    return vis.filter(g => !g.chains).slice(0, 60).concat(vis.filter(g => g.chains).slice(0, 25));
  }

  function renderGaz() {
    gazLayer.clearLayers();
    const n = $('sm-gaz-n');
    if (n) n.textContent = gazetteer.length ? `${gazetteer.length} 个` : '';
    gazetteer.forEach(g => {
      if (g.chains) {
        g.chains.forEach(ch => L.polyline(ch, { color: g.kind.includes('河') || g.kind.includes('沟') ? '#1e88e5' : '#f9a825', weight: 2, opacity: 0.5, interactive: false }).addTo(gazLayer));
      }
      L.marker(g.ll, {
        interactive: false, keyboard: false,
        icon: L.divIcon({ className: 'gaz-label', iconSize: [0, 0], html: `<span>${escapeXml(g.name)}</span>` }),
      }).addTo(gazLayer);
    });
  }

  function saveGaz() { try { localStorage.setItem('rescue-plot-gaz', JSON.stringify(gazetteer)); } catch (e) { /* 忽略 */ } }
  try { gazetteer = JSON.parse(localStorage.getItem('rescue-plot-gaz') || '[]'); } catch (e) { gazetteer = []; }
  app.onSave(() => (gazetteer.length ? { gazetteer } : {}));
  app.onLoad(gj => { gazetteer = Array.isArray(gj.gazetteer) ? gj.gazetteer : []; saveGaz(); renderGaz(); });

  function anchorTable() {
    const geo = { point: '点', line: '线', polygon: '面' };
    const rows = { F: [], G: [], P: [] };
    Object.entries(anchors).forEach(([k, a]) => {
      if (k === 'O') return;
      if (a.gaz) {
        const g = a.gaz;
        let row = `${k} | ${g.name} | ${g.kind}`;
        if (g.chains) {
          const c = g.chains[0];
          row += ` | 线 | 走向 ${JSON.stringify(toXY(c[0]))}→${JSON.stringify(toXY(c[c.length - 1]))}`;
          const t = topology(k, g);
          if (t.passes.length) row += ` | 沿途经过:${t.passes.join('→')}`;
          if (t.meets.length) row += ` | 相交:${t.meets.join('、')}`;
        } else row += ` | 位置${JSON.stringify(toXY(g.ll))}`;
        rows.G.push(row);
        return;
      }
      rows[k[0]].push(featRow(k, a));
    });
    return `### 图上要素\n${rows.F.join('\n') || '（无）'}` +
      (rows.G.length ? `\n### 真实地名（OSM）\n${rows.G.join('\n')}` : '') +
      (rows.P.length ? `\n### 参考点\n${rows.P.join('\n')}` : '');
  }

  // 道路/河流的拓扑提示：沿途经过的地名（按走向排序）、与哪些道路相交 —— 帮助模型把多段 along 串成合理路线
  function topology(k, g) {
    const xy = g.chains.map(c => c.map(toXY));
    const nearIdx = p => {
      let best = { d: Infinity, i: 0, ci: 0 };
      xy.forEach((c, ci) => c.forEach((q, i) => { const d = Math.hypot(q[0] - p[0], q[1] - p[1]); if (d < best.d) best = { d, i, ci }; }));
      return best;
    };
    const passes = [], meets = [];
    Object.entries(anchors).forEach(([k2, a2]) => {
      if (!a2.gaz || k2 === k) return;
      if (!a2.gaz.chains) {
        const n = nearIdx(toXY(a2.ll));
        if (n.d < 400) passes.push({ name: `${a2.name}(${k2})`, ord: n.ci * 1e6 + n.i });
      } else {
        const other = a2.gaz.chains.flat().map(toXY);
        const hit = other.some(p => nearIdx(p).d < 40);
        if (hit) meets.push(`${a2.name}(${k2})`);
      }
    });
    return { passes: passes.sort((x, y) => x.ord - y.ord).map(x => x.name), meets };
  }

  function featRow(k, a) {
    const geo = { point: '点', line: '线', polygon: '面' };
    {
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
    }
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
- {"ref":"F3"} / {"ref":"G2"}：就在参照物处（F 为图上要素，G 为真实地名，P 为参考点；面、线取其中心）
- {"ref":"F3","dir":"西","dist":200}：F3 的西方 200 米。dir 取 北/东北/东/东南/南/西南/西/西北，或方位角数字（正北为 0，顺时针）；“北偏东30度”写 30，“南偏西20度”写 200，只说“北偏东”未给度数按 30
- {"ref":"F12.start"} / {"ref":"F12.end"}：线要素 F12 的起点 / 终点
- {"xy":[x,y]}：直接给平面坐标
- {"ref":"G5.start"} / {"ref":"G5.end"} 同样适用于道路、河流
- 线的 path 中可写 {"along":"G5"}（或图上线要素 F12），表示沿该道路/河流/线路行进：程序会自动截取 along 前后两个位置之间的那一段，因此 along 前后都应给出位置（出发地、目的地）

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
2. 参照物按名称匹配下方“参照物”列表：图上要素（如“堆积区”“前指”）和真实地名（村镇、道路编号如 G345、河流、学校医院）都可以用。“沿某路/某河”用 along。找不到参照物或方位距离不明时，不要猜，写入 questions。
3. 没说距离时：“附近/旁边”按 100 米，“一侧”按 200 米。
4. 行动路线从出发位置画到目标位置；“向X搜救/推进”用 XF-6.3.18 进攻方向（heading 为推进方向）或 XF-6.3.17 预计行动路线。
5. 被困人员用 XF-6.3.22，失联用 X-A01，并填 count。
6. 已有要素的人数、状态变化用 update，不要重复新增；若原注记里写有人数等数值，update 时同时给出改写后的 note。
7. 泥石流、滑坡等灾情优先用 GB- 开头的预设符号（如 GB-A10400-泥石流）。
8. “派/调/转移”图上已有的力量或装备到某处，用 move 移动该要素，不要新增，也不要只改注记。
9. note 只写注记内容本身（番号、单位、状态、人数），不要带上符号名称；label 只用于 GB- 开头的点符号。
10. 部队“到达/进至”某处：move 该部队符号，不改其注记。“开设/设立”指挥所、医疗点、安置点等：新增对应符号（图上已有同类且指令是转移时才 move）。
11. 机动、撤离、转运等路线要沿真实道路：按参照物中道路的“沿途经过”“相交”信息，从出发地起，用一个或多个 {"along":"Gx"} 依次串联到目的地，不要两点直连穿越山体或城区。

## 常用叫法 → 符号
- 现场指挥部/基本指挥所 → GB-D10100-地质灾害（国标）或 XF-6.1.12；前进指挥所/前指 → XF-6.1.13
- 伤员救治点/临时医疗点/医疗点 → GB-D10200-临时医疗；医院 → GB-D50100
- 安置点 → GB-D10200-临时安置；避难场所 → GB-D60100；物资发放点 → GB-D10200-物资发放
- 监测点/观察哨/预警点 → X-D03；侦察组 → XF-6.1.26；无人机 → XF-6.2.36
- 被困人员 → XF-6.3.22；失联 → X-A01；伤亡 → X-A02
- 救援车辆机动路线 → GB-E30100；群众撤离路线 → GB-E30200；人员行动/搜救路线 → XF-6.3.17；伤员转运路线 → XF-6.3.17（note 写明）
- 警戒区 → GB-F10100；事故控制区 → GB-F10200；蔓延区 → GB-F10300；搜救责任区 → X-F03
- 道路中断 → GB-A21300-公路设施（点）或 GB-E20500（线）；房屋倒塌/掩埋 → GB-A21300-建筑垮塌

## 符号目录
${catalog()}`;
  }

  function userPrompt(text) {
    return `## 参照物\n${anchorTable()}\n\n## 指令\n${text}`;
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
      if (!a.chains) throw new Error(`${ref} 不是线，不能取${which === 'start' ? '起点' : '终点'}`);
      const c = a.chains[0];
      ll = which === 'start' ? c[0] : c[c.length - 1];
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

  // 沿线：在该线（可能由多段组成）上截取离前一点、后一点最近的两个节点之间的一段
  function alongSegment(a, prev, next) {
    const dd = (p, q) => { const [x1, y1] = toXY(p), [x2, y2] = toXY(q); return Math.hypot(x1 - x2, y1 - y2); };
    const nearest = (c, p) => c.reduce((best, ll, i) => (dd(ll, p) < dd(c[best], p) ? i : best), 0);
    let best = null;
    a.chains.forEach(c => {
      const i = prev ? nearest(c, prev) : 0;
      const j = next ? nearest(c, next) : c.length - 1;
      const cost = (prev ? dd(c[i], prev) : 0) + (next ? dd(c[j], next) : 0);
      if (!best || cost < best.cost) best = { c, i, j, cost };
    });
    const { c, i, j } = best;
    return i <= j ? c.slice(i, j + 1) : c.slice(j, i + 1).reverse();
  }

  function resolvePath(list) {
    const items = (list || []).map(p => (p && p.along ? { along: String(p.along) } : { ll: resolvePos(p) }));
    const out = [];
    items.forEach((it, k) => {
      if (!it.along) { out.push(it.ll); return; }
      const a = anchors[it.along];
      if (!a || !a.chains) throw new Error(`along 引用的 ${it.along} 不是线`);
      const next = items.slice(k + 1).find(x => x.ll);
      const seg = alongSegment(a, out[out.length - 1], next && next.ll);
      out.push(...seg);
    });
    return out.filter((ll, i) => i === 0 || map.distance(ll, out[i - 1]) > 1);
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
    '武警某支队从集结地域出发，沿G345向东机动到城关镇，在三眼村西侧300米开设前进指挥所',
    '在舟曲县人民医院设伤员救治点，标一条从泥石流堆积区沿S576到县人民医院的伤员转运路线',
    '罗家峪群众向西撤离到第二小学安置点；二中队转移到罗家峪，在罗家峪东侧100米发现3人被困',
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
      <div class="sm-bar">
        <button id="sm-gaz" title="从 OSM 载入当前视野内的村镇、道路、河流、学校医院等真实地名，指令中可直接引用">载入地名</button>
        <label class="chk" style="margin:0"><input type="checkbox" id="sm-gaz-show"> 显示地名参照</label>
        <span class="muted" id="sm-gaz-n"></span>
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
    $('sm-gaz').onclick = loadGazetteer;
    $('sm-gaz-show').onchange = e => { if (e.target.checked) map.addLayer(gazLayer); else map.removeLayer(gazLayer); };
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
  renderGaz();
  detectProxy().then(info => { proxyInfo = info; if (info && info.enabled) cfg.mode = 'proxy'; renderSettings(); });

  // 供测试
  window.smartPlot = { buildAnchors, systemPrompt, userPrompt, extractJson, plan, resolvePos, run, apply, get pending() { return pending; }, refPoints };
})();
