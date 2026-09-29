"""生成抢险救援标绘符号库（symbols.json）和预览页（preview.html）。

符号分类框架参考公开国家标准 GB/T 35649-2017《突发事件应急标绘符号规范》
（点状：事件/危险源/防护目标/应急保障资源；另有线状、面状），
具体图形、颜色和编码为本项目自定义示意，并非该标准或任何部队条令的原文。

用法：python build_symbols.py
"""

import json
from pathlib import Path

OUT_DIR = Path(__file__).parent

# 颜色约定（可在 symbols.json 的 palette 中统一修改）
PALETTE = {
    "event": "#D35400",  # 灾害事件：橙
    "hazard": "#8E44AD",  # 危险源/隐患：紫
    "target": "#1F6FB2",  # 防护目标：蓝
    "force": "#C0392B",  # 救援力量与行动（我方）：红
    "support": "#1E8449",  # 应急保障资源：绿
    "debris": "#7B4A1E",  # 泥石流本体：棕
}

FONT = "font-family='Microsoft YaHei,PingFang SC,Noto Sans CJK SC,sans-serif'"


def svg(body):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>{body}</svg>"


def text(label, color, size=22, y=40):
    return (
        f"<text x='32' y='{y}' text-anchor='middle' font-size='{size}' "
        f"font-weight='bold' fill='{color}' {FONT}>{label}</text>"
    )


def triangle(color, label):
    return svg(
        f"<polygon points='32,5 60,57 4,57' fill='#fff' stroke='{color}' "
        f"stroke-width='3.5' stroke-linejoin='round'/>" + text(label, color, 20, 49)
    )


def diamond(color, label):
    return svg(
        f"<polygon points='32,3 61,32 32,61 3,32' fill='#fff' stroke='{color}' "
        f"stroke-width='3.5'/>" + text(label, color, 20, 40)
    )


def square(color, label):
    return svg(
        f"<rect x='6' y='6' width='52' height='52' rx='4' fill='#fff' "
        f"stroke='{color}' stroke-width='3.5'/>" + text(label, color)
    )


def rect(color, label):
    return svg(
        f"<rect x='3' y='14' width='58' height='36' fill='#fff' stroke='{color}' "
        f"stroke-width='3.5'/>" + text(label, color, 20, 39)
    )


def circle(color, label):
    return svg(
        f"<circle cx='32' cy='32' r='27' fill='#fff' stroke='{color}' "
        f"stroke-width='3.5'/>" + text(label, color)
    )


def flag(color, label):
    """指挥所：旗杆 + 旗面（会意图形）。"""
    return svg(
        f"<line x1='12' y1='6' x2='12' y2='60' stroke='{color}' stroke-width='4'/>"
        f"<rect x='12' y='6' width='46' height='30' fill='#fff' stroke='{color}' "
        f"stroke-width='3.5'/>" + text(label, color, 18, 28)
    )


def point(sid, name, category, frame, glyph, desc, attrs=None):
    color = PALETTE[category]
    return {
        "id": sid,
        "name": name,
        "geometry": "point",
        "category": category,
        "color": color,
        "svg": frame(color, glyph),
        "description": desc,
        "attributes": attrs or ["label", "time", "remark"],
    }


def line_preview(sid, stroke, dash="", arrow=False, width=4, double=False):
    marker = ""
    end = ""
    if arrow:
        marker = (
            f"<defs><marker id='arr-{sid}' viewBox='0 0 10 10' refX='8' refY='5' "
            "markerWidth='4' markerHeight='4' orient='auto'>"
            f"<path d='M0,0 L10,5 L0,10 z' fill='{stroke}'/></marker></defs>"
        )
        end = f"marker-end='url(#arr-{sid})'"
    dash_attr = f"stroke-dasharray='{dash}'" if dash else ""
    body = marker
    if double:
        body += (
            f"<path d='M4,26 C20,14 40,34 58,22' fill='none' stroke='{stroke}' "
            f"stroke-width='{width}' {dash_attr}/>"
            f"<path d='M4,40 C20,28 40,48 58,36' fill='none' stroke='{stroke}' "
            f"stroke-width='{width}' {dash_attr}/>"
        )
    else:
        body += (
            f"<path d='M4,44 C18,20 40,48 56,18' fill='none' stroke='{stroke}' "
            f"stroke-width='{width}' {dash_attr} {end}/>"
        )
    return svg(body)


