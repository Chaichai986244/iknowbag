"""知识库开发"""
import os
import config_data as cfg
import hashlib
from io import BytesIO
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from datetime import datetime

def check_md5(md5_str:str):
    if not os.path.exists(cfg.md5_path):
        open(cfg.md5_path,"w").close()
        return False
    else:
        for line in open(cfg.md5_path,"r",encoding="utf-8").readlines():
            line = line.strip()
            if line == md5_str :
                return True
        return False



def save_md5(md5_str:str):
    with open(cfg.md5_path,"a",encoding="utf-8") as f:
        f.write(md5_str+"\n")



def get_string_md5(input_str:str,encoding='utf-8'):
    str_bytes = input_str.encode(encoding=encoding)
    #创建md5对象
    md5_obj = hashlib.md5()
    #更新md5对象
    md5_obj.update(str_bytes)
    #获取md5值
    return md5_obj.hexdigest()


def get_bytes_md5(input_bytes: bytes):
    md5_obj = hashlib.md5()
    md5_obj.update(input_bytes)
    return md5_obj.hexdigest()



class KnowledgeBaseService(object):
    def __init__(self):
        os.makedirs(cfg.persist_directory,exist_ok=True)
        self.chroma = Chroma(
            collection_name=cfg.collection_name,
            embedding_function=DashScopeEmbeddings(model="text-embedding-v4"),
            persist_directory=cfg.persist_directory,# 持久化目录
            )
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=cfg.chunk_size,# 每个chunk的字符数，不能超过模型的最大输入长度
            chunk_overlap=cfg.chunk_overlap,# 两个chunk之间的重叠字符数
            length_function=len,# 计算字符数的函数
            separators=cfg.separators# 自然段落分割符，按顺序匹配
            )

    def get_statistics(self):
        """返回向量库的文本块数量和文件来源。"""
        collection_data = self.chroma.get(include=["metadatas"])
        metadatas = collection_data.get("metadatas") or []
        source_counts = {}
        source_types = {}
        for metadata in metadatas:
            if not metadata or not metadata.get("source"):
                continue
            source = metadata["source"]
            source_counts[source] = source_counts.get(source, 0) + 1
            source_types[source] = metadata.get("file_type", "txt")

        sources = sorted(source_counts)
        source_details = [
            {
                "source": source,
                "chunk_count": source_counts[source],
                "file_type": source_types[source],
            }
            for source in sources
        ]
        return {
            "document_count": len(collection_data.get("ids") or []),
            "source_count": len(sources),
            "sources": sources,
            "source_details": source_details,
        }

    def _is_duplicate(self, file_hash: str, file_name: str):
        """检查文件内容是否已存在，并兼容旧数据。"""
        hash_result = self.chroma.get(
            where={"file_hash": file_hash},
            include=[],
        )
        if hash_result.get("ids"):
            return True

        source_result = self.chroma.get(
            where={"source": file_name},
            include=["metadatas"],
        )
        source_metadatas = source_result.get("metadatas") or []
        # 旧数据没有 file_hash；同名文件按已存在处理。
        return any(
            not metadata or not metadata.get("file_hash")
            for metadata in source_metadatas
        )

    def delete_by_source(self, source: str):
        """删除某个来源对应的全部向量文本块。"""
        if not source or not source.strip():
            raise ValueError("文件来源不能为空")

        source = source.strip()
        source_result = self.chroma.get(
            where={"source": source},
            include=[],
        )
        ids = source_result.get("ids") or []
        if not ids:
            return 0

        self.chroma.delete(ids=ids)
        return len(ids)

    def upload_by_str(self,data,file_name):#将上传的字符串存到向量数据库
        if not data or not data.strip():
            return "文件内容为空，未写入知识库"

        md5_hex = get_string_md5(data)
        if self._is_duplicate(md5_hex, file_name):
            return "文件已存在，无需重复上传"
        if len(data) > cfg.max_split:
            knowledge_chunks = self.spliter.split_text(data)
        else:
            knowledge_chunks = [data]

        metadata = {
            "create_time":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source":file_name,
            "operator":"system",
            "file_type":"txt",
            "file_hash":md5_hex,
        }
        
        self.chroma.add_texts(
            knowledge_chunks,
            metadatas=[metadata for _ in knowledge_chunks]
        )
        return f"上传成功，共写入 {len(knowledge_chunks)} 个文本块"

    def upload_pdf(self, pdf_bytes: bytes, file_name: str):
        """解析 PDF，按页提取文本、切分后写入向量库。"""
        if not pdf_bytes:
            return "PDF 文件为空，未写入知识库"

        md5_hex = get_bytes_md5(pdf_bytes)
        if self._is_duplicate(md5_hex, file_name):
            return "文件已存在，无需重复上传"

        reader = PdfReader(BytesIO(pdf_bytes))
        page_documents = []
        create_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for page_index, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            page_text = page_text.strip()
            if not page_text:
                continue

            metadata = {
                "create_time": create_time,
                "source": file_name,
                "page": page_index + 1,
                "operator": "system",
                "file_type": "pdf",
                "file_hash": md5_hex,
            }
            page_documents.append(
                Document(page_content=page_text, metadata=metadata)
            )

        if not page_documents:
            return "PDF 中未提取到文本；如果是扫描件，需要先进行 OCR"

        knowledge_chunks = self.spliter.split_documents(page_documents)
        self.chroma.add_documents(knowledge_chunks)

        return (
            f"上传成功，共解析 {len(reader.pages)} 页，"
            f"写入 {len(knowledge_chunks)} 个文本块"
        )
