"""生成抢险救援标绘符号库（symbols.json）和预览页（preview.html）。

符号来源（优先级从高到低）：
1. GB/T 35649-2017《突发事件应急标绘符号规范》：点状 60 个（原图矢量化）、
   线状 9 个、面状 3 个，见 gb35649.py；
2. 泥石流场景预设：GB/T 35649 符号 + 标准“子类文字标识”，如 A10400 + “泥石流”；
3. XF/T 3013-2020《国家综合性消防救援队伍常用标号》：救援力量、指挥、人员、
   车辆器材、战斗行动，见 xf3013.py；
4. 自定义补充：以上两项标准均未覆盖的，按 GB/T 35649 第 7 章扩充原则设计
   （沿用外框、颜色与构成规则）。

用法：python build_symbols.py
"""

import json
from pathlib import Path

import gb35649
import xf3013

OUT_DIR = Path(__file__).parent

# ---------------- 泥石流场景预设（GB/T 35649 子类文字） ----------------

P = gb35649.preset
PRESETS = [
    P("A10400", "泥石流"),
    P("A10400", "滑坡"),
    P("A10400", "崩塌"),
    P("A10400", "塌陷"),
    P("A10400", "堰塞体", "泥石流/滑坡堵江形成"),
    P("A10100", "山洪"),
    P("A10100", "洪水"),
    P("A10200", "暴雨"),
    P("A21300", "公路设施", "道路冲毁、中断"),
    P("A21300", "桥梁隧道", "桥梁冲毁、隧道掩埋"),
    P("A21300", "建筑垮塌", "房屋被冲毁、掩埋"),
    P("A21300", "电力设施", "供电中断"),
    P("A21300", "通讯设施", "通信中断"),
    P("A21300", "水利设施", "水库、堤坝受损"),
    P("B10100", "加油站"),
    P("B10100", "贮罐"),
    P("D10100", "地质灾害", "地质灾害现场指挥部"),
    P("D10200", "临时安置"),
    P("D10200", "物资发放"),
    P("D10200", "临时医疗"),
    P("D10200", "临时取水"),
    P("D20400", "地震救援", "也用于山地、废墟搜救"),
    P("D40200", "专用作业", "挖掘机、装载机等工程机械"),
]

# ---------------- 自定义补充（按 GB/T 35649 第 7 章扩充） ----------------

FONT = "font-family='SimHei,Heiti SC,Noto Sans CJK SC,Microsoft YaHei,sans-serif'"
CUSTOM_COLOR = {
    "A": gb35649.COLOR_STD["A"],
    "B": gb35649.COLOR_STD["B"],
    "C": gb35649.COLOR_STD["C"],
    "D": gb35649.COLOR_STD["D"],
}
CUSTOM_CLASS = {
    "A": "突发事件（扩充）",
    "B": "危险源（扩充：自然灾害风险隐患）",
    "C": "防护目标（扩充）",
    "D": "应急保障资源（扩充）",
    "L": "线状（扩充）",
    "F": "面状（扩充）",
}


def custom_point(sid, cls, name, glyph, label, desc, attrs=None):
    color = CUSTOM_COLOR[cls]
    body = (
        f"<text x='16' y='19.5' text-anchor='middle' font-size='15' font-weight='bold' "
        f"fill='{color}' {FONT}>{glyph}</text>"
    )
    return {
        "id": sid,
        "source": "自定义（按 GB/T 35649 第 7 章扩充）",
        "official": False,
        "name": name,
        "geometry": "point",
        "category": f"X{cls}",
        "color": color,
        "label": label,
        "svg": gb35649.frame_svg(color, cls == "A", body, label),
        "description": desc,
        "attributes": attrs or ["label", "time", "remark"],
    }


R = gb35649.LINE_RED


def _wide(body, h=32):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 96 {h}'>{body}</svg>"


def custom_line(sid, name, desc, svg, style):
    return {
        "id": sid, "source": "自定义（按 GB/T 35649 第 7 章扩充）", "official": False,
        "name": name, "geometry": "line", "category": "XL", "color": R,
        "style": style, "svg": svg, "description": desc,
        "attributes": ["label", "time", "remark"],
    }


def custom_area(sid, name, desc, svg, style):
    return {
        "id": sid, "source": "自定义（按 GB/T 35649 第 7 章扩充）", "official": False,
        "name": name, "geometry": "polygon", "category": "XF", "color": R,
        "style": style, "svg": svg, "description": desc,
        "attributes": ["label", "time", "remark"],
    }


BLOB = gb35649.AREA_BLOB

