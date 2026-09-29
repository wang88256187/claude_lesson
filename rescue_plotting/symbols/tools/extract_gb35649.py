"""从 GB/T 35649-2017 PDF 附录 A 提取点状符号，矢量化为 gb35649_points.json。

流程：
1. 以 600 dpi 渲染附录 A 页面（PDF 第 10–19 页），按饱和度找出彩色像素；
2. 连通域定位每个符号的外框，按页面顺序与 CATALOG 一一对应（共 60 个）；
3. 按外框的圆角/直角形状和实测线宽扣除外框，按空白行切掉底部标识文字；
4. 用 potrace 把剩下的"符号主体"描成 SVG 路径，坐标归一到 32×32（标准 6.2.1）。

外框与标识文字不描摹，由 build_symbols.py 按标准 6.2.1 重建，
从而可以替换子类文字（如 A10400 地质灾害 → “泥石流”）。

用法：
    pip install pymupdf numpy scipy potracer
    python tools/extract_gb35649.py ../refs/gbt35649.pdf
"""

import json
import sys
from pathlib import Path

import numpy as np
import potrace
import pymupdf
from scipy import ndimage

DPI = 600
PAGES = range(9, 19)  # 0-based：PDF 第 10–19 页为附录 A
OUT = Path(__file__).resolve().parent.parent / "gb35649_points.json"

