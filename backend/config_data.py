"""全局配置：路径、向量库参数、运行时参数默认值。

迁移说明：
- BASE_DIR 由 backend 目录上溯到项目根目录（Hweb），所有数据目录统一放在项目根。
- 路径支持从 .env 覆盖：CHROMA_PERSIST_PATH / SQLITE_DB_PATH / DOC_STORE_PATH。
- 运行时参数（chunk_size 等）不再从 runtime_settings.json 读取，
  改由 settings_store 从 SQLite 持久化后调用 apply_settings() 回写。
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载项目根目录下的 .env（DASHSCOPE_API_KEY / STEPFUN_API_KEY 等）
load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, ".env"))

BASE_DIR = Path(__file__).resolve().parent.parent
md5_path = str(BASE_DIR / "md5.text")
runtime_settings_path = str(BASE_DIR / "runtime_settings.json")


collection_name = "rag"
persist_directory = os.getenv(
    "CHROMA_PERSIST_PATH",
    str(BASE_DIR / "chroma_db"),
)
if not os.path.isabs(persist_directory):
    persist_directory = str(BASE_DIR / persist_directory)

# SQLite 数据库文件路径（可由 .env 的 SQLITE_DB_PATH 覆盖）
sqlite_db_path = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "chat.db"))
if not os.path.isabs(sqlite_db_path):
    sqlite_db_path = str(BASE_DIR / sqlite_db_path)

# 上传文档落盘路径（当前版本文档直接写入向量库，此路径预留）
doc_store_path = os.getenv("DOC_STORE_PATH", str(BASE_DIR / "upload_files"))
if not os.path.isabs(doc_store_path):
    doc_store_path = str(BASE_DIR / doc_store_path)


separators = ["\n\n", "\n", " ", "\t"]
chunk_size = 1000
chunk_overlap = 100

max_split = 1000
similarity_threshold = 2
top_k = 10

embedding_model = "text-embedding-v4"

# 和风天气 API：密钥与专属 Host 均从 .env 读取（QWEATHER_API_KEY / QWEATHER_API_HOST），
# 未配置时天气功能自动降级，不影响其余功能。
qweather_api_key = os.getenv("QWEATHER_API_KEY", "")
qweather_api_host = os.getenv("QWEATHER_API_HOST", "")


session_config = {
    "configurable": {
        "session_id": "user001",
    }
}
