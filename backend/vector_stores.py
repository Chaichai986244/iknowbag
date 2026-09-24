from huggingface_hub import delete_file

import config_data as cfg
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings







class VectorStoreService(object):
    def __init__(self):
        self.embedding = DashScopeEmbeddings(model="text-embedding-v4")
        self.vector_store = Chroma(
            collection_name=cfg.collection_name,
            embedding_function=self.embedding,
            persist_directory=cfg.persist_directory,# 持久化目录
            )
    def get_retriever(self):
        return self.vector_store.as_retriever(
            search_kwargs={"k": cfg.top_k}
        )



if __name__ == "__main__":
    vector_store_service = VectorStoreService()
    retriever = vector_store_service.get_retriever()
    print(retriever.invoke("AI领域发生了什么"))