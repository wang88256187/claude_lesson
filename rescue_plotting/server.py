"""抢险救援标绘 —— 本地服务（仅用 Python 标准库，无需安装依赖）。

作用：
1. 提供 app/ 目录下的标绘页面；
2. 转发大模型请求到 OpenAI 兼容接口（本地 Ollama / vLLM / Xinference 等），
   避免浏览器跨域限制，API Key 也不会暴露给页面；
3. 地图瓦片缓存代理：/tiles/<底图>/<z>/<x>/<y>。联网时边浏览边缓存到本地磁盘，
   断网（--offline）后仍可显示已浏览过的区域；
4. OSM 地名查询（Overpass，多镜像重试）与地名搜索（Nominatim），供“智能标图”引用真实地名。

用法：
    # 本地大模型（vLLM / Xinference 等 OpenAI 兼容服务）
    python server.py --llm-url http://127.0.0.1:8000/v1 --model qwen2.5-14b-instruct

    # Ollama
    python server.py --llm-url http://127.0.0.1:11434/v1 --model qwen2.5:14b

    # Qwen3 等推理模型：加 --no-think 关闭思考过程，响应从十几秒降到几秒
    python server.py --llm-url http://127.0.0.1:8000/v1 --model Qwen3-32B --no-think

    # 断网使用：只用本地已缓存的瓦片，不访问外网
    python server.py --offline

然后浏览器打开 http://127.0.0.1:8765

参数也可用环境变量：LLM_URL、LLM_MODEL、LLM_API_KEY（或 OPENROUTER_API_KEY）。

注意：在线底图（OSM、Esri 影像、OpenTopoMap）有各自的使用条款，请勿批量下载；
正式部署建议在内网搭建瓦片服务，并在页面“自定义瓦片地址”中填写。
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP_DIR = ROOT / "app"
MAX_BODY = 2 * 1024 * 1024
UA = "rescue-plotting/0.4 (emergency plotting tool; local tile cache)"

# 瓦片源：{z}{x}{y}；{s} 为子域名轮换
TILE_SOURCES = {
    "osm": ("https://tile.openstreetmap.org/{z}/{x}/{y}.png", "png", ""),
    "img": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "jpg", ""),
    "label": ("https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}", "png", ""),
    "topo": ("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", "png", "abc"),
}
TILE_RE = re.compile(r"^/tiles/(\w+)/(\d{1,2})/(\d{1,7})/(\d{1,7})(?:\.\w+)?$")

OVERPASS = [
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]
NOMINATIM = "https://nominatim.openstreetmap.org/search"


def fetch(url, data=None, timeout=60):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


class Handler(SimpleHTTPRequestHandler):
    llm = {}
    offline = False
    cache_dir = ROOT / "tile_cache"

    def log_message(self, fmt, *args):  # 精简日志：不记录瓦片请求和请求内容
        if not getattr(self, "path", "").startswith("/tiles/"):
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            raise ValueError("请求过大")
        return json.loads(self.rfile.read(length) or b"{}")

    # ------------------------------------------------------------ GET

    def do_GET(self):
        path = urllib.parse.urlsplit(self.path).path
        if path == "/api/llm/config":
            return self._json(200, {
                "enabled": bool(self.llm.get("url")),
                "model": self.llm.get("model", ""),
                "provider": self.llm.get("url", "").split("/")[2] if self.llm.get("url") else "",
            })
        if path == "/api/status":
            return self._json(200, {
                "llm": bool(self.llm.get("url")), "offline": self.offline,
                "tiles": sorted(TILE_SOURCES), "osm": not self.offline,
            })
        if path == "/api/geocode":
            return self._geocode()
        m = TILE_RE.match(path)
        if m:
            return self._tile(*m.groups())
        return super().do_GET()

    def _tile(self, src, z, x, y):
        if src not in TILE_SOURCES or int(z) > 19:
            return self.send_error(404)
        url_t, ext, subs = TILE_SOURCES[src]
        f = self.cache_dir / src / z / x / f"{y}.{ext}"
        if not f.exists():
            if self.offline:
                return self.send_error(404, "Tile not cached (offline mode)")
            s = subs[(int(x) + int(y)) % len(subs)] if subs else ""
            try:
                data, _ = fetch(url_t.format(z=z, x=x, y=y, s=s), timeout=30)
            except Exception:
                return self.send_error(502, "Tile fetch failed")
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        body = f.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg" if ext == "jpg" else "image/png")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "max-age=604800")
        self.end_headers()
        self.wfile.write(body)

    def _geocode(self):
        if self.offline:
            return self._json(503, {"error": "离线模式不可用"})
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("q", [""])[0].strip()
        if not q:
            return self._json(400, {"error": "缺少 q"})
        url = NOMINATIM + "?" + urllib.parse.urlencode({"format": "json", "q": q, "limit": 5, "accept-language": "zh-CN"})
        try:
            data, _ = fetch(url, timeout=30)
        except Exception as e:
            return self._json(502, {"error": f"地名搜索失败：{e}"})
        res = [{"name": r["display_name"], "lat": float(r["lat"]), "lon": float(r["lon"]),
                "bbox": [float(v) for v in r.get("boundingbox", [])]} for r in json.loads(data)]
        return self._json(200, {"results": res})

    # ------------------------------------------------------------ POST

    def do_POST(self):
        try:
            req = self._read_json()
        except ValueError as e:
            return self._json(400, {"error": f"请求不合法：{e}"})
        if self.path == "/api/llm/chat":
            return self._llm(req)
        if self.path == "/api/osm/overpass":
            return self._overpass(req)
        return self._json(404, {"error": "not found"})

    def _overpass(self, req):
        if self.offline:
            return self._json(503, {"error": "离线模式不可用"})
        q = req.get("query", "")
        if not q or len(q) > 4000:
            return self._json(400, {"error": "查询为空或过长"})
        body = urllib.parse.urlencode({"data": q}).encode()
        last = ""
        for attempt in range(3):
            for url in OVERPASS:
                try:
                    data, _ = fetch(url, data=body, timeout=90)
                    return self._json(200, json.loads(data))
                except Exception as e:  # 镜像不稳定：换下一个
                    last = str(e)
            time.sleep(1.5)
        return self._json(502, {"error": f"OSM 地名查询失败：{last}"})

    def _llm(self, req):
        if not self.llm.get("url"):
            return self._json(503, {"error": "未配置大模型，请用 --llm-url 启动"})
        payload = {
            "model": self.llm["model"],
            "messages": req.get("messages", []),
            "temperature": req.get("temperature", 0.1),
        }
        if self.llm.get("json_mode"):
            payload["response_format"] = {"type": "json_object"}
        payload.update(self.llm.get("extra_body") or {})
        headers = {"Content-Type": "application/json", "User-Agent": UA}
        if self.llm.get("key"):
            headers["Authorization"] = "Bearer " + self.llm["key"]
        up = urllib.request.Request(
            self.llm["url"].rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(up, timeout=self.llm.get("timeout", 180)) as r:
                data = json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            return self._json(502, {"error": f"大模型接口返回 {e.code}", "detail": detail})
        except Exception as e:  # 网络不通、超时等
            return self._json(502, {"error": f"无法连接大模型接口：{e}"})
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return self._json(502, {"error": "大模型返回格式不符合 OpenAI 接口", "detail": str(data)[:500]})
        return self._json(200, {"content": content, "model": data.get("model", self.llm["model"])})


def main():
    ap = argparse.ArgumentParser(description="抢险救援标绘本地服务")
    ap.add_argument("--host", default="127.0.0.1", help="监听地址，局域网共享可用 0.0.0.0")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--llm-url", default=os.environ.get("LLM_URL", ""), help="OpenAI 兼容接口地址，如 http://127.0.0.1:8000/v1")
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL", ""))
    ap.add_argument("--api-key", default=os.environ.get("LLM_API_KEY") or os.environ.get("OPENROUTER_API_KEY", ""))
    ap.add_argument("--json-mode", action="store_true", help="向接口请求 JSON 输出（需模型服务支持 response_format）")
    ap.add_argument("--no-think", action="store_true",
                    help="关闭 Qwen3 等推理模型的思考过程（chat_template_kwargs.enable_thinking=false），响应快得多")
    ap.add_argument("--extra-body", default=os.environ.get("LLM_EXTRA_BODY", ""),
                    help='附加到请求体的 JSON，如 \'{"top_p":0.8}\'')
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--offline", action="store_true", help="离线模式：只使用本地已缓存的瓦片，不访问外网")
    ap.add_argument("--cache-dir", default=str(ROOT / "tile_cache"), help="瓦片缓存目录")
    a = ap.parse_args()

    extra = json.loads(a.extra_body) if a.extra_body else {}
    if a.no_think:
        extra.setdefault("chat_template_kwargs", {})["enable_thinking"] = False

    Handler.llm = {
        "url": a.llm_url, "model": a.model, "key": a.api_key,
        "json_mode": a.json_mode, "timeout": a.timeout, "extra_body": extra,
    }
    Handler.offline = a.offline
    Handler.cache_dir = Path(a.cache_dir)
    srv = ThreadingHTTPServer((a.host, a.port), partial(Handler, directory=str(APP_DIR)))
    print(f"标绘页面：http://{a.host}:{a.port}")
    print(f"大模型：{a.llm_url or '未配置（智能标图不可用）'} {a.model}" + ("（已关闭思考）" if a.no_think else ""))
    print(f"瓦片缓存：{Handler.cache_dir}" + ("（离线模式）" if a.offline else ""))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
