"""核心配置模块 - 集中管理项目配置（支持环境变量覆盖，便于容器化部署）"""
import os
from pathlib import Path

# 项目根目录（server/）
BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file() -> None:
    """从项目根目录或 server/ 加载 .env，已存在的环境变量不覆盖"""
    candidates = [BASE_DIR.parent / ".env", BASE_DIR / ".env"]
    for path in candidates:
        if not path.is_file():
            continue
        parsed: dict[str, str] = {}
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            if key:
                parsed[key] = value
        for key, value in parsed.items():
            if key not in os.environ:
                os.environ[key] = value
        break


_load_env_file()


def _env(name: str, default: str = "") -> str:
    """读取字符串环境变量"""
    value = os.getenv(name)
    return default if value is None or value == "" else value


def _env_int(name: str, default: int) -> int:
    """读取整数环境变量"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    """读取浮点环境变量"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    """读取布尔环境变量"""
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


# 项目名称
PROJECT_NAME = _env("PROJECT_NAME", "AI智能医疗问诊平台系统")
APP_ENV = _env("APP_ENV", "development").lower()
LOG_LEVEL = _env("LOG_LEVEL", "INFO")

# MySQL数据库配置（本地默认 3308，Docker 中通过环境变量改为 3306）
MYSQL_HOST = _env("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = _env_int("MYSQL_PORT", 3308)
MYSQL_USER = _env("MYSQL_USER", "root")
MYSQL_PASSWORD = _env("MYSQL_PASSWORD")
MYSQL_DATABASE = _env("MYSQL_DATABASE", "db_ai_medical")
DATABASE_URL = _env(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4",
)

# Neo4j知识图谱配置
NEO4J_URI = _env("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = _env("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = _env("NEO4J_PASSWORD")
NEO4J_REQUIRED = _env_bool("NEO4J_REQUIRED", True)

# LLM：默认走本机 Ollama 的 OpenAI 兼容接口
OPENAI_API_KEY = _env("OPENAI_API_KEY", "")
OPENAI_BASE_URL = _env("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
LLM_MODEL = _env("LLM_MODEL", "qwen3.6-plus")
LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", 0.2)
LLM_REASONING = _env_bool("LLM_REASONING", False)
EMBEDDING_MODEL = _env("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIMENSIONS = _env_int("EMBEDDING_DIMENSIONS", 0)
EMBEDDING_BATCH_SIZE = _env_int("EMBEDDING_BATCH_SIZE", 10)

# CORS 仅允许显式配置的前端来源；本地默认覆盖常用开发端口。
CORS_ORIGINS = [
    item.strip().rstrip("/")
    for item in _env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if item.strip()
]

# 本地 Ollama 不校验密钥，但 OpenAI SDK 要求 api_key 非空
_local_llm = any(token in OPENAI_BASE_URL.lower() for token in ("127.0.0.1", "localhost", "host.docker.internal", "11434", "ollama"))
if not OPENAI_API_KEY and _local_llm:
    OPENAI_API_KEY = "ollama"

# 文件上传目录（Docker 中设为 /data/uploads；本地默认项目内 uploads）
UPLOAD_DIR = _env("UPLOAD_DIR", str(BASE_DIR / "uploads"))

# Chroma向量数据库目录
CHROMA_PERSIST_DIR = _env("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_db"))
CHROMA_COLLECTION = _env("CHROMA_COLLECTION", "medical_knowledge")

# JWT配置
JWT_SECRET_KEY = _env("JWT_SECRET_KEY")
JWT_ALGORITHM = _env("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = _env_int("JWT_EXPIRE_MINUTES", 60 * 24)

# RAG配置
CHUNK_SIZE = _env_int("CHUNK_SIZE", 500)
CHUNK_OVERLAP = _env_int("CHUNK_OVERLAP", 80)
RETRIEVAL_TOP_K = _env_int("RETRIEVAL_TOP_K", 5)

# Redis、缓存与后台任务
REDIS_URL = _env("REDIS_URL", "redis://127.0.0.1:6379/0")
CACHE_TTL_SECONDS = _env_int("CACHE_TTL_SECONDS", 120)
VECTOR_QUEUE_NAME = _env("VECTOR_QUEUE_NAME", "ai_medical:vectorize")
SSE_HEARTBEAT_SECONDS = _env_int("SSE_HEARTBEAT_SECONDS", 15)
SSE_MAX_SECONDS = _env_int("SSE_MAX_SECONDS", 300)

# 生产检索与服务拆分
VECTOR_BACKEND = _env("VECTOR_BACKEND", "qdrant")
QDRANT_URL = _env("QDRANT_URL", "http://127.0.0.1:6333")
QDRANT_API_KEY = _env("QDRANT_API_KEY")
HYBRID_VECTOR_WEIGHT = _env_float("HYBRID_VECTOR_WEIGHT", 0.65)
HYBRID_KEYWORD_WEIGHT = _env_float("HYBRID_KEYWORD_WEIGHT", 0.35)
RERANKER_URL = _env("RERANKER_URL")
RERANKER_MODEL = _env("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
AI_SERVICE_URL = _env("AI_SERVICE_URL")
OTEL_EXPORTER_OTLP_ENDPOINT = _env("OTEL_EXPORTER_OTLP_ENDPOINT")
OTEL_SERVICE_NAME = _env("OTEL_SERVICE_NAME", "ai-medical-api")

if APP_ENV in {"production", "prod"}:
    missing = ["JWT_SECRET_KEY"] if not JWT_SECRET_KEY else []
    if DATABASE_URL.startswith("mysql") and not MYSQL_PASSWORD:
        missing.append("MYSQL_PASSWORD")
    if NEO4J_REQUIRED and not NEO4J_PASSWORD:
        missing.append("NEO4J_PASSWORD")
    if missing:
        raise RuntimeError(f"生产环境缺少必要密钥配置: {', '.join(missing)}")
    insecure = []
    if DATABASE_URL.startswith("mysql") and MYSQL_PASSWORD in {"123456", "password", "root"}:
        insecure.append("MYSQL_PASSWORD")
    if NEO4J_REQUIRED and NEO4J_PASSWORD in {"12345678", "password", "neo4j"}:
        insecure.append("NEO4J_PASSWORD")
    if JWT_SECRET_KEY == "ai-medical-consult-secret-key-2026":
        insecure.append("JWT_SECRET_KEY")
    if insecure:
        raise RuntimeError(f"生产环境禁止使用已知默认密钥: {', '.join(insecure)}")

if JWT_SECRET_KEY and len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY 长度至少需要 32 个字符")


class Settings:
    """配置类 - 统一访问入口"""

    project_name: str = PROJECT_NAME
    app_env: str = APP_ENV
    log_level: str = LOG_LEVEL
    mysql_host: str = MYSQL_HOST
    mysql_port: int = MYSQL_PORT
    mysql_user: str = MYSQL_USER
    mysql_password: str = MYSQL_PASSWORD
    mysql_database: str = MYSQL_DATABASE
    database_url: str = DATABASE_URL
    neo4j_uri: str = NEO4J_URI
    neo4j_user: str = NEO4J_USER
    neo4j_password: str = NEO4J_PASSWORD
    neo4j_required: bool = NEO4J_REQUIRED
    openai_api_key: str = OPENAI_API_KEY
    openai_base_url: str = OPENAI_BASE_URL
    llm_model: str = LLM_MODEL
    llm_temperature: float = LLM_TEMPERATURE
    llm_reasoning: bool = LLM_REASONING
    embedding_model: str = EMBEDDING_MODEL
    embedding_dimensions: int = EMBEDDING_DIMENSIONS
    embedding_batch_size: int = EMBEDDING_BATCH_SIZE
    cors_origins: list[str] = CORS_ORIGINS
    upload_dir: str = UPLOAD_DIR
    chroma_persist_dir: str = CHROMA_PERSIST_DIR
    chroma_collection: str = CHROMA_COLLECTION
    jwt_secret_key: str = JWT_SECRET_KEY
    jwt_algorithm: str = JWT_ALGORITHM
    jwt_expire_minutes: int = JWT_EXPIRE_MINUTES
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP
    retrieval_top_k: int = RETRIEVAL_TOP_K
    redis_url: str = REDIS_URL
    cache_ttl_seconds: int = CACHE_TTL_SECONDS
    vector_queue_name: str = VECTOR_QUEUE_NAME
    sse_heartbeat_seconds: int = SSE_HEARTBEAT_SECONDS
    sse_max_seconds: int = SSE_MAX_SECONDS
    vector_backend: str = VECTOR_BACKEND
    qdrant_url: str = QDRANT_URL
    qdrant_api_key: str = QDRANT_API_KEY
    hybrid_vector_weight: float = HYBRID_VECTOR_WEIGHT
    hybrid_keyword_weight: float = HYBRID_KEYWORD_WEIGHT
    reranker_url: str = RERANKER_URL
    reranker_model: str = RERANKER_MODEL
    ai_service_url: str = AI_SERVICE_URL
    otel_exporter_otlp_endpoint: str = OTEL_EXPORTER_OTLP_ENDPOINT
    otel_service_name: str = OTEL_SERVICE_NAME


settings = Settings()
