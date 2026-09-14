"""混合检索与 reranker 编排。"""
import logging
from typing import List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.config import settings
from models.knowledge import KnowledgeChunk
from rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)


def _keyword_search(db: Session, query: str, limit: int) -> List[dict]:
    terms = [term.strip() for term in query.split() if len(term.strip()) >= 2][:8]
    if not terms:
        return []
    filters = [KnowledgeChunk.content.like(f"%{term}%") for term in terms]
    rows = db.query(KnowledgeChunk).filter(or_(*filters)).limit(limit).all()
    return [{"content": row.content, "metadata": {"file_id": str(row.file_id), "chunk_index": row.chunk_index}, "keyword_score": 1.0} for row in rows]


def _rerank(query: str, candidates: List[dict]) -> List[dict]:
    """调用可选 reranker；未配置时使用词项覆盖率的确定性 fallback。"""
    if settings.reranker_url:
        try:
            import httpx
            response = httpx.post(settings.reranker_url, json={"model": settings.reranker_model, "query": query, "documents": [item["content"] for item in candidates]}, timeout=15)
            response.raise_for_status()
            scores = response.json().get("scores", [])
            for item, score in zip(candidates, scores):
                item["rerank_score"] = float(score)
        except Exception:
            logger.warning("reranker unavailable; fallback scoring used", exc_info=True, extra={"event": "reranker_failed"})
    query_terms = {term for term in query.split() if len(term) >= 2}
    for item in candidates:
        coverage = sum(term in item["content"] for term in query_terms) / max(len(query_terms), 1)
        item["rerank_score"] = item.get("rerank_score", coverage)
        item["score"] = settings.hybrid_vector_weight * item.get("score", 0.0) + settings.hybrid_keyword_weight * max(item.get("keyword_score", 0.0), coverage) + item["rerank_score"] * 0.2
    return sorted(candidates, key=lambda item: item["score"], reverse=True)


def hybrid_search(db: Session, query: str, top_k: int | None = None) -> List[dict]:
    limit = max((top_k or settings.retrieval_top_k) * 3, 10)
    vector_items = get_vector_store().search(query, limit)
    keyword_items = _keyword_search(db, query, limit)
    merged = {}
    for item in [*vector_items, *keyword_items]:
        key = item.get("metadata", {}).get("vector_id") or item["content"][:200]
        current = merged.get(key)
        if current is None or item.get("score", 0) > current.get("score", 0):
            merged[key] = item
    return _rerank(query, list(merged.values()))[:top_k or settings.retrieval_top_k]
