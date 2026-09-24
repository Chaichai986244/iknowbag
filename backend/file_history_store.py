"""会话历史存储：基于 SQLite 的实现（迁移自原 JSON 文件方案）。

对外接口与原实现保持完全一致：
- get_history(session_id) -> BaseChatMessageHistory
- delete_history(session_id) -> bool
- list_histories() -> list[dict]
- FileChatMessageHistory 类（SQLiteChatMessageHistory 的别名）

数据迁移：原 chat_history/*.json 中的历史记录可通过 migrate_data.py 导入。
"""
import logging
import os
import re
from datetime import datetime
from typing import List, Sequence

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from sqlalchemy import delete, func, select

import config_data as cfg
import database as db_module
from database import MessageRecord

logger = logging.getLogger(__name__)

# 保留原 HISTORY_DIR 定义（旧 JSON 数据目录，供迁移脚本引用）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "chat_history")


def normalize_session_id(value: str) -> str:
    """会话 ID 规范化：去危险字符、限长，空值回退 user001。"""
    safe_session_id = re.sub(r"[^\w\u4e00-\u9fff.-]", "_", str(value))
    return safe_session_id.strip("._")[:64] or "user001"


def _role_to_class(role: str):
    return {
        "human": HumanMessage,
        "ai": AIMessage,
        "system": SystemMessage,
    }.get(role, HumanMessage)


def _class_to_role(message: BaseMessage) -> str:
    return {
        "human": "human",
        "ai": "ai",
        "system": "system",
    }.get(message.type, "human")


class SQLiteChatMessageHistory(BaseChatMessageHistory):
    """基于 SQLite 的 langchain 会话历史。"""

    def __init__(self, session_id: str, storage_path=None, db: db_module.Database = None):
        self.session_id = normalize_session_id(session_id)
        # storage_path 保留兼容旧签名（FileChatMessageHistory(session_id, storage_path)）
        self.storage_path = storage_path
        self.db = db or db_module.get_db()

    @property
    def messages(self) -> List[BaseMessage]:
        with self.db.get_session() as session:
            rows = session.execute(
                select(MessageRecord)
                .where(MessageRecord.session_id == self.session_id)
                .order_by(MessageRecord.id.asc())
            ).scalars().all()
        result = []
        for row in rows:
            message_class = _role_to_class(row.role)
            result.append(
                message_class(
                    content=row.content or "",
                    additional_kwargs={"created_at": _format_created_at(row.created_at)},
                )
            )
        return result

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        rows = []
        now = datetime.now()
        with self.db.get_session() as session:
            for message in messages:
                created_at = message.additional_kwargs.get("created_at")
                if not created_at:
                    created_at = now.isoformat(timespec="seconds")
                rows.append(MessageRecord(
                    session_id=self.session_id,
                    role=_class_to_role(message),
                    content=str(message.content),
                    created_at=_parse_created_at(created_at),
                    metadata_json=db_module.json_dumps(
                        message.additional_kwargs
                    ) if message.additional_kwargs else None,
                ))
            session.add_all(rows)
            session.commit()
        logger.debug("会话 %s 写入 %d 条消息", self.session_id, len(rows))

    def clear(self) -> None:
        with self.db.get_session() as session:
            session.execute(
                delete(MessageRecord).where(MessageRecord.session_id == self.session_id)
            )
            session.commit()


# 兼容旧名称
FileChatMessageHistory = SQLiteChatMessageHistory


def get_history(session_id: str, db: db_module.Database = None) -> SQLiteChatMessageHistory:
    safe_session_id = normalize_session_id(session_id)
    return SQLiteChatMessageHistory(session_id=safe_session_id, db=db)


def delete_history(session_id: str, db: db_module.Database = None) -> bool:
    safe_session_id = normalize_session_id(session_id)
    database = db or db_module.get_db()
    with database.get_session() as session:
        result = session.execute(
            delete(MessageRecord).where(MessageRecord.session_id == safe_session_id)
        )
        session.commit()
    deleted = result.rowcount > 0
    logger.info("删除会话 %s：%s", safe_session_id, "成功" if deleted else "不存在")
    return deleted


def list_histories(db: db_module.Database = None) -> list:
    """返回会话列表（按最近更新时间倒序），字段与原 JSON 方案一致。"""
    database = db or db_module.get_db()
    with database.get_session() as session:
        rows = session.execute(
            select(
                MessageRecord.session_id,
                func.count(MessageRecord.id).label("message_count"),
                func.max(MessageRecord.created_at).label("updated_at"),
            )
            .group_by(MessageRecord.session_id)
            .order_by(func.max(MessageRecord.created_at).desc())
        ).all()

    items = []
    for row in rows:
        session_id, message_count, updated_at = row
        first_question = _first_question(session_id, database)
        items.append({
            "session_id": session_id,
            "title": (first_question[:20] if first_question else "") or "新对话",
            "updated_at": _format_created_at(updated_at) if updated_at else "",
            "message_count": message_count,
        })
    return items


def _first_question(session_id: str, database: db_module.Database) -> str:
    with database.get_session() as session:
        row = session.execute(
            select(MessageRecord.content)
            .where(
                MessageRecord.session_id == session_id,
                MessageRecord.role == "human",
            )
            .order_by(MessageRecord.id.asc())
            .limit(1)
        ).scalar_one_or_none()
    return str(row or "").strip()


def _parse_created_at(value):
    """兼容 ISO 字符串与 datetime 对象。"""
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return datetime.now()


def _format_created_at(value) -> str:
    if isinstance(value, str):
        return value
    return value.isoformat(timespec="seconds") if value else ""
