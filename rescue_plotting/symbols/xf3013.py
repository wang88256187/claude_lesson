"""XF/T 3013-2020《国家综合性消防救援队伍常用标号》中与抢险救援相关的标号。

图形按标准原文的"标号"图和"标绘要领"重绘为 SVG（viewBox 0 0 64 64），
编号 std_code 为标准原文条目号。只收录与泥石流等自然灾害抢险救援相关的条目，
灭火剂、水源、建筑消防设施等专用于灭火的条目未收录。

颜色（标准 4.1.2）：队伍机构、作战人员、被困人员、消防车辆、直升机、消防艇、
作战行动用红色；其他装备器材、建筑用黑色；队号用黑色。
线形（标准 4.4.2）：实际部署/行动用实线，计划（准备）用虚线；
级别、人员、车辆轮廓用粗实线。
"""

RED = "#E53935"
BLACK = "#222222"
THICK = 3.5  # 粗实线
THIN = 2  # 实线
FONT = "font-family='Arial,Microsoft YaHei,sans-serif' font-weight='bold'"


def _svg(body):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>{body}</svg>"


def _code(x, y, s, size=10, color=BLACK):
    return (
        f"<text x='{x}' y='{y}' text-anchor='middle' font-size='{size}' "
        f"fill='{color}' {FONT}>{s}</text>"
    )


def _g(color, width, body):
    return (
        f"<g fill='none' stroke='{color}' stroke-width='{width}' "
        f"stroke-linejoin='round' stroke-linecap='round'>{body}</g>"
    )


# ---------------- 6.1 级别、人员标号 ----------------


def triangle_org(code):
    """6.1.1–6.1.3 应急管理部/厅/局：三角形，粗实线。"""
    return _svg(
        _g(RED, THICK, "<polygon points='32,8 58,54 6,54'/>") + _code(32, 47, code, 10)
    )


def shield_org(code):
    """6.1.4–6.1.11 消防救援局/总队/支队/大队/站等：左右对称盾形，长:宽=4:3，粗实线。"""
    path = (
        "M14,15 Q20,15 22,8 L42,8 Q44,15 50,15 L50,38 "
        "Q50,49 32,56 Q14,49 14,38 Z"
    )
    return _svg(_g(RED, THICK, f"<path d='{path}'/>") + _code(32, 36, code, 10))


def command_post(code):
    """6.1.12–6.1.14 指挥部：旗杆+旗面（展向右方）+底部等边三角形，粗实线。"""
    body = (
        "<line x1='20' y1='6' x2='20' y2='48'/>"
        "<rect x='20' y='6' width='34' height='17'/>"
        "<polygon points='20,48 15.4,56 24.6,56'/>"
    )
    return _svg(_g(RED, THICK, body) + _code(37, 18.5, code, 10))


def commander(kind):
    """6.1.15–6.1.19 各级指挥员：旗 + 圆，旗杆延长线过圆心，旗杆长:圆直径=3:2。"""
    cx, cy, r = 26, 45, 10
    body = (
        f"<line x1='{cx}' y1='6' x2='{cx}' y2='{cy - r}'/>"
        f"<rect x='{cx}' y='6' width='22' height='11'/>"
        f"<circle cx='{cx}' cy='{cy}' r='{r}'/>"
    )
    h = r / 2
    inner = {
        "chief": f"<circle cx='{cx}' cy='{cy}' r='2' fill='{RED}'/>",
        "deputy": "",
        "assistant": f"<line x1='{cx - r}' y1='{cy}' x2='{cx + r}' y2='{cy}'/>",
        "battalion": (
            f"<line x1='{cx - 8.7}' y1='{cy - h}' x2='{cx + 8.7}' y2='{cy - h}'/>"
            f"<line x1='{cx - 8.7}' y1='{cy + h}' x2='{cx + 8.7}' y2='{cy + h}'/>"
        ),
        "station": (
            f"<line x1='{cx - r}' y1='{cy}' x2='{cx + r}' y2='{cy}'/>"
            f"<line x1='{cx - 8.7}' y1='{cy - h}' x2='{cx + 8.7}' y2='{cy - h}'/>"
            f"<line x1='{cx - 8.7}' y1='{cy + h}' x2='{cx + 8.7}' y2='{cy + h}'/>"
        ),
    }[kind]
    return _svg(_g(RED, THICK, body + inner))