CUSTOM = [
    custom_point("X-A01", "A", "失联人员", "失", "失联", "失联人员最后已知位置；已确认被困人员用 XF 6.3.22", ["label", "count", "time", "remark"]),
    custom_point("X-A02", "A", "伤亡人员", "伤", "伤亡", "伤员或遇难人员位置", ["label", "count", "time", "remark"]),
    custom_point("X-B01", "B", "不稳定斜坡", "坡", "不稳定坡", "存在二次滑塌风险的斜坡"),
    custom_point("X-B02", "B", "松散物源", "源", "松散物源", "沟道内可能再次启动的松散堆积物"),
    custom_point("X-B03", "B", "堰塞湖溃决风险", "溃", "溃决风险", "可能溃决的堰塞体或水库"),
    custom_point("X-B04", "B", "危险建筑", "危", "危险建筑", "受损、可能倒塌的建筑物"),
    custom_point("X-C01", "C", "居民点", "居", "居民点", "村庄、居民集中区"),
    custom_point("X-D01", "D", "直升机起降点", "H", "起降点", "临时直升机起降场"),
    custom_point("X-D02", "D", "生命探测", "探", "生命探测", "生命探测仪、搜救犬等"),
    custom_point("X-D03", "D", "监测预警点", "警", "监测预警", "泥石流沟上游监测、预警哨位"),
    custom_line(
        "X-L01", "泥石流流向", "泥石流运动方向（粗实线 + 实心箭头）",
        _wide(f"<path d='M6,24 C30,8 56,30 78,14' fill='none' stroke='{R}' stroke-width='5'/>"
              f"<polygon points='74,6 92,10 80,24' fill='{R}'/>"),
        {"stroke": R, "width": 5, "arrow_end": "filled-large"},
    ),
    custom_line(
        "X-L02", "泥石流沟道", "主沟、支沟走向（双虚线）",
        _wide(f"<path d='M4,12 C30,4 60,20 92,10' fill='none' stroke='{R}' stroke-width='2' stroke-dasharray='8,4'/>"
              f"<path d='M4,22 C30,14 60,30 92,20' fill='none' stroke='{R}' stroke-width='2' stroke-dasharray='8,4'/>"),
        {"stroke": R, "width": 2, "dash": "8,4", "double": True},
    ),
    custom_line(
        "X-L03", "任务分界线", "相邻分队责任区分界（长虚线）",
        _wide(f"<line x1='4' y1='16' x2='92' y2='16' stroke='{R}' stroke-width='2' stroke-dasharray='16,6'/>"),
        {"stroke": R, "width": 2, "dash": "16,6"},
    ),
    custom_area(
        "X-F01", "泥石流堆积区", "已形成的堆积扇、掩埋区（红色边线 + 点状填充）",
        _wide("<defs><pattern id='dots' width='4' height='4' patternUnits='userSpaceOnUse'>"
              f"<circle cx='2' cy='2' r='0.8' fill='{R}'/></pattern></defs>"
              f"<path d='{BLOB}' fill='url(#dots)' stroke='{R}' stroke-width='1.5'/>", 56),
        {"stroke": R, "width": 2, "fill_pattern": "dots"},
    ),
    custom_area(
        "X-F02", "核心危险区", "禁止无关人员进入（红色边线 + 斜线填充）",
        _wide("<defs><pattern id='hatch' width='5' height='5' patternUnits='userSpaceOnUse' "
              f"patternTransform='rotate(45)'><line x1='0' y1='0' x2='0' y2='5' stroke='{R}' stroke-width='1'/>"
              f"</pattern></defs><path d='{BLOB}' fill='url(#hatch)' stroke='{R}' stroke-width='2'/>", 56),
        {"stroke": R, "width": 2, "fill_pattern": "hatch-45"},
    ),
    custom_area(
        "X-F03", "搜救责任区", "分配给某分队的搜救区域（细实线，内注分队）",
        _wide(f"<path d='{BLOB}' fill='{R}' fill-opacity='0.06' stroke='{R}' stroke-width='1.2'/>"
              f"<text x='50' y='30' text-anchor='middle' font-size='9' fill='{R}' {FONT}>一中队</text>", 56),
        {"stroke": R, "width": 2, "fill": R, "fill_opacity": 0.06},
    ),
]


