# RAG 聊天机器人查询处理流程图

## 完整架构流程图

```mermaid
graph TB
    %% 前端层
    subgraph Frontend["🌐 前端层 (Frontend)"]
        A[👤 用户输入问题] --> B[script.js: sendMessage]
        B --> C{禁用输入框<br/>显示加载动画}
        C --> D[POST /api/query<br/>{query, session_id}]
    end

    %% FastAPI 层
    subgraph Backend["⚙️ 后端层 (Backend)"]
        D --> E[app.py: query_documents]
        E --> F{检查 session_id}
        F -->|不存在| G[创建新会话]
        F -->|存在| H[rag_system.query]
        G --> H
    end

    %% RAG 系统层
    subgraph RAGSystem["🧠 RAG 系统层"]
        H --> I[构建提示词]
        I --> J[获取对话历史<br/>session_manager]
        J --> K[ai_generator.generate_response<br/>带工具定义]
    end

    %% AI 生成层
    subgraph AILayer["🤖 AI 生成层"]
        K --> L[准备 API 参数<br/>system prompt + tools]
        L --> M[Claude API 第1次调用]
        M --> N{Claude 决策}
        N -->|直接回答| O[返回文本答案]
        N -->|需要搜索| P[返回 tool_use 请求]
    end

    %% 工具执行层
    subgraph ToolLayer["🔧 工具执行层"]
        P --> Q[tool_manager.execute_tool]
        Q --> R[search_tool.execute<br/>query, course_name, lesson_number]
        R --> S[vector_store.search]
    end

    %% 向量存储层
    subgraph VectorLayer["💾 向量存储层"]
        S --> T{提供了 course_name?}
        T -->|是| U[_resolve_course_name<br/>模糊匹配课程]
        T -->|否| V[构建过滤器]
        U --> V
        V --> W[ChromaDB.query<br/>course_content 集合]
        W --> X[向量相似度搜索<br/>返回 top-5]
    end

    %% 结果处理层
    subgraph ResultLayer["📊 结果处理层"]
        X --> Y[format_results<br/>添加课程/课程上下文]
        Y --> Z[保存来源到 last_sources]
        Z --> AA[返回格式化文本]
        AA --> AB[Claude API 第2次调用<br/>基于搜索结果生成答案]
    end

    %% 响应返回层
    subgraph ResponseLayer["📤 响应返回层"]
        O --> AC[获取最终答案]
        AB --> AC
        AC --> AD[tool_manager.get_last_sources]
        AD --> AE[rag_system 返回<br/>answer, sources]
        AE --> AF[app.py 构建响应<br/>QueryResponse]
        AF --> AG[JSON 返回给前端]
    end

    %% 前端渲染层
    subgraph FrontendRender["🎨 前端渲染层"]
        AG --> AH[script.js 接收响应]
        AH --> AI[移除加载动画]
        AI --> AJ[marked.js 渲染 Markdown]
        AJ --> AK[添加来源折叠区域]
        AK --> AL[👤 用户看到答案]
    end

    %% 样式定义
    classDef frontend fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef backend fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef ai fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef vector fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    classDef result fill:#fce4ec,stroke:#880e4f,stroke-width:2px

    class A,B,C,D,AH,AI,AJ,AK,AL frontend
    class E,F,G,H backend
    class K,L,M,N,O,P,AB,AC ai
    class S,T,U,V,W,X vector
    class Y,Z,AA,AD,AE,AF,AG result
```

---

## 数据流详细视图

