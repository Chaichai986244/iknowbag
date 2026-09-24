"""SQLite 数据库层：连接池、ORM 模型、会话管理。

迁移说明：
- 原项目使用 JSON 文件存储对话历史（chat_history/*.json）与运行时设置
  （runtime_settings.json），本模块将其统一迁移到 SQLite。
- 通过 SQLAlchemy 管理连接，SQLite 采用 NullPool 以避免跨线程共享连接问题。
- 表结构：
  * messages —— 对话消息（会话维度）
  * settings —— 键值型运行时设置（JSON 序列化）
"""
import json
import logging
import os
from datetime import datetime

import config_data as cfg
from sqlalchemy import Column, DateTime, Index, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

Base = declarative_base()


class MessageRecord(Base):
    """对话消息记录。"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    role = Column(String(16), nullable=False, default="human")  # human / ai / system
    content = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, index=True)
    # 额外元数据（JSON 字符串），预留 langchain additional_kwargs 等扩展字段
    metadata_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_messages_session_created", "session_id", "created_at"),
    )


class SettingRecord(Base):
    """运行时设置记录（键值对，值为 JSON）。"""

    __tablename__ = "settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)  # JSON 字符串
    updated_at = Column(DateTime, nullable=False)


SETTINGS_KEY = "runtime"


def _default_database_path() -> str:
    return cfg.sqlite_db_path


class Database:
    """数据库访问层：负责引擎、会话工厂与建表。

    可通过传入 db_path 构造独立实例（测试/多库场景），
    默认使用 config_data.sqlite_db_path。
    """

    def __init__(self, db_path: str = None):
        db_path = db_path or _default_database_path()
        parent = os.path.dirname(os.path.abspath(db_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        self.db_path = db_path
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=NullPool,
        )
        self.SessionLocal = sessionmaker(
            bind=self.engine,
            autoflush=False,
            expire_on_commit=False,
        )
        Base.metadata.create_all(self.engine)
        logger.info("SQLite 数据库已就绪：%s", db_path)

    def get_session(self):
        """获取一个新的 SQLAlchemy Session。"""
        return self.SessionLocal()


# 模块级默认数据库实例（惰性创建）
_default_db = None


def get_db() -> Database:
    """获取全局默认数据库实例。"""
    global _default_db
    if _default_db is None:
        _default_db = Database()
    return _default_db


def configure(db_path: str = None) -> Database:
    """重建全局默认数据库实例（供测试或切换库使用）。"""
    global _default_db
    _default_db = Database(db_path)
    return _default_db


def init_db() -> None:
    """显式初始化数据库（幂等）。"""
    get_db()


# ---------- 通用工具函数 ----------

def _now() -> datetime:
    return datetime.now()


def json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_loads(value: str):
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None
