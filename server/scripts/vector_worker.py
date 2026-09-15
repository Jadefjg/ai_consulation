"""知识库向量化 Redis Worker。"""
import json
import logging
import os
import sys
import time
from pathlib import Path

from redis import Redis
from redis.exceptions import RedisError, TimeoutError as RedisTimeoutError

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from core.config import settings
from core.logging import configure_logging
from db.session import SessionLocal
from models.knowledge import KnowledgeFile
from services.rag_service import get_rag_service

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def process_job(payload: str) -> None:
    job = json.loads(payload)
    file_id = int(job["file_id"])
    task_id = job["task_id"]
    db = SessionLocal()
    try:
        record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
        if not record:
            logger.warning("vector job ignored because file is missing", extra={"event": "vector_job_missing", "file_id": file_id})
            return
        record.vector_task_id = task_id
        record.vector_status = 1
        record.vector_error = None
        db.commit()
        count = get_rag_service().process_file(db, record)
        logger.info("vector job completed: chunks=%s", count, extra={"event": "vector_job_completed", "file_id": file_id})
    except Exception as exc:
        db.rollback()
        record = db.query(KnowledgeFile).filter(KnowledgeFile.id == file_id).first()
        if record:
            record.vector_status = 3
            record.vector_error = str(exc)[:1000]
            db.commit()
        logger.exception("vector job failed", extra={"event": "vector_job_failed", "file_id": file_id})
    finally:
        db.close()


def main() -> None:
    # BLPOP 会阻塞等待；不能复用业务 Redis 客户端的 3s socket_timeout
    client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=None,
        health_check_interval=30,
    )
    logger.info("vector worker started", extra={"event": "vector_worker_started"})
    while True:
        try:
            item = client.blpop(settings.vector_queue_name, timeout=30)
            if item:
                process_job(item[1])
        except RedisTimeoutError:
            continue
        except RedisError:
            logger.exception("vector worker redis error", extra={"event": "vector_worker_redis_error"})
            time.sleep(2)


if __name__ == "__main__":
    main()