```mermaid
sequenceDiagram
    participant User as 👤 用户
    participant FE as 🌐 前端
    participant API as ⚙️ FastAPI
    participant RAG as 🧠 RAG System
    participant AI as 🤖 AI Generator
    participant Claude1 as 🔮 Claude (1st)
    participant Tool as 🔧 Search Tool
    participant Vector as 💾 Vector Store
    participant Chroma as 🗄️ ChromaDB
    participant Claude2 as 🔮 Claude (2nd)

    User->>FE: 输入问题并发送
    FE->>FE: 显示用户消息 + 加载动画
    FE->>API: POST /api/query<br/>{query, session_id}

    API->>API: 检查/创建 session_id
    API->>RAG: query(query, session_id)

    RAG->>RAG: 构建提示词
    RAG->>RAG: 获取对话历史
    RAG->>AI: generate_response()<br/>with tools

    AI->>AI: 构建系统提示词 + 工具定义
    AI->>Claude1: messages.create()<br/>with tool definitions

    Note over Claude1: Claude 分析问题<br/>决定需要搜索

    Claude1-->>AI: tool_use request<br/>{name: search_course_content<br/>input: {query, course_name}}

    AI->>Tool: execute_tool(name, **params)
    Tool->>Vector: search(query, course_name, lesson)

    alt 提供了 course_name
        Vector->>Chroma: query course_catalog<br/>模糊匹配课程名
        Chroma-->>Vector: 返回精确 course_title
    end

    Vector->>Vector: 构建过滤器
    Vector->>Chroma: query course_content<br/>with filters

    Note over Chroma: 向量相似度搜索<br/>Sentence Transformer 嵌入<br/>余弦相似度计算

    Chroma-->>Vector: 返回 top-5 相似文档<br/>{documents, metadatas, distances}

    Vector->>Tool: SearchResults
    Tool->>Tool: format_results()<br/>添加课程/课程标签
    Tool->>Tool: 保存来源到 last_sources
    Tool-->>AI: 格式化的搜索结果文本

    AI->>AI: 将搜索结果作为 tool_result<br/>添加到消息历史
    AI->>Claude2: messages.create()<br/>with tool results

    Note over Claude2: 基于搜索结果<br/>生成最终答案

    Claude2-->>AI: 最终答案文本
    AI-->>RAG: response text

    RAG->>Tool: get_last_sources()
    Tool-->>RAG: sources list
    RAG->>RAG: 更新对话历史
    RAG-->>API: (answer, sources)

    API->>API: 构建 QueryResponse
    API-->>FE: JSON {answer, sources, session_id}

    FE->>FE: 移除加载动画
    FE->>FE: marked.js 渲染 Markdown
    FE->>FE: 添加来源折叠区域
    FE->>User: 显示答案 + 来源
```

---

## 核心组件交互图

```mermaid
graph LR
    subgraph "前端"
        UI[用户界面]
    end

    subgraph "FastAPI 应用"
        EP[/api/query 端点]
    end

    subgraph "RAG 系统核心"
        RAG[RAG System<br/>rag_system.py]
        SM[Session Manager<br/>会话管理]
        DP[Document Processor<br/>文档处理]
    end

    subgraph "AI 生成"
        AIG[AI Generator<br/>ai_generator.py]
        TM[Tool Manager<br/>工具管理器]
        ST[Search Tool<br/>搜索工具]
    end

    subgraph "存储层"
        VS[Vector Store<br/>vector_store.py]
        CD[ChromaDB<br/>向量数据库]
    end

    subgraph "外部服务"
        Claude[Anthropic Claude API]
    end

    UI -->|HTTP POST| EP
    EP --> RAG
    RAG --> SM
    RAG --> AIG
    AIG -->|第1次调用| Claude
    Claude -->|tool_use| TM
    TM --> ST
    ST --> VS
    VS --> CD
    CD -->|搜索结果| VS
    VS -->|格式化结果| ST
    ST -->|tool_result| AIG
    AIG -->|第2次调用| Claude
    Claude -->|最终答案| AIG
    AIG --> RAG
    RAG --> EP
    EP -->|JSON| UI
    DP -.->|启动时加载| VS

    style Claude fill:#ff6b6b,stroke:#c92a2a,color:#fff
    style CD fill:#4ecdc4,stroke:#0a6e68,color:#fff
    style RAG fill:#ffe66d,stroke:#f9c74f,color:#000
```

---

## 向量搜索详细流程

```mermaid
graph TD
    A[用户查询: What is MCP?] --> B[AI Generator]
    B --> C{Claude 决定<br/>使用搜索工具}
    C -->|tool_use| D[search_course_content<br/>query: MCP<br/>course_name: MCP Course]

    D --> E[Vector Store Search]

    E --> F[步骤1: 解析课程名]
    F --> G[ChromaDB.query<br/>collection: course_catalog<br/>query: MCP Course]
    G --> H[向量匹配]
    H --> I[返回: MCP: Build Rich-Context AI Apps]

    I --> J[步骤2: 构建过滤器]
    J --> K{filter = <br/>course_title: MCP: Build Rich-Context AI Apps}

    K --> L[步骤3: 搜索内容]
    L --> M[ChromaDB.query<br/>collection: course_content<br/>query: MCP<br/>where: filter]

    M --> N[Sentence Transformer<br/>将 MCP 转为 384 维向量]
    N --> O[计算余弦相似度<br/>所有 course_content 向量]
    O --> P[应用过滤器<br/>只保留 MCP 课程]
    P --> Q[排序并返回 top-5]

    Q --> R[SearchResults<br/>documents + metadata]
    R --> S[格式化结果]
    S --> T["[MCP Course - Lesson 1]<br/>MCP stands for Model Context Protocol...<br/><br/>[MCP Course - Lesson 2]<br/>MCP allows AI applications to..."]

    T --> U[返回给 Claude]
    U --> V[Claude 生成最终答案]

    style A fill:#e3f2fd
    style V fill:#c8e6c9
    style N fill:#fff9c4
    style O fill:#fff9c4
```

