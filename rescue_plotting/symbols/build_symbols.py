"""生成抢险救援标绘符号库（symbols.json）和预览页（preview.html）。

符号分两部分：
1. 官方标号：XF/T 3013-2020《国家综合性消防救援队伍常用标号》中与抢险救援相关的条目，
   按标准原图重绘，见 xf3013.py。
2. 自定义补充：泥石流等灾情、危险源、防护目标、保障资源，XF/T 3013 未覆盖。
   外框按 GB/T 35649-2017《突发事件应急标绘符号规范》5.1 的规则：
   突发事件用圆角正方形，危险源/防护目标/应急保障资源用直角正方形，
   标识文字限 2~4 个汉字、位于外框下部。GB/T 35649 附录 A 的原始符号图未取得，
   框内图形和编号为本项目自定义。

用法：python build_symbols.py
"""

import json
from pathlib import Path

import xf3013

OUT_DIR = Path(__file__).parent

PALETTE = {
    "event": "#E53935",  # 灾情：红（XF/T 3013 4.1.2 b/e：灾害部位与发展方向用红色）
    "hazard": "#8E44AD",  # 危险源/隐患：紫（自定义）
    "target": "#1F6FB2",  # 防护目标：蓝（自定义）
    "support": "#1E8449",  # 应急保障资源：绿（自定义）
    "debris": "#7B4A1E",  # 泥石流本体：棕（自定义）
    "force": xf3013.RED,  # 救援力量与行动：红（XF/T 3013）
}

FONT = "font-family='Microsoft YaHei,PingFang SC,Noto Sans CJK SC,sans-serif'"


def svg(body):
    return f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'>{body}</svg>"


def framed(color, glyph, label, rounded):
    """GB/T 35649 点状符号：外框 + 符号主体 + 下部 1/4 标识文字。"""
    rx = 10 if rounded else 0
    return svg(
        f"<rect x='4' y='4' width='56' height='56' rx='{rx}' fill='#fff' "
        f"stroke='{color}' stroke-width='3'/>"
        f"<text x='32' y='37' text-anchor='middle' font-size='24' font-weight='bold' "
        f"fill='{color}' {FONT}>{glyph}</text>"
        f"<text x='32' y='54' text-anchor='middle' font-size='9' fill='{color}' "
        f"{FONT}>{label}</text>"
    )


def point(sid, name, category, glyph, label, desc, attrs=None):
    color = PALETTE[category]
    return {
        "id": sid,
        "source": "自定义（外框规则参照 GB/T 35649-2017）",
        "official": False,
        "name": name,
        "geometry": "point",
        "category": category,
        "svg": framed(color, glyph, label, rounded=category == "event"),
        "description": desc,
        "attributes": attrs or ["label", "time", "remark"],
    }


def line_preview(sid, stroke, dash="", arrow=False, width=4):
    marker = end = ""
    if arrow:
        marker = (
            f"<defs><marker id='arr-{sid}' viewBox='0 0 10 10' refX='8' refY='5' "
            "markerWidth='4' markerHeight='4' orient='auto'>"
            f"<path d='M0,0 L10,5 L0,10 z' fill='{stroke}'/></marker></defs>"
        )
        end = f"marker-end='url(#arr-{sid})'"
    dash_attr = f"stroke-dasharray='{dash}'" if dash else ""
    return svg(
        marker + f"<path d='M4,44 C18,20 40,48 56,18' fill='none' stroke='{stroke}' "
        f"stroke-width='{width}' {dash_attr} {end}/>"
    )