def build():
    symbols = gb35649.SYMBOLS + PRESETS + xf3013.SYMBOLS + CUSTOM
    ids = [s["id"] for s in symbols]
    assert len(ids) == len(set(ids)), "符号 id 重复"
    lib = {
        "name": "抢险救援标绘符号库（泥石流场景）",
        "version": "0.3.0",
        "sources": {
            "gb35649": "GB/T 35649-2017《突发事件应急标绘符号规范》",
            "xf3013": "XF/T 3013-2020《国家综合性消防救援队伍常用标号》",
        },
        "rules": {"gb35649": gb35649.RULES, "xf3013": xf3013.RULES},
        "codes_xf3013": xf3013.CODES,
        "categories": {
            **gb35649.CLASSES,
            **xf3013.CATEGORIES,
            **{f"X{k}": v for k, v in CUSTOM_CLASS.items()},
        },
        "symbols": symbols,
    }
    (OUT_DIR / "symbols.json").write_text(
        json.dumps(lib, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    (OUT_DIR / "preview.html").write_text(render_preview(lib), encoding="utf-8")
    counts = {
        "GB/T 35649": len(gb35649.SYMBOLS),
        "场景预设": len(PRESETS),
        "XF/T 3013": len(xf3013.SYMBOLS),
        "自定义": len(CUSTOM),
    }
    print(f"已生成 {len(symbols)} 个符号：{counts}")


def render_preview(lib):
    def cards(items):
        out = []
        for s in items:
            tag = s.get("std_code") or s["id"]
            badge = "official" if s["official"] else "custom"
            wide = " wide" if s["geometry"] != "point" else ""
            out.append(
                f"<div class='card{wide}'><div class='icon'>{s['svg']}</div>"
                f"<div class='id {badge}'>{tag}</div><div class='nm'>{s['name']}</div>"
                f"<div class='ds'>{s['description']}</div></div>"
            )
        return "".join(out)

    def section(title, items):
        return f"<h2>{title}</h2><div class='grid'>{cards(items)}</div>" if items else ""

    syms = lib["symbols"]
    gb = [s for s in syms if s["source"] == gb35649.STD and "preset_of" not in s]
    parts = ["<h1 class='part'>一、泥石流场景常用（GB/T 35649 符号 + 子类文字标识）</h1>"]
    parts.append(section("预设", [s for s in syms if "preset_of" in s]))
    parts.append("<h1 class='part'>二、GB/T 35649-2017 突发事件应急标绘符号（全部）</h1>")
    for cls, title in gb35649.CLASSES.items():
        parts.append(section(f"{cls} · {title}", [s for s in gb if s["category"] == cls]))
    parts.append("<h1 class='part'>三、XF/T 3013-2020 救援队伍常用标号（选录）</h1>")
    for cat, title in xf3013.CATEGORIES.items():
        parts.append(section(title, [s for s in syms if s["source"] == xf3013.STD and s["category"] == cat]))
    parts.append("<h1 class='part'>四、自定义补充（两项标准均未覆盖）</h1>")
    for k, title in CUSTOM_CLASS.items():
        parts.append(section(title, [s for s in syms if s["category"] == f"X{k}"]))

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>抢险救援标号库</title>
<style>
body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;margin:0;padding:16px;background:#f6f6f4;color:#222}}
h1{{font-size:20px}} h1.part{{font-size:17px;margin-top:32px;padding:6px 10px;background:#fff;border-radius:6px}}
h2{{font-size:15px;margin-top:22px;border-left:4px solid #E53935;padding-left:8px}}
.note{{background:#fff4e5;border:1px solid #f0c080;padding:10px;border-radius:6px;font-size:13px;line-height:1.7}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px;text-align:center}}
.card.wide{{grid-column:span 2}}
.icon svg{{width:64px;height:64px}} .wide .icon svg{{width:192px;height:64px}}
.nm{{font-weight:bold;font-size:14px}}
.id{{font-size:11px;display:inline-block;padding:1px 6px;border-radius:8px;margin:2px 0}}
.id.official{{background:#e8f5e9;color:#1b5e20}} .id.custom{{background:#eee;color:#666}}
.ds{{font-size:12px;color:#555;margin-top:4px}}
</style></head><body>
<h1>{lib['name']} v{lib['version']}</h1>
<div class="note">
<b>GB/T 35649-2017</b>：点状符号主体由标准原图矢量化，外框与标识文字按标准 5.1、6.2.1 重建；线状、面状按附录 B、C 参数绘制；颜色按表 3。<br>
<b>XF/T 3013-2020</b>：按标准原图重绘（前身为武警消防部队标号体系）。<br>
绿色标签 = 标准原有符号或标准子类文字；灰色标签 = 按 GB/T 35649 第 7 章扩充的自定义符号。
</div>
{''.join(parts)}
</body></html>"""


if __name__ == "__main__":
    build()
