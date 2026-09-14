"""独立 AI 推理服务，仅负责模型生成。"""
from typing import Any

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from core.config import settings

app = FastAPI(title="AI Medical Inference", docs_url=None, redoc_url=None)


class GenerateRequest(BaseModel):
    messages: list[dict[str, Any]] = Field(..., max_length=20)


@app.get("/health/ready")
async def ready():
    return {"status": "ready"}


@app.post("/internal/generate")
async def generate(request: GenerateRequest):
    llm = ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
        streaming=True,
        temperature=settings.llm_temperature,
        timeout=300,
    )

    async def stream():
        async for chunk in llm.astream(request.messages):
            if chunk.content:
                yield str(chunk.content)

    return StreamingResponse(stream(), media_type="text/plain")