def person(kind, number="1"):
    """6.1.20–6.1.26 人员：圆形 + 内部/外部图形，粗实线。"""
    cx, cy, r = 32, 36, 14
    circle = f"<circle cx='{cx}' cy='{cy}' r='{r}'/>"
    if kind == "squad_leader":  # 竖线长度等于圆直径，延长线过圆心
        cy = 42
        return _svg(
            _g(
                RED,
                THICK,
                f"<circle cx='{cx}' cy='{cy}' r='12'/>"
                f"<line x1='{cx}' y1='6' x2='{cx}' y2='{cy - 12}'/>",
            )
        )
    if kind == "fighter":  # 数字标于圆形中心
        return _svg(_g(RED, THICK, circle) + _code(cx, cy + 5, number, 14, RED))
    if kind == "signaller":  # N 形闪电
        inner = (
            f"<polyline points='{cx - 7},{cy + 7} {cx - 3},{cy - 7} "
            f"{cx + 3},{cy + 7} {cx + 7},{cy - 7}'/>"
        )
    elif kind == "driver":  # 三线三等分，竖线向下
        inner = (
            f"<line x1='{cx}' y1='{cy}' x2='{cx}' y2='{cy + r}'/>"
            f"<line x1='{cx}' y1='{cy}' x2='{cx - 12.1}' y2='{cy - 7}'/>"
            f"<line x1='{cx}' y1='{cy}' x2='{cx + 12.1}' y2='{cy - 7}'/>"
        )
    elif kind == "safety":  # 等边三角形中心与圆心重合
        inner = (
            f"<polygon points='{cx},{cy - 9} {cx + 7.8},{cy + 4.5} {cx - 7.8},{cy + 4.5}'/>"
        )
    elif kind in ("scout", "scout_team"):  # 两短线延长线交于圆心，夹角 70°
        # 与竖直方向各偏 35°
        s, c = 0.5736, 0.8192
        inner = (
            f"<line x1='{cx - s * (r + 3):.1f}' y1='{cy - c * (r + 3):.1f}' "
            f"x2='{cx - s * (r + 12):.1f}' y2='{cy - c * (r + 12):.1f}'/>"
            f"<line x1='{cx + s * (r + 3):.1f}' y1='{cy - c * (r + 3):.1f}' "
            f"x2='{cx + s * (r + 12):.1f}' y2='{cy - c * (r + 12):.1f}'/>"
        )
        if kind == "scout_team":
            inner += f"<circle cx='{cx}' cy='{cy}' r='2.5' fill='{RED}'/>"
    else:
        raise ValueError(kind)
    return _svg(_g(RED, THICK, circle + inner))


def assembly_area():
    """6.1.27 集结地：长方形 长:宽=2:1，图内三角形居中。"""
    return _svg(
        _g(RED, THICK, "<rect x='8' y='20' width='48' height='24'/>")
        + f"<polygon points='32,28 37,35 27,35' fill='{RED}'/>"
    )


# ---------------- 6.2 消防车辆、器材装备标号 ----------------


def vehicle(inner="", extra="", x0=4):
    """车体 长:宽=2:1，车头占车体长 1/3，车头内为三角形，粗实线。"""
    w, h, y0 = 60 - x0, (60 - x0) / 2, 32 - (60 - x0) / 4
    xc = x0 + w * 2 / 3
    body = (
        f"<rect x='{x0}' y='{y0}' width='{w}' height='{h}'/>"
        f"<line x1='{xc}' y1='{y0}' x2='{xc}' y2='{y0 + h}'/>"
        f"<polyline points='{xc + 2.5},{y0} {xc + 2.5},{y0 + h}'/>"
        f"<polyline points='{xc + 2.5},{y0} {x0 + w},{32} {xc + 2.5},{y0 + h}'/>"
    )
    return _svg(_g(RED, THICK, body) + _g(RED, THIN + 0.5, inner) + extra)


def _veh_center(x0=4):
    w = 60 - x0
    return x0 + w / 3, 32  # 车身区域中心


def v_rescue():
    """6.2.13 抢险救援消防车：车尾长方形 长:宽=3:1，1/3 在车身内。"""
    x0 = 16
    cx, cy = _veh_center(x0)
    tail = "<rect x='2' y='28' width='21' height='7'/>"
    lamp = (
        f"<ellipse cx='{cx + 2}' cy='{cy}' rx='4' ry='5'/>"
        f"<path d='M{cx + 6},{cy - 5} L{cx + 10},{cy - 7} L{cx + 10},{cy + 7} "
        f"L{cx + 6},{cy + 5}'/>"
    )
    return vehicle(tail + lamp, x0=x0)


