from langchain_core.documents import Document

from cache_service import cache
from vector_stores import VectorStoreService


class RagService(object):
    """RAG 检索能力，只作为 Agent 可调用工具的底层依赖。

    检索结果通过 Redis 缓存（键 knowbao:rag:{question_md5}），
    TTL 默认 300 秒；知识库变更时由 cache.invalidate_knowledge() 整体作废。
    """

    def __init__(self):
        self.vector_store_service = VectorStoreService()
        self.retriever = self.vector_store_service.get_retriever()

    def retrieve_documents(self, question: str) -> list[Document]:
        key = cache.key_rag(question)
        ttl = cache.ttl("rag")

        cached = cache.get_json(key)
        if cached is not None:
            return [
                Document(
                    page_content=item.get("content", ""),
                    metadata=item.get("metadata", {}),
                )
                for item in cached
            ]

        docs = self.retriever.invoke(question)
        cache.set_json(
            key,
            [
                {"content": doc.page_content, "metadata": doc.metadata}
                for doc in docs
            ],
            ttl,
        )
        return docs

    def format_documents(self, docs: list[Document]):
        if not docs:
            return "无相关资料"
        formatted_str = ""
        for doc in docs:
            formatted_str += f"文档片段：{doc.page_content}\n文档源数据：{doc.metadata}\n\n"
        return formatted_str

    def format_sources(self, docs: list[Document]) -> list[dict]:
        seen = set()
        sources = []
        for doc in docs:
            source_key = (
                doc.metadata.get("source", "未知来源"),
                doc.metadata.get("page"),
            )
            if source_key in seen:
                continue
            seen.add(source_key)
            sources.append(
                {"source": source_key[0], "page": source_key[1]}
            )
        return sources
