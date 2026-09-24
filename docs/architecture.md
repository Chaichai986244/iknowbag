# 架构说明

本文档描述 Hweb（Know包）迁移版的项目架构、模块职责、数据流与缓存/存储设计。

## 1. 总体架构

```
┌───────────────────────────── Vue3 前端 (frontend/) ─────────────────────────────┐
│  ChatView / KnowledgeView / SettingsView                                        │
│  Pinia store（会话、RAG 模式、会话列表、天气、Toast）                             │
│  api/（NDJSON 流式解析）   utils/（Markdown 渲染、格式化）                        │
└───────────────┬─────────────────────────────────────────────────────────────────┘
                │  HTTP /api/*（开发模式由 Vite 代理，生产由后端托管 dist）
┌───────────────▼────────────────────────── FastAPI (backend/app_server.py) ──────┐
│  路由层：knowledge / history / sessions / settings / weather / chat(NDJSON 流)   │
│  缓存接入：cache_service（Redis）——统计/设置/会话/天气/RAG/历史                   │
├──────────────────────────────────────────────────────────────────────────────────┤
│  AgentService（agent_service.py）                                                │
│    ReAct 式决策：天气工具选择 → RAG 检索 → 资料相关性评分 → 流式回答              │
│    └─ RAGTool → RagService(rag.py) → VectorStoreService(vector_stores.py)       │
│         │                        └─ Chroma + DashScope 嵌入（检索结果 Redis 缓存）│
│    └─ WeatherTool(tools/weather_tool.py) → 和风天气 API                           │
├──────────────────────────────────────────────────────────────────────────────────┤
│  KnowledgeBaseService（knowledge_base.py）→ Chroma（切分/去重/统计/删除）          │
├──────────────────────────────────────────────────────────────────────────────────┤
│  存储层：                                                                         │
│    database.py          SQLAlchemy 引擎 + 模型（messages / settings）            │
│    file_history_store.py  会话历史 → messages 表                                 │
│    settings_store.py      运行时设置 → settings 表                               │
│    chroma_db/            向量数据持久化目录                                      │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## 2. 模块职责

| 模块 | 职责 |
|---|---|
| `app_server.py` | FastAPI 应用工厂、路由注册、静态托管、流式对话桥接、服务重建 |
| `agent_service.py` | Agent 编排：天气决策、上下文相关性评分、消息组装、流式生成 |
| `rag.py` | 检索封装（带 Redis 缓存回填）与文档/来源格式化 |
| `knowledge_base.py` | PDF/TXT 解析切分、MD5 去重、统计、按来源删除 |
| `vector_stores.py` | Chroma 客户端与 Retriever（`top_k` 动态读取） |
| `config_data.py` | 全局常量与路径解析（`.env` 可覆盖） |
| `database.py` | SQLite 连接池（NullPool）、ORM 模型、会话工厂 |
| `file_history_store.py` | langchain `BaseChatMessageHistory` 的 SQLite 实现 |
| `settings_store.py` | 设置规范化/校验 + SQLite 持久化 + 回写 `config_data` |
| `cache_service.py` | Redis 连接池、键管理、TTL、失效策略、优雅降级 |

## 3. 数据流

### 3.1 对话（流式）

1. 前端 `POST /api/chat`（`{input, session_id, rag_mode}`）。
2. 后端启动生产者线程，驱动 `AgentService.stream_answer()`：
   - **天气决策**（若启用）：LLM 判断是否调用天气工具 → `WeatherTool.run()` 产出 `tool` 事件。
   - **RAG 检索**（按模式）：
     - `off`：直接回答；
     - `force`：强制检索并参考；
     - `auto`：检索 → LLM 判定资料相关性 → 产出 `sources` 事件。
   - **回答**：`chat_model.stream()` 逐 token 产出 `chunk` 事件。
3. 事件经 `asyncio.Queue` 桥接到响应流，按 NDJSON 逐行写出；结束后写入会话历史（SQLite）并作废缓存。
4. 客户端断连时通过 `threading.Event` 通知生产者提前退出，避免悬挂线程。

### 3.2 知识库上传

1. 前端 multipart 上传 → 后端限制 ≤30MB、仅 `.pdf/.txt`。
2. `KnowledgeBaseService`：PDF 按页提取文本 → `RecursiveCharacterTextSplitter` 切分 → Chroma 入库（含 `file_hash`/`source`/`page` 元数据，MD5 去重）。
3. 成功后作废 `stats` 与全部 `rag` 缓存。

### 3.3 设置变更

1. `PUT /api/settings` → 规范化校验 → 写入 SQLite `settings` 表 → 回写 `config_data` 模块参数。
2. 作废 `settings` 与 `rag:*` 缓存；重建 `KnowledgeBaseService` / `AgentService`（切分参数生效于新上传）。

## 4. Redis 缓存设计

### 4.1 连接与降级

- 通过 `redis.ConnectionPool` 建立连接池（`max_connections=20`，`decode_responses=True`），模块级单例 `cache`。
- 启动时 `ping` 探活；失败自动降级为直连存储，仅输出告警日志，不影响业务。
- 连接地址可用环境变量 `REDIS_URL` 覆盖（默认 `redis://127.0.0.1:6379/0`）。

