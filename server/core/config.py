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


def _env(name: str, default: str) -> str:
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

# MySQL数据库配置（本地默认 3308，Docker 中通过环境变量改为 3306）
MYSQL_HOST = _env("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = _env_int("MYSQL_PORT", 3308)
MYSQL_USER = _env("MYSQL_USER", "root")
MYSQL_PASSWORD = _env("MYSQL_PASSWORD", "123456")
MYSQL_DATABASE = _env("MYSQL_DATABASE", "db_ai_medical")
DATABASE_URL = _env(
    "DATABASE_URL",
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4",
)

# Neo4j知识图谱配置
NEO4J_URI = _env("NEO4J_URI", "bolt://127.0.0.1:7687")
NEO4J_USER = _env("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = _env("NEO4J_PASSWORD", "12345678")

# LLM：默认走本机 Ollama 的 OpenAI 兼容接口
OPENAI_API_KEY = _env("OPENAI_API_KEY", "")
OPENAI_BASE_URL = _env("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
LLM_MODEL = _env("LLM_MODEL", "qwen3.6-plus")
LLM_TEMPERATURE = _env_float("LLM_TEMPERATURE", 0.2)
LLM_REASONING = _env_bool("LLM_REASONING", False)
EMBEDDING_MODEL = _env("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_DIMENSIONS = _env_int("EMBEDDING_DIMENSIONS", 0)
EMBEDDING_BATCH_SIZE = _env_int("EMBEDDING_BATCH_SIZE", 10)

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
JWT_SECRET_KEY = _env("JWT_SECRET_KEY", "ai-medical-consult-secret-key-2026")
JWT_ALGORITHM = _env("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = _env_int("JWT_EXPIRE_MINUTES", 60 * 24)

# RAG配置
CHUNK_SIZE = _env_int("CHUNK_SIZE", 500)
CHUNK_OVERLAP = _env_int("CHUNK_OVERLAP", 80)
RETRIEVAL_TOP_K = _env_int("RETRIEVAL_TOP_K", 5)

if not OPENAI_API_KEY:
    print("[警告] 未检测到环境变量 OPENAI_API_KEY，LLM和向量化功能将无法正常使用！")
elif _local_llm:
    print(f"[配置] 使用本地 LLM 接口 {OPENAI_BASE_URL} ，模型 {LLM_MODEL}")


class Settings:
    """配置类 - 统一访问入口"""

    project_name: str = PROJECT_NAME
    mysql_host: str = MYSQL_HOST
    mysql_port: int = MYSQL_PORT
    mysql_user: str = MYSQL_USER
    mysql_password: str = MYSQL_PASSWORD
    mysql_database: str = MYSQL_DATABASE
    database_url: str = DATABASE_URL
    neo4j_uri: str = NEO4J_URI
    neo4j_user: str = NEO4J_USER
    neo4j_password: str = NEO4J_PASSWORD
    openai_api_key: str = OPENAI_API_KEY
    openai_base_url: str = OPENAI_BASE_URL
    llm_model: str = LLM_MODEL
    llm_temperature: float = LLM_TEMPERATURE
    llm_reasoning: bool = LLM_REASONING
    embedding_model: str = EMBEDDING_MODEL
    embedding_dimensions: int = EMBEDDING_DIMENSIONS
    embedding_batch_size: int = EMBEDDING_BATCH_SIZE
    upload_dir: str = UPLOAD_DIR
    chroma_persist_dir: str = CHROMA_PERSIST_DIR
    chroma_collection: str = CHROMA_COLLECTION
    jwt_secret_key: str = JWT_SECRET_KEY
    jwt_algorithm: str = JWT_ALGORITHM
    jwt_expire_minutes: int = JWT_EXPIRE_MINUTES
    chunk_size: int = CHUNK_SIZE
    chunk_overlap: int = CHUNK_OVERLAP
    retrieval_top_k: int = RETRIEVAL_TOP_K


settings = Settings()
