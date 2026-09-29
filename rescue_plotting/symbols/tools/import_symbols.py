"""本单位标号导入工具（离线运行，不访问网络）。

把本单位标号的图片矢量化，生成可在标绘页面中使用的“本单位”符号库。
导入结果只写到本机的 symbols/local/ 和 app/local_symbols.js（均已加入 .gitignore，不会提交到代码仓库）。

输入（二选一）：
  1. 标号采集页（app/tools/cropper.html）导出的 JSON：扫描件上框选的标号 + 编号/名称/类型；
  2. 一个文件夹：每个标号一张图片（png/jpg/bmp），可附 manifest.csv 说明编号、名称等。

用法：
  python import_symbols.py 采集结果.json
  python import_symbols.py 标号图片文件夹/
  python import_symbols.py init 标号图片文件夹/      # 为文件夹生成 manifest.csv 模板，填好后再导入
  python import_symbols.py pdf2png 规定.pdf 输出文件夹/ [--dpi 200]   # 把 PDF 扫描件转成图片（需 pymupdf）

常用参数：
  --source "某部常用标号（2024）"   符号来源说明，显示在页面上
  --snap                             把颜色吸附到标准色（红/黑/蓝/绿/黄/粉红），适合扫描件偏色
  --append                           追加到已有的本单位库（默认覆盖）
  --preview                          同时生成 symbols/local/preview.html 核对效果

manifest.csv 列（除 file 外均可留空）：
  file,code,name,geometry,category,color,mode,description,stroke,width,dash,arrow
  geometry：point（默认）/ line / polygon；线、面符号的图片只作预览，
            地图上按 stroke（颜色）、width（线宽）、dash（虚线，如 8,4）、arrow（open/filled）绘制
  mode：mono（单色，默认自动判断）/ multi（保留多种颜色）

依赖：pip install numpy pillow potracer   （pdf2png 另需 pymupdf）
"""

import argparse
import base64
import csv
import html
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
import potrace
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]          # rescue_plotting/
LOCAL_DIR = ROOT / "symbols" / "local"
LOCAL_JSON = LOCAL_DIR / "unit_symbols.json"
LOCAL_JS = ROOT / "app" / "local_symbols.js"
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"}

STD_COLORS = {  # 军队标号/XF 3013 常用色
    "#E53935": (229, 57, 53),    # 红
    "#222222": (34, 34, 34),     # 黑
    "#1E4FB5": (30, 79, 181),    # 蓝
    "#2E9E3E": (46, 158, 62),    # 绿
    "#F2C200": (242, 194, 0),    # 黄
    "#F48FB1": (244, 143, 177),  # 粉红（友军）
}


# ---------------------------------------------------------------- 图像处理

def load_rgb(src):
    """src: 路径或 data URL；透明背景按白色处理。"""
    if isinstance(src, str) and src.startswith("data:"):
        im = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1])))
    else:
        im = Image.open(src)
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    return np.asarray(Image.alpha_composite(bg, im).convert("RGB")).astype(np.int16)


def otsu(values):
    hist, edges = np.histogram(values, bins=256)
    w = hist.cumsum()
    mu = (hist * edges[:-1]).cumsum()
    total, mu_t = w[-1], mu[-1]
    w1 = total - w
    valid = (w > 0) & (w1 > 0)
    between = np.zeros_like(mu, dtype=float)
    between[valid] = (mu_t * w[valid] - mu[valid] * total) ** 2 / (w[valid] * w1[valid])
    return edges[between.argmax()]


def ink_mask(rgb):
    """以边缘像素估计纸张底色，按与底色的差异用 Otsu 自适应分割笔迹（兼容泛黄、泛灰、模糊的扫描件）。
    返回 (笔迹掩膜, 差异值)。"""
    border = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    paper = np.median(border, axis=0)
    diff = np.sqrt(((rgb - paper) ** 2).sum(-1))
    t = max(otsu(diff.ravel()), 45.0)  # 下限防止把纸张纹理当笔迹
    return diff > t, diff