def v_icon(kind):
    cx, cy = _veh_center()
    inner = {
        # 6.2.16 照明消防车：半圆灯面 + 三条射线
        "light": (
            f"<path d='M{cx - 7},{cy + 4} A7,7 0 0 1 {cx + 7},{cy + 4} Z'/>"
            f"<line x1='{cx}' y1='{cy - 5}' x2='{cx}' y2='{cy - 10}'/>"
            f"<line x1='{cx - 7}' y1='{cy - 3}' x2='{cx - 11}' y2='{cy - 7}'/>"
            f"<line x1='{cx + 7}' y1='{cy - 3}' x2='{cx + 11}' y2='{cy - 7}'/>"
        ),
        # 6.2.17 通信指挥消防车：旗（下角 30°）
        "comm": (
            f"<line x1='{cx - 7}' y1='{cy - 9}' x2='{cx - 7}' y2='{cy + 9}'/>"
            f"<polyline points='{cx - 7},{cy - 9} {cx + 9},{cy} {cx - 7},{cy}'/>"
        ),
        # 6.2.23 供水消防车：车内正方形
        "water": f"<rect x='{cx - 7}' y='{cy - 7}' width='14' height='14'/>",
        # 6.2.26 生活饮食保障消防车：勺叉交叉
        "food": (
            f"<line x1='{cx - 9}' y1='{cy - 9}' x2='{cx + 8}' y2='{cy + 9}'/>"
            f"<line x1='{cx + 9}' y1='{cy - 9}' x2='{cx - 8}' y2='{cy + 9}'/>"
            f"<ellipse cx='{cx - 9}' cy='{cy - 9}' rx='3' ry='2' fill='{RED}'/>"
            f"<line x1='{cx + 6}' y1='{cy - 11}' x2='{cx + 11}' y2='{cy - 6}'/>"
        ),
        # 6.2.28 运兵消防车：人形
        "troop": (
            f"<circle cx='{cx}' cy='{cy - 7}' r='3.5'/>"
            f"<line x1='{cx}' y1='{cy - 3.5}' x2='{cx}' y2='{cy + 4}'/>"
            f"<line x1='{cx - 6}' y1='{cy - 1}' x2='{cx + 6}' y2='{cy - 1}'/>"
            f"<polyline points='{cx - 5},{cy + 11} {cx},{cy + 4} {cx + 5},{cy + 11}'/>"
        ),
        # 6.2.30 救护车："十"字
        "ambulance": (
            f"<line x1='{cx}' y1='{cy - 8}' x2='{cx}' y2='{cy + 8}'/>"
            f"<line x1='{cx - 8}' y1='{cy}' x2='{cx + 8}' y2='{cy}'/>"
        ),
        # 6.2.31 清障消防车：车身空，车头前加对称符号
        "clear": "",
    }[kind]
    if kind == "clear":
        return _svg(
            _g(
                RED,
                THICK,
                "<rect x='2' y='17.5' width='52' height='29'/>"
                "<line x1='36.7' y1='17.5' x2='36.7' y2='46.5'/>"
                "<polyline points='39,17.5 54,32 39,46.5'/>"
                "<line x1='54' y1='32' x2='60' y2='32'/>"
                "<line x1='60' y1='26' x2='60' y2='38'/>",
            )
        )
    return vehicle(inner)


def v_fuel():
    """6.2.27 加油消防车：车身下部 1/3 涂色。"""
    x0, w, h = 4, 56, 28
    y0 = 18
    xc = x0 + w * 2 / 3
    fill = f"<rect x='{x0}' y='{y0 + h * 2 / 3}' width='{xc - x0}' height='{h / 3}' fill='{RED}'/>"
    return vehicle("", fill)


def helicopter():
    """6.2.35 消防直升机：旋翼"><"与机身同长，交角锐角 35°~40°。"""
    body = (
        "<line x1='8' y1='13' x2='56' y2='29'/>"
        "<line x1='8' y1='29' x2='56' y2='13'/>"
        "<line x1='32' y1='21' x2='32' y2='58'/>"
    )
    return _svg(_g(RED, THICK, body))


