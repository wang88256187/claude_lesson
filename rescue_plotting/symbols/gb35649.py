"""GB/T 35649-2017《突发事件应急标绘符号规范》符号。

- 点状（附录 A，60 个）：符号主体来自 gb35649_points.json（由 tools/extract_gb35649.py
  从标准原图矢量化），外框与标识文字按标准 5.1、6.2.1 重建：
  32×32，突发事件圆角正方形、其余直角正方形，标识文字限外框下部 1/4、黑体加粗、2~4 字。
- 线状（附录 B，7 个）和面状（附录 C，3 个）：按标准给出的像素参数绘制，统一红色（6.1.2）。

颜色（表 3）：突发事件红 (255,0,0)、危险源黄 (255,255,0)、防护目标蓝 (0,0,255)、
应急保障资源绿 (0,255,0)；线状、面状红 (255,0,0)。另记录了标准印刷稿中的实际颜色
color_print，屏幕显示时可按需切换。
"""

import json
from pathlib import Path

STD = "GB/T 35649-2017"
DATA = Path(__file__).parent / "gb35649_points.json"

COLOR_STD = {"A": "#FF0000", "B": "#FFFF00", "C": "#0000FF", "D": "#00FF00"}
LINE_RED = "#FF0000"
FONT = "font-family='SimHei,Heiti SC,Noto Sans CJK SC,Microsoft YaHei,sans-serif'"

# 外框参数取标准印刷稿实测中位数（32 单位制）
FRAME_W = 1.4
CORNER_R = 6.9

CLASSES = {
    "A1": "突发事件 · 自然灾害",
    "A2": "突发事件 · 事故灾难",
    "A3": "突发事件 · 公共卫生事件",
    "A4": "突发事件 · 社会安全事件",
    "B1": "危险源 · 事故灾难危险源",
    "C1": "防护目标 · 重要部位",
    "C2": "防护目标 · 关键基础设施",
    "D1": "应急保障资源 · 应急机构",
    "D2": "应急保障资源 · 应急人力资源",
    "D3": "应急保障资源 · 应急物资与装备资源",
    "D4": "应急保障资源 · 应急运输与物流资源",
    "D5": "应急保障资源 · 医疗卫生资源",
    "D6": "应急保障资源 · 应急避难场区",
    "E1": "线状 · 隔离符号",
    "E2": "线状 · 道路及基础设施符号",
    "E3": "线状 · 行动路线符号",
    "F1": "面状 · 区域标识符号",
}


def frame_svg(color, rounded, body, label=""):
    """按标准 5.1、6.2.1 生成点状符号：外框 + 符号主体 body（32 单位制 SVG 片段）+ 标识文字。"""
    half = FRAME_W / 2
    rx = CORNER_R - half if rounded else 0
    text = ""
    if label:
        size = min(7.2, 29 / len(label))
        text = (
            f"<text x='16' y='29.4' text-anchor='middle' font-size='{size:.2f}' "
            f"font-weight='bold' fill='{color}' {FONT}>{label}</text>"
        )
    return (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'>"
        f"<rect x='{half}' y='{half}' width='{32 - FRAME_W}' height='{32 - FRAME_W}' "
        f"rx='{rx:.2f}' fill='#fff' stroke='{color}' stroke-width='{FRAME_W}'/>"
        f"{body}{text}</svg>"
    )


def point_svg(entry, label=None, color=None):
    """重建标准点状符号。label 传子类文字（如"泥石流"）可替换标识文字。"""
    code = entry.get("code") or entry["std_code"]
    color = color or COLOR_STD[code[0]]
    label = entry["label"] if label is None else label
    body = f"<path d='{entry['glyph_path']}' fill='{color}' fill-rule='evenodd'/>"
    return frame_svg(color, entry["rounded"], body, label)


def _points():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    out = []
    for e in entries:
        code = e["code"]
        out.append(
            {
                "id": f"GB-{code}",
                "std_code": code,
                "source": STD,
                "official": True,
                "name": e["name"],
                "geometry": "point",
                "category": code[:2],
                "color": COLOR_STD[code[0]],
                "color_print": e["color_print"],
                "label": e["label"],
                "sub_labels": e["sub_labels"],
                "rounded": e["rounded"],
                "glyph_path": e["glyph_path"],
                "svg": point_svg(e),
                "description": ("子类文字标识：" + "、".join(e["sub_labels"]))
                if e["sub_labels"]
                else "",
                "attributes": ["label", "time", "remark"],
            }
        )
    return out