# (编码, 名称, 标识文字, 子类文字标识)；按附录 A 表格顺序
CATALOG = [
    ("A10100", "水旱灾害", "水旱灾害", "洪水、内涝、水库险情、堤防险情、凌汛灾害、山洪、农业干旱、城镇缺水、生态干旱、饮水困难"),
    ("A10200", "气象灾害", "气象灾害", "台风、龙卷风、暴雨、雪灾、寒潮、大风、沙尘暴、低温冻害、冻雨、高温天气、热浪、干热风、下击暴流、雪崩、雷电、冰雹、霜冻、大雾、霾、风切变"),
    ("A10300", "地震灾害", "地震灾害", "人工地震、天然地震"),
    ("A10400", "地质灾害", "地质灾害", "滑坡、泥石流、崩塌、塌陷、地裂、地面沉降、火山喷发、海(咸)水入侵"),
    ("A10500", "海洋灾害", "海洋灾害", "海啸、风暴潮、海冰、巨浪、赤潮、绿潮"),
    ("A10600", "森林火灾", "森林火灾", "境内火灾、跨境火灾、境外威胁"),
    ("A10700", "草原火灾", "草原火灾", "境内火灾、跨境火灾、境外威胁"),
    ("A20100", "煤矿事故", "煤矿事故", "瓦斯、顶板、运输、水害、机电、放炮、火灾事故"),
    ("A20200", "金属与非金属矿山事故", "金属矿山", "顶板、运输、水害、中毒窒息、尾矿垮坝、火灾、机电、火药爆炸"),
    ("A20300", "建筑业事故", "施工安全", "施工安全"),
    ("A20400", "危险化学品事故", "危化品", "爆炸、泄漏、火灾、中毒窒息、灼烫"),
    ("A20500", "烟花爆竹和民用爆炸物事故", "烟花爆竹", "生产爆炸、运输爆炸、民用爆炸"),
    ("A20600", "火灾事故", "火灾事故", "一般工业、特种工业、一般民用、高层民用、地下建筑、公用建筑、隧道"),
    ("A20700", "道路交通事故", "道路交通", "撞车、翻车、坠水坠沟、车辆起火、校车"),
    ("A20800", "水上交通事故", "水上事故", "碰撞、触礁、搁浅、风灾、火灾、船舶失踪、海上遇险、渔业设施"),
    ("A20900", "铁路交通事故", "铁路事故", "脱轨、追尾、撞车、撞人、火灾、爆炸"),
    ("A21000", "城市轨道事故", "城市轨道", "脱轨、追尾、撞车、撞人、火灾、爆炸"),
    ("A21100", "民用航空器飞行事故", "飞行事故", "坠机、撞机、刮蹭、航班延误"),
    ("A21200", "特种设备事故", "特种设备", "锅炉、压力容器、压力管道、电梯、起重机械、客运索道、游乐设施"),
    ("A21300", "基础设施和公用设施事故", "基础设施", "公路设施、铁路设施、城轨设施、桥梁隧道、水运交通、民航设施、水利设施、电力设施、油气设施、通讯设施、金融设施、生命线、建筑垮塌"),
    ("A21400", "环境污染和生态破坏事故", "环境污染", "水域污染、空气污染、土壤污染、海上溢油、供水中断、种群死亡、生态破坏、危险废物"),
    ("A21500", "农业机械事故", "农业机械", "行驶事故、作业事故、碾压事件、碰撞事件、翻车事件、落车事件、火灾事件、机械事故"),
    ("A21600", "踩踏事件", "踩踏", "活动踩踏、校园踩踏"),
    ("A30100", "传染病事件", "传染病", "鼠疫、霍乱、肺炭疽、非典、禽流感"),
    ("A30200", "食品药品安全事件", "食药安全", "药品安全、食品安全"),
    ("A30300", "群体性中毒、感染事件", "感染事件", "职业中毒、重金属"),
    ("A30400", "动物疫情事件", "动物疫情", "禽流感、口蹄疫、疯牛病、狂犬病、动物炭疽"),
    ("A40100", "金融突发事件", "金融事件", "银行业、证券业、保险业"),
    ("A40200", "信息安全事件", "信息安全", "病毒传播、网络攻击"),
    ("A40300", "恐怖袭击事件", "恐怖袭击", ""),
    ("A40400", "核辐射事故", "辐射事故", ""),
    ("A40500", "大规模集会事件", "集会事件", ""),
    ("B10100", "生产安全危险源", "生产安全", "贮罐、库区、生产场所、压力管道、锅炉、压力容器、煤矿、非煤矿山、尾矿库、气瓶充装、加油站、油气田"),
    ("B10200", "运输安全危险源", "运输安全", "危化车辆、危化船舶、油轮"),
    ("B10300", "环境污染危险源", "环境污染", "污染源、放射源、危险废物"),
    ("C10100", "党政机关", "", ""),
    ("C10200", "学校", "", ""),
    ("C10300", "新闻广播机构", "", ""),
    ("C10400", "公众聚集场所", "", ""),
    ("C10500", "金融机构", "", ""),
    ("C10600", "重要场所", "", "重点居住、外交场所、文物保护、储备物资"),
    ("C20100", "铁路基础设施", "", ""),
    ("C20200", "水运交通基础设施", "", ""),
    ("C20300", "民航交通设施", "", ""),
    ("C20400", "通讯基础设施", "", ""),
    ("C20500", "水利设施", "", ""),
    ("C20600", "电力基础设施", "", ""),
    ("C20700", "石油天然气设施", "", ""),
    ("D10100", "现场指挥部", "现场指挥", "防汛抗旱、抗震救灾、地质灾害、森林防火、民航事故、公共卫生、动物疫情、食品安全、粮食应急"),
    ("D10200", "应急临时机构", "临时机构", "临时安置、物资发放、临时医疗、临时取水"),
    ("D20100", "军队", "军队", ""),
    ("D20200", "武警", "武警", ""),
    ("D20300", "人民警察", "警察", ""),
    ("D20400", "救援队", "救援队", "矿山救护、危化救援、地震救援、海上搜救"),
    ("D30100", "物资储备库", "物资储备", "粮食储备、医药储备"),
    ("D40100", "运输场站", "运输场站", "机场、港口码头、火车站、汽车站"),
    ("D40200", "救援车辆", "救援车辆", "客运车辆、货运车辆、专用作业"),
    ("D50100", "医疗机构", "医疗机构", "综合医院、专科医院、急救中心、社区医疗"),
    ("D50200", "疾控中心", "疾控中心", "疾控中心"),
    ("D60100", "避难场所", "避难场所", "避难场所"),
]


