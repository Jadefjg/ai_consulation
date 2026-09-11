"""AI智能医疗问诊平台系统 - FastAPI应用入口"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from core.config import settings
from db.session import engine, Base
from api.v1 import api_router
from utils.validation import format_validation_errors
import models  # noqa: F401  注册全部 ORM 模型，供 create_all 使用
import asyncio
from services.scheduler import expired_appointment_worker


def _ensure_runtime_dirs() -> None:
    """确保上传目录与向量库目录存在"""
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(os.path.join(settings.upload_dir, "knowledge"), exist_ok=True)
    os.makedirs(os.path.join(settings.upload_dir, "avatar"), exist_ok=True)
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化目录并确保数据表存在"""
    _ensure_runtime_dirs()
    Base.metadata.create_all(bind=engine)
    print(f"[启动] {settings.project_name} 服务已就绪")
    if settings.jwt_secret_key == "ai-medical-consult-secret-key-2026":
        print("[警告] JWT_SECRET_KEY 使用默认值，生产环境请通过环境变量设置强密钥")
    if not settings.openai_api_key:
        print("[警告] OPENAI_API_KEY 未设置，LLM功能不可用")
    stop = asyncio.Event()
    task = asyncio.create_task(expired_appointment_worker(stop))
    yield
    stop.set()
    await task


app = FastAPI(
    title=settings.project_name,
    description="基于RAG+LangChain+Neo4j的AI智能医疗问诊平台",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一 HTTP 异常响应格式，便于前端展示 message"""
    detail = exc.detail
    if isinstance(detail, str):
        message = detail
    elif isinstance(detail, list):
        message = "；".join(str(item) for item in detail)
    else:
        message = str(detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": message, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """统一参数校验错误为中文提示"""
    message = format_validation_errors(exc.errors())
    return JSONResponse(
        status_code=422,
        content={"code": 422, "message": message, "data": None},
    )
# CORS跨域（Bearer Token 场景不依赖 Cookie，无需 credentials）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件仅挂载头像目录，知识库文件不对外暴露
_ensure_runtime_dirs()
_avatar_dir = os.path.join(settings.upload_dir, "avatar")
app.mount("/uploads33/avatar", StaticFiles(directory=_avatar_dir), name="avatar_uploads")

# 注册API路由
app.include_router(api_router)


@app.get("/")
async def root():
    """根路径"""
    return {"message": f"欢迎使用{settings.project_name}", "docs": "/docs"}


@app.get("/health")
async def health():
    """容器健康检查"""
    return {"status": "ok"}