def drone():
    """6.2.36 消防无人机："X"交角 90°，两端短线与之垂直。"""
    body = (
        "<line x1='14' y1='14' x2='50' y2='50'/><line x1='50' y1='14' x2='14' y2='50'/>"
        "<line x1='8' y1='20' x2='20' y2='8'/><line x1='44' y1='8' x2='56' y2='20'/>"
        "<line x1='8' y1='44' x2='20' y2='56'/><line x1='44' y1='56' x2='56' y2='44'/>"
    )
    return _svg(_g(RED, THICK, body))


def boat():
    """6.2.37 消防艇：a:b=3:1，上下弧对称，内部椭圆居中。"""
    body = (
        "<path d='M6,24 Q6,20 12,20 L40,20 Q52,20 60,32 Q52,44 40,44 "
        "L12,44 Q6,44 6,40 Z'/>"
        "<ellipse cx='28' cy='32' rx='13' ry='5'/>"
    )
    return _svg(_g(RED, THICK, body))


def _black(body, width=THIN):
    return _svg(_g(BLACK, width, body))


EQUIPMENT_SVG = {
    # 6.2.66 手抬机动泵：长:宽=2:1，实心等边三角形位于下边中心
    "portable_pump": _black(
        "<rect x='12' y='22' width='40' height='20'/>"
        "<line x1='4' y1='26' x2='12' y2='26'/><line x1='4' y1='22' x2='4' y2='30'/>"
        "<line x1='52' y1='26' x2='60' y2='26'/><line x1='60' y1='22' x2='60' y2='30'/>"
        f"<polygon points='32,34 37,42 27,42' fill='{BLACK}'/>"
    ),
    # 6.2.72 救援三脚架
    "tripod": _black(
        "<rect x='26' y='6' width='12' height='6'/>"
        "<line x1='32' y1='12' x2='32' y2='58'/>"
        "<line x1='32' y1='12' x2='12' y2='58'/><line x1='32' y1='12' x2='52' y2='58'/>"
    ),
    # 6.2.73 液压破拆工具
    "hydraulic_breaker": _black(
        "<polygon points='4,32 16,26 22,32 16,38'/>"
        "<line x1='4' y1='32' x2='22' y2='32'/>"
        "<rect x='22' y='29' width='26' height='6'/>"
        "<rect x='48' y='24' width='10' height='16'/>"
    ),
    # 6.2.74 链锯
    "chainsaw": _black(
        "<path d='M18,24 A8,8 0 0 0 18,40'/><rect x='18' y='22' width='12' height='20'/>"
        "<path d='M30,27 L56,27 A5,5 0 0 1 56,37 L30,37'/>"
    ),
    # 6.2.80 起重气垫：气垫 长:宽=4:3 + 气瓶
    "lifting_bag": _black(
        "<rect x='24' y='20' width='32' height='24'/>"
        "<rect x='8' y='30' width='8' height='16' rx='3'/>"
        "<polyline points='12,30 12,24 20,24 20,32 24,32'/>"
    ),
    # 6.2.83 照明灯：半圆灯面 + 射线 + 三脚架
    "floodlight": _black(
        "<line x1='28' y1='20' x2='28' y2='44'/>"
        "<line x1='28' y1='44' x2='16' y2='58'/><line x1='28' y1='44' x2='40' y2='58'/>"
        "<line x1='28' y1='44' x2='28' y2='58'/>"
        "<path d='M28,10 A10,10 0 0 1 28,30 Z'/>"
        "<line x1='40' y1='20' x2='48' y2='20'/><line x1='37' y1='12' x2='44' y2='6'/>"
        "<line x1='37' y1='28' x2='44' y2='34'/>"
    ),
    # 6.2.84 手持电台：长方形 长:宽=2:1，小圆居中
    "handheld_radio": _black(
        "<rect x='22' y='16' width='20' height='40'/>"
        "<line x1='26' y1='4' x2='26' y2='16'/><circle cx='32' cy='40' r='5'/>"
    ),
    # 6.2.85 基地无线电台：等边三角形 + 左边延长线闪电天线
    "base_radio": _black(
        "<polygon points='28,26 42,50 14,50'/>"
        "<polyline points='28,26 36,12 36,18 44,6'/>"
    ),
    # 6.2.87 无线电转信台
    "repeater": _black(
        "<polygon points='32,30 46,54 18,54'/>"
        "<polyline points='32,30 22,14 22,20 14,8'/>"
        "<polyline points='32,30 42,14 42,20 50,8'/>"
    ),
    # 6.2.88 卫星通信地面站：三角形 + 抛物面（弧口朝右上）
    "sat_station": _black(
        "<polygon points='30,30 44,54 16,54'/>"
        "<line x1='30' y1='30' x2='38' y2='20'/>"
        "<path d='M32,12 A10,10 0 0 0 46,26'/>"
    ),
    # 6.2.91 便携式卫星地面站：圆 + 连线（60°）+ 抛物面
    "portable_sat": _black(
        "<circle cx='22' cy='48' r='9'/>"
        "<line x1='26.5' y1='40.2' x2='38' y2='20'/>"
        "<path d='M36,8 A12,12 0 0 0 52,22'/>"
    ),
}


