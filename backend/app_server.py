"""KnowFlow / Know包 的 FastAPI 后端服务。

迁移说明：
- 原实现基于 aiohttp（app_server.py），本文件迁移为 FastAPI + uvicorn。
- API 路径、请求/响应结构与流式 NDJSON 协议与原实现完全一致。
- 新增：Redis 缓存（知识库统计/设置/会话列表/天气/RAG 检索/对话历史）。
- 静态资源：构建后的 Vue3 前端（frontend/dist）与 assets/background 目录。
"""
import asyncio
import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from agent_service import AgentService
from cache_service import cache
from file_history_store import (
    delete_history,
    get_history,
    list_histories,
    normalize_session_id,
)
from knowledge_base import KnowledgeBaseService
from settings_store import get_settings, save_settings
from tools.weather_tool import WeatherTool

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
ASSETS_DIR = BASE_DIR / "assets"
BACKGROUND_DIR = BASE_DIR / "background"
MAX_UPLOAD_SIZE = 30 * 1024 * 1024

ALLOWED_RAG_MODES = {"off", "force", "auto"}


# ---------- 应用状态 ----------

class AppState:
    """服务实例容器：设置变更后按原逻辑重建知识库与 Agent。"""

    def __init__(self):
        self.knowledge_base = KnowledgeBaseService()
        self.agent = AgentService()
        self.weather_tool = WeatherTool()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    from database import init_db

    init_db()
    get_settings()  # 首次读取并回写 config_data 参数
    state = AppState()
    _app.state.app_state = state
    logger.info("应用启动：数据库/知识库/Agent 已就绪，Redis=%s", cache.enabled)
    yield
    # 关闭阶段：连接池随进程释放即可


app = FastAPI(title="Know包 · 个人知识库", lifespan=lifespan)


# ---------- 工具函数 ----------

def _json_response(data: dict, status: int = 200):
    return JSONResponse(
        content=data,
        status_code=status,
    )


def _encode_ndjson(event: dict) -> bytes:
    return (json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8")


def _get_state(request: Request) -> AppState:
    return request.app.state.app_state


def _normalize_rag_mode(value: str) -> str:
    value = str(value or "auto").strip()
    return value if value in ALLOWED_RAG_MODES else "auto"


async def _stream_answer(question: str, session_id: str, rag_mode: str, client_ip: str = ""):
    """将同步 Agent 流式生成转换为 NDJSON 异步生成器。"""
    agent = app.state.app_state.agent
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    loop = asyncio.get_running_loop()
    stop_event = threading.Event()

    def produce_chunks():
        try:
            for event in agent.stream_answer(
                question,
                session_id,
                stop_event,
                rag_mode,
                client_ip,
            ):
                loop.call_soon_threadsafe(queue.put_nowait, event)
        except Exception as error:
            logger.exception("Agent 流式生成异常")
            loop.call_soon_threadsafe(queue.put_nowait, {"type": "error", "content": str(error)})
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=produce_chunks, daemon=True).start()

    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield _encode_ndjson(event)
    except asyncio.CancelledError:
        stop_event.set()
        raise
    finally:
        # 会话写入完成后作废历史缓存
        cache.invalidate_history(session_id)


# ---------- 页面 ----------

@app.get("/", include_in_schema=False)
async def index():
    index_file = FRONTEND_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        {"ok": False, "message": "前端尚未构建，请先执行 pnpm build 或运行前端开发服务器"},
        status_code=404,
    )


@app.get("/api/health")
async def health():
    return _json_response({
        "ok": True,
        "service": "Know包",
        "cache": {"enabled": cache.enabled, "backend": "redis"},
    })


@app.get("/api/cache/stats")
async def cache_stats():
    """缓存状态与键概览（调试用）。"""
    keys = []
    if cache.enabled:
        keys = [
            key for key in cache.client.scan_iter(match=f"{cache.prefix}:*", count=100)
        ][:50]
    return _json_response({
        "ok": True,
        "enabled": cache.enabled,
        "key_count": len(keys),
        "sample_keys": keys,
    })


# ---------- 知识库 ----------

@app.get("/api/knowledge")
async def get_knowledge_stats(request: Request):
    state = _get_state(request)

    def load_stats():
        return state.knowledge_base.get_statistics()

    try:
        stats = await asyncio.to_thread(
            lambda: cache.get_or_set(
                cache.key_stats(),
                cache.ttl("knowledge_stats"),
                load_stats,
            )
        )
        return _json_response({"ok": True, "data": stats})
    except Exception as error:
        return _json_response({"ok": False, "message": str(error)}, status=500)


@app.post("/api/knowledge/upload")
async def upload_knowledge_file(request: Request, file: UploadFile = File(...)):
    state = _get_state(request)
    file_name = Path(file.filename or "").name
    suffix = Path(file_name).suffix.lower()
    if suffix not in {".pdf", ".txt"}:
        return _json_response({"ok": False, "message": "仅支持 PDF 和 TXT 文件"}, status=400)

    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 256)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE:
            return _json_response({"ok": False, "message": "文件不能超过 30 MB"}, status=413)
        chunks.append(chunk)
    file_bytes = b"".join(chunks)

    try:
        if suffix == ".pdf":
            result = await asyncio.to_thread(
                state.knowledge_base.upload_pdf, file_bytes, file_name
            )
        else:
            try:
                text = file_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                return _json_response({"ok": False, "message": "TXT 文件必须使用 UTF-8 编码"}, status=400)
            result = await asyncio.to_thread(
                state.knowledge_base.upload_by_str, text, file_name
            )

        is_success = "成功" in result
        if is_success:
            cache.invalidate_knowledge()
        return _json_response(
            {"ok": is_success, "message": result},
            status=200 if is_success else 409,
        )
    except Exception as error:
        return _json_response({"ok": False, "message": f"文件处理失败：{error}"}, status=500)


