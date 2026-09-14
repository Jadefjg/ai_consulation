import pytest


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