def line(sid, name, category, desc, dash="", arrow=False, width=4, double=False):
    color = PALETTE[category]
    return {
        "id": sid,
        "name": name,
        "geometry": "line",
        "category": category,
        "color": color,
        "style": {
            "stroke": color,
            "width": width,
            "dash": dash or None,
            "arrow_end": arrow,
            "double": double,
        },
        "svg": line_preview(sid, color, dash, arrow, width, double),
        "description": desc,
        "attributes": ["label", "time", "remark"],
    }


def area(sid, name, category, desc, fill_opacity=0.25, dash="", hatch=False):
    color = PALETTE[category]
    dash_attr = f"stroke-dasharray='{dash}'" if dash else ""
    pattern = ""
    fill = color
    if hatch:
        pattern = (
            f"<defs><pattern id='hatch-{sid}' width='8' height='8' patternUnits='userSpaceOnUse' "
            "patternTransform='rotate(45)'>"
            f"<line x1='0' y1='0' x2='0' y2='8' stroke='{color}' stroke-width='3'/>"
            "</pattern></defs>"
        )
        fill = f"url(#hatch-{sid})"
    preview = svg(
        pattern + f"<polygon points='8,14 50,6 58,40 34,58 6,46' fill='{fill}' "
        f"fill-opacity='{fill_opacity if not hatch else 0.6}' stroke='{color}' "
        f"stroke-width='3' {dash_attr}/>"
    )
    return {
        "id": sid,
        "name": name,
        "geometry": "polygon",
        "category": category,
        "color": color,
        "style": {
            "stroke": color,
            "width": 3,
            "dash": dash or None,
            "fill": color,
            "fill_opacity": fill_opacity,
            "hatch": hatch,
        },
        "svg": preview,
        "description": desc,
        "attributes": ["label", "time", "remark"],
    }


UNIT_ATTRS = ["label", "echelon", "headcount", "equipment", "task", "time", "remark"]

