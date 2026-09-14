"""可切换向量存储：生产 Qdrant，迁移期兼容 Chroma。"""
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from core.config import settings
from rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, texts: List[str], metadatas: List[dict], ids: List[str]) -> None: ...

    @abstractmethod
    def search(self, query: str, top_k: int | None = None) -> List[dict]: ...

    @abstractmethod
    def delete_by_file_id(self, file_id: int) -> None: ...


class QdrantVectorStore(VectorStore):
    def __init__(self):
        from qdrant_client import QdrantClient, models
        self.models = models
        self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None, timeout=30)
        self.collection_name = settings.chroma_collection
        self.embeddings = get_embeddings()

    def _ensure_collection(self, vector_size: int) -> None:
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(collection_name=self.collection_name, vectors_config=self.models.VectorParams(size=vector_size, distance=self.models.Distance.COSINE))
            self.client.create_payload_index(collection_name=self.collection_name, field_name="file_id", field_schema=self.models.PayloadSchemaType.KEYWORD)

    @staticmethod
    def _point_id(value: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"ai-medical:{value}"))

    def add_documents(self, texts: List[str], metadatas: List[dict], ids: List[str]) -> None:
        for start in range(0, len(texts), settings.embedding_batch_size):
            batch = texts[start:start + settings.embedding_batch_size]
            vectors = self.embeddings.embed_documents(batch)
            if not vectors:
                continue
            self._ensure_collection(len(vectors[0]))
            points = [self.models.PointStruct(id=self._point_id(ids[start + i]), vector=vector, payload={**metadatas[start + i], "content": batch[i], "source_id": ids[start + i]}) for i, vector in enumerate(vectors)]
            self.client.upsert(collection_name=self.collection_name, points=points, wait=True)

    def search(self, query: str, top_k: int | None = None) -> List[dict]:
        if not self.client.collection_exists(self.collection_name):
            return []
        hits = self.client.query_points(collection_name=self.collection_name, query=self.embeddings.embed_query(query), limit=top_k or settings.retrieval_top_k, with_payload=True).points
        return [{"content": (hit.payload or {}).get("content", ""), "metadata": {k: v for k, v in (hit.payload or {}).items() if k != "content"}, "distance": 1.0 - float(hit.score), "score": float(hit.score)} for hit in hits]

    def delete_by_file_id(self, file_id: int) -> None:
        if not self.client.collection_exists(self.collection_name):
            return
        selector = self.models.FilterSelector(filter=self.models.Filter(must=[self.models.FieldCondition(key="file_id", match=self.models.MatchValue(value=str(file_id)))]))
        self.client.delete(collection_name=self.collection_name, points_selector=selector, wait=True)


class ChromaVectorStore(VectorStore):
    def __init__(self):
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir, settings=ChromaSettings(anonymized_telemetry=False))
        self.collection = self.client.get_or_create_collection(name=settings.chroma_collection, metadata={"hnsw:space": "cosine"})
        self.embeddings = get_embeddings()

    def add_documents(self, texts: List[str], metadatas: List[dict], ids: List[str]) -> None:
        self.collection.upsert(documents=texts, embeddings=self.embeddings.embed_documents(texts), metadatas=metadatas, ids=ids)

    def search(self, query: str, top_k: int | None = None) -> List[dict]:
        result = self.collection.query(query_embeddings=[self.embeddings.embed_query(query)], n_results=top_k or settings.retrieval_top_k, include=["documents", "metadatas", "distances"])
        return [{"content": doc, "metadata": result["metadatas"][0][i], "distance": result["distances"][0][i]} for i, doc in enumerate(result.get("documents", [[]])[0])]

    def delete_by_file_id(self, file_id: int) -> None:
        for value in (file_id, str(file_id)):
            try:
                self.collection.delete(where={"file_id": value})
            except Exception:
                logger.warning("Chroma vector deletion failed", exc_info=True, extra={"event": "vector_delete_failed", "file_id": file_id})


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore() if settings.vector_backend == "chroma" else QdrantVectorStore()
    return _vector_store
