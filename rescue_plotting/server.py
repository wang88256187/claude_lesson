"""抢险救援标绘 —— 本地服务（仅用 Python 标准库，无需安装依赖）。

作用：
1. 提供 app/ 目录下的标绘页面；
2. 把页面的大模型请求转发到 OpenAI 兼容接口（本地 Ollama / vLLM / Xinference 等，
   或测试用的 OpenRouter），避免浏览器跨域限制，API Key 也不会暴露给页面。

用法：
    # 本地大模型（示例：vLLM / Xinference 等 OpenAI 兼容服务）
    python server.py --llm-url http://127.0.0.1:8000/v1 --model qwen2.5-14b-instruct

    # Ollama
    python server.py --llm-url http://127.0.0.1:11434/v1 --model qwen2.5:14b

    # Qwen3 等推理模型：加 --no-think 关闭思考过程，响应从十几秒降到几秒
    python server.py --llm-url http://127.0.0.1:8000/v1 --model Qwen3-32B --no-think

    # OpenRouter 免费模型（仅用于测试，勿发送真实数据）
    set OPENROUTER_API_KEY=...        (Windows)  /  export OPENROUTER_API_KEY=...
    python server.py --llm-url https://openrouter.ai/api/v1 --model qwen/qwen3.8-27b:free

然后浏览器打开 http://127.0.0.1:8765

参数也可用环境变量：LLM_URL、LLM_MODEL、LLM_API_KEY（或 OPENROUTER_API_KEY）。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent / "app"
MAX_BODY = 2 * 1024 * 1024


class Handler(SimpleHTTPRequestHandler):
    llm = {}

    def log_message(self, fmt, *args):  # 精简日志：不打印请求内容
        sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/llm/config":
            return self._json(
                200,
                {
                    "enabled": bool(self.llm.get("url")),
                    "model": self.llm.get("model", ""),
                    "provider": self.llm.get("url", "").split("/")[2] if self.llm.get("url") else "",
                },
            )
        return super().do_GET()

    def do_POST(self):
        if self.path != "/api/llm/chat":
            return self._json(404, {"error": "not found"})
        if not self.llm.get("url"):
            return self._json(503, {"error": "未配置大模型，请用 --llm-url 启动"})
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY:
            return self._json(413, {"error": "请求过大"})
        try:
            req = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json(400, {"error": "请求不是合法 JSON"})

        payload = {
            "model": self.llm["model"],
            "messages": req.get("messages", []),
            "temperature": req.get("temperature", 0.1),
        }
        if self.llm.get("json_mode"):
            payload["response_format"] = {"type": "json_object"}
        payload.update(self.llm.get("extra_body") or {})
        headers = {"Content-Type": "application/json"}
        if self.llm.get("key"):
            headers["Authorization"] = "Bearer " + self.llm["key"]
        up = urllib.request.Request(
            self.llm["url"].rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
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
    a = ap.parse_args()

    extra = json.loads(a.extra_body) if a.extra_body else {}
    if a.no_think:
        extra.setdefault("chat_template_kwargs", {})["enable_thinking"] = False

    Handler.llm = {
        "url": a.llm_url, "model": a.model, "key": a.api_key,
        "json_mode": a.json_mode, "timeout": a.timeout, "extra_body": extra,
    }
    srv = ThreadingHTTPServer((a.host, a.port), partial(Handler, directory=str(APP_DIR)))
    print(f"标绘页面：http://{a.host}:{a.port}")
    print(f"大模型：{a.llm_url or '未配置（智能标图不可用）'} {a.model}" + ("（已关闭思考）" if a.no_think else ""))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