# ---------------- 附录 B 线状、附录 C 面状 ----------------


def _svg_wide(body, h=32):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 {h}'>{body}</svg>"


R = LINE_RED


def _x(cx, cy, s=3):
    return (
        f"<path d='M{cx - s},{cy - s}L{cx + s},{cy + s}M{cx + s},{cy - s}L{cx - s},{cy + s}' "
        f"stroke='{R}' stroke-width='1.6'/>"
    )


def _arrowhead(x, y):
    """箭头部分长 12 高 8（B.2、B.3）。"""
    return f"<polygon points='{x - 12},{y - 4} {x},{y} {x - 12},{y + 4} {x - 9},{y}' fill='{R}'/>"


LINE_PREVIEW = {
    # E10100 隔离线："×"高 6、间距 2，两端突出 2
    "E10100": _svg_wide(
        f"<path d='M8,14V16H36M60,16H88V14' fill='none' stroke='{R}' stroke-width='2'/>"
        + _x(40, 16) + _x(48, 16) + _x(56, 16)
    ),
    # E10200 生态隔离线：主体 90° 折线 + 箭形交叉
    "E10200": _svg_wide(
        "<polyline points='6,24 16,10 26,24 36,10 46,24 56,10 66,24 76,10 86,24' "
        f"fill='none' stroke='{R}' stroke-width='2'/>"
        + "".join(
            f"<path d='M{x - 6},{12}L{x + 6},{22}' stroke='{R}' stroke-width='2'/>"
            for x in (11, 31, 51, 71)
        )
    ),
    # E20100 通信光缆线路：直径 20~25 的圆 + 箭头，线宽 1
    "E20100": _svg_wide(
        f"<line x1='4' y1='16' x2='92' y2='16' stroke='{R}' stroke-width='2'/>"
        f"<circle cx='48' cy='16' r='11' fill='#fff' stroke='{R}' stroke-width='1.5'/>"
        f"<line x1='38' y1='16' x2='56' y2='16' stroke='{R}' stroke-width='1.5'/>"
        f"<polyline points='50,11 57,16 50,21' fill='none' stroke='{R}' stroke-width='1.5'/>"
    ),
    # E20200 输电线路：圆 + 闪电
    "E20200": _svg_wide(
        f"<line x1='4' y1='16' x2='92' y2='16' stroke='{R}' stroke-width='2'/>"
        f"<circle cx='48' cy='16' r='11' fill='#fff' stroke='{R}' stroke-width='1.5'/>"
        f"<polygon points='50,7 42,18 48,18 45,25 54,13 48,13' fill='{R}'/>"
    ),
    # E20300 疏通道路：上下短线长 25~30、间距 10~15，距主体 10；箭头长 12 高 8
    "E20300": _svg_wide(
        f"<line x1='6' y1='16' x2='82' y2='16' stroke='{R}' stroke-width='2'/>"
        + "".join(
            f"<line x1='{x}' y1='{y}' x2='{x + 26}' y2='{y}' stroke='{R}' stroke-width='2'/>"
            for x in (12, 50)
            for y in (6, 26)
        )
        + _arrowhead(92, 16)
    ),
    # E20400 危险路段：双短线高 6、间距 2，每组间距 15~20
    "E20400": _svg_wide(
        f"<line x1='4' y1='20' x2='92' y2='20' stroke='{R}' stroke-width='2'/>"
        + "".join(
            f"<path d='M{x},20V14M{x + 3},20V14' stroke='{R}' stroke-width='1.6'/>"
            for x in (14, 32, 50, 68, 86)
        )
    ),
    # E20500 遭破坏的道路：方点虚线 + "×××"（高 6、间距 4）
    "E20500": _svg_wide(
        f"<line x1='4' y1='16' x2='34' y2='16' stroke='{R}' stroke-width='4' stroke-dasharray='5,2'/>"
        f"<line x1='62' y1='16' x2='92' y2='16' stroke='{R}' stroke-width='4' stroke-dasharray='5,2'/>"
        + _x(40, 16) + _x(48, 16) + _x(56, 16)
    ),
    # E30100 救援车辆行进路线：竖线 + 五边形旗（长 35~45，竖线高 ≤20）+ 箭头
    "E30100": _svg_wide(
        f"<line x1='4' y1='16' x2='90' y2='16' stroke='{R}' stroke-width='2'/>"
        f"<line x1='30' y1='6' x2='30' y2='26' stroke='{R}' stroke-width='2.5'/>"
        f"<polygon points='30,10 62,10 68,16 62,22 30,22' fill='#fff' stroke='{R}' stroke-width='2'/>"
        + _arrowhead(94, 16)
    ),
    # E30200 灾民撤离线路：每两个菱形（长 25~30、高 ≤20）为一组 + 箭头
    "E30200": _svg_wide(
        f"<line x1='4' y1='16' x2='90' y2='16' stroke='{R}' stroke-width='2'/>"
        + "".join(
            f"<polygon points='{x},16 {x + 6},10 {x + 18},10 {x + 24},16 {x + 18},22 {x + 6},22' "
            f"fill='#fff' stroke='{R}' stroke-width='2'/>"
            for x in (18, 48)
        )
        + _arrowhead(94, 16)
    ),
}

