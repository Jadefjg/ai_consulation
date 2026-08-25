"""Docker 容器启动入口：等待依赖、建表、可选初始化图谱/知识库后启动 uvicorn"""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


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
            print("[entrypoint] MySQL 已就绪")
            return
        except Exception as exc:
            last_error = exc
            print(f"[entrypoint] 等待 MySQL ... {exc}")
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
            print("[entrypoint] Neo4j 已就绪")
            return
        except Exception as exc:
            last_error = exc
            print(f"[entrypoint] 等待 Neo4j ... {exc}")
            time.sleep(3)
        finally:
            if driver is not None:
                driver.close()
    raise SystemExit(f"[entrypoint] Neo4j 等待超时: {last_error}")


def ensure_schema() -> None:
    """根据 ORM 创建缺失数据表"""
    from db.session import engine, Base
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    print("[entrypoint] 数据表检查完成")


def main() -> None:
    """容器启动主流程"""
    wait_for_mysql()
    wait_for_neo4j()
    ensure_schema()

    from scripts.seed_demo import seed_demo
    seed_demo()

    if _truthy("INIT_GRAPH", "true"):
        print("[entrypoint] 开始初始化知识图谱")
        from scripts.init_graph import init_graph
        init_graph()
    else:
        print("[entrypoint] 跳过知识图谱初始化（INIT_GRAPH=false）")

    if _truthy("INIT_KNOWLEDGE", "false"):
        from core.config import settings
        if not settings.openai_api_key:
            print("[entrypoint] 未配置 OPENAI_API_KEY，跳过知识库向量化")
        else:
            print("[entrypoint] 开始初始化知识库向量")
            from scripts.init_knowledge import init_knowledge
            init_knowledge()
    else:
        print("[entrypoint] 跳过知识库向量化（INIT_KNOWLEDGE=false）")

    print("[entrypoint] 启动 uvicorn")
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
