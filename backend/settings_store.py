"""运行时设置存储：基于 SQLite 的实现（迁移自原 runtime_settings.json）。

对外接口与原实现保持一致：
- get_settings() / save_settings(payload) / normalize_settings(payload)
- apply_settings(settings) 回写 config_data 模块参数

设置以 JSON 序列化后存储于 settings 表的 "runtime" 键中。
"""
import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select

import config_data as cfg
import database as db_module
from database import SETTINGS_KEY, SettingRecord

logger = logging.getLogger(__name__)

# 保留原 JSON 文件路径定义（旧数据由 migrate_data.py 导入）
SETTINGS_FILE = Path(cfg.runtime_settings_path)

DEFAULT_SETTINGS = {
    "separators": cfg.separators,
    "chunk_size": cfg.chunk_size,
    "chunk_overlap": cfg.chunk_overlap,
    "max_split": cfg.max_split,
    "top_k": cfg.top_k,
    "weather": {
        "default_location": "北京",
    },
    "agent_tools": {
        "weather": True,
    },
}


def _decode_separator(value):
    mapping = {
        "\\n\\n": "\n\n",
        "\\n": "\n",
        "\\t": "\t",
        "空格": " ",
    }
    return mapping.get(value, value)


def _normalize_int(payload, key, minimum, maximum):
    try:
        value = int(payload[key])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{key} 必须是数字")

    if value < minimum or value > maximum:
        raise ValueError(f"{key} 必须在 {minimum} 到 {maximum} 之间")
    return value


def normalize_settings(payload):
    separators = [_decode_separator(str(item)) for item in payload.get("separators", [])]
    separators = [item for item in separators if item != ""]
    if not separators:
        raise ValueError("至少保留一个分隔符")

    chunk_size = _normalize_int(payload, "chunk_size", 100, 8000)
    chunk_overlap = _normalize_int(payload, "chunk_overlap", 0, 4000)
    max_split = _normalize_int(payload, "max_split", 100, 20000)
    top_k = _normalize_int(payload, "top_k", 1, 30)

    if chunk_overlap >= chunk_size:
        raise ValueError("重叠长度必须小于分块长度")

    weather_payload = payload.get("weather") or {}
    agent_tools_payload = payload.get("agent_tools") or {}

    return {
        "separators": separators,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "max_split": max_split,
        "top_k": top_k,
        "weather": {
            "default_location": str(weather_payload.get("default_location", "北京")).strip() or "北京",
        },
        "agent_tools": {
            "weather": bool(agent_tools_payload.get("weather", True)),
        },
    }


def apply_settings(settings):
    cfg.separators = settings["separators"]
    cfg.chunk_size = settings["chunk_size"]
    cfg.chunk_overlap = settings["chunk_overlap"]
    cfg.max_split = settings["max_split"]
    cfg.top_k = settings["top_k"]


def _read_settings_from_db(db) -> dict:
    with db.get_session() as session:
        row = session.execute(
            select(SettingRecord).where(SettingRecord.key == SETTINGS_KEY)
        ).scalar_one_or_none()
    if row is None:
        return {}
    try:
        value = json.loads(row.value)
        return value if isinstance(value, dict) else {}
    except (TypeError, json.JSONDecodeError):
        logger.warning("设置数据解析失败，使用默认值")
        return {}


def _write_settings_to_db(settings, db) -> None:
    with db.get_session() as session:
        record = session.execute(
            select(SettingRecord).where(SettingRecord.key == SETTINGS_KEY)
        ).scalar_one_or_none()
        payload = json.dumps(settings, ensure_ascii=False)
        if record is None:
            record = SettingRecord(
                key=SETTINGS_KEY,
                value=payload,
                updated_at=datetime.now(),
            )
            session.add(record)
        else:
            record.value = payload
            record.updated_at = datetime.now()
        session.commit()


def get_settings(db: db_module.Database = None) -> dict:
    database = db or db_module.get_db()
    settings = DEFAULT_SETTINGS.copy()
    runtime = _read_settings_from_db(database)
    settings.update(runtime)
    settings = normalize_settings(settings)
    apply_settings(settings)
    return settings


def save_settings(payload, db: db_module.Database = None) -> dict:
    database = db or db_module.get_db()
    settings = normalize_settings(payload)
    _write_settings_to_db(settings, database)
    apply_settings(settings)
    return settings