def line(sid, name, category, desc, dash="", arrow=False, width=4):
    color = PALETTE[category]
    return {
        "id": sid,
        "source": "自定义",
        "official": False,
        "name": name,
        "geometry": "line",
        "category": category,
        "style": {
            "stroke": color,
            "width": width,
            "dash": dash or None,
            "arrow_end": "filled" if arrow else None,
        },
        "svg": line_preview(sid, color, dash, arrow, width),
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
            f"<defs><pattern id='hatch-{sid}' width='8' height='8' "
            "patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>"
            f"<line x1='0' y1='0' x2='0' y2='8' stroke='{color}' stroke-width='3'/>"
            "</pattern></defs>"
        )
        fill = f"url(#hatch-{sid})"
    preview = svg(
        pattern + f"<polygon points='8,14 50,6 58,40 34,58 6,46' fill='{fill}' "
        f"fill-opacity='{0.6 if hatch else fill_opacity}' stroke='{color}' "
        f"stroke-width='3' {dash_attr}/>"
    )
    return {
        "id": sid,
        "source": "自定义",
        "official": False,
        "name": name,
        "geometry": "polygon",
        "category": category,
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


CUSTOM = [
    # ---------- 突发事件（圆角正方形） ----------
    point("EV-01", "泥石流", "event", "泥", "泥石流", "泥石流发生或暴发位置"),
    point("EV-02", "滑坡", "event", "滑", "滑坡", "滑坡发生位置"),
    point("EV-03", "崩塌", "event", "崩", "崩塌", "崩塌、落石发生位置"),
    point("EV-04", "堰塞体", "event", "堰", "堰塞体", "泥石流/滑坡堵江形成的堰塞体"),
    point("EV-05", "房屋倒塌/掩埋", "event", "塌", "房屋掩埋", "房屋被冲毁、掩埋位置"),
    point("EV-06", "道路中断", "event", "断", "道路中断", "道路被冲毁、掩埋的断点"),
    point("EV-07", "桥梁损毁", "event", "桥", "桥梁损毁", "桥梁冲毁或受损"),
    point(
        "EV-08",
        "失联人员（最后位置）",
        "event",
        "失",
        "失联",
        "失联人员最后已知位置；已确认被困人员用 XF 6.3.22",
        ["label", "count", "time", "remark"],
    ),
    point(
        "EV-09",
        "伤亡人员",
        "event",
        "伤",
        "伤亡",
        "伤员或遇难人员位置",
        ["label", "count", "time", "remark"],
    ),
    point("EV-10", "通信中断", "event", "讯", "通信中断", "公网/专网通信中断"),
    point("EV-11", "电力中断", "event", "电", "电力中断", "供电中断点"),
    # ---------- 危险源（直角正方形） ----------
    point("HZ-01", "不稳定斜坡", "hazard", "坡", "不稳定坡", "存在二次滑塌风险的斜坡"),
    point("HZ-02", "松散物源", "hazard", "源", "松散物源", "沟道内可能再次启动的松散堆积物"),
    point("HZ-03", "危险建筑", "hazard", "危", "危险建筑", "受损、可能倒塌的建筑物"),
    point("HZ-04", "危化品/油气", "hazard", "化", "危化品", "加油站、危化品仓库等"),
    point("HZ-05", "堰塞湖溃决风险点", "hazard", "溃", "溃决风险", "可能溃决的堰塞体或水库"),
    # ---------- 防护目标（直角正方形） ----------
    point("TG-01", "居民点", "target", "居", "居民点", "村庄、居民集中区"),
    point("TG-02", "学校", "target", "学", "学校", "学校、幼儿园"),
    point("TG-03", "医院/卫生院", "target", "医", "医院", "医疗机构"),
    point("TG-04", "水库/水电站", "target", "库", "水库", "水库、水电站"),
    point("TG-05", "重要设施", "target", "设", "重要设施", "变电站、通信基站、水厂等"),
    # ---------- 应急保障资源（直角正方形） ----------
    point("SP-01", "直升机起降点", "support", "H", "起降点", "临时直升机起降场"),
    point("SP-02", "临时医疗点", "support", "+", "医疗点", "伤员救治、转运点"),
    point("SP-03", "物资储备/发放点", "support", "资", "物资点", "救援物资集中点"),
    point("SP-04", "临时安置点", "support", "安", "安置点", "受灾群众临时安置"),
    point("SP-05", "工程机械", "support", "挖", "工程机械", "挖掘机、装载机等（XF/T 3013 无对应标号）"),
    point("SP-06", "生命探测设备", "support", "探", "生命探测", "生命探测仪、搜救犬等（XF/T 3013 无对应标号）"),
    point(
        "SP-07",
        "监测预警点",
        "support",
        "警",
        "监测预警",
        "泥石流沟上游监测、预警哨位；执勤人员可叠加 XF 6.1.25 侦察员",
    ),
    # ---------- 线状 ----------
    line("LN-01", "泥石流流向", "debris", "泥石流运动方向", arrow=True, width=6),
    line("LN-02", "泥石流沟道", "debris", "主沟、支沟走向", dash="10,6", width=4),
    line("LN-03", "救援行进路线（实施）", "force", "已实施的机动路线（实线=实际行动，XF 4.4.2）；计划路线用 XF 6.3.17", arrow=True, width=3),
    line("LN-04", "群众撤离路线", "support", "避险撤离方向；救援人员撤退用 XF 6.3.21", arrow=True, width=4),
    line("LN-05", "道路中断段", "event", "被冲毁或掩埋的路段", dash="2,5", width=6),
    line("LN-06", "警戒线", "force", "警戒/封控线", dash="12,4,2,4", width=3),
    line("LN-07", "任务分界线", "force", "相邻分队责任区分界", dash="16,6", width=3),
    # ---------- 面状 ----------
    area("AR-01", "泥石流堆积区", "debris", "已形成的堆积扇、掩埋区", fill_opacity=0.45),
    area("AR-02", "核心危险区", "event", "禁止无关人员进入", fill_opacity=0.35, hatch=True),
    area("AR-03", "警戒区", "event", "限制进入", fill_opacity=0.12, dash="10,5"),
    area("AR-04", "潜在影响区", "hazard", "二次泥石流可能波及范围", fill_opacity=0.15, dash="4,4"),
    area("AR-05", "搜救责任区", "force", "分配给某分队的搜救区域", fill_opacity=0.1),
    area("AR-06", "临时安置区", "support", "群众安置区域", fill_opacity=0.2),
    area("AR-07", "直升机作业区", "support", "起降及净空保护区", fill_opacity=0.15, dash="6,4"),
]

CUSTOM_CATEGORIES = {
    "event": "突发事件/灾情",
    "hazard": "危险源",
    "target": "防护目标",
    "support": "应急保障资源",
    "debris": "泥石流本体",
    "force": "救援行动",
}


def build():
    symbols = xf3013.SYMBOLS + CUSTOM
    ids = [s["id"] for s in symbols]
    assert len(ids) == len(set(ids)), "符号 id 重复"
    lib = {
        "name": "抢险救援标绘符号库（泥石流场景）",
        "version": "0.2.0",
        "sources": {
            "official": "XF/T 3013-2020《国家综合性消防救援队伍常用标号》（应急管理部 2020-11-10 发布）",
            "framework": "GB/T 35649-2017《突发事件应急标绘符号规范》（外框与分类规则）",
        },
        "rules": xf3013.RULES,
        "codes": xf3013.CODES,
        "palette": PALETTE,
        "categories": {**xf3013.CATEGORIES, **CUSTOM_CATEGORIES},
        "symbols": symbols,
    }
    (OUT_DIR / "symbols.json").write_text(
        json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (OUT_DIR / "preview.html").write_text(render_preview(lib), encoding="utf-8")
    n_off = sum(s["official"] for s in symbols)
    print(f"已生成 {len(symbols)} 个符号（官方 {n_off}，自定义 {len(symbols) - n_off}）")


def render_preview(lib):
    def cards(items):
        out = []
        for s in items:
            tag = s.get("std_code") or s["id"]
            badge = "official" if s["official"] else "custom"
            out.append(
                f"<div class='card'><div class='icon'>{s['svg']}</div>"
                f"<div class='id {badge}'>{tag}</div><div class='nm'>{s['name']}</div>"
                f"<div class='ds'>{s['description']}</div></div>"
            )
        return "".join(out)

    sections = ["<h1 class='part'>一、官方标号 · XF/T 3013-2020（重绘）</h1>"]
    for cat, cat_name in xf3013.CATEGORIES.items():
        items = [s for s in lib["symbols"] if s["official"] and s["category"] == cat]
        if items:
            sections.append(f"<h2>{cat_name}</h2><div class='grid'>{cards(items)}</div>")
    sections.append("<h1 class='part'>二、自定义补充（外框规则参照 GB/T 35649-2017）</h1>")
    geo_names = {"point": "点状", "line": "线状", "polygon": "面状"}
    for geo in ["point", "line", "polygon"]:
        for cat, cat_name in CUSTOM_CATEGORIES.items():
            items = [
                s
                for s in lib["symbols"]
                if not s["official"] and s["geometry"] == geo and s["category"] == cat
            ]
            if items:
                sections.append(
                    f"<h2>{geo_names[geo]} · {cat_name}</h2><div class='grid'>{cards(items)}</div>"
                )
    rules = lib["rules"]
    rule_rows = "".join(
        f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rules["color"].items()
    )
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>抢险救援标号库</title>
<style>
body{{font-family:"Microsoft YaHei","PingFang SC",sans-serif;margin:0;padding:16px;background:#f6f6f4;color:#222}}
h1{{font-size:20px}} h1.part{{font-size:17px;margin-top:32px;padding:6px 10px;background:#fff;border-radius:6px}}
h2{{font-size:15px;margin-top:22px;border-left:4px solid #E53935;padding-left:8px}}
.note{{background:#fff4e5;border:1px solid #f0c080;padding:10px;border-radius:6px;font-size:13px;line-height:1.6}}
table{{border-collapse:collapse;font-size:13px;margin-top:8px}} td{{border:1px solid #ddd;padding:4px 8px;background:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:10px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:8px;padding:10px;text-align:center}}
.icon svg{{width:60px;height:60px}} .nm{{font-weight:bold;font-size:14px}}
.id{{font-size:11px;display:inline-block;padding:1px 6px;border-radius:8px;margin:2px 0}}
.id.official{{background:#e8f5e9;color:#1b5e20}} .id.custom{{background:#eee;color:#666}}
.ds{{font-size:12px;color:#555;margin-top:4px}}
</style></head><body>
<h1>{lib['name']} v{lib['version']}</h1>
<div class="note">
<b>官方部分</b>：{lib['sources']['official']}，按标准原图重绘，编号为标准条目号（绿色标签）。<br>
<b>自定义部分</b>：泥石流等灾情符号 XF/T 3013 未覆盖，外框规则参照 {lib['sources']['framework']}；框内图形与编号为自定义（灰色标签）。<br>
武警部队内部标号未公开，本库不含。
</div>
<table><tr><td colspan="2"><b>XF/T 3013 颜色规定（4.1.2）</b></td></tr>{rule_rows}</table>
{''.join(sections)}
</body></html>"""


if __name__ == "__main__":
    build()
