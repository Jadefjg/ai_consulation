import pytest
from fastapi import HTTPException

from services.wechat_service import jscode2session


def test_devtools_mock_code_works_without_secret(monkeypatch):
    from services import wechat_service

    monkeypatch.setattr(wechat_service.settings, "wechat_mini_appid", "")
    monkeypatch.setattr(wechat_service.settings, "wechat_mini_secret", "")
    monkeypatch.setattr(wechat_service.settings, "wechat_dev_login", False)

    openid, unionid = jscode2session("the code is a mock one")
    assert openid == "devtools_mock_openid"
    assert unionid is None


def test_dev_prefix_code_works_when_secret_missing(monkeypatch):
    from services import wechat_service

    monkeypatch.setattr(wechat_service.settings, "wechat_mini_appid", "wx312528eab8f11a72")
    monkeypatch.setattr(wechat_service.settings, "wechat_mini_secret", "")
    monkeypatch.setattr(wechat_service.settings, "wechat_dev_login", False)

    openid, unionid = jscode2session("dev_localtestuser")
    assert openid == "localtestuser"
    assert unionid is None


def test_mock_code_rejected_when_production_secrets_ready(monkeypatch):
    from services import wechat_service

    monkeypatch.setattr(wechat_service.settings, "wechat_mini_appid", "wx312528eab8f11a72")
    monkeypatch.setattr(wechat_service.settings, "wechat_mini_secret", "real-secret")
    monkeypatch.setattr(wechat_service.settings, "wechat_dev_login", False)

    with pytest.raises(HTTPException) as exc:
        jscode2session("the code is a mock one")
    assert exc.value.status_code == 401


def test_empty_code_rejected():
    with pytest.raises(HTTPException) as exc:
        jscode2session("  ")
    assert exc.value.status_code == 400


def test_wechat_login_api_accepts_devtools_mock(client, monkeypatch):
    from services import wechat_service

    monkeypatch.setattr(wechat_service.settings, "wechat_mini_appid", "")
    monkeypatch.setattr(wechat_service.settings, "wechat_mini_secret", "")
    monkeypatch.setattr(wechat_service.settings, "wechat_dev_login", False)

    response = client.post(
        "/api/v1/auth/wechat",
        json={"code": "the code is a mock one", "nickname": "开发者工具"},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["role"] == "user"
    assert data["access_token"]
    assert data["nickname"] == "开发者工具"