### 4.2 键管理（统一前缀 `knowbao:`）

| 键 | 内容 | TTL | 失效时机 |
|---|---|---|---|
| `knowbao:stats:knowledge` | 知识库统计 | 60s | 上传/删除资料 |
| `knowbao:settings` | 运行时设置 | 60s | 保存设置 |
| `knowbao:sessions` | 会话列表 | 30s | 写消息/删会话 |
| `knowbao:history:{session_id}` | 会话消息 | 120s | 写消息/删会话 |
| `knowbao:weather:{md5(location)}` | 天气结果 | 600s | 自然过期 |
| `knowbao:rag:{md5(question)}` | RAG 检索结果 | 300s | 上传/删除资料、保存设置（`rag:*` 模式删除） |

### 4.3 失效策略

- **精确删除**：`delete(key)` 用于 settings/history/sessions。
- **模式删除**：`delete_pattern("knowbao:rag:*")` 使用 `scan_iter` 非阻塞批量作废，避免阻塞 Redis 单线程。
- **失效入口**：`invalidate_settings()` / `invalidate_knowledge()` / `invalidate_history(session_id)`，统一由 API 层在写操作后调用。

## 5. SQLite 数据层

### 5.1 Schema

**messages**

| 列 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增 |
| session_id | TEXT(64) | 规范化会话 ID，索引 |
| role | TEXT(16) | human / ai / system |
| content | TEXT | 消息内容 |
| created_at | DATETIME | 创建时间，索引 |
| metadata_json | TEXT | 预留扩展字段（JSON） |

**settings**

| 列 | 类型 | 说明 |
|---|---|---|
| key | TEXT(64) PK | 设置键（当前 `runtime`） |
| value | TEXT | JSON 序列化的设置对象 |
| updated_at | DATETIME | 更新时间 |

### 5.2 连接策略

- SQLAlchemy 2.0 + `NullPool`，`check_same_thread=False`；每个操作独立获取短生命周期 Session，避免跨线程共享连接。
- `database.get_db()` 返回全局单例；测试可通过 `Database(temp_path)` 独立实例化。

### 5.3 langchain 兼容

`SQLiteChatMessageHistory` 实现 `BaseChatMessageHistory` 接口（`messages` / `add_messages` / `clear`），
`get_history()` / `delete_history()` / `list_histories()` 函数签名与原 JSON 方案完全一致，
`AgentService` 与前端无需感知存储变更。

## 6. 前端（Vue3）设计

- **状态管理**：Pinia 单一 store（`stores/app.js`）——页面导航、会话 ID、RAG 模式（localStorage 持久化）、会话列表、天气、Toast、知识库计数。
- **组合式 API**：所有视图/组件使用 `<script setup>`；流式对话逻辑封装于 `ChatView`（AbortController 取消、自动滚动、来源折叠、重试）。
- **API 客户端**：`api/index.js` 保持原 NDJSON 协议；`streamChat()` 逐行解析事件。
- **响应式**：沿用原 `responsive.css`（桌面三栏 → ≤768px 抽屉式侧栏），并适配安全区与移动端交互。
- **导航**：非路由式标签页切换（与原生版一致），移动端通过抽屉打开侧栏。

## 7. 部署

- 生产：`pnpm build` 产物 `frontend/dist` 由 FastAPI 以 `StaticFiles(html=True)` 托管，同源无跨域。
- 开发：`pnpm dev`（5173）通过 Vite 代理 `/api`、`/assets`、`/background` 到后端（4389）。