@app.delete("/api/knowledge/source")
async def delete_knowledge_source(request: Request):
    state = _get_state(request)
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return _json_response({"ok": False, "message": "请求数据格式错误"}, status=400)
    source = str(payload.get("source", "")).strip()
    if not source:
        return _json_response({"ok": False, "message": "缺少要删除的文件名"}, status=400)

    try:
        deleted_count = await asyncio.to_thread(state.knowledge_base.delete_by_source, source)
        if deleted_count == 0:
            return _json_response({"ok": False, "message": "未找到该文件"}, status=404)
        cache.invalidate_knowledge()
        return _json_response({
            "ok": True,
            "message": f"已删除 {source}，共移除 {deleted_count} 个文本块",
            "deleted_count": deleted_count,
        })
    except Exception as error:
        return _json_response({"ok": False, "message": f"删除失败：{error}"}, status=500)


# ---------- 会话历史 ----------

@app.get("/api/history")
async def get_chat_history(session_id: str = "user001"):
    session_id = normalize_session_id(session_id)

    def load_messages():
        history = get_history(session_id)
        return [
            {
                "role": "user" if message.type == "human" else "assistant",
                "content": str(message.content),
                "created_at": message.additional_kwargs.get("created_at") or "",
            }
            for message in history.messages
            if message.type in {"human", "ai"}
        ]

    messages = await asyncio.to_thread(
        lambda: cache.get_or_set(
            cache.key_history(session_id),
            cache.ttl("history"),
            load_messages,
        )
    )
    return _json_response({"ok": True, "data": messages})


@app.get("/api/sessions")
async def get_sessions():
    sessions = await asyncio.to_thread(
        lambda: cache.get_or_set(
            cache.key_sessions(),
            cache.ttl("sessions"),
            list_histories,
        )
    )
    return _json_response({"ok": True, "data": sessions})


@app.delete("/api/history/{session_id}")
async def clear_chat_history(session_id: str):
    session_id = normalize_session_id(session_id)
    deleted = await asyncio.to_thread(delete_history, session_id)
    cache.invalidate_history(session_id)
    if not deleted:
        return _json_response({"ok": False, "message": "未找到该对话"}, status=404)
    return _json_response({"ok": True, "message": "已删除对话"})


# ---------- 运行时设置 ----------

@app.get("/api/settings")
async def get_runtime_settings():
    try:
        settings = await asyncio.to_thread(
            lambda: cache.get_or_set(
                cache.key_settings(),
                cache.ttl("settings"),
                get_settings,
            )
        )
        return _json_response({"ok": True, "data": settings})
    except Exception as error:
        return _json_response({"ok": False, "message": f"读取设置失败：{error}"}, status=500)


@app.put("/api/settings")
async def update_runtime_settings(request: Request, body: dict):
    try:
        settings = await asyncio.to_thread(save_settings, body)
        cache.invalidate_settings()
        # 设置变更后重建知识库与 Agent（与原文行为一致）
        state = _get_state(request)
        state.knowledge_base = await asyncio.to_thread(KnowledgeBaseService)
        state.agent = await asyncio.to_thread(AgentService)
        return _json_response({
            "ok": True,
            "data": settings,
            "message": "设置已保存",
        })
    except ValueError as error:
        return _json_response({"ok": False, "message": str(error)}, status=400)
    except Exception as error:
        return _json_response({"ok": False, "message": f"保存设置失败：{error}"}, status=500)


# ---------- 天气 ----------

@app.get("/api/weather/current")
async def get_current_weather(request: Request, location: Optional[str] = ""):
    state = _get_state(request)
    location = (location or "").strip()

    # 获取客户端公网 IP（优先从反向代理头读取，其次用直连 IP）
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or (request.client.host if request.client else "")
    )

    # 未提供位置时，用 IP 定位尝试获取城市（解决公网 HTTP 下浏览器无法获取坐标的问题）
    if not location and client_ip:
        ip_location = state.weather_tool._resolve_location_by_ip(client_ip)
        if ip_location:
            location = ip_location

    def load_weather():
        result = state.weather_tool.run(location)
        if not result.ok:
            raise ValueError(result.message or result.summary)
        return result.data

    try:
        data = await asyncio.to_thread(
            lambda: cache.get_or_set(
                cache.key_weather(location),
                cache.ttl("weather"),
                load_weather,
            )
        )
        return _json_response({"ok": True, "data": data, "message": "ok"})
    except ValueError as error:
        return _json_response({"ok": False, "message": str(error)}, status=400)
    except Exception as error:
        return _json_response({"ok": False, "message": str(error)}, status=400)


# ---------- 对话流式接口 ----------

@app.post("/api/chat")
async def stream_chat(body: dict, request: Request):
    question = str(body.get("input", "")).strip()
    session_id = normalize_session_id(str(body.get("session_id", "user001")))
    rag_mode = _normalize_rag_mode(body.get("rag_mode", "auto"))

    if not question:
        return _json_response({"ok": False, "message": "问题不能为空"}, status=400)

    # 提取客户端公网 IP，供 Agent 天气工具定位使用
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or (request.client.host if request.client else "")
    )

    return StreamingResponse(
        _stream_answer(question, session_id, rag_mode, client_ip),
        media_type="application/x-ndjson; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


# ---------- 静态资源 ----------

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/background", StaticFiles(directory=BACKGROUND_DIR), name="background")

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    # 监听 0.0.0.0 允许公网访问；仅本机访问可改回 127.0.0.1
    uvicorn.run(app, host="0.0.0.0", port=4389)