LINE_STYLE = {
    "E10100": {"stroke": R, "width": 2, "marker": "xxx", "marker_spacing": "manual", "end_ticks": 2},
    "E10200": {"stroke": R, "width": 2, "pattern": "zigzag-90", "cross_arrow_angle": 20, "inner_stroke_len": [20, 25]},
    "E20100": {"stroke": R, "width": 2, "marker": "circle-arrow", "marker_diameter": [20, 25], "marker_stroke": 1},
    "E20200": {"stroke": R, "width": 2, "marker": "circle-lightning", "marker_diameter": [20, 25], "marker_stroke": 1},
    "E20300": {"stroke": R, "width": 2, "side_dashes": {"length": [25, 30], "gap": [10, 15], "offset": 10}, "arrow_end": [12, 8]},
    "E20400": {"stroke": R, "width": 2, "ticks": {"height": 6, "pair_gap": 2, "group_spacing": [15, 20]}},
    "E20500": {"stroke": R, "width": 4, "dash": "5,2", "marker": "xxx", "marker_gap": 4},
    "E30100": {"stroke": R, "width": 2, "marker": "flag-pentagon", "marker_length": [35, 45], "marker_height_max": 20, "arrow_end": [12, 8]},
    "E30200": {"stroke": R, "width": 2, "marker": "hexagon-pair", "marker_length": [25, 30], "marker_height_max": 20, "arrow_end": [12, 8]},
}

LINES = [
    ("E10100", "E1", "隔离线", "“×”高 6 像素、间距 2 像素；两端突出 2 像素；自行掌握间距，间断标记"),
    ("E10200", "E1", "生态隔离线", "箭头高 10 像素、夹角 20°；主体夹角 90°；折线内线划长 20~25 像素"),
    ("E20100", "E2", "通信光缆线路", "圆直径 20~25 像素、线宽 1；箭头长 12 高 8；间断标记"),
    ("E20200", "E2", "输电线路", "圆直径 20~25 像素、线宽 1；间断标记"),
    ("E20300", "E2", "疏通道路", "上下短线长 25~30、间距 10~15，距主体 10 像素；箭头长 12 高 8"),
    ("E20400", "E2", "危险路段", "双短线高 6、间距 2；每组间距 15~20 像素"),
    ("E20500", "E2", "遭破坏的道路", "“×”高 6、间距 4 像素；间断标记"),
    ("E30100", "E3", "救援车辆行进路线", "旗形长 35~45 像素，左侧竖线高 ≤20；箭头长 12 高 8；间断标记"),
    ("E30200", "E3", "灾民撤离线路", "菱形长 25~30、高 ≤20，每两个一组；箭头长 12 高 8；间断标记"),
]

AREA_BLOB = "M20,34 C10,20 30,6 52,6 C76,6 88,20 84,30 C80,40 62,34 54,44 C46,54 28,48 20,34 Z"


def _area_arrows(inward):
    # 4 个箭头均匀分布，高 20 像素（此处按比例缩小）、夹角 40°
    pts = [(52, 6, 0, 1), (84, 30, -1, 0), (40, 50, 0, -1), (20, 34, 1, 0)]
    out = ""
    for x, y, dx, dy in pts:
        s = 1 if inward else -1
        tipx, tipy = x + dx * 5 * s, y + dy * 5 * s
        bx, by = x - dx * 1 * s, y - dy * 1 * s
        px, py = -dy * 2.2, dx * 2.2
        out += (
            f"<polygon points='{tipx},{tipy} {bx + px},{by + py} {bx - px},{by - py}' "
            f"fill='none' stroke='{R}' stroke-width='1'/>"
        )
    return out


