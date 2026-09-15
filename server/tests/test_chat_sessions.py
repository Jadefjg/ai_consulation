import sys
from types import ModuleType

from fastapi import FastAPI
from fastapi.testclient import TestClient

from db.session import get_db
from models.consult import ConsultSession


# 会话列表不依赖 RAG；测试环境无需加载其可选的 LangChain 依赖。
rag_service = ModuleType("services.rag_service")
rag_service.get_rag_service = lambda: None
sys.modules.setdefault("services.rag_service", rag_service)

from api.v1 import chat  # noqa: E402


def test_user_can_list_chat_sessions(db_session, auth_headers):
    db_session.add(ConsultSession(user_id=1, title="头痛咨询", message_count=2))
    db_session.commit()

    app = FastAPI()
    app.include_router(chat.router, prefix="/api/v1/chat")

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    with TestClient(app) as client:
        response = client.get("/api/v1/chat/sessions", headers=auth_headers("user"))

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "头痛咨询"
    assert data[0]["message_count"] == 2
    assert data[0]["human_review"] is None