# ---------------- 6.3 战斗行动标号 ----------------


def north_arrow():
    """6.3.2 指北矢标。"""
    return _svg(
        _g(BLACK, THIN, "<circle cx='32' cy='38' r='18'/>")
        + f"<polygon points='32,22 24,52 32,46' fill='#fff' stroke='{BLACK}' stroke-width='1.5'/>"
        + f"<polygon points='32,22 40,52 32,46' fill='{BLACK}'/>"
        + _code(32, 14, "N", 11)
    )


def wind():
    """6.3.4 风力和指向：数字代表风力级别，箭头表明风向。"""
    body = (
        "<line x1='6' y1='38' x2='58' y2='38'/>"
        "<polygon points='50,31 58,38 50,38' fill='#222'/>"
        + "".join(f"<line x1='{6 + i * 4}' y1='30' x2='{10 + i * 4}' y2='38'/>" for i in range(4))
        + "<line x1='6' y1='30' x2='22' y2='30'/>"
    )
    return _svg(_g(BLACK, THIN, body) + _code(36, 34, "3", 10))


def entrance(out=False):
    """6.3.11 入口 / 6.3.12 出口。"""
    if out:
        body = (
            f"<circle cx='12' cy='32' r='5' fill='{BLACK}'/>"
            "<line x1='12' y1='32' x2='56' y2='32'/><polyline points='48,26 56,32 48,38'/>"
        )
    else:
        body = (
            "<line x1='6' y1='32' x2='48' y2='32'/><polyline points='40,26 48,32 40,38'/>"
            f"<circle cx='53' cy='32' r='5' fill='{BLACK}'/>"
        )
    return _svg(_g(BLACK, THIN, body))


def attack_direction():
    """6.3.18 进攻方向：上下对称双折线箭头。"""
    return _svg(
        _g(
            RED,
            THIN + 0.5,
            "<path d='M10,10 L36,32 L10,54 M24,10 L50,32 L24,54'/>"
            "<path d='M10,10 L24,10 M10,54 L24,54'/>",
        )
    )


def main_work_face():
    """6.3.20 主要作业面：长:宽=2:1，内注 ZYM。"""
    return _svg(
        _g(RED, THIN + 0.5, "<rect x='6' y='18' width='52' height='26'/>")
        + _code(32, 35, "ZYM", 11)
    )


def trapped_person():
    """6.3.22 被困人员：长方形 长:宽=2:1（竖放），内有人形。"""
    body = (
        "<rect x='20' y='6' width='24' height='52'/>"
        "<circle cx='32' cy='18' r='5'/>"
        "<line x1='32' y1='23' x2='32' y2='38'/>"
        "<line x1='25' y1='29' x2='39' y2='29'/>"
        "<polyline points='26,52 32,38 38,52'/>"
    )
    return _svg(_g(RED, THIN + 0.5, body))


def safe_retreat():
    """6.3.21 安全撤退路线：人形 + 箭头。"""
    body = (
        "<circle cx='14' cy='20' r='5'/>"
        "<line x1='14' y1='25' x2='14' y2='40'/>"
        "<line x1='7' y1='31' x2='21' y2='31'/>"
        "<polyline points='8,54 14,40 20,54'/>"
        "<line x1='24' y1='20' x2='58' y2='20'/><polyline points='50,14 58,20 50,26'/>"
    )
    return _svg(_g(RED, THIN, body))


def planned_route():
    """6.3.17 预计行动路线：虚线 + 开口箭头。"""
    return _svg(
        _g(
            RED,
            THIN + 0.5,
            "<line x1='4' y1='32' x2='56' y2='32' stroke-dasharray='8,6'/>"
            "<polyline points='48,25 57,32 48,39'/>",
        )
    )


