/* 抢险救援标绘 —— 主程序（无构建步骤，直接在浏览器运行，支持 file:// 离线打开） */
(function () {
  'use strict';

  const LIB = window.SYMBOL_LIB;
  // 本单位标号（local_symbols.js，由 symbols/tools/import_symbols.py 在本机生成，不入代码仓库）
  const LOCAL = window.LOCAL_SYMBOL_LIB;
  if (LOCAL && Array.isArray(LOCAL.symbols)) {
    const ids = new Set(LIB.symbols.map(s => s.id));
    LIB.symbols.push(...LOCAL.symbols.filter(s => !ids.has(s.id)));
    Object.assign(LIB.categories, LOCAL.categories || {});
  }
  const { LINE_STYLES, AREA_STYLES, ARROWS, gbPointSvg, escapeXml } = window.PLOT_STYLES;
  const SYM = Object.fromEntries(LIB.symbols.map(s => [s.id, s]));
  const STORE_KEY = 'rescue-plot-v1';
  const POINT_PX = 36;

  // ---------------------------------------------------------------- 符号面板

  const COMMON = [
    'GB-D20200', 'GB-D20100', 'GB-D20400', 'GB-D10100-地质灾害', 'XF-6.1.12', 'XF-6.1.13',
    'XF-6.1.26', 'XF-6.1.27', 'XF-6.3.22', 'X-A01', 'X-A02', 'XF-6.3.18', 'XF-6.2.36',
    'XF-6.2.35', 'X-D01', 'X-D03', 'X-B01', 'X-B02',
    'XF-6.3.17', 'GB-E30100', 'GB-E30200', 'XF-6.3.21', 'GB-E20500', 'X-L01', 'X-L02',
    'GB-F10100', 'GB-F10200', 'GB-F10300', 'X-F01', 'X-F02', 'X-F03',
  ];

  const TABS = [
    ...(LOCAL && LOCAL.symbols && LOCAL.symbols.length ? [{
      key: 'unit', name: '本单位', groups: () => Object.entries(LIB.categories)
        .filter(([k]) => k.startsWith('U-'))
        .map(([k, t]) => ({ title: t, items: LIB.symbols.filter(s => s.category === k) })),
    }] : []),
    {
      key: 'common', name: '泥石流常用', groups: () => [
        { title: '灾情（GB/T 35649 子类）', items: LIB.symbols.filter(s => s.preset_of) },
        { title: '力量、行动与区域', items: COMMON.map(id => SYM[id]).filter(Boolean) },
      ],
    },
    {
      key: 'gb', name: 'GB/T 35649', groups: () => Object.entries(LIB.categories)
        .filter(([k]) => /^[A-F]\d$/.test(k))
        .map(([k, t]) => ({ title: `${k} ${t}`, items: LIB.symbols.filter(s => s.category === k && !s.preset_of) })),
    },
    {
      key: 'xf', name: 'XF/T 3013', groups: () => Object.entries(LIB.categories)
        .filter(([k]) => !/^[A-F]\d$/.test(k) && !k.startsWith('X') && !k.startsWith('U-'))
        .map(([k, t]) => ({ title: t, items: LIB.symbols.filter(s => s.source.startsWith('XF') && s.category === k) })),
    },
    {
      key: 'x', name: '扩充', groups: () => Object.entries(LIB.categories)
        .filter(([k]) => k.startsWith('X'))
        .map(([k, t]) => ({ title: t, items: LIB.symbols.filter(s => s.category === k) })),
    },
  ];

  let activeTab = 'common';
  const $ = id => document.getElementById(id);

  function renderTabs() {
    $('tabs').innerHTML = TABS.map(t =>
      `<button data-tab="${t.key}" class="${t.key === activeTab ? 'on' : ''}">${t.name}</button>`).join('');
  }

  function symButton(s) {
    const wide = s.geometry !== 'point';
    const code = s.preset_of || s.std_code || s.id;
    return `<button class="sym-btn${wide ? ' wide' : ''}${tool && tool.symId === s.id ? ' on' : ''}" data-sym="${escapeXml(s.id)}" title="${escapeXml(s.name + '  ' + (s.description || ''))}">
      <span class="ic">${s.svg}</span><span><span class="nm">${escapeXml(s.name)}</span><br><span class="code">${escapeXml(code)}</span></span></button>`;
  }

  function renderPalette() {
    const q = $('search').value.trim();
    let groups;
    if (q) {
      const hit = LIB.symbols.filter(s =>
        [s.name, s.label, s.std_code, s.id, s.description].some(v => v && String(v).includes(q)));
      groups = [{ title: `搜索结果（${hit.length}）`, items: hit }];
    } else {
      groups = TABS.find(t => t.key === activeTab).groups();
    }
    $('symbol-list').innerHTML = groups.filter(g => g.items.length).map(g =>
      `<div class="grp-title">${escapeXml(g.title)}</div><div class="sym-grid">${g.items.map(symButton).join('')}</div>`).join('');
  }

  $('tabs').addEventListener('click', e => {
    const b = e.target.closest('button[data-tab]');
    if (!b) return;
    activeTab = b.dataset.tab;
    $('search').value = '';
    renderTabs(); renderPalette();
  });
  $('search').addEventListener('input', renderPalette);
  $('symbol-list').addEventListener('click', e => {
    const b = e.target.closest('.sym-btn');
    if (!b) return;
    const id = b.dataset.sym;
    if (tool && tool.symId === id) cancelTool(); else startTool(id);
  });

  // ---------------------------------------------------------------- 地图

  const map = L.map('map', { zoomControl: true, doubleClickZoom: true, zoomSnap: 0.25, zoomDelta: 0.5 }).setView([31.105, 103.603], 15);
  const renderer = L.svg({ padding: 0.5 }).addTo(map);
  (function addPatterns() {
    const svgEl = renderer._container;
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    defs.innerHTML =
      `<pattern id="pat-dots" width="6" height="6" patternUnits="userSpaceOnUse"><rect width="6" height="6" fill="rgba(255,255,255,0.35)"/><circle cx="3" cy="3" r="1.1" fill="#FF0000"/></pattern>` +
      `<pattern id="pat-hatch" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="7" height="7" fill="rgba(255,255,255,0.2)"/><line x1="0" y1="0" x2="0" y2="7" stroke="#FF0000" stroke-width="1.5"/></pattern>`;
    svgEl.insertBefore(defs, svgEl.firstChild);
  })();
  L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);

  // 底图：页面由 server.py 提供时经本地瓦片缓存（/tiles/…，可离线复用），否则直连公网瓦片
  const VIA_SERVER = location.protocol.startsWith('http');
  const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services';
  const TILES = {
    osm: { url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png', max: 19, attr: '&copy; OpenStreetMap contributors' },
    img: { url: `${ESRI}/World_Imagery/MapServer/tile/{z}/{y}/{x}`, max: 19, attr: 'Imagery &copy; Esri' },
    label: { url: `${ESRI}/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}`, max: 19, attr: '' },
    topo: { url: 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', max: 17, attr: '&copy; OpenTopoMap (CC-BY-SA)' },
  };
  function tileLayer(key) {
    const t = TILES[key];
    const url = VIA_SERVER ? `/tiles/${key}/{z}/{x}/{y}` : t.url;
    return L.tileLayer(url, { maxZoom: 19, maxNativeZoom: t.max, attribution: t.attr, subdomains: 'abc' });
  }

  let baseLayers = [];
  function setBasemap(kind, url) {
    baseLayers.forEach(l => map.removeLayer(l));
    baseLayers = [];
    $('map').classList.toggle('no-basemap', kind === 'none');
    if (kind === 'imglabel') baseLayers = [tileLayer('img'), tileLayer('label')];
    else if (TILES[kind]) baseLayers = [tileLayer(kind)];
    else if (kind === 'custom' && url) baseLayers = [L.tileLayer(url, { maxZoom: 20 })];
    baseLayers.forEach(l => l.addTo(map));
    baseLayers.slice().reverse().forEach(l => l.bringToBack());
    localSet('basemap', kind);
  }
  $('basemap').addEventListener('change', e => {
    const v = e.target.value;
    if (v === 'custom') {
      const url = prompt('瓦片地址模板（如内网瓦片服务）：\n例：http://10.0.0.8/tiles/{z}/{x}/{y}.png', localGet('tile-url') || '');
      if (!url) { e.target.value = 'none'; setBasemap('none'); return; }
      localSet('tile-url', url);
      setBasemap('custom', url);
    } else setBasemap(v);
  });

  $('geo-q').addEventListener('keydown', async e => {
    if (e.key !== 'Enter' || !e.target.value.trim()) return;
    if (!VIA_SERVER) return hint('地名搜索需用 server.py 启动页面', 2500);
    try {
      const r = await fetch('/api/geocode?q=' + encodeURIComponent(e.target.value.trim()));
      const d = await r.json();
      if (!r.ok) throw new Error(d.error);
      if (!d.results.length) return hint('没有找到该地名', 2000);
      const g = d.results[0];
      if (g.bbox.length === 4) map.fitBounds([[g.bbox[0], g.bbox[2]], [g.bbox[1], g.bbox[3]]], { maxZoom: 15 });
      else map.setView([g.lat, g.lon], 14);
      hint(g.name, 3000);
    } catch (err) { hint('地名搜索失败：' + err.message, 3000); }
  });

  $('btn-image').addEventListener('click', () => $('file-image').click());
  $('file-image').addEventListener('change', e => {
    const f = e.target.files[0];
    if (!f) return;
    const rd = new FileReader();
    rd.onload = () => {
      L.imageOverlay(rd.result, map.getBounds(), { opacity: 0.95 }).addTo(map).bringToBack();
      hint('图片已铺满当前视野（仅显示用，不随文件保存）', 3000);
    };
    rd.readAsDataURL(f);
    e.target.value = '';
  });

  // ---------------------------------------------------------------- 状态、历史、自动保存

  let features = [];
  let selectedId = null;
  let tool = null;
  const history = { stack: [], idx: -1 };

  const uid = () => Math.random().toString(36).slice(2, 10);
  const snapshot = () => JSON.stringify({ title: $('title').value, features });

  function commit() {
    history.stack = history.stack.slice(0, history.idx + 1);
    history.stack.push(snapshot());
    if (history.stack.length > 200) history.stack.shift();
    history.idx = history.stack.length - 1;
    localSet(STORE_KEY, history.stack[history.idx]);
    renderLegend();
  }

  function restore(json) {
    const d = JSON.parse(json);
    features = d.features || [];
    $('title').value = d.title || '';
    updateTitleBlock();
    if (!features.some(f => f.id === selectedId)) selectedId = null;
    renderAll(); renderProps(); renderLegend();
  }

  function undo() { if (history.idx > 0) { history.idx--; restore(history.stack[history.idx]); localSet(STORE_KEY, history.stack[history.idx]); } }
  function redo() { if (history.idx < history.stack.length - 1) { history.idx++; restore(history.stack[history.idx]); localSet(STORE_KEY, history.stack[history.idx]); } }
  $('btn-undo').addEventListener('click', undo);
  $('btn-redo').addEventListener('click', redo);

  function localGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function localSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* 隐私模式等不可用时忽略 */ } }

  // ---------------------------------------------------------------- 渲染

  const plotLayer = L.layerGroup().addTo(map);
  const decoLayer = L.layerGroup().addTo(map);
  const editLayer = L.layerGroup().addTo(map);

  function nowStamp() {
    const d = new Date(), p = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}.${p(d.getMonth() + 1)}.${p(d.getDate())}.${p(d.getHours())}${p(d.getMinutes())}`;
  }

  function pointSvg(f) {
    const s = SYM[f.sym];
    if (s.glyph_path) return gbPointSvg(s, f.props.label != null ? f.props.label : s.label);
    return s.svg;
  }

  function noteText(f) {
    const p = f.props, parts = [];
    if (p.note) parts.push(p.note);
    if (p.count) parts.push(`${p.count}人`);
    if (p.time) parts.push(p.time);
    return parts.join(' / ');
  }

  function rotIcon(svg, w, h, angle, cls = 'plot-deco') {
    return L.divIcon({
      className: cls, iconSize: [w, h], iconAnchor: [w / 2, h / 2],
      html: `<div style="width:${w}px;height:${h}px;transform:rotate(${angle}deg)">${svg}</div>`,
    });
  }

  function drawPoint(f) {
    const size = POINT_PX * (f.props.scale || 1);
    const note = noteText(f);
    const icon = L.divIcon({
      className: 'plot-point' + (f.id === selectedId ? ' selected' : ''),
      iconSize: [size, size], iconAnchor: [size / 2, size / 2],
      html: `<div class="sym" style="width:${size}px;height:${size}px;opacity:${f.props.opacity ?? 1};transform:rotate(${f.props.rotation || 0}deg)">${pointSvg(f)}</div>` +
        (note ? `<div class="note" style="top:${size + 2}px">${escapeXml(note)}</div>` : ''),
    });
    const m = L.marker(f.coords[0], { icon, draggable: !tool, interactive: !tool, keyboard: false, riseOnHover: true }).addTo(plotLayer);
    m.on('click', e => { L.DomEvent.stop(e); if (!tool) select(f.id); });
    m.on('dragend', () => { const ll = m.getLatLng(); f.coords = [[ll.lat, ll.lng]]; commit(); });
  }

  // 沿屏幕路径按像素间隔取点，返回 {latlng, angle}
  function samplePath(latlngs, spacing, offset, closed) {
    const pts = latlngs.map(ll => map.latLngToLayerPoint(ll));
    if (closed) pts.push(pts[0]);
    const out = [];
    let next = offset, acc = 0;
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], b = pts[i + 1], len = a.distanceTo(b);
      if (!len) continue;
      const ang = Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI;
      while (next <= acc + len) {
        const t = (next - acc) / len;
        const p = L.point(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t);
        out.push({ latlng: map.layerPointToLatLng(p), angle: ang, layerPoint: p });
        next += spacing;
      }
      acc += len;
    }
    return { out, total: acc };
  }

  function segAngle(a, b) {
    const pa = map.latLngToLayerPoint(a), pb = map.latLngToLayerPoint(b);
    return Math.atan2(pb.y - pa.y, pb.x - pa.x) * 180 / Math.PI;
  }

  // 未在 styles.js 中专门定义的线、面符号（如本单位导入的），按符号数据里的 style 绘制
  function styleFromSymbol(s, geom) {
    const y = (s && s.style) || {};
    const color = y.stroke || y.color || (s && s.color) || '#FF0000';
    const arrow = y.arrow_end ? (y.arrow_end === 'open' ? 'open' : 'filled') : undefined;
    const st = { color, width: Number(y.width) || 2, dash: y.dash || undefined, arrow };
    if (geom === 'polygon') st.fill = { color: y.fill || color, opacity: y.fill_opacity ?? 0.05 };
    return st;
  }

  function drawLine(f) {
    const st = LINE_STYLES[f.sym] || styleFromSymbol(SYM[f.sym], 'line');
    const op = f.props.opacity ?? 1;
    const ll = f.coords;
    const base = L.polyline(ll, {
      renderer, color: st.color, weight: st.width, dashArray: st.dash, opacity: op,
      lineCap: st.dash ? 'butt' : 'round', lineJoin: 'round', interactive: !tool,
    }).addTo(plotLayer);
    const hit = L.polyline(ll, { renderer, color: '#000', weight: 16, opacity: 0, interactive: !tool }).addTo(plotLayer);
    if (st.casing) {
      L.polyline(ll, { renderer, color: '#fff', weight: st.casing, dashArray: st.dash, opacity: op, lineCap: 'butt', interactive: false }).addTo(plotLayer);
    }
    [base, hit].forEach(l => l.on('click', e => { L.DomEvent.stop(e); if (!tool) select(f.id); }));

    if (st.deco) {
      const { out } = samplePath(ll, st.deco.spacing, st.deco.spacing / 2);
      out.forEach(s => L.marker(s.latlng, { icon: rotIcon(st.deco.svg, st.deco.w, st.deco.h, s.angle), interactive: false, keyboard: false }).addTo(decoLayer));
    }
    if (st.arrow && ll.length > 1) {
      const n = ll.length, ang = segAngle(ll[n - 2], ll[n - 1]);
      const sz = st.arrow === 'big' ? 40 : 24;
      L.marker(ll[n - 1], { icon: rotIcon(ARROWS[st.arrow](st.color), sz, sz, ang), interactive: false, keyboard: false }).addTo(decoLayer);
    }
    if (st.startIcon) {
      const si = st.startIcon;
      L.marker(ll[0], { icon: rotIcon(si.svg, si.w, si.h, 0), interactive: false, keyboard: false }).addTo(decoLayer);
    }
    if (f.props.note) base.bindTooltip(escapeXml(f.props.note), { permanent: true, direction: 'center', className: 'plot-label' });
    if (f.id === selectedId) highlight(ll, false);
  }

  function drawArea(f) {
    const st = AREA_STYLES[f.sym] || styleFromSymbol(SYM[f.sym], 'polygon');
    const op = f.props.opacity ?? 1;
    const fill = st.fill || {};
    const poly = L.polygon(f.coords, {
      renderer, color: st.color, weight: st.width, dashArray: st.dash, opacity: op,
      fill: true,
      fillColor: fill.pattern ? `url(#pat-${fill.pattern})` : (fill.color || st.color),
      fillOpacity: fill.pattern ? op : (fill.opacity ?? 0.05) * op, interactive: !tool,
    }).addTo(plotLayer);
    poly.on('click', e => { L.DomEvent.stop(e); if (!tool) select(f.id); });

    if (st.arrows) {
      const pts = f.coords.map(c => map.latLngToLayerPoint(c));
      const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
      const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
      const perim = samplePath(f.coords, 1e9, 0, true).total;
      const { out } = samplePath(f.coords, perim / 4, perim / 8, true);
      out.slice(0, 4).forEach(s => {
        const rad = s.angle * Math.PI / 180;
        let nx = -Math.sin(rad), ny = Math.cos(rad);      // 法线
        const inward = (cx - s.layerPoint.x) * nx + (cy - s.layerPoint.y) * ny > 0;
        if (!inward) { nx = -nx; ny = -ny; }                // 现在指向区域内
        if (st.arrows === 'out') { nx = -nx; ny = -ny; }
        const ang = Math.atan2(ny, nx) * 180 / Math.PI;
        L.marker(s.latlng, { icon: rotIcon(ARROWS.area(st.color), 20, 20, ang), interactive: false, keyboard: false }).addTo(decoLayer);
      });
    }
    if (f.props.note) poly.bindTooltip(escapeXml(f.props.note), { permanent: true, direction: 'center', className: 'plot-label' });
    if (f.id === selectedId) highlight(f.coords, true);
  }

  function highlight(ll, closed) {
    const Ctor = closed ? L.polygon : L.polyline;
    Ctor(ll, { renderer, color: '#1565c0', weight: 3, dashArray: '6,4', fill: false, interactive: false }).addTo(editLayer);
    const f = features.find(x => x.id === selectedId);
    ll.forEach((c, i) => {
      const h = L.marker(c, {
        draggable: true, keyboard: false,
        icon: L.divIcon({ className: 'vertex-handle', iconSize: [12, 12], iconAnchor: [6, 6] }),
      }).addTo(editLayer);
      h.bindTooltip('拖动修改；右键删除该点', { direction: 'top', offset: [0, -6] });
      h.on('dragend', () => { const p = h.getLatLng(); f.coords[i] = [p.lat, p.lng]; renderAll(); commit(); });
      h.on('contextmenu', e => {
        L.DomEvent.stop(e);
        const min = closed ? 3 : 2;
        if (f.coords.length <= min) return hint(`至少保留 ${min} 个点`, 1500);
        f.coords.splice(i, 1); renderAll(); commit();
      });
    });
  }

  function renderAll() {
    plotLayer.clearLayers(); decoLayer.clearLayers(); editLayer.clearLayers();
    // 面在下、线居中、点在上
    const order = { polygon: 0, line: 1, point: 2 };
    [...features].sort((a, b) => order[a.type] - order[b.type]).forEach(f => {
      if (!SYM[f.sym]) return;
      if (f.type === 'point') drawPoint(f);
      else if (f.type === 'line') drawLine(f);
      else drawArea(f);
    });
  }
  map.on('zoomend', renderAll);

  // ---------------------------------------------------------------- 绘制工具

  const drawLayer = L.layerGroup().addTo(map);
  let rubber = null;

  function hint(msg, ms) {
    const el = $('hint');
    el.textContent = msg; el.style.display = msg ? 'block' : 'none';
    clearTimeout(hint._t);
    if (ms) hint._t = setTimeout(() => { el.style.display = 'none'; if (tool) toolHint(); }, ms);
  }

  function toolHint() {
    const s = SYM[tool.symId];
    if (s.geometry === 'point') hint(`单击地图放置「${s.name}」（可连续放置），Esc 结束`);
    else hint(`「${s.name}」：依次单击各点，双击或 Enter 结束，Esc 取消（已 ${tool.pts.length} 点）`);
  }

  function startTool(symId) {
    cancelTool();
    select(null);
    tool = { symId, pts: [] };
    map.doubleClickZoom.disable();
    $('map').style.cursor = 'crosshair';
    renderAll(); renderPalette(); toolHint();
  }

  function cancelTool() {
    tool = null;
    drawLayer.clearLayers(); rubber = null;
    map.doubleClickZoom.enable();
    $('map').style.cursor = '';
    hint('');
    renderAll(); renderPalette();
  }

  function redrawTemp(cursor) {
    drawLayer.clearLayers();
    const s = SYM[tool.symId];
    const pts = cursor ? [...tool.pts, cursor] : tool.pts;
    if (pts.length > 1) {
      const Ctor = s.geometry === 'polygon' && pts.length > 2 ? L.polygon : L.polyline;
      Ctor(pts, { renderer, color: '#1565c0', weight: 2, dashArray: '5,5', fillOpacity: 0.08, interactive: false }).addTo(drawLayer);
    }
    tool.pts.forEach(p => L.circleMarker(p, { renderer, radius: 4, color: '#1565c0', fillColor: '#fff', fillOpacity: 1, weight: 2, interactive: false }).addTo(drawLayer));
  }

  function addFeature(symId, type, coords, props = {}) {
    const s = SYM[symId];
    const f = {
      id: uid(), sym: symId, type, coords,
      props: { label: s.glyph_path ? s.label : undefined, note: '', time: '', rotation: 0, scale: 1, opacity: 1, ...props },
    };
    features.push(f);
    return f;
  }

  function finishShape() {
    const s = SYM[tool.symId];
    // 双击会先触发两次单击：去掉屏幕上几乎重合的相邻点
    const pts = tool.pts.filter((p, i, a) => i === 0 ||
      map.latLngToLayerPoint(p).distanceTo(map.latLngToLayerPoint(a[i - 1])) > 4);
    const min = s.geometry === 'polygon' ? 3 : 2;
    if (pts.length < min) return hint(`至少需要 ${min} 个点`, 1500);
    const f = addFeature(tool.symId, s.geometry === 'polygon' ? 'polygon' : 'line', pts.map(p => [p.lat, p.lng]));
    tool.pts = [];
    drawLayer.clearLayers();
    commit();
    const id = f.id;
    cancelTool();
    select(id);
  }

  map.on('click', e => {
    if (!tool) { select(null); return; }
    const s = SYM[tool.symId];
    if (s.geometry === 'point') {
      const f = addFeature(tool.symId, 'point', [[e.latlng.lat, e.latlng.lng]]);
      commit(); renderAll();
      selectedId = f.id; renderProps();
      return;
    }
    tool.pts.push(e.latlng);
    redrawTemp(); toolHint();
  });
  map.on('mousemove', e => { if (tool && tool.pts.length) redrawTemp(e.latlng); });
  map.on('dblclick', e => { if (tool && SYM[tool.symId].geometry !== 'point') { L.DomEvent.stop(e); finishShape(); } });

  document.addEventListener('keydown', e => {
    const typing = /INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName);
    if (e.key === 'Escape') { if (tool) cancelTool(); else select(null); }
    else if (e.key === 'Enter' && tool && !typing) finishShape();
    else if ((e.key === 'Delete' || e.key === 'Backspace') && selectedId && !typing) { e.preventDefault(); removeSelected(); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'z' && !typing) { e.preventDefault(); e.shiftKey ? redo() : undo(); }
    else if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'y' && !typing) { e.preventDefault(); redo(); }
  });

  // ---------------------------------------------------------------- 选择与属性

  function select(id) {
    selectedId = id;
    renderAll(); renderProps();
  }

  function removeSelected() {
    features = features.filter(f => f.id !== selectedId);
    selectedId = null;
    renderAll(); renderProps(); commit();
  }

  function field(label, html, tpl) {
    return `<label class="field"><span${tpl ? ` data-tpl="${tpl}"` : ''}>${label}</span>${html}</label>`;
  }
  const rangeText = (k, v) => (k === 'opacity' ? Math.round(v * 100) : v);
  const val = v => escapeXml(v == null ? '' : v);

  function renderProps() {
    const f = features.find(x => x.id === selectedId);
    $('props-empty').hidden = !!f;
    $('props-form').hidden = !f;
    if (!f) return;
    const s = SYM[f.sym], p = f.props, attrs = s.attributes || [];
    const icon = f.type === 'point' ? pointSvg(f) : s.svg;
    let h = `<div class="pf-head"><span class="ic">${icon}</span><div><div class="nm">${escapeXml(s.name)}</div>
      <div class="src">${escapeXml(s.source)} ${escapeXml(s.preset_of || s.std_code || s.id)}</div></div></div>`;
    if (s.glyph_path) {
      const opts = (SYM['GB-' + (s.preset_of || s.std_code)] || s).sub_labels || [];
      h += field('标识文字（2~4 字，GB/T 35649 5.1）',
        `<input data-k="label" value="${val(p.label)}" list="dl-sub"><datalist id="dl-sub">${opts.map(o => `<option value="${escapeXml(o)}">`).join('')}</datalist>`);
    }
    h += field(f.type === 'point' ? '注记（显示在符号下方，如番号、单位）' : '注记（显示在线/面中部）', `<input data-k="note" value="${val(p.note)}">`);
    if (attrs.includes('count') || attrs.includes('headcount')) h += field('人数', `<input data-k="count" type="number" min="0" value="${val(p.count)}">`);
    if (attrs.includes('equipment')) h += field('装备', `<input data-k="equipment" value="${val(p.equipment)}">`);
    if (attrs.includes('task')) h += field('任务', `<input data-k="task" value="${val(p.task)}">`);
    h += field('时间（XF/T 3013 4.5.7 格式）', `<div class="inline"><input data-k="time" value="${val(p.time)}" placeholder="2026.09.29.0830"><button type="button" id="btn-now">现在</button></div>`);
    if (f.type === 'point') {
      h += `<div class="row2">${field(`旋转 ${p.rotation || 0}°`, `<input data-k="rotation" type="range" min="-180" max="180" step="5" value="${p.rotation || 0}">`, '旋转 {v}°')}
        ${field(`大小 ×${p.scale || 1}`, `<input data-k="scale" type="range" min="0.5" max="3" step="0.1" value="${p.scale || 1}">`, '大小 ×{v}')}</div>`;
    }
    h += field(`透明度 ${Math.round((p.opacity ?? 1) * 100)}%（GB/T 35649 6.5）`, `<input data-k="opacity" type="range" min="0.2" max="1" step="0.05" value="${p.opacity ?? 1}">`, '透明度 {v}%（GB/T 35649 6.5）');
    h += field('备注', `<textarea data-k="remark">${val(p.remark)}</textarea>`);
    if (s.description) h += `<p class="muted">${escapeXml(s.description)}</p>`;
    h += `<div class="pf-actions"><button id="btn-del" class="danger">删除</button><button id="btn-dup">复制</button></div>`;
    $('props-form').innerHTML = h;
  }

  const NUM = new Set(['rotation', 'scale', 'opacity', 'count']);
  $('props-form').addEventListener('input', e => {
    const k = e.target.dataset.k, f = features.find(x => x.id === selectedId);
    if (!k || !f) return;
    f.props[k] = NUM.has(k) && e.target.value !== '' ? Number(e.target.value) : e.target.value;
    renderAll();
    const span = e.target.closest('.field').querySelector('span[data-tpl]');
    if (span) span.textContent = span.dataset.tpl.replace('{v}', rangeText(k, f.props[k]));
  });
  $('props-form').addEventListener('change', e => { if (e.target.dataset.k) commit(); });
  $('props-form').addEventListener('click', e => {
    const f = features.find(x => x.id === selectedId);
    if (!f) return;
    if (e.target.id === 'btn-del') removeSelected();
    if (e.target.id === 'btn-now') { f.props.time = nowStamp(); renderAll(); renderProps(); commit(); }
    if (e.target.id === 'btn-dup') {
      const d = 0.0006;
      const c = addFeature(f.sym, f.type, f.coords.map(([a, b]) => [a - d, b + d]), JSON.parse(JSON.stringify(f.props)));
      renderAll(); commit(); select(c.id);
    }
  });

  // ---------------------------------------------------------------- 图廓：标题、时间、指北针、图例

  function updateTitleBlock() {
    $('tb-title').textContent = $('title').value;
    const t = nowStamp();
    $('tb-time').textContent = `制图时间：${t.slice(0, 4)}年${t.slice(5, 7)}月${t.slice(8, 10)}日 ${t.slice(11, 13)}:${t.slice(13, 15)}`;
    document.title = $('title').value || '抢险救援标绘';
  }
  $('title').addEventListener('input', updateTitleBlock);
  $('title').addEventListener('change', commit);
  $('north').innerHTML = (SYM['XF-6.3.2'] || {}).svg || '';

  function renderLegend() {
    const seen = new Map();
    features.forEach(f => {
      const s = SYM[f.sym];
      if (!s) return;
      const key = f.sym + '|' + (f.props.label || '');
      if (!seen.has(key)) seen.set(key, { name: s.glyph_path ? (f.props.label || s.name) : s.name, svg: f.type === 'point' ? pointSvg(f) : s.svg });
    });
    $('legend-items').innerHTML = [...seen.values()].map(i =>
      `<div class="lg-item"><span class="ic">${i.svg}</span>${escapeXml(i.name)}</div>`).join('');
  }
  $('show-legend').addEventListener('change', e => { $('legend').hidden = !e.target.checked; });

  // ---------------------------------------------------------------- 文件：保存 / 打开 / 打印 / 演示 / 清空

  const saveHooks = [], loadHooks = [];

  function toGeoJSON() {
    const extra = Object.assign({}, ...saveHooks.map(h => h()));
    return {
      ...extra,
      type: 'FeatureCollection',
      title: $('title').value,
      generator: '抢险救援标绘 ' + LIB.version,
      features: features.map(f => ({
        type: 'Feature',
        id: f.id,
        properties: { symbol: f.sym, symbol_name: SYM[f.sym].name, ...f.props },
        geometry: f.type === 'point'
          ? { type: 'Point', coordinates: [f.coords[0][1], f.coords[0][0]] }
          : f.type === 'line'
            ? { type: 'LineString', coordinates: f.coords.map(([a, b]) => [b, a]) }
            : { type: 'Polygon', coordinates: [[...f.coords, f.coords[0]].map(([a, b]) => [b, a])] },
      })),
    };
  }

  function fromGeoJSON(gj) {
    const out = [], skipped = [];
    (gj.features || []).forEach(ft => {
      const { symbol, symbol_name, ...props } = ft.properties || {};
      if (!SYM[symbol]) { skipped.push(symbol); return; }
      const g = ft.geometry;
      let type, coords;
      if (g.type === 'Point') { type = 'point'; coords = [[g.coordinates[1], g.coordinates[0]]]; }
      else if (g.type === 'LineString') { type = 'line'; coords = g.coordinates.map(([x, y]) => [y, x]); }
      else if (g.type === 'Polygon') { type = 'polygon'; coords = g.coordinates[0].slice(0, -1).map(([x, y]) => [y, x]); }
      else { skipped.push(g.type); return; }
      out.push({ id: ft.id || uid(), sym: symbol, type, coords, props });
    });
    return { features: out, skipped };
  }

  function loadData(gj, fit = true) {
    const { features: fs, skipped } = fromGeoJSON(gj);
    features = fs;
    loadHooks.forEach(h => h(gj));
    $('title').value = gj.title || $('title').value;
    selectedId = null;
    updateTitleBlock(); renderAll(); renderProps(); commit();
    if (fit && features.length) {
      const b = L.latLngBounds(features.flatMap(f => f.coords));
      map.fitBounds(b.pad(0.08));
    }
    if (skipped.length) alert(`有 ${skipped.length} 个要素的符号不在当前符号库中，已跳过：\n${[...new Set(skipped)].join('、')}`);
  }

  $('btn-save').addEventListener('click', () => {
    const blob = new Blob([JSON.stringify(toGeoJSON(), null, 1)], { type: 'application/geo+json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${($('title').value || '标绘').replace(/[\\/:*?"<>|]/g, '_')}_${nowStamp()}.geojson`;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  });
  $('btn-open').addEventListener('click', () => $('file-open').click());
  $('file-open').addEventListener('change', e => {
    const f = e.target.files[0];
    if (!f) return;
    const rd = new FileReader();
    rd.onload = () => {
      try { loadData(JSON.parse(rd.result)); } catch (err) { alert('文件无法解析：' + err.message); }
    };
    rd.readAsText(f, 'utf-8');
    e.target.value = '';
  });
  $('btn-print').addEventListener('click', () => {
    select(null); updateTitleBlock();
    setTimeout(() => { map.invalidateSize(); window.print(); }, 100);
  });
  window.addEventListener('afterprint', () => map.invalidateSize());
  $('btn-demo').addEventListener('click', () => {
    if (features.length && !confirm('载入演示数据会替换当前标绘，是否继续？（可撤销）')) return;
    loadData(window.DEMO_PLOT);
  });
  $('btn-clear').addEventListener('click', () => {
    if (!features.length || !confirm('清空全部标绘？（可撤销）')) return;
    features = []; selectedId = null; renderAll(); renderProps(); commit();
  });

  // ---------------------------------------------------------------- 启动

  renderTabs(); renderPalette();
  const bm = localGet('basemap') || 'imglabel';
  $('basemap').value = bm === 'custom' ? 'none' : bm;
  setBasemap($('basemap').value);
  const saved = localGet(STORE_KEY);
  if (saved) {
    try { restore(saved); } catch (e) { /* 损坏的缓存直接忽略 */ }
  }
  updateTitleBlock();
  commit();
  if (features.length) map.fitBounds(L.latLngBounds(features.flatMap(f => f.coords)).pad(0.15));

  // 供调试与后续“智能标图”调用
  function removeFeature(id) {
    features = features.filter(f => f.id !== id);
    if (selectedId === id) selectedId = null;
  }

  // 供调试与“智能标图”（smart.js）调用；批量修改后调用 renderAll() + commit() 形成一步可撤销操作
  window.plotApp = {
    map, LIB, SYM, get features() { return features; },
    loadData, toGeoJSON, addFeature, removeFeature, renderAll, renderProps, commit, select, hint,
    onSave: fn => saveHooks.push(fn), onLoad: fn => loadHooks.push(fn),
  };
})();