def render(page):
    pix = page.get_pixmap(dpi=DPI)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n)[..., :3]


def find_symbols(img):
    rgb = img.astype(int)
    colored = (rgb.max(-1) - rgb.min(-1)) > 60
    lab, _ = ndimage.label(colored)
    boxes = []
    for sl in ndimage.find_objects(lab):
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if h > 300 and w > 300 and 0.8 < h / w < 1.25:  # 外框
            boxes.append(sl)
    def inside(a, b):  # a 在 b 内
        return a is not b and all(
            b[i].start <= a[i].start and a[i].stop <= b[i].stop for i in range(2)
        )

    boxes = [a for a in boxes if not any(inside(a, b) for b in boxes)]
    boxes.sort(key=lambda s: s[0].start)
    return colored, boxes


def rounded_depth(h, w, r):
    """每个像素到圆角矩形边界的内侧距离。"""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    qx = np.abs(xx + 0.5 - w / 2) - (w / 2 - r)
    qy = np.abs(yy + 0.5 - h / 2) - (h / 2 - r)
    outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0))
    inside = np.minimum(np.maximum(qx, qy), 0)
    return -(outside + inside - r)


def trace(mask, h, w):
    bm = potrace.Bitmap(~mask)  # potracer 以 False 为前景
    path = bm.trace(turdsize=20, alphamax=1.0, opticurve=True, opttolerance=0.2)
    sx, sy = 32 / w, 32 / h

    def p(pt):
        return f"{pt.x * sx:.2f},{pt.y * sy:.2f}"

    parts = []
    for curve in path:
        parts.append(f"M{p(curve.start_point)}")
        for seg in curve:
            if seg.is_corner:
                parts.append(f"L{p(seg.c)}L{p(seg.end_point)}")
            else:
                parts.append(f"C{p(seg.c1)} {p(seg.c2)} {p(seg.end_point)}")
        parts.append("Z")
    return "".join(parts)


def extract(pdf_path):
    doc = pymupdf.open(pdf_path)
    found = []
    for pno in PAGES:
        img = render(doc[pno])
        colored, boxes = find_symbols(img)
        for sl in boxes:
            found.append((img[sl], colored[sl]))
    assert len(found) == len(CATALOG), f"找到 {len(found)} 个符号，应为 {len(CATALOG)}"

    out = []
    for (crop, mask), (code, name, label, subs) in zip(found, CATALOG):
        h, w = mask.shape
        color = np.median(crop[mask], axis=0).astype(int).tolist()
        mid = mask[h // 2]
        t = int(np.argmax(~mid))  # 外框线宽（像素）
        rounded = code.startswith("A")
        k = int(np.argmax([mask[i, i] for i in range(min(h, w) // 3)]))
        r = k / (1 - 2**-0.5) if rounded else 0.0
        frame = rounded_depth(h, w, r) < t * 1.3
        glyph = mask & ~frame
        if label:  # 在 55%–85% 高度内找空白行，切掉底部标识文字
            rows = glyph.sum(1)
            lo, hi = int(h * 0.55), int(h * 0.85)
            cut = lo + int(np.argmin(rows[lo:hi]))
            glyph[cut:] = False
        glyph = ndimage.binary_opening(glyph, iterations=1)
        out.append(
            {
                "code": code,
                "name": name,
                "label": label,
                "sub_labels": [s for s in subs.split("、") if s] if subs else [],
                "rounded": rounded,
                "color_print": "#%02x%02x%02x" % tuple(color),
                "frame_width": round(t / w * 32, 2),
                "corner_radius": round(r / w * 32, 2),
                "glyph_path": trace(glyph, h, w),
            }
        )
        print(code, name, f"t={t}px r={r:.0f}px", out[-1]["color_print"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"写出 {OUT}（{len(out)} 个）")


if __name__ == "__main__":
    extract(sys.argv[1] if len(sys.argv) > 1 else "../refs/gbt35649.pdf")
