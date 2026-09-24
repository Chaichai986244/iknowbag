from dataclasses import dataclass


@dataclass
class RAGToolResult:
    context: str
    sources: list[dict]


class RAGTool:
    name = "rag_search"
    description = "检索用户知识库中的 PDF/TXT 资料片段。"

    def __init__(self, rag_service):
        self.rag_service = rag_service

    def run(self, query: str) -> RAGToolResult:
        docs = self.rag_service.retrieve_documents(query)
        return RAGToolResult(
            context=self.rag_service.format_documents(docs),
            sources=self.rag_service.format_sources(docs),
        )
