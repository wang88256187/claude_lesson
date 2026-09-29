/* 线状、面状符号在地图上的绘制方式（按 GB/T 35649 附录 B/C、XF/T 3013 6.3 的样式）。
 *
 * 线：color/width/dash 为主体线；arrow 为终点箭头（'open' 开口、'filled' 实心、'big' 大实心）；
 *     deco 为沿线按屏幕像素间隔重复的装饰（svg 以线方向为 x 轴绘制，自动旋转）；
 *     startIcon 为起点图标；casing 为同样式白色内线（形成双线效果）。
 * 面：dash 为边线；fill 为填充（颜色+透明度，或 pattern: 'dots'|'hatch'）；
 *     arrows 为沿边线均匀分布的箭头（'in' 指向区域内 / 'out' 指向区域外）。
 */
(function () {
  const R = '#FF0000';      // GB/T 35649 线状、面状统一红色
  const XR = '#E53935';     // XF/T 3013 行动标号红色

  const svg = (w, h, body) =>
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${-w / 2} ${-h / 2} ${w} ${h}">${body}</svg>`;
  const cross = (x, s = 3, c = R) =>
    `<path d="M${x - s},${-s}L${x + s},${s}M${x + s},${-s}L${x - s},${s}" stroke="${c}" stroke-width="1.8"/>`;

  const DECO = {
    xxx: { w: 30, h: 10, svg: svg(30, 10, `<rect x="-14" y="-5" width="28" height="10" fill="#fff"/>` + cross(-8) + cross(0) + cross(8)) },
    ecoCross: { w: 16, h: 16, svg: svg(16, 16, `<path d="M-6,-6L6,6M6,-6L-6,6" stroke="${R}" stroke-width="2"/><path d="M3,-7L6,-6L5,-3" fill="none" stroke="${R}" stroke-width="1.5"/>`) },
    circleArrow: { w: 24, h: 24, svg: svg(24, 24, `<circle r="10" fill="#fff" stroke="${R}" stroke-width="1.5"/><path d="M-8,0H7M2,-4L7,0L2,4" fill="none" stroke="${R}" stroke-width="1.5"/>`) },
    circleBolt: { w: 24, h: 24, svg: svg(24, 24, `<circle r="10" fill="#fff" stroke="${R}" stroke-width="1.5"/><polygon points="2,-8 -5,1 0,1 -2,8 6,-2 1,-2" fill="${R}"/>`) },
    sideDash: { w: 28, h: 26, svg: svg(28, 26, `<path d="M-13,-10H13M-13,10H13" stroke="${R}" stroke-width="2"/>`) },
    ticks: { w: 8, h: 14, svg: svg(8, 14, `<path d="M-1.5,0V-6M1.5,0V-6" stroke="${R}" stroke-width="1.6"/>`) },
    flag: { w: 44, h: 22, svg: svg(44, 22, `<path d="M-20,-10V10" stroke="${R}" stroke-width="2.5"/><polygon points="-20,-6 12,-6 18,0 12,6 -20,6" fill="#fff" stroke="${R}" stroke-width="2"/>`) },
    hexPair: { w: 56, h: 16, svg: svg(56, 16, [-14, 14].map(x => `<polygon points="${x - 12},0 ${x - 6},-6 ${x + 6},-6 ${x + 12},0 ${x + 6},6 ${x - 6},6" fill="#fff" stroke="${R}" stroke-width="2"/>`).join('')) },
  };

  const PERSON = svg(20, 30, `<g fill="none" stroke="${XR}" stroke-width="2"><circle cy="-9" r="4"/><path d="M0,-5V5M-6,-1H6M-5,13L0,5L5,13"/></g>`);

  const LINE_STYLES = {
    'GB-E10100': { color: R, width: 2, deco: { ...DECO.xxx, spacing: 140 } },
    'GB-E10200': { color: R, width: 2, deco: { ...DECO.ecoCross, spacing: 26 } },
    'GB-E20100': { color: R, width: 2, deco: { ...DECO.circleArrow, spacing: 140 } },
    'GB-E20200': { color: R, width: 2, deco: { ...DECO.circleBolt, spacing: 140 } },
    'GB-E20300': { color: R, width: 2, deco: { ...DECO.sideDash, spacing: 42 }, arrow: 'filled' },
    'GB-E20400': { color: R, width: 2, deco: { ...DECO.ticks, spacing: 18 } },
    'GB-E20500': { color: R, width: 4, dash: '5,2', deco: { ...DECO.xxx, spacing: 140 } },
    'GB-E30100': { color: R, width: 2, deco: { ...DECO.flag, spacing: 170 }, arrow: 'filled' },
    'GB-E30200': { color: R, width: 2, deco: { ...DECO.hexPair, spacing: 150 }, arrow: 'filled' },
    'XF-6.3.17': { color: XR, width: 2.5, dash: '10,7', arrow: 'open' },
    'XF-6.3.19': { color: XR, width: 2.5, arrow: 'open', smooth: true },
    'XF-6.3.21': { color: XR, width: 2, arrow: 'open', startIcon: { svg: PERSON, w: 20, h: 30 } },
    'X-L01': { color: R, width: 6, arrow: 'big', smooth: true },
    'X-L02': { color: R, width: 7, dash: '10,5', casing: 3 },
    'X-L03': { color: R, width: 2, dash: '16,6' },
  };

  const AREA_STYLES = {
    'GB-F10100': { color: R, width: 2, dash: '8,2,2,2', fill: { color: R, opacity: 0.03 } },
    'GB-F10200': { color: R, width: 2, fill: { color: R, opacity: 0.03 }, arrows: 'in' },
    'GB-F10300': { color: R, width: 2, fill: { color: R, opacity: 0.03 }, arrows: 'out' },
    'X-F01': { color: R, width: 2, fill: { pattern: 'dots' } },
    'X-F02': { color: R, width: 2.5, fill: { pattern: 'hatch' } },
    'X-F03': { color: R, width: 1.5, fill: { color: R, opacity: 0.06 } },
    'XF-6.3.20': { color: XR, width: 2.5, fill: { color: XR, opacity: 0.04 } },
  };

  // 箭头（以线方向为 x 轴，尖端在原点）
  const ARROWS = {
    open: c => svg(24, 24, `<path d="M-10,-7L0,0L-10,7" fill="none" stroke="${c}" stroke-width="2.5"/>`),
    filled: c => svg(24, 24, `<polygon points="-12,-4 0,0 -12,4 -9,0" fill="${c}"/>`),
    big: c => svg(40, 40, `<polygon points="-18,-11 0,0 -18,11 -13,0" fill="${c}"/>`),
    area: c => svg(20, 20, `<path d="M-7,-3.5L0,0L-7,3.5Z" fill="none" stroke="${c}" stroke-width="1.3"/>`),
  };

  // GB/T 35649 点状符号重建（与 symbols/gb35649.py frame_svg 一致），用于替换标识文字
  const FONT = "font-family='SimHei,Heiti SC,Noto Sans CJK SC,Microsoft YaHei,sans-serif'";
  function gbPointSvg(sym, label, color) {
    const FW = 1.4, CR = 6.9, half = FW / 2;
    color = color || sym.color;
    const rx = sym.rounded ? CR - half : 0;
    let text = '';
    if (label) {
      const size = Math.min(7.2, 29 / [...label].length);
      text = `<text x='16' y='29.4' text-anchor='middle' font-size='${size.toFixed(2)}' font-weight='bold' fill='${color}' ${FONT}>${escapeXml(label)}</text>`;
    }
    return `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>` +
      `<rect x='${half}' y='${half}' width='${32 - FW}' height='${32 - FW}' rx='${rx.toFixed(2)}' fill='#fff' stroke='${color}' stroke-width='${FW}'/>` +
      `<path d='${sym.glyph_path}' fill='${color}' fill-rule='evenodd'/>${text}</svg>`;
  }

  function escapeXml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  window.PLOT_STYLES = { LINE_STYLES, AREA_STYLES, ARROWS, gbPointSvg, escapeXml };
})();