SYMBOLS = [
    # ---------- A 灾害事件（点） ----------
    point("EV-01", "泥石流发生点", "event", triangle, "泥", "泥石流发生或暴发位置"),
    point("EV-02", "滑坡", "event", triangle, "滑", "滑坡发生位置"),
    point("EV-03", "崩塌", "event", triangle, "崩", "崩塌、落石发生位置"),
    point("EV-04", "堰塞体", "event", triangle, "堰", "泥石流/滑坡堵江形成的堰塞体"),
    point("EV-05", "房屋倒塌/掩埋", "event", triangle, "塌", "房屋被冲毁、掩埋位置"),
    point("EV-06", "道路中断点", "event", triangle, "断", "道路被冲毁、掩埋的断点"),
    point("EV-07", "桥梁损毁", "event", triangle, "桥", "桥梁冲毁或受损"),
    point(
        "EV-08",
        "被困人员",
        "event",
        triangle,
        "困",
        "已确认被困人员位置",
        ["label", "count", "time", "remark"],
    ),
    point(
        "EV-09",
        "失联人员（最后位置）",
        "event",
        triangle,
        "失",
        "失联人员最后已知位置",
        ["label", "count", "time", "remark"],
    ),
    point(
        "EV-10",
        "伤亡人员",
        "event",
        triangle,
        "伤",
        "伤员或遇难人员位置",
        ["label", "count", "time", "remark"],
    ),
    point("EV-11", "通信中断", "event", triangle, "讯", "公网/专网通信中断区域中心点"),
    point("EV-12", "电力中断", "event", triangle, "电", "供电中断点"),
    # ---------- B 危险源 / 隐患（点） ----------
    point("HZ-01", "不稳定斜坡", "hazard", diamond, "坡", "存在二次滑塌风险的斜坡"),
    point("HZ-02", "松散物源", "hazard", diamond, "源", "沟道内可能再次启动的松散堆积物"),
    point("HZ-03", "危险建筑", "hazard", diamond, "危", "受损、可能倒塌的建筑物"),
    point("HZ-04", "危化品/油气", "hazard", diamond, "化", "加油站、危化品仓库等"),
    point("HZ-05", "堰塞湖溃决风险点", "hazard", diamond, "溃", "可能溃决的堰塞体或水库"),
    # ---------- C 防护目标（点） ----------
    point("TG-01", "居民点", "target", square, "居", "村庄、居民集中区"),
    point("TG-02", "学校", "target", square, "学", "学校、幼儿园"),
    point("TG-03", "医院/卫生院", "target", square, "医", "医疗机构"),
    point("TG-04", "水库/水电站", "target", square, "库", "水库、水电站"),
    point("TG-05", "重要设施", "target", square, "设", "变电站、通信基站、水厂等"),
    # ---------- D 救援力量与指挥（点，我方） ----------
    point("FC-01", "现场指挥部", "force", flag, "指", "现场（基本）指挥所", UNIT_ATTRS),
    point("FC-02", "前进指挥所", "force", flag, "前指", "靠前设置的前进指挥所", UNIT_ATTRS),
    point("FC-03", "救援分队", "force", rect, "救", "救援分队（通过 echelon 标注规模）", UNIT_ATTRS),
    point("FC-04", "搜救组", "force", rect, "搜", "搜索、营救小组", UNIT_ATTRS),
    point("FC-05", "警戒/封控组", "force", rect, "警", "负责警戒、交通管制", UNIT_ATTRS),
    point("FC-06", "工程抢修组", "force", rect, "工", "道路抢通、清障（含工程机械）", UNIT_ATTRS),
    point("FC-07", "医疗救护组", "force", rect, "医", "随队医疗救护力量", UNIT_ATTRS),
    point("FC-08", "观察哨/监测预警点", "force", circle, "哨", "监测泥石流沟上游动态，负责预警", UNIT_ATTRS),
    point("FC-09", "无人机侦察组", "force", rect, "机", "无人机侦察、测绘、喊话", UNIT_ATTRS),
    point("FC-10", "友邻/地方救援力量", "force", rect, "友", "消防、应急、医疗等协同力量", UNIT_ATTRS),
    # ---------- E 应急保障资源（点） ----------
    point("SP-01", "直升机起降点", "support", circle, "H", "临时直升机起降场"),
    point("SP-02", "临时医疗点", "support", circle, "+", "伤员救治、转运点"),
    point("SP-03", "物资储备/发放点", "support", circle, "资", "救援物资集中点"),
    point("SP-04", "临时安置点", "support", circle, "安", "受灾群众临时安置"),
    point("SP-05", "通信中继/应急通信车", "support", circle, "通", "应急通信保障"),
    point("SP-06", "油料/装备补给点", "support", circle, "补", "油料、装备、器材补给"),
    point("SP-07", "工程机械", "support", circle, "挖", "挖掘机、装载机等"),
    point("SP-08", "生命探测设备", "support", circle, "探", "生命探测仪、搜救犬等"),
    # ---------- F 线状 ----------
    line("LN-01", "泥石流流向", "debris", "泥石流运动方向", arrow=True, width=6),
    line("LN-02", "泥石流沟道", "debris", "主沟、支沟走向", dash="10,6", width=4),
    line("LN-03", "救援行进路线（计划）", "force", "计划的机动/行进路线", dash="8,6", arrow=True),
    line("LN-04", "救援行进路线（实施）", "force", "已实施的机动路线", arrow=True),
    line("LN-05", "群众撤离路线", "support", "避险撤离方向", arrow=True, width=4),
    line("LN-06", "道路中断段", "event", "被冲毁或掩埋的路段", dash="2,5", width=6),
    line("LN-07", "警戒线", "force", "警戒/封控线", dash="12,4,2,4"),
    line("LN-08", "任务分界线", "force", "相邻分队责任区分界", dash="16,6", width=3),
    line("LN-09", "预警撤离信号传递线", "force", "观察哨至指挥部/群众的预警链路", dash="4,4", arrow=True, width=3),
    # ---------- G 面状 ----------
    area("AR-01", "泥石流堆积区", "debris", "已形成的堆积扇、掩埋区", fill_opacity=0.45),
    area("AR-02", "核心危险区", "force", "禁止无关人员进入", fill_opacity=0.35, hatch=True),
    area("AR-03", "警戒区", "event", "限制进入，需佩戴防护、有撤离预案", fill_opacity=0.2, dash="10,5"),
    area("AR-04", "潜在影响区", "hazard", "二次泥石流可能波及范围", fill_opacity=0.15, dash="4,4"),
    area("AR-05", "搜救责任区", "force", "分配给某分队的搜救区域", fill_opacity=0.12),
    area("AR-06", "集结地域", "force", "救援力量集结待命区域", fill_opacity=0.12, dash="8,4"),
    area("AR-07", "临时安置区", "support", "群众安置区域", fill_opacity=0.2),
    area("AR-08", "直升机作业区", "support", "起降及净空保护区", fill_opacity=0.15, dash="6,4"),
]

