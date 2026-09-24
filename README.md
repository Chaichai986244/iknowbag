# Know包 · 个人知识库 RAG 应用

基于 **LangChain + Chroma** 的检索增强生成（RAG）个人知识库应用：上传 PDF / TXT 文档建立本地向量知识库，与大模型流式对话，支持会话历史、知识库管理、运行时参数调节与天气查询。

![tech](https://img.shields.io/badge/Python-3.11-3776AB) ![tech](https://img.shields.io/badge/Vue-3.5-42b883) ![tech](https://img.shields.io/badge/FastAPI-latest-009688) ![license](https://img.shields.io/badge/License-MIT-yellow)

## 功能特性

- **知识库管理**：上传 PDF / TXT（≤30MB），自动切分、向量化入库，支持按来源删除与统计
- **RAG 流式对话**：NDJSON 流式输出，回答附带引用来源，Agent 自动判断是否需要检索
- **多轮会话**：会话历史 SQLite 持久化，支持会话列表、切换与删除
- **运行时设置**：分块大小 / 重叠 / 检索 top_k 等参数在线调节，即时生效
- **Redis 缓存**：检索结果、统计、设置、会话、天气多级缓存，未启动 Redis 时自动降级
- **天气工具**：和风天气 API，Agent 可按需调用，侧栏天气卡片展示（可选配置）

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3.5 + Vite 6 + Pinia（Composition API） |
| Web 框架 | FastAPI + uvicorn |
| LLM / Agent | LangChain 1.x + langchain-openai（StepFun step 系列） |
| 向量库 | Chroma + DashScope `text-embedding-v4` 嵌入 |
| 文档解析 | pypdf / pdfplumber（PDF）、TXT |
| 缓存 | Redis（连接池，自动降级） |
| 数据库 | SQLite（SQLAlchemy 2.0） |
| 工具 | 和风天气 API（Agent 天气工具 + 侧栏天气卡片） |

## 目录结构

```
Hweb/
├── backend/                # Python 后端
│   ├── app_server.py       # FastAPI 入口（API + 静态托管 + NDJSON 流式对话）
│   ├── agent_service.py    # Agent：天气决策 / 资料相关性筛选 / 流式回答
│   ├── rag.py              # RAG 检索（带 Redis 缓存）
│   ├── knowledge_base.py   # 知识库：上传/删除/统计（PDF、TXT 切分）
│   ├── vector_stores.py    # Chroma 向量库封装
│   ├── config_data.py      # 全局配置与路径（支持 .env 覆盖）
│   ├── database.py         # SQLite 数据层（SQLAlchemy 模型）
│   ├── file_history_store.py  # 会话历史（SQLite 存储，langchain 接口兼容）
│   ├── settings_store.py   # 运行时设置（SQLite 存储）
│   ├── cache_service.py    # Redis 缓存服务（连接池/键管理/失效策略）
│   ├── migrate_data.py     # 旧 JSON 数据 → SQLite 迁移脚本
│   ├── tools/              # rag_tool / weather_tool
│   └── legacy/             # 原 Streamlit 版本文件（保留）
├── frontend/               # Vue3 前端工程
│   ├── src/
│   │   ├── api/            # API 客户端（NDJSON 流式解析）
│   │   ├── stores/app.js   # Pinia 全局状态
│   │   ├── utils/          # markdown 渲染 / 格式化工具
│   │   ├── components/     # Sidebar/TopBar/Icon/对话框等
│   │   └── views/          # ChatView/KnowledgeView/SettingsView
│   └── vite.config.js      # 开发代理 → 后端
├── frontend_legacy/        # 原原生 JS 前端（保留）
├── assets/                 # 头像等静态资源
├── background/             # 背景图
├── tests/                  # unittest 测试
└── docs/                   # 架构与迁移文档
```

> 运行后自动生成（不入库）：`chat.db`（SQLite）、`chroma_db/`（向量库）、`upload_files/`（上传文档）。

## 快速开始

### 1. 克隆并安装依赖

```bash
git clone <本仓库地址>
cd Hweb

# Python 3.11 虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Redis（缓存依赖；未启动时自动降级，不影响业务）
redis-server --daemonize yes
```

### 2. 配置密钥

复制模板并填入真实密钥：

```bash
cp .env.example .env
```

必填项见下表，密钥获取入口见 `.env.example` 内注释：

| 变量 | 必填 | 说明 |
|---|---|---|
| `STEPFUN_API_KEY` | ✅ | 模型密钥 |
| `STEPFUN_BASE_URL` | — | 路由 |
| `DASHSCOPE_API_KEY` | ✅ | 文本嵌入模型 |
| `QWEATHER_API_KEY` | — | 天气api |
| `QWEATHER_API_HOST` | — |  API Host |
| `DOC_STORE_PATH` | — | 上传文档存储路径，默认 `./upload_files` |
| `CHROMA_PERSIST_PATH` | — | Chroma 向量库路径，默认 `./chroma_db` |
| `SQLITE_DB_PATH` | — | SQLite 路径，默认 `./chat.db` |



### 3. 构建前端

```bash
cd frontend
pnpm install      # 或 npm install / yarn
pnpm build        # 产物输出到 frontend/dist
```

### 4. 启动后端

```bash
cd backend
uvicorn app_server:app --host 0.0.0.0 --port 4389
```

- `--host 0.0.0.0`：监听所有网卡
- 

访问 http://127.0.0.1:4389 即可使用（后端自动托管 `frontend/dist`）。

### 5. 前端开发模式（可选，热更新）

```bash
cd frontend && pnpm dev   # http://127.0.0.1:5173，自动代理 /api 到后端
```

### 6. 运行测试

```bash
cd tests && python -m unittest discover -s . -p "test_*.py" -v
```

## 核心 API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查（含缓存状态） |
| GET | `/api/knowledge` | 知识库统计（Redis 缓存 60s） |
| POST | `/api/knowledge/upload` | 上传 PDF/TXT（≤30MB） |
| DELETE | `/api/knowledge/source` | 删除指定来源资料 |
| GET | `/api/history?session_id=` | 会话消息 |
| GET | `/api/sessions` | 会话列表（Redis 缓存 30s） |
| DELETE | `/api/history/{session_id}` | 删除会话 |
| GET | `/api/settings` | 运行时设置（Redis 缓存 60s） |
| PUT | `/api/settings` | 保存设置（并作废相关缓存） |
| GET | `/api/weather/current` | 当前天气（Redis 缓存 600s） |
| POST | `/api/chat` | 流式对话（NDJSON，SSE 兼容） |
| GET | `/api/cache/stats` | 缓存状态与键概览（调试） |

流式事件类型：`status` / `sources` / `chunk` / `tool` / `error` / `done`。

## 常见问题

- **未启动 Redis 会怎样？** 缓存层自动降级为直连数据库，业务功能不受影响，日志中会有降级提示。
- **天气查询报"请先配置 QWEATHER_API_KEY"？** 在 `.env` 中补齐 `QWEATHER_API_KEY` 与 `QWEATHER_API_HOST` 后重启后端。
- **旧版 JSON 历史数据如何导入？**（本项目历史迁移用，新用户可跳过）`cd backend && python migrate_data.py`，幂等可重复执行。

## 文档

- [架构说明](docs/architecture.md)
- [迁移说明](docs/migration.md)

## License

[MIT](LICENSE)