def deep_attack():
    """6.3.19 深入内攻：曲线 + 箭头。"""
    return _svg(
        _g(
            RED,
            THIN + 0.5,
            "<path d='M4,54 Q38,54 54,14'/><polyline points='46,18 54,13 56,22'/>",
        )
    )


# ---------------- 6.6 常用建筑及构件标号 ----------------


def building(code="", thick=False, dashed=False):
    dash = " stroke-dasharray='6,4'" if dashed else ""
    w = THICK if thick else THIN
    return _svg(
        f"<rect x='6' y='18' width='52' height='26' fill='none' stroke='{BLACK}' "
        f"stroke-width='{w}'{dash}/>"
        + (_code(32, 35, code, 11) if code else "")
    )


# ---------------- 条目清单 ----------------

STD = "XF/T 3013-2020"


def _item(code, name, category, svg, desc, geometry="point", attrs=None, style=None):
    item = {
        "id": f"XF-{code}",
        "std_code": code,
        "source": STD,
        "official": True,
        "name": name,
        "geometry": geometry,
        "category": category,
        "svg": svg,
        "description": desc,
        "attributes": attrs or ["label", "time", "remark"],
    }
    if style:
        item["style"] = style
    return item


UNIT = ["label", "code", "headcount", "equipment", "task", "time", "remark"]

