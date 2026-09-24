"""历史数据迁移脚本：将原 JSON 存储迁移到 SQLite。

迁移内容：
1. chat_history/*.json → messages 表（会话历史）
2. runtime_settings.json → settings 表（运行时设置）

幂等性：目标表中已有数据则跳过，可安全重复执行。

用法：
    python migrate_data.py
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from langchain_core.messages import messages_from_dict

import config_data as cfg
import database as db_module
from database import MessageRecord, SETTINGS_KEY, SettingRecord

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

HISTORY_DIR = Path(cfg.BASE_DIR) / "chat_history"
RUNTIME_SETTINGS = Path(cfg.runtime_settings_path)


def migrate_settings(database: db_module.Database) -> bool:
    """将 runtime_settings.json 导入 settings 表（仅当目标键为空时）。"""
    if not RUNTIME_SETTINGS.exists():
        logger.info("未找到 runtime_settings.json，跳过设置迁移")
        return False
    try:
        payload = json.loads(RUNTIME_SETTINGS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        logger.warning("runtime_settings.json 读取失败：%s", error)
        return False

    with database.get_session() as session:
        existing = session.get(SettingRecord, SETTINGS_KEY)
        if existing is not None:
            logger.info("设置已存在于 SQLite，跳过（key=%s）", SETTINGS_KEY)
            return False
        session.add(SettingRecord(
            key=SETTINGS_KEY,
            value=json.dumps(payload, ensure_ascii=False),
            updated_at=datetime.now(),
        ))
        session.commit()
    logger.info("已迁移运行时设置：%s", sorted(payload.keys()))
    return True


def migrate_chat_history(database: db_module.Database) -> int:
    """将 chat_history/*.json 导入 messages 表，返回导入的会话数。"""
    if not HISTORY_DIR.exists():
        logger.info("未找到 chat_history 目录，跳过历史迁移")
        return 0

    imported = 0
    for file_path in sorted(HISTORY_DIR.glob("*.json")):
        session_id = file_path.stem
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            messages = messages_from_dict(data)
        except (OSError, json.JSONDecodeError, ValueError) as error:
            logger.warning("跳过 %s：%s", file_path.name, error)
            continue

        with database.get_session() as session:
            has_rows = session.query(MessageRecord.id).filter(
                MessageRecord.session_id == session_id
            ).first() is not None
            if has_rows:
                logger.info("会话 %s 已存在，跳过", session_id)
                continue

            fallback_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            rows = []
            for message in messages:
                if message.type not in {"human", "ai", "system"}:
                    continue
                created_at = message.additional_kwargs.get("created_at") or fallback_time
                rows.append(MessageRecord(
                    session_id=session_id,
                    role=message.type,
                    content=str(message.content),
                    created_at=_parse_time(created_at),
                    metadata_json=json.dumps(
                        message.additional_kwargs, ensure_ascii=False
                    ) if message.additional_kwargs else None,
                ))
            session.add_all(rows)
            session.commit()
        logger.info("已迁移会话 %s（%d 条消息）", session_id, len(rows))
        imported += 1
    return imported


def _parse_time(value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return datetime.now()


def main():
    logger.info("开始迁移历史数据到 SQLite（%s）", cfg.sqlite_db_path)
    database = db_module.Database()
    migrate_settings(database)
    count = migrate_chat_history(database)
    logger.info("迁移完成：会话历史 %d 个", count)


if __name__ == "__main__":
    sys.exit(main())
