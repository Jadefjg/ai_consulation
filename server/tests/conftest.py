import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SERVER_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVER_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_permissions.db")
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-key-at-least-32-chars")
os.environ.setdefault("NEO4J_REQUIRED", "false")

from api.v1 import article, appointment, auth, user  # noqa: E402
from core.security import create_access_token, hash_password  # noqa: E402
from db.session import Base, get_db  # noqa: E402
from fastapi import FastAPI  # noqa: E402
import models  # noqa: E402,F401
from models.admin import Admin  # noqa: E402
from models.doctor import Doctor  # noqa: E402
from models.user import User  # noqa: E402


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'permissions.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        User(id=1, username="patient", password=hash_password("password"), real_name="患者", status=1),
        Doctor(id=2, username="doctor", password=hash_password("password"), real_name="医生", status=1),
        Admin(id=3, username="admin", password=hash_password("password"), nickname="管理员", status=1),
        Admin(id=4, username="root", password=hash_password("password"), nickname="超级管理员", status=1, admin_role="root"),
    ])
    session.commit()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/v1/auth")
    app.include_router(user.router, prefix="/api/v1/users")
    app.include_router(appointment.router, prefix="/api/v1/appointments")
    app.include_router(article.router, prefix="/api/v1/articles")

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def auth_headers():
    def build(role: str):
        identities = {
            "user": (1, "patient"),
            "doctor": (2, "doctor"),
            "admin": (3, "admin"),
            "root": (4, "root"),
        }
        user_id, username = identities[role]
        token = create_access_token({"sub": username, "user_id": user_id, "role": role})
        return {"Authorization": f"Bearer {token}"}

    return build