def kmeans(px, k, iters=12, seed=0):
    rng = np.random.default_rng(seed)
    c = px[rng.choice(len(px), size=min(k, len(px)), replace=False)].astype(float)
    for _ in range(iters):
        d = ((px[:, None, :] - c[None]) ** 2).sum(-1)
        lab = d.argmin(1)
        for i in range(len(c)):
            if (lab == i).any():
                c[i] = px[lab == i].mean(0)
    return c, lab


def color_layers(rgb, mask, diff, mode="auto", fixed_color=None, snap=False):
    """把笔迹分成若干颜色层：[(颜色hex, 掩膜)]，面积大的在前。
    取色只用笔画中心（与纸色差异最大的一半像素），避免边缘与纸色混合导致发灰发暗。"""
    core = mask & (diff >= np.percentile(diff[mask], 50))
    px = rgb[core].astype(float)
    if fixed_color:
        return [(fixed_color, mask)]
    layers = []
    if mode != "mono" and len(px) > 50:
        sample = px[np.random.default_rng(1).choice(len(px), size=min(4000, len(px)), replace=False)]
        centers, _ = kmeans(sample, 3)
        # 合并相近的颜色中心
        merged = []
        for c in centers:
            if all(np.linalg.norm(c - m) > 70 for m in merged):
                merged.append(c)
        if len(merged) > 1:
            allpx = rgb[mask].astype(float)
            d = ((allpx[:, None, :] - np.array(merged)[None]) ** 2).sum(-1)
            lab = d.argmin(1)
            full = np.zeros(mask.shape, dtype=int) - 1
            full[mask] = lab
            for i, c in enumerate(merged):
                m = full == i
                if m.sum() > 0.03 * mask.sum():
                    layers.append((c, m))
    if len(layers) <= 1 or mode == "mono":
        layers = [(np.median(px, axis=0), mask)]
    layers.sort(key=lambda t: -t[1].sum())
    return [(to_hex(c, snap), m) for c, m in layers]


def to_hex(c, snap):
    c = np.clip(np.asarray(c), 0, 255)
    if snap:
        best = min(STD_COLORS.items(), key=lambda kv: np.linalg.norm(c - np.array(kv[1])))
        return best[0]
    # 扫描件颜色偏灰：以灰度为中心适度提高饱和度
    g = c.mean()
    c = np.clip(g + (c - g) * 1.25, 0, 255)
    return "#%02X%02X%02X" % tuple(int(v) for v in c)


def trace_mask(mask, sx, sy):
    path = potrace.Bitmap(~mask).trace(turdsize=12, alphamax=1.0, opticurve=True, opttolerance=0.2)

    def p(pt):
        return f"{pt.x * sx:.2f},{pt.y * sy:.2f}"

    out = []
    for curve in path:
        out.append(f"M{p(curve.start_point)}")
        for seg in curve:
            if seg.is_corner:
                out.append(f"L{p(seg.c)}L{p(seg.end_point)}")
            else:
                out.append(f"C{p(seg.c1)} {p(seg.c2)} {p(seg.end_point)}")
        out.append("Z")
    return "".join(out)


def vectorize(src, mode="auto", color=None, snap=False, max_px=600):
    rgb = load_rgb(src)
    h, w = rgb.shape[:2]
    if max(h, w) > max_px:  # 过大的图先缩小，加快描摹
        s = max_px / max(h, w)
        im = Image.fromarray(rgb.astype(np.uint8)).resize((max(1, int(w * s)), max(1, int(h * s))), Image.LANCZOS)
        rgb = np.asarray(im).astype(np.int16)
    mask, diff = ink_mask(rgb)
    ys, xs = np.nonzero(mask)
    if not len(xs):
        raise ValueError("图片中没有识别到笔迹（可能太淡或全白）")
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    p = int(max(y1 - y0, x1 - x0) * 0.05) + 1
    y0, x0 = max(0, y0 - p), max(0, x0 - p)
    y1, x1 = min(mask.shape[0], y1 + p), min(mask.shape[1], x1 + p)
    rgb, mask, diff = rgb[y0:y1, x0:x1], mask[y0:y1, x0:x1], diff[y0:y1, x0:x1]
    h, w = mask.shape
    scale = 64 / max(h, w)
    vw, vh = round(w * scale, 2), round(h * scale, 2)
    layers = color_layers(rgb, mask, diff, mode, color, snap)
    paths = "".join(
        f"<path d='{trace_mask(m, scale, scale)}' fill='{c}' fill-rule='evenodd'/>" for c, m in layers
    )
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {vw} {vh}'>{paths}</svg>"
    return svg, layers[0][0], [c for c, _ in layers]


