import pytest
from models.user import User


@pytest.mark.parametrize(
    ("path", "allowed_roles"),
    [
        ("/api/v1/articles/admin/list", {"admin", "root"}),
        ("/api/v1/users/list", {"admin", "root"}),
        ("/api/v1/appointments/my", {"user"}),
        ("/api/v1/appointments/doctor/my", {"doctor"}),
        ("/api/v1/appointments/admin/list", {"admin", "root"}),
    ],
)
def test_core_endpoint_role_matrix(client, auth_headers, path, allowed_roles):
    for role in ("user", "doctor", "admin", "root"):
        response = client.get(path, headers=auth_headers(role))
        if role in allowed_roles:
            assert response.status_code == 200, (path, role, response.text)
        else:
            assert response.status_code == 403, (path, role, response.text)


def test_protected_endpoint_rejects_anonymous(client):
    response = client.get("/api/v1/articles/admin/list")
    assert response.status_code == 401


def test_public_registration_cannot_create_admin(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "attacker",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "role": "admin",
            "real_name": "非法管理员",
        },
    )
    assert response.status_code == 400


def test_public_article_list_remains_anonymous(client):
    response = client.get("/api/v1/articles/list")
    assert response.status_code == 200


def test_wechat_login_issues_patient_token(client, db_session, monkeypatch):
    from services import wechat_service

    monkeypatch.setattr(wechat_service, "jscode2session", lambda code: ("openid_demo1", None))
    response = client.post("/api/v1/auth/wechat", json={"code": "wx_code_demo", "nickname": "小程序用户"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["role"] == "user"
    assert data["access_token"]
    assert data["nickname"] == "小程序用户"
    user = db_session.query(User).filter(User.wx_openid == "openid_demo1").one()
    assert user.username.startswith("wx")

    again = client.post("/api/v1/auth/wechat", json={"code": "wx_code_demo"})
    assert again.status_code == 200
    assert again.json()["data"]["user_id"] == data["user_id"]
