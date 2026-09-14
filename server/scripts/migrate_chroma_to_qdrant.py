"""将现有 Chroma 集合批量迁移到 Qdrant，可重复执行。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from core.config import settings
from rag.vector_store import ChromaVectorStore, QdrantVectorStore


def main() -> None:
    source = ChromaVectorStore()
    target = QdrantVectorStore()
    offset = 0
    batch_size = 100
    while True:
        batch = source.collection.get(limit=batch_size, offset=offset, include=["documents", "metadatas"])
        ids = batch.get("ids", [])
        if not ids:
            break
        target.add_documents(batch["documents"], batch["metadatas"], ids)
        offset += len(ids)
    print(f"Migrated {offset} vectors to {settings.qdrant_url}")


if __name__ == "__main__":
    main()