AREA_PREVIEW = {
    "F10100": _svg_wide(
        f"<path d='{AREA_BLOB}' fill='none' stroke='{R}' stroke-width='1.2' "
        "stroke-dasharray='7,1,1.5,1'/>",
        56,
    ),
    "F10200": _svg_wide(
        f"<path d='{AREA_BLOB}' fill='none' stroke='{R}' stroke-width='1.2'/>" + _area_arrows(True), 56
    ),
    "F10300": _svg_wide(
        f"<path d='{AREA_BLOB}' fill='none' stroke='{R}' stroke-width='1.2'/>" + _area_arrows(False), 56
    ),
}

AREAS = [
    ("F10100", "警戒区域", "点划线边缘：长划 6~8 像素、短划 1~2 像素、间隔 1 像素",
     {"stroke": R, "width": 2, "dash": "7,1,1.5,1"}),
    ("F10200", "事故控制区域", "箭头 4 个均匀分布，高 20 像素，夹角 40°（指向区域内）",
     {"stroke": R, "width": 2, "arrows": {"count": 4, "height": 20, "angle": 40, "direction": "inward"}}),
    ("F10300", "事故蔓延区域", "箭头 4 个均匀分布，高 20 像素，夹角 40°（指向区域外）",
     {"stroke": R, "width": 2, "arrows": {"count": 4, "height": 20, "angle": 40, "direction": "outward"}}),
]


def _lines_areas():
    out = []
    for code, cls, name, desc in LINES:
        out.append({
            "id": f"GB-{code}", "std_code": code, "source": STD, "official": True,
            "name": name, "geometry": "line", "category": cls, "color": R,
            "style": LINE_STYLE[code], "svg": LINE_PREVIEW[code],
            "description": desc, "attributes": ["label", "time", "remark"],
        })
    for code, name, desc, style in AREAS:
        out.append({
            "id": f"GB-{code}", "std_code": code, "source": STD, "official": True,
            "name": name, "geometry": "polygon", "category": "F1", "color": R,
            "style": style, "svg": AREA_PREVIEW[code],
            "description": desc, "attributes": ["label", "time", "remark"],
        })
    return out


SYMBOLS = _points() + _lines_areas()

RULES = {
    "point_frame": "突发事件：圆角正方形；危险源、防护目标、应急保障资源：直角正方形",
    "point_size": "最小 32×32 像素；边框 ≥1 像素；圆角半径 5 像素；文字区 8×32 像素；黑体 7pt 加粗",
    "label": "标识文字位于外框下部 1/4，2~4 个汉字；标识子类时用“子类文字标识”中的名称",
    "color": "突发事件红 (255,0,0)；危险源黄 (255,255,0)；防护目标蓝 (0,0,255)；应急保障资源绿 (0,255,0)；线状、面状红 (255,0,0)",
    "line_width": "线状符号线宽 ≥2 像素；面状符号边线 ≥2 像素",
    "leader_note": "动态标注用引线框：轮廓红 (255,0,0)，填充白杏仁色 (255,235,205)，黑色宋体 12 号",
    "transparency": "点状、面状符号不应压盖底图重要地物，应提供百分比透明度设置",
    "code": "6 位编码：大类字母(A~Y，不含 I/O/Z) + 中类 1 位 + 小类 2 位 + 子类 2 位（小类取 00）",
}


_BY_CODE = {s["std_code"]: s for s in SYMBOLS if s["geometry"] == "point"}


def preset(code, label, note=""):
    """用标准“子类文字标识”生成子类符号，如 preset("A10400", "泥石流")。"""
    base = _BY_CODE[code]
    official_label = label in base["sub_labels"]
    return {
        **{k: v for k, v in base.items() if k not in ("svg", "description", "sub_labels")},
        "id": f"GB-{code}-{label}",
        "name": label,
        "label": label,
        "preset_of": code,
        "official": official_label,
        "svg": point_svg(base, label=label),
        "description": f"{code} {base['name']}，标识文字“{label}”"
        + ("（标准子类文字标识）" if official_label else "（扩充，非标准子类文字）")
        + (f"；{note}" if note else ""),
    }
