"""Redis 缓存服务：连接池、统一键管理、TTL 与失效策略。

设计要点：
- 连接池：通过 redis.ConnectionPool 复用连接，decode_responses=True。
- 优雅降级：Redis 不可用时自动禁用缓存，业务直连底层存储，不影响主流程。
- 键管理：统一前缀 knowbao:，按域划分（stats/settings/sessions/weather/rag/history）。
- 失效策略：见下方 `invalidate_*` 方法；失效时使用 scan_iter 非阻塞匹配删除。

用法（FastAPI 后端）：
    from cache_service import cache
    data = cache.get_or_set(cache.key_stats(), cache.ttl("stats"), factory=load_stats)
"""
import hashlib
import json
import logging
import os

from redis import ConnectionPool, Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

# 各域默认 TTL（秒）
_DEFAULT_TTLS = {
    "knowledge_stats": 60,
    "settings": 60,
    "sessions": 30,
    "weather": 600,
    "rag": 300,
}

_PREFIX = "knowbao"


def _digest(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()[:16]


class CacheService:
    """基于 Redis 的通用缓存服务。"""

    def __init__(self, url: str = None, prefix: str = _PREFIX, enabled: bool = None):
        self.prefix = prefix
        self.client = None
        self.enabled = False
        url = url or os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")

        if enabled is False:
            return
        try:
            pool = ConnectionPool.from_url(
                url,
                max_connections=20,
                decode_responses=True,
            )
            client = Redis(connection_pool=pool, socket_connect_timeout=2, socket_timeout=3)
            client.ping()
            self.client = client
            self.enabled = True
            logger.info("Redis 缓存已启用：%s", url)
        except RedisError as error:
            self.client = None
            self.enabled = False
            logger.warning("Redis 不可用（%s），缓存功能降级，业务直连存储", error)

    # ---------- 键管理 ----------

    def _key(self, *parts) -> str:
        return ":".join([self.prefix, *[str(part) for part in parts]])

    def key_stats(self) -> str:
        return self._key("stats", "knowledge")

    def key_settings(self) -> str:
        return self._key("settings")

    def key_sessions(self) -> str:
        return self._key("sessions")

    def key_weather(self, location: str) -> str:
        return self._key("weather", _digest(location or ""))

    def key_rag(self, question: str) -> str:
        return self._key("rag", _digest(question))

    def key_history(self, session_id: str) -> str:
        return self._key("history", session_id)

    @staticmethod
    def ttl(domain: str) -> int:
        return _DEFAULT_TTLS.get(domain, 300)

    # ---------- 基础读写 ----------

    def get_json(self, key: str):
        """读取缓存并反序列化为 JSON。未命中或不可用时返回 None。"""
        if not self.enabled:
            return None
        try:
            raw = self.client.get(key)
            return json.loads(raw) if raw is not None else None
        except (RedisError, json.JSONDecodeError) as error:
            logger.debug("缓存读取失败：%s", error)
            return None

    def set_json(self, key: str, value, ttl: int = 300) -> bool:
        """写入 JSON 缓存，返回是否成功。"""
        if not self.enabled:
            return False
        try:
            self.client.set(key, json.dumps(value, ensure_ascii=False), ex=ttl)
            return True
        except RedisError as error:
            logger.debug("缓存写入失败：%s", error)
            return False

    def get_or_set(self, key: str, ttl: int, factory):
        """缓存直读，未命中时调用 factory() 生成并回填。"""
        cached = self.get_json(key)
        if cached is not None:
            return cached
        value = factory()
        self.set_json(key, value, ttl)
        return value

    # ---------- 失效策略 ----------

    def delete(self, *keys: str) -> None:
        """精确删除一个或多个键。"""
        if not self.enabled:
            return
        keys = [key for key in keys if key]
        if not keys:
            return
        try:
            self.client.delete(*keys)
        except RedisError as error:
            logger.debug("缓存删除失败：%s", error)

    def delete_pattern(self, pattern: str) -> None:
        """按模式非阻塞删除（scan_iter），用于批量失效。"""
        if not self.enabled:
            return
        try:
            for key in self.client.scan_iter(match=pattern, count=200):
                self.client.delete(key)
        except RedisError as error:
            logger.debug("缓存批量删除失败：%s", error)

    def invalidate_settings(self) -> None:
        """设置变更：清空设置缓存，并作废依赖切分参数的 RAG 缓存。"""
        self.delete(self.key_settings())
        self.delete_pattern(f"{self.prefix}:rag:*")

    def invalidate_knowledge(self) -> None:
        """知识库变更（上传/删除）：清空统计与全部 RAG 检索缓存。"""
        self.delete(self.key_stats())
        self.delete_pattern(f"{self.prefix}:rag:*")

    def invalidate_history(self, session_id: str = None) -> None:
        """会话变更：清空会话列表缓存，可选清空指定会话历史缓存。"""
        self.delete(self.key_sessions())
        if session_id:
            self.delete(self.key_history(session_id))

    def flush_all(self) -> None:
        """清空本服务前缀下的全部缓存。"""
        self.delete_pattern(f"{self.prefix}:*")


# 模块级默认实例（随应用启动创建，Redis 不可用时自动降级）
cache = CacheService()
