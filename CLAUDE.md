# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于检索增强生成（RAG）的课程资料问答系统。使用 ChromaDB 进行向量存储，Google Gemini API 生成回答，并提供 Web 界面进行交互。

## 核心架构

### 主要组件

**RAGSystem** (backend/rag_system.py) - 系统主协调器：
- 协调文档处理、向量存储、AI 生成和对话历史等所有组件
- 处理单个文件或文件夹的课程文档导入
- 实现基于工具的搜索架构，AI 可以动态调用搜索工具
- 返回结构化响应和来源信息

**VectorStore** (backend/vector_store.py) - 基于 ChromaDB 的向量存储：
- 使用两个集合：`course_catalog`（课程元数据）和 `course_content`（实际内容块）
- 实现智能课程名称解析，使用语义搜索
- 支持按课程名称和课时编号过滤
- 使用 sentence-transformers 进行嵌入（all-MiniLM-L6-v2 模型）

**AIGenerator** (backend/ai_generator.py) - Google Gemini API 接口：
- 使用 Gemini 2.5 Flash 模型（通过 GEMINI_API_KEY 环境变量配置）
- 将工具定义从 Anthropic 格式转换为 Gemini 函数调用格式
- 实现工具执行循环：查询 → 函数调用 → 工具执行 → 最终响应
- 系统提示强制要求简洁回答和正确的工具使用

**ToolManager & CourseSearchTool** (backend/search_tools.py)：
- 抽象的 `Tool` 接口，支持可扩展的工具系统
- `CourseSearchTool` 提供课程内容的语义搜索
- 跟踪搜索来源以便在 UI 中显示
- 工具定义兼容 AI 函数调用

**DocumentProcessor** (backend/document_processor.py)：
- 解析特定格式的课程文档（标题、链接、讲师、课时）
- 实现基于句子的分块，可配置重叠部分
- 从文档中提取课时结构和元数据
- 为分块添加上下文前缀（例如："Course X Lesson Y content: ..."）

### 数据模型

**Course, Lesson, CourseChunk** (backend/models.py)：
- 使用 Pydantic 的结构化课程数据模型
- Course 使用 title 作为唯一标识符
- CourseChunk 跟踪 course_title、lesson_number 和 chunk_index

### API 应用

**FastAPI 应用** (backend/app.py)：
- `/api/query` - POST 端点用于查询（接受 query 和可选的 session_id）
- `/api/courses` - GET 端点获取课程统计信息
- 从 `frontend/` 目录提供前端静态文件
- 启动时从 `docs/` 文件夹加载文档

## 开发命令

### 安装开发依赖

**首次设置：**
```bash
# 安装开发工具（Windows conda 环境）
conda activate ragchatbot
pip install -e ".[dev]"

# 或单独安装
pip install black flake8 isort pre-commit
```

### 代码质量工具

项目使用以下工具确保代码质量：
- **Black** - 自动代码格式化（行长度 88）
- **isort** - 导入语句排序
- **flake8** - 代码风格和质量检查
- **pre-commit** - Git 提交前自动检查

**格式化代码：**
```bash
# Windows
format_code.bat

# Unix/Linux/Mac
chmod +x format_code.sh
./format_code.sh
```

**运行质量检查：**
```bash
# Windows
quality_check.bat

# Unix/Linux/Mac
chmod +x quality_check.sh
./quality_check.sh
```

**手动运行工具：**
```bash
# 格式化代码
black backend
isort backend

# 检查代码质量
flake8 backend

# 设置 pre-commit hooks
pre-commit install
pre-commit run --all-files
```

### 运行应用

**Windows（推荐用于当前环境）：**
```bash
# 使用 conda 环境
conda activate ragchatbot
cd backend
python -m uvicorn app:app --reload --port 8000

# 使用 HuggingFace 镜像（解决模型下载问题）
cmd /c start_with_mirror.bat
```

**Unix/Linux/Mac：**
```bash
# 使用 uv 包管理器
./run.sh

# 或手动运行
cd backend
uv run uvicorn app:app --reload --port 8000
```

### 测试

使用 curl 测试 API 端点：
```bash
# 测试基本查询
curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" -d "{\"query\":\"What courses are available?\"}" --max-time 30

# 测试特定课程查询
curl -X POST http://localhost:8000/api/query -H "Content-Type: application/json" -d "{\"query\":\"Tell me about MCP course\"}" --max-time 60

# 获取课程统计信息
curl http://localhost:8000/api/courses
```

访问地址：
- Web 界面：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 配置

**环境变量**（.env 文件）：
- `GEMINI_API_KEY` - Google Gemini API 密钥（必需，为了兼容性存储为 ANTHROPIC_API_KEY）
- 模型：gemini-2.5-flash（在 backend/config.py 中配置）

**配置设置**（backend/config.py）：
- `CHUNK_SIZE: 800` - 向量存储的文本块大小
- `CHUNK_OVERLAP: 100` - 块之间的字符重叠
- `MAX_RESULTS: 5` - 返回的最大搜索结果数
- `MAX_HISTORY: 2` - 记住的对话消息数
- `EMBEDDING_MODEL: all-MiniLM-L6-v2` - Sentence transformer 模型
- `CHROMA_PATH: ./chroma_db` - ChromaDB 存储位置

## 文档格式

`docs/` 文件夹中的课程文档应遵循以下结构：

```
Course Title: [标题]
Course Link: [URL]
Course Instructor: [讲师名]

Lesson 0: [课时标题]
Lesson Link: [URL]
[课时内容]

Lesson 1: [课时标题]
Lesson Link: [URL]
[课时内容]
```

支持的格式：.pdf、.docx、.txt

## 关键设计模式

### 基于工具的 RAG 架构
系统不是直接检索文档并传递给 AI，而是使用函数调用：
1. 用户查询发送给 AI，带有工具定义
2. AI 决定用适当参数调用 `search_course_content` 工具
3. ToolManager 执行搜索并返回格式化结果
4. AI 从搜索结果中合成最终响应

### 双集合向量策略
- **course_catalog**：存储课程元数据（标题、讲师、课时 JSON），用于语义课程名称匹配
- **course_content**：存储带有元数据过滤器的内容块，用于精确检索

### 智能课程名称解析
当用户提到课程名称（部分或非正式的）时，VectorStore 在 course_catalog 上使用语义搜索找到最匹配的课程标题，然后用它来过滤内容搜索。

## 常见问题

- **模型下载问题**：在有网络限制的 Windows 上，使用 `HF_HUB_OFFLINE=1` 环境变量或 HuggingFace 镜像端点（https://hf-mirror.com）
- **重复课程**：系统在添加前检查现有课程标题，避免重复处理
- **块上下文**：文档处理器为块添加课时上下文以提高检索准确性
- **API 密钥命名**：尽管使用 Gemini，配置仍使用 `ANTHROPIC_API_KEY` 变量名以保持向后兼容

## Windows 特定说明

此代码库包含 Windows 特定的批处理文件：
- `start_with_mirror.bat` - 启动前设置 HF_ENDPOINT 为中国镜像
- `start_offline.bat` - 强制 HuggingFace 模型离线模式
- 使用名为 `ragchatbot` 的 conda 环境，Python 位于 `F:/miniconda/envs/ragchatbot/`
