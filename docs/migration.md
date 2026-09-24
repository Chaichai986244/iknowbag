# 迁移说明

本文档记录从原 `/home/RAG项目实战` 迁移到 `/home/Hweb` 的过程、改动点、数据迁移与验证结果。

## 1. 迁移目标

- **完整性**：保留全部原始实现与数据，无丢失。
- **增强**：新增 Redis 缓存、SQLite 持久化、Vue3 前端、FastAPI 后端。
- **兼容性**：API 路径与流式协议不变，Agent/知识库核心逻辑不改。

## 2. 目录与文件映射

| 原位置（RAG项目实战） | 新位置（Hweb） | 说明 |
|---|---|---|
| `app_server.py` | `backend/app_server.py` | **重写**：aiohttp → FastAPI，协议不变 |
| `agent_service.py` / `rag.py` / `vector_stores.py` | `backend/` 同名 | 保留，`rag.py` 增加 Redis 缓存 |
| `knowledge_base.py` / `config_data.py` | `backend/` 同名 | 保留；`config_data` 路径改为项目根 |
| `settings_store.py` | `backend/settings_store.py` | **重写**：JSON 文件 → SQLite |
| `file_history_store.py` | `backend/file_history_store.py` | **重写**：JSON 文件 → SQLite |
| `tools/rag_tool.py` / `weather_tool.py` | `backend/tools/` | 保留 |
| `app_qa.py` / `app_file_uploader.py` / `ui_components.py` | `backend/legacy/` | 原 Streamlit 版本，保留存档 |
| `frontend/` | `frontend_legacy/` | 原原生 JS 前端，保留存档 |
| `frontend/`（新） | `frontend/` | **新建**：Vue3 + Vite |
| `data/ assets/ background/ chroma_db/ chat_history/` | 项目根同名目录 | 原样迁移 |
| `tests/` | `tests/` | 适配 SQLite 存储 |
| `.streamlit/` | 项目根 | 保留（legacy 使用） |
| `md5.text` / `runtime_settings.json` | 项目根 | 保留 |

## 3. 关键改动点

### 3.1 后端框架：aiohttp → FastAPI

- 同一套 API 路由与请求/响应结构，流式对话仍为 NDJSON（`application/x-ndjson`）。
- 上传大小限制、文件类型校验、设置校验逻辑逐行保留。
- 设置变更后重建服务对象的行为保留（`update_runtime_settings` 中重建 `KnowledgeBaseService` / `AgentService`）。

### 3.2 Redis 缓存（新增）

- 新增 `backend/cache_service.py`：连接池、统一键前缀 `knowbao:`、TTL 管理、精确/模式删除失效、Redis 不可用自动降级。
- 接入点：知识库统计、设置、会话列表、天气、RAG 检索结果、对话历史。
- 失效入口：`invalidate_settings` / `invalidate_knowledge` / `invalidate_history`。

### 3.3 SQLite 数据层（新增）

- 新增 `backend/database.py`：SQLAlchemy 2.0、`messages` 与 `settings` 两张表、NullPool 连接策略。
- `file_history_store.py` 改为 SQLite 实现，对外接口（`get_history` / `delete_history` / `list_histories` / `FileChatMessageHistory`）不变，`AgentService` 与测试无需改动。
- `settings_store.py` 改为 SQLite 实现，`get_settings` / `save_settings` / `normalize_settings` 接口不变。
- 新增 `backend/migrate_data.py` 一次性导入旧 JSON 数据。

### 3.4 前端：原生 JS → Vue3

- Vite 6 + Vue 3.5 + Pinia，Composition API（`<script setup>`）。
- 三个视图页（对话 / 知识库 / 设置）完整复刻原交互：
  - 流式对话 + 思考状态 + 来源折叠 + 中止 + 重试；
  - 拖拽/选择上传 + 校验 + 来源删除确认；
  - 设置表单的切分参数/分隔符/top_k/天气默认位置/工具开关。
- 沿用原 9 个 CSS 文件（含响应式与玻璃拟态），移动端抽屉导航保留。
- API 客户端保持原 NDJSON 协议，`streamChat()` 逐行解析。

## 4. 数据迁移

执行 `python backend/migrate_data.py`：

1. **会话历史**：`chat_history/*.json`（langchain 消息格式）→ `messages` 表，会话 ID 取文件名，`created_at` 取消息时间戳（缺失时用文件 mtime）。仅当目标会话无数据时导入（幂等）。
2. **运行时设置**：`runtime_settings.json` → `settings` 表 `runtime` 键。仅当键为空时导入。

迁移结果（本次执行）：

```
已迁移运行时设置：['chunk_overlap', 'chunk_size', 'max_split', 'separators', 'top_k']
已迁移会话 0fcdb7cd-...（4 条消息）
已迁移会话 s1（58 条消息）
```

## 5. 依赖变化

新增依赖（写入 `requirements.txt`）：

- `fastapi` / `uvicorn` / `sse-starlette` / `python-multipart`（Web 框架与上传）
- `langchain-chroma`（langchain 1.x 起 Chroma 集成独立成包）
- `pypdf`（PDF 解析，原依赖隐式提供）
- `redis`（缓存客户端）

前端依赖：`vue`、`pinia`、`vite`、`@vitejs/plugin-vue`。

## 6. 验证结果

### 6.1 单元测试（13/13 通过）

```
tests/test_agent_service.py     5 项通过（Agent 天气/RAG 决策、流式事件）
tests/test_file_history_store.py 4 项通过（SQLite 历史读写/删除/列表）
tests/test_settings_store.py     4 项通过（默认值/保存/校验）
```

### 6.2 API 端到端（curl）

| 接口 | 结果 |
|---|---|
| `GET /api/health` | 200，Redis 已启用 |
| `GET /api/sessions` / `/api/settings` / `/api/knowledge` | 200，数据正确，首次请求后 Redis 出现 `knowbao:sessions` / `knowbao:settings` / `knowbao:stats:knowledge` |
| `POST /api/chat`（流式） | status → chunk → done，回答完整持久化至 SQLite |
| `PUT /api/settings` | 200，缓存按策略作废（键数 3 → 1） |
| `POST /api/knowledge/upload` + `DELETE source` | 上传 1 文本块、删除 1 文本块，闭环正常 |
| `GET /`（Vue 构建产物） | 200，JS/CSS 资源正常 |

### 6.3 浏览器 UI 验证

- 页面加载、标题、品牌、天气卡片（实时和风数据）、会话列表正常。
- 知识库页：8 份资料 / 139 个内容片段，来源列表完整。
- 设置页：字段从后端正确回填。
- 流式对话：发送"你好"约 5 秒返回回答，会话列表新增记录，历史持久化。
- 控制台无应用级错误。

## 7. 兼容性说明

- `langchain-community` 已进入维护期（官方弃用警告），但当前检索链路依赖其
  `DashScopeEmbeddings`，短期内可继续使用；后续可迁移至独立集成包。
- 原 Streamlit 版本文件（`backend/legacy/`）与原生 JS 前端（`frontend_legacy/`）
  仅作存档保留，不属于新运行链路。
- Redis 未启动时应用自动降级为直连存储，功能不受影响（仅缓存失效）。

## 8. 回滚

- 原始项目完整保留在 `/home/RAG项目实战`，未做任何修改。
- 如需回退，直接继续使用原始目录即可；新库 `chat.db` 为增量产物，不影响旧数据。