SYMBOLS = [
    # 6.1 级别、人员
    _item("6.1.1", "应急管理部", "org", triangle_org("YJB"), "三角形为粗实线", attrs=UNIT),
    _item("6.1.2", "应急管理厅", "org", triangle_org("YJT"), "三角形为粗实线", attrs=UNIT),
    _item("6.1.3", "应急管理局（处）", "org", triangle_org("YJJ"), "三角形为粗实线", attrs=UNIT),
    _item("6.1.4", "应急管理部消防救援局", "org", shield_org("XFJ"), "盾形 长:宽=4:3，注记代字", attrs=UNIT),
    _item("6.1.5", "总队", "org", shield_org("ZOD"), "盾形 长:宽=4:3，注记代字 ZOD", attrs=UNIT),
    _item("6.1.6", "支队", "org", shield_org("ZHD"), "盾形 长:宽=4:3，注记代字 ZHD", attrs=UNIT),
    _item("6.1.7", "大队", "org", shield_org("DD"), "盾形 长:宽=4:3，注记代字 DD", attrs=UNIT),
    _item("6.1.8", "站", "org", shield_org("ZH"), "盾形 长:宽=4:3，注记代字 ZH", attrs=UNIT),
    _item("6.1.9", "政府专职消防队", "org", shield_org("ZFD"), "盾形，注记代字 ZFD", attrs=UNIT),
    _item("6.1.10", "企业专职消防队", "org", shield_org("QYD"), "盾形，注记代字 QYD", attrs=UNIT),
    _item("6.1.11", "志愿消防队", "org", shield_org("ZYD"), "盾形，注记代字 ZYD", attrs=UNIT),
    _item("6.1.12", "现场指挥部", "command", command_post("XZB"), "旗杆长:旗面长:旗面宽=2.5:2:1，旗面展向右方；旗面内注记代字", attrs=UNIT),
    _item("6.1.13", "前方指挥部", "command", command_post("QZB"), "旗杆垂直于等边三角形底边，旗杆长:三角形高=5:1", attrs=UNIT),
    _item("6.1.14", "后方指挥部", "command", command_post("HZB"), "同前方指挥部，注记 HZB", attrs=UNIT),
    _item("6.1.15", "总指挥", "command", commander("chief"), "旗杆延长线过圆心，旗杆长:圆直径=3:2，圆心加点"),
    _item("6.1.16", "副总指挥", "command", commander("deputy"), "旗 + 空心圆"),
    _item("6.1.17", "助理指挥", "command", commander("assistant"), "圆内线为水平直径"),
    _item("6.1.18", "大队指挥", "command", commander("battalion"), "圆内两条水平线，平分垂直直径"),
    _item("6.1.19", "站指挥", "command", commander("station"), "圆内中线为水平直径，上下两线为垂直半径平分线"),
    _item("6.1.20", "战斗班长", "person", person("squad_leader"), "竖线长度等于圆直径，延长线过圆心"),
    _item("6.1.21", "战斗员", "person", person("fighter"), "数字标于圆形中心，代表战斗员编号", attrs=["number", "label", "time", "remark"]),
    _item("6.1.22", "通信员", "person", person("signaller"), "两斜线平行，中竖线与斜线夹角约 35°"),
    _item("6.1.23", "驾驶员", "person", person("driver"), "三线三等分圆，竖线为水平线的垂线"),
    _item("6.1.24", "安全员", "person", person("safety"), "等边三角形中心与圆心重合"),
    _item("6.1.25", "侦察员", "person", person("scout"), "两短线延长线相交于圆心，夹角 70°"),
    _item("6.1.26", "侦察组", "person", person("scout_team"), "同侦察员，圆心加圆点", attrs=UNIT),
    _item("6.1.27", "集结地", "command", assembly_area(), "长方形 长:宽=2:1，图内三角形居中", attrs=UNIT),
    # 6.2 车辆、器材装备（选录）
    _item("6.2.13", "抢险救援消防车", "vehicle", v_rescue(), "主参数：抢险救援器材件数", attrs=UNIT),
    _item("6.2.16", "照明消防车", "vehicle", v_icon("light"), "主参数：发电机组额定功率 kW", attrs=UNIT),
    _item("6.2.17", "通信指挥消防车", "vehicle", v_icon("comm"), "主参数：通信指挥设备总功率 W", attrs=UNIT),
    _item("6.2.23", "供水消防车", "vehicle", v_icon("water"), "主参数：额定水装载量 t", attrs=UNIT),
    _item("6.2.26", "生活饮食保障消防车", "vehicle", v_icon("food"), "后勤保障车辆", attrs=UNIT),
    _item("6.2.27", "加油消防车", "vehicle", v_fuel(), "主参数：额定油装载量 t", attrs=UNIT),
    _item("6.2.28", "运兵消防车", "vehicle", v_icon("troop"), "主参数：额定运载量（人）", attrs=UNIT),
    _item("6.2.30", "救护车", "vehicle", v_icon("ambulance"), "车身内“十”字居中", attrs=UNIT),
    _item("6.2.31", "清障消防车", "vehicle", v_icon("clear"), "车头前符号对称，水平线:垂直线=1:2", attrs=UNIT),
    _item("6.2.35", "消防直升机", "aircraft", helicopter(), "旋翼与机身同长，交角锐角 35°~40°", attrs=UNIT),
    _item("6.2.36", "消防无人机", "aircraft", drone(), "“X”交角 90°，两端短线与之垂直", attrs=UNIT),
    _item("6.2.37", "消防艇", "aircraft", boat(), "a:b=3:1，内部椭圆居中", attrs=UNIT),
    _item("6.2.66", "手抬机动泵", "equipment", EQUIPMENT_SVG["portable_pump"], "可用于排水；实心等边三角形位于下边中心"),
    _item("6.2.72", "救援三脚架", "equipment", EQUIPMENT_SVG["tripod"], "三条线与垂直线夹角 30°"),
    _item("6.2.73", "液压破拆工具", "equipment", EQUIPMENT_SVG["hydraulic_breaker"], "上下对称图形"),
    _item("6.2.74", "链锯", "equipment", EQUIPMENT_SVG["chainsaw"], "上下对称图形"),
    _item("6.2.80", "起重气垫", "equipment", EQUIPMENT_SVG["lifting_bag"], "气垫 长:宽=4:3"),
    _item("6.2.83", "照明灯", "equipment", EQUIPMENT_SVG["floodlight"], "灯面为半圆，射线指向圆心"),
    _item("6.2.84", "手持电台", "comm", EQUIPMENT_SVG["handheld_radio"], "长方形 长:宽=2:1，小圆居中"),
    _item("6.2.85", "基地无线电台", "comm", EQUIPMENT_SVG["base_radio"], "定位点在三角形中心"),
    _item("6.2.87", "无线电转信台", "comm", EQUIPMENT_SVG["repeater"], "图形左右对称"),
    _item("6.2.88", "卫星通信地面站", "comm", EQUIPMENT_SVG["sat_station"], "圆弧略小于半圆，弧口朝右上"),
    _item("6.2.91", "便携式卫星地面站", "comm", EQUIPMENT_SVG["portable_sat"], "连线与水平线夹角 60°"),
    # 6.3 战斗行动（选录）
    _item("6.3.2", "指北矢标", "action", north_arrow(), "尖角指向北方"),
    _item("6.3.4", "风力和指向", "action", wind(), "数字代表风力级别，箭头表明风向", attrs=["level", "direction", "time"]),
    _item("6.3.11", "入口", "action", entrance(), "实心圆位于箭头前方"),
    _item("6.3.12", "出口", "action", entrance(out=True), "实心圆位于箭尾后方"),
    _item("6.3.17", "预计行动路线", "action", planned_route(), "虚线；箭头指向按实际情况标绘", geometry="line",
          style={"stroke": RED, "width": 2.5, "dash": "8,6", "arrow_end": "open"}),
    _item("6.3.18", "进攻方向", "action", attack_direction(), "上下对称；抢险救援中表示救援推进方向", attrs=["label", "direction", "time"]),
    _item("6.3.19", "深入内攻", "action", deep_attack(), "线条弧度和箭头指向按实际情况标绘；可表示深入搜救路线", geometry="line",
          style={"stroke": RED, "width": 2.5, "dash": None, "arrow_end": "open", "curve": True}),
    _item("6.3.20", "主要作业面", "action", main_work_face(), "长:宽=2:1，注记 ZYM", geometry="polygon",
          style={"stroke": RED, "width": 2.5, "fill": RED, "fill_opacity": 0.05, "label": "ZYM"}),
    _item("6.3.21", "安全撤退路线", "action", safe_retreat(), "人形在起点，箭头指向撤退方向", geometry="line",
          style={"stroke": RED, "width": 2, "dash": None, "arrow_end": "open", "start_icon": "person"}),
    _item("6.3.22", "被困人员", "action", trapped_person(), "左右对称，长方形 长:宽=2:1", attrs=["count", "label", "time", "remark"]),
    # 6.6 建筑（选录）
    _item("6.6.1", "建筑物", "building", building(), "长方形 长:宽=2:1"),
    _item("6.6.2", "地下建筑物或构筑物", "building", building(dashed=True), "虚线长方形"),
    _item("6.6.3", "民用建筑", "building", building("MJ"), "字母居中"),
    _item("6.6.4", "工业建筑", "building", building("GJ"), "字母居中"),
    _item("6.6.5", "消防安全重点单位", "building", building("ZDW", thick=True), "粗实线，字母居中"),
]

