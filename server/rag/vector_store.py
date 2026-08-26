"""Chroma向量数据库封装"""
import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from core.config import settings
from rag.embeddings import get_embeddings


class VectorStore:
    """Chroma向量存储管理器"""

    def __init__(self):
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "cosine"},
        )
        self.embeddings = get_embeddings()

    def add_documents(self, texts: List[str], metadatas: List[dict], ids: List[str]):
        """
        添加文档向量（分批嵌入）
        :param texts: 文本列表
        :param metadatas: 元数据列表
        :param ids: 向量ID列表
        """
        batch_size = settings.embedding_batch_size
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metas = metadatas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]
            vectors = self.embeddings.embed_documents(batch_texts)
            self.collection.add(
                documents=batch_texts,
                embeddings=vectors,
                metadatas=batch_metas,
                ids=batch_ids,
            )

    def search(self, query: str, top_k: int = None) -> List[dict]:
        """
        向量相似度检索
        :param query: 查询文本
        :param top_k: 返回数量
        :return: 检索结果列表
        """
        top_k = top_k or settings.retrieval_top_k
        query_vector = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        items = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                items.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return items

    def delete_by_file_id(self, file_id: int):
        """删除指定文件的所有向量（兼容 int/str 元数据）"""
        for value in (file_id, str(file_id)):
            try:
                self.collection.delete(where={"file_id": value})
            except Exception as exc:
                print(f"[VectorStore] delete_by_file_id({value}) failed: {exc}", flush=True)


# 全局单例
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取向量存储单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