---

## 数据库结构

```mermaid
erDiagram
    COURSE_CATALOG ||--o{ COURSE_CONTENT : contains

    COURSE_CATALOG {
        string id "course_title (唯一ID)"
        string document "课程标题文本"
        string title "课程标题"
        string instructor "讲师"
        string course_link "课程链接"
        json lessons_json "课程列表 JSON"
        int lesson_count "课程数量"
        vector embedding "384维向量"
    }

    COURSE_CONTENT {
        string id "course_title_chunkIndex"
        string document "文本内容"
        string course_title "所属课程"
        int lesson_number "课程编号"
        int chunk_index "块索引"
        vector embedding "384维向量"
    }
```

---

## 会话管理流程

```mermaid
stateDiagram-v2
    [*] --> NoSession: 用户首次访问
    NoSession --> NewSession: 发送第一个问题
    NewSession --> HasSession: 返回 session_id
    HasSession --> HasSession: 后续问题<br/>携带 session_id

    note right of HasSession
        会话状态：
        - session_id: "session_1"
        - 历史消息: 最多 4 条
          (2 轮对话)
        - 格式:
          User: 问题1
          Assistant: 答案1
          User: 问题2
          Assistant: 答案2
    end note

    HasSession --> [*]: 用户关闭页面<br/>会话保留在内存
```

---

## 工具调用详细流程

```mermaid
graph TB
    A[Claude 收到问题] --> B{需要搜索?}
    B -->|否| C[直接回答<br/>使用已有知识]
    B -->|是| D[生成 tool_use 块]

    D --> E["content_block = {<br/>type: 'tool_use'<br/>id: 'toolu_xxx'<br/>name: 'search_course_content'<br/>input: {<br/>  query: '...'<br/>  course_name: '...'<br/>}<br/>}"]

    E --> F[AI Generator 接收]
    F --> G[遍历 content blocks]
    G --> H{类型是 tool_use?}
    H -->|是| I[调用 tool_manager.execute_tool]
    H -->|否| J[跳过]

    I --> K[执行搜索]
    K --> L["tool_result = {<br/>type: 'tool_result'<br/>tool_use_id: 'toolu_xxx'<br/>content: '搜索结果文本'<br/>}"]

    L --> M[构建新消息]
    M --> N["messages = [<br/>  {role: 'user', content: 问题},<br/>  {role: 'assistant', content: [tool_use]},<br/>  {role: 'user', content: [tool_result]}<br/>]"]

    N --> O[Claude 第2次调用]
    O --> P[基于搜索结果生成答案]

    C --> Q[最终答案]
    P --> Q

    style E fill:#ffecb3
    style L fill:#c8e6c9
    style N fill:#e1bee7
```

---

## 关键配置参数

```mermaid
mindmap
  root((RAG 系统配置))
    文本处理
      CHUNK_SIZE: 800
      CHUNK_OVERLAP: 100
      分句策略: 正则表达式
    向量搜索
      EMBEDDING_MODEL: all-MiniLM-L6-v2
      向量维度: 384
      MAX_RESULTS: 5
      相似度: 余弦距离
    AI 生成
      MODEL: claude-sonnet-4
      TEMPERATURE: 0
      MAX_TOKENS: 800
      工具模式: auto
    会话管理
      MAX_HISTORY: 2 轮
      session_id: 自动生成
      格式: session_N
```

---

## 性能优化点

```mermaid
graph LR
    subgraph "优化策略"
        A[静态系统提示词] --> A1[避免每次重建字符串]
        B[预构建 API 参数] --> B1[减少字典操作]
        C[ChromaDB 持久化] --> C1[避免重复加载]
        D[Sentence Transformer 缓存] --> D1[模型只加载一次]
        E[会话历史限制] --> E1[控制 Token 使用]
    end

    style A fill:#c8e6c9
    style B fill:#c8e6c9
    style C fill:#c8e6c9
    style D fill:#c8e6c9
    style E fill:#c8e6c9
```