# ---------------------------------------------------------------- 条目

def norm_geom(g):
    g = (g or "point").strip().lower()
    return {"点": "point", "线": "line", "面": "polygon", "area": "polygon"}.get(g, g if g in ("point", "line", "polygon") else "point")


def make_entry(src, meta, args, idx):
    code = (meta.get("code") or "").strip() or f"{idx:03d}"
    name = (meta.get("name") or "").strip() or code
    geom = norm_geom(meta.get("geometry"))
    color = (meta.get("color") or "").strip() or None
    svg, main_color, colors = vectorize(src, (meta.get("mode") or "auto").strip() or "auto", color, args.snap)
    e = {
        "id": "U-" + re.sub(r"\s+", "", code),
        "std_code": code,
        "source": args.source,
        "official": True,
        "unit": True,
        "name": name,
        "geometry": geom,
        "category": "U-" + ((meta.get("category") or "").strip() or "未分类"),
        "color": main_color,
        "svg": svg,
        "description": (meta.get("description") or "").strip(),
        "attributes": ["label", "headcount", "equipment", "task", "time", "remark"] if geom == "point" else ["label", "time", "remark"],
    }
    if geom != "point":
        stroke = (meta.get("stroke") or "").strip() or main_color
        style = {"stroke": stroke, "width": float(meta.get("width") or 2.5)}
        if (meta.get("dash") or "").strip():
            style["dash"] = meta["dash"].strip()
        if (meta.get("arrow") or "").strip():
            style["arrow_end"] = meta["arrow"].strip()
        if geom == "polygon":
            style.update({"fill": stroke, "fill_opacity": float(meta.get("fill_opacity") or 0.08)})
        e["style"] = style
    return e


def read_manifest(folder):
    f = folder / "manifest.csv"
    if not f.exists():
        return {}
    with open(f, encoding="utf-8-sig", newline="") as fh:
        return {row["file"].strip(): row for row in csv.DictReader(fh) if row.get("file")}


def from_folder(folder, args):
    manifest = read_manifest(folder)
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)
    if not files:
        sys.exit(f"文件夹中没有图片：{folder}")
    out, errs = [], []
    for i, p in enumerate(files, 1):
        meta = dict(manifest.get(p.name, {}))
        meta.setdefault("name", p.stem)
        if not meta.get("code"):
            m = re.match(r"^([\w.\-]+?)[_\s]+(.+)$", p.stem)  # 文件名“编号_名称”
            if m:
                meta["code"] = m.group(1)
                if meta.get("name", "").strip() in ("", p.stem):  # 用户在清单里填了名称则保留
                    meta["name"] = m.group(2)
        try:
            out.append(make_entry(str(p), meta, args, i))
            print(f"  ✓ {p.name} → {out[-1]['id']} {out[-1]['name']}")
        except Exception as e:
            errs.append(f"{p.name}: {e}")
    return out, errs


def from_capture(jsonfile, args):
    data = json.loads(Path(jsonfile).read_text(encoding="utf-8"))
    if not args.source_given and data.get("source"):
        args.source = data["source"]
    out, errs = [], []
    for i, it in enumerate(data.get("items", []), 1):
        try:
            out.append(make_entry(it["image"], it, args, i))
            print(f"  ✓ {out[-1]['id']} {out[-1]['name']}")
        except Exception as e:
            errs.append(f"第 {i} 个（{it.get('name', '')}）: {e}")
    return out, errs


# ---------------------------------------------------------------- 输出

