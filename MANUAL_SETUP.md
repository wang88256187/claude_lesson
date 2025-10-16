# 手动启动指南

由于网络问题导致模型下载困难，这里提供完整的手动解决方案。

## 🎯 当前问题

嵌入模型配置文件下载超时，原因可能是：
1. HuggingFace 访问受限
2. 网络代理设置问题
3. 防火墙拦截

---

## ✅ 解决方案

### 方案 A: 使用已下载的模型（推荐）

模型主体已经下载成功（90MB），只是配置文件有问题。

**步骤：**

1. **打开新的命令行窗口**（以管理员身份）

2. **激活环境**
   ```bash
   conda activate ragchatbot
   ```

3. **进入项目目录**
   ```bash
   cd F:\case_ml\starting-ragchatbot-codebase\backend
   ```

4. **设置环境变量并启动**
   ```bash
   set HF_ENDPOINT=https://hf-mirror.com
   set HF_HUB_OFFLINE=1
   python -m uvicorn app:app --reload --port 8000
   ```

   `HF_HUB_OFFLINE=1` 会让系统使用已下载的模型，不再尝试联网。

---

### 方案 B: 配置代理（如果你有VPN）

1. **设置HTTP代理**
   ```bash
   set HTTP_PROXY=http://127.0.0.1:7890
   set HTTPS_PROXY=http://127.0.0.1:7890
   ```
   （根据你的代理端口调整）

2. **启动服务**
   ```bash
   conda activate ragchatbot
   cd F:\case_ml\starting-ragchatbot-codebase\backend
   python -m uvicorn app:app --reload --port 8000
   ```

---

### 方案 C: 简化测试（跳过嵌入模型）

如果只想测试 Gemini 是否工作，可以暂时禁用向量搜索功能。

---

## 🧪 测试步骤

启动成功后，你会看到：
```
INFO:     Application startup complete.
Loading initial documents...
Loaded X courses with Y chunks
```

然后访问：
- **前端**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

---

## 📝 测试问题

启动后尝试这些问题：

1. **通用问题**（不需要搜索）
   - "What is AI?"
   - "Explain machine learning"

2. **课程相关问题**（需要搜索）
   - "What courses are available?"
   - "Tell me about the MCP course"

---

## ❓ 常见问题

### Q: 服务启动很慢
A: 首次加载嵌入模型需要时间，请耐心等待2-3分钟

### Q: 仍然提示模型下载错误
A: 使用 `HF_HUB_OFFLINE=1` 环境变量强制离线模式

### Q: Gemini API 报错
A: 检查 `.env` 文件中的 `GEMINI_API_KEY` 是否正确

---

## 🔍 检查日志

如果有问题，查看终端输出的错误信息：
- `404 models/xxx` → 模型名称错误
- `401` → API Key 无效
- `timeout` → 网络问题

---

## 📞 下一步

如果方案 A 成功启动，请：
1. 访问 http://localhost:8000
2. 尝试发送一个简单问题
3. 观察是否有响应

成功后我们可以进一步优化配置。
