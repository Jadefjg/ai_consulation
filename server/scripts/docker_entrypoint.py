"""Docker 容器启动入口：等待依赖、建表、可选初始化图谱/知识库后启动 uvicorn"""
import os
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from core.logging import configure_logging

configure_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


def _truthy(name: str, default: str = "false") -> bool:
    """解析布尔环境变量"""
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


def wait_for_mysql(timeout: int = 120) -> None:
    """等待 MySQL 可连接"""
    import pymysql
    from core.config import settings

    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        try:
            conn = pymysql.connect(
                host=settings.mysql_host,
                port=settings.mysql_port,
                user=settings.mysql_user,
                password=settings.mysql_password,
                database=settings.mysql_database,
                charset="utf8mb4",
                connect_timeout=3,
            )
            conn.close()
            logger.info("MySQL is ready", extra={"event": "mysql_ready"})
            return
        except Exception as exc:
            last_error = exc
            logger.warning("waiting for MySQL: %s", exc, extra={"event": "mysql_wait"})
            time.sleep(2)
    raise SystemExit(f"[entrypoint] MySQL 等待超时: {last_error}")


def wait_for_neo4j(timeout: int = 180) -> None:
    """等待 Neo4j Bolt 可连接"""
    from neo4j import GraphDatabase
    from core.config import settings

    deadline = time.time() + timeout
    last_error = None
    while time.time() < deadline:
        driver = None
        try:
            driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            driver.verify_connectivity()
            logger.info("Neo4j is ready", extra={"event": "neo4j_ready"})
            return
        except Exception as exc:
            last_error = exc
            logger.warning("waiting for Neo4j: %s", exc, extra={"event": "neo4j_wait"})
            time.sleep(3)
        finally:
            if driver is not None:
                driver.close()
    raise SystemExit(f"[entrypoint] Neo4j 等待超时: {last_error}")


def ensure_schema() -> None:
    """通过 Alembic 升级数据库，并兼容历史密码字段长度。"""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text
    from db.session import engine

    alembic_config = Config(str(ROOT / "alembic.ini"))
    command.upgrade(alembic_config, "head")
    # 兼容旧库：明文密码列过短，哈希后需扩容
    alter_sql = [
        "ALTER TABLE t_admin MODIFY COLUMN password VARCHAR(255) NOT NULL COMMENT '密码'",
        "ALTER TABLE t_user MODIFY COLUMN password VARCHAR(255) NOT NULL COMMENT '密码'",
        "ALTER TABLE t_doctor MODIFY COLUMN password VARCHAR(255) NOT NULL COMMENT '密码'",
        "ALTER TABLE t_admin ADD COLUMN admin_role VARCHAR(20) DEFAULT 'admin' COMMENT '管理员类型: admin/root'",
    ]
    with engine.begin() as conn:
        for sql in alter_sql:
            try:
                conn.execute(text(sql))
            except Exception as exc:
                logger.info("schema compatibility statement skipped: %s", exc, extra={"event": "schema_compat_skipped"})
    logger.info("database schema checked", extra={"event": "schema_checked"})


def main() -> None:
    """容器启动主流程"""
    wait_for_mysql()
    if _truthy("NEO4J_REQUIRED", "true"):
        wait_for_neo4j()
    else:
        logger.warning(
            "NEO4J_REQUIRED=false; skip Neo4j wait, graph API degraded",
            extra={"event": "neo4j_skipped"},
        )
    ensure_schema()

    if _truthy("SEED_DEMO", "false"):
        from scripts.seed_demo import seed_demo
        seed_demo()

    from scripts.ensure_root import ensure_root_admin
    ensure_root_admin()

    if _truthy("INIT_GRAPH", "true"):
        logger.info("initializing knowledge graph", extra={"event": "graph_init_started"})
        from scripts.init_graph import init_graph
        init_graph()
    else:
        logger.info("knowledge graph initialization skipped", extra={"event": "graph_init_skipped"})

    if _truthy("INIT_KNOWLEDGE", "false"):
        from core.config import settings
        if not settings.openai_api_key:
            logger.warning("knowledge vectorization skipped: OPENAI_API_KEY missing", extra={"event": "knowledge_init_skipped"})
        else:
            logger.info("initializing knowledge vectors", extra={"event": "knowledge_init_started"})
            from scripts.init_knowledge import init_knowledge
            init_knowledge()
    else:
        logger.info("knowledge vector initialization skipped", extra={"event": "knowledge_init_skipped"})

    logger.info("starting uvicorn", extra={"event": "uvicorn_start"})
    os.execvp(
        "uvicorn",
        [
            "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--proxy-headers",
            "--forwarded-allow-ips", "*",
        ],
    )


if __name__ == "__main__":
    main()
