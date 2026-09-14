"""Redis 缓存与任务队列封装，缓存故障时业务降级运行。"""
import json
import logging
import uuid
from typing import Any, Optional

from redis import Redis
from redis.exceptions import RedisError

from core.config import settings

logger = logging.getLogger(__name__)
_client: Optional[Redis] = None


def get_redis() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=3)
    return _client


def cache_get(key: str) -> Optional[Any]:
    try:
        value = get_redis().get(key)
        return json.loads(value) if value is not None else None
    except (RedisError, ValueError):
        logger.warning("Redis cache read failed: key=%s", key, exc_info=True, extra={"event": "cache_read_failed"})
        return None


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    try:
        get_redis().set(
            key,
            json.dumps(value, ensure_ascii=False, default=str),
            ex=ttl or settings.cache_ttl_seconds,
        )
    except RedisError:
        logger.warning("Redis cache write failed: key=%s", key, exc_info=True, extra={"event": "cache_write_failed"})


def cache_delete_pattern(pattern: str) -> None:
    try:
        client = get_redis()
        keys = list(client.scan_iter(match=pattern, count=100))
        if keys:
            client.delete(*keys)
    except RedisError:
        logger.warning("Redis cache invalidation failed: pattern=%s", pattern, exc_info=True, extra={"event": "cache_invalidate_failed"})


def enqueue_vectorization(file_id: int) -> str:
    """提交持久化向量任务；队列不可用时由调用者返回 503。"""
    task_id = uuid.uuid4().hex
    payload = json.dumps({"task_id": task_id, "file_id": file_id}, ensure_ascii=False)
    get_redis().rpush(settings.vector_queue_name, payload)
    return task_id