CATEGORIES = {
    "org": "队伍机构（6.1）",
    "command": "指挥与集结（6.1）",
    "person": "人员（6.1）",
    "vehicle": "车辆（6.2）",
    "aircraft": "航空器与船艇（6.2）",
    "equipment": "器材装备（6.2）",
    "comm": "通信装备（6.2）",
    "action": "战斗行动（6.3）",
    "building": "建筑（6.6）",
}

# 表 1 代字（选录）
CODES = {
    "YJB": "应急管理部",
    "YJT": "应急管理厅",
    "YJJ": "应急管理局（处）",
    "GJXF": "国家综合性消防救援队伍",
    "XFJ": "消防救援局",
    "ZOD": "总队",
    "ZHD": "支队",
    "DD": "大队",
    "ZH": "站",
    "B": "班",
    "Z": "组",
    "ZFD": "政府专职消防队",
    "QYD": "企业专职消防队",
    "ZYD": "志愿消防队",
    "XZB": "现场指挥部",
    "QZB": "前方指挥部",
    "HZB": "后方指挥部",
    "QX": "气象",
    "ZC": "侦察",
    "BZ": "保障",
    "ZYM": "主要作业面",
    "MJ": "民用建筑",
    "GJ": "工业建筑",
    "ZDW": "重点单位",
}

RULES = {
    "color": {
        "red": "队伍机构、作战人员、被困人员；消防车辆、直升机、消防艇、水枪水炮；灾害发展方向、进攻方向、搜救路线、救援作战范围",
        "black": "其他装备器材、消防设施、常用建筑及构件；各种队号",
        "blue": "消防水源和供水线路（干线）",
        "yellow": "易燃易爆、有毒、放射性物质污染区域轮廓线内衬",
    },
    "line": {
        "solid": "实际力量部署、行动；地上建筑",
        "dashed": "计划（准备）或已经转移阵地的部署、行动；地下建筑",
        "thick_solid": "级别、人员、消防车辆、重点单位轮廓",
        "thick_dashed": "铁路隧道",
    },
    "direction": "有直立含义的（指挥部、电台）直立标示；有行动方向的（车辆、人员疏散、进攻）按实际方向标示；不宜倒置",
    "annotation": "机关名称按“地名+级别代字”由左至右书写，如“江苏 XFZOD”；参数注记在标号下方，按单位/编号/技术指标顺序，以“/”隔开",
    "time": "按年.月.日.时分书写，时分数字下加一划线，如 2019.06.06.0808",
}