CATEGORIES = {
    "event": "灾害事件",
    "hazard": "危险源/隐患",
    "target": "防护目标",
    "force": "救援力量与行动",
    "support": "应急保障资源",
    "debris": "泥石流本体",
}

ECHELONS = ["组", "班", "排", "中队", "大队", "支队"]


def build():
    ids = [s["id"] for s in SYMBOLS]
    assert len(ids) == len(set(ids)), "符号 id 重复"
    lib = {
        "name": "抢险救援标绘符号库（泥石流场景）",
        "version": "0.1.0",
        "basis": "分类框架参考 GB/T 35649-2017《突发事件应急标绘符号规范》；图形、颜色、编码为本项目自定义示意",
        "not_official": True,
        "palette": PALETTE,
        "categories": CATEGORIES,
        "echelons": ECHELONS,
        "symbols": SYMBOLS,
    }
    (OUT_DIR / "symbols.json").write_text(
        json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "preview.html").write_text(render_preview(lib), encoding="utf-8")
    print(f"已生成 {len(SYMBOLS)} 个符号")


def render_preview(lib):
    geo_names = {"point": "点状", "line": "线状", "polygon": "面状"}
    sections = []
    for geo in ["point", "line", "polygon"]:
        for cat, cat_name in lib["categories"].items():
            items = [
                s for s in lib["symbols"] if s["geometry"] == geo and s["category"] == cat
            ]
            if not items:
                continue
            cards = "".join(
                f"<div class='card'><div class='icon'>{s['svg']}</div>"
                f"<div class='id'>{s['id']}</div><div class='nm'>{s['name']}</div>"
                f"<div class='ds'>{s['description']}</div></div>"
                for s in items
            )
            sections.append(
                f"<h2>{geo_names[geo]} · {cat_name}</h2><div class='grid'>{cards}</div>"
            )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>抢险救援标号库</title>
<style>
body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;margin:0;padding:16px;background:#f6f6f4;color:#222}}
h1{{font-size:20px}} h2{{font-size:16px;margin-top:28px;border-left:4px solid #C0392B;padding-left:8px}}
.note{{background:#fff4e5;border:1px solid #f0c080;padding:10px;border-radius:6px;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px;text-align:center}}
.icon svg{{width:56px;height:56px}} .id{{font-size:11px;color:#888}} .nm{{font-weight:bold;font-size:14px}}
.ds{{font-size:12px;color:#555;margin-top:4px}}
</style></head><body>
<h1>{lib['name']} v{lib['version']}</h1>
<div class="note">⚠ {lib['basis']}。非武警部队或解放军正式标号，正式使用前请按本单位下发的标图规定替换或校核。</div>
{''.join(sections)}
</body></html>"""


if __name__ == "__main__":
    build()