def write_outputs(entries, args):
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    old = []
    if args.append and LOCAL_JSON.exists():
        old = json.loads(LOCAL_JSON.read_text(encoding="utf-8")).get("symbols", [])
    ids = {e["id"] for e in entries}
    merged = [e for e in old if e["id"] not in ids] + entries
    cats = sorted({e["category"] for e in merged})
    lib = {"source": args.source, "symbols": merged, "categories": {c: "本单位 · " + c[2:] for c in cats}}
    LOCAL_JSON.write_text(json.dumps(lib, ensure_ascii=False, indent=1), encoding="utf-8")
    LOCAL_JS.write_text(
        "/* 本单位标号（由 symbols/tools/import_symbols.py 生成；本文件已加入 .gitignore，请勿提交或外传） */\n"
        "window.LOCAL_SYMBOL_LIB = " + json.dumps(lib, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    if args.preview:
        cards = "".join(
            f"<div class=c><div class=i>{e['svg']}</div><b>{html.escape(e['name'])}</b>"
            f"<small>{html.escape(e['std_code'])} · {html.escape(e['category'][2:])} · {e['geometry']}</small></div>"
            for e in merged
        )
        (LOCAL_DIR / "preview.html").write_text(
            "<!doctype html><meta charset=utf-8><title>本单位标号预览</title>"
            "<style>body{font-family:sans-serif;padding:16px;background:#f5f5f5}.c{display:inline-flex;flex-direction:column;"
            "align-items:center;gap:4px;width:130px;margin:6px;padding:8px;background:#fff;border:1px solid #ddd;border-radius:6px}"
            ".i svg{width:72px;height:72px}small{color:#777;font-size:11px}</style>"
            f"<h2>{html.escape(args.source)}（{len(merged)} 个）</h2>{cards}",
            encoding="utf-8",
        )
    return merged


def cmd_init(folder):
    folder = Path(folder)
    files = sorted(p.name for p in folder.iterdir() if p.suffix.lower() in IMG_EXT)
    f = folder / "manifest.csv"
    if f.exists():
        sys.exit(f"{f} 已存在，未覆盖")
    with open(f, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "code", "name", "geometry", "category", "color", "mode", "description", "stroke", "width", "dash", "arrow"])
        for n in files:
            w.writerow([n, "", Path(n).stem, "point", "", "", "", "", "", "", "", ""])
    print(f"已生成 {f}（{len(files)} 行），请用 Excel/WPS 填写后再导入")


def cmd_pdf2png(pdf, outdir, dpi):
    import pymupdf
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    d = pymupdf.open(pdf)
    for i, page in enumerate(d, 1):
        page.get_pixmap(dpi=dpi).save(outdir / f"page_{i:03d}.png")
    print(f"已输出 {d.page_count} 页到 {outdir}，可在标号采集页中打开框选")


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        return cmd_init(sys.argv[2])
    if len(sys.argv) > 1 and sys.argv[1] == "pdf2png":
        dpi = int(sys.argv[sys.argv.index("--dpi") + 1]) if "--dpi" in sys.argv else 200
        return cmd_pdf2png(sys.argv[2], sys.argv[3], dpi)
    ap = argparse.ArgumentParser(description="本单位标号导入（离线）")
    ap.add_argument("input", help="采集页导出的 JSON，或标号图片文件夹")
    ap.add_argument("--source", default="本单位常用标号")
    ap.add_argument("--snap", action="store_true", help="颜色吸附到标准色")
    ap.add_argument("--append", action="store_true", help="追加到已有的本单位库")
    ap.add_argument("--preview", action="store_true", help="生成 symbols/local/preview.html")
    args = ap.parse_args()
    args.source_given = "--source" in sys.argv

    src = Path(args.input)
    print(f"导入：{src}")
    entries, errs = from_folder(src, args) if src.is_dir() else from_capture(src, args)
    if not entries:
        sys.exit("没有成功导入任何标号。\n" + "\n".join(errs))
    merged = write_outputs(entries, args)
    print(f"\n完成：本次 {len(entries)} 个，本单位库共 {len(merged)} 个")
    print(f"  符号库：{LOCAL_JSON}")
    print(f"  页面加载文件：{LOCAL_JS}（刷新标绘页面即可在「本单位」分组中使用）")
    if args.preview:
        print(f"  预览：{LOCAL_DIR / 'preview.html'}")
    if errs:
        print("\n以下条目失败：\n  " + "\n  ".join(errs))


if __name__ == "__main__":
    main()
