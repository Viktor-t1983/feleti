"""Auth endpoint tests."""
from __future__ import annotations


def test_login_json_success(client):
    resp = client.post(
        "/auth/login/json",
        json={"username": "admin", "password": "admin"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_json_wrong_password(client):
    resp = client.post(
        "/auth/login/json",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "admin"
    assert data["is_superuser"] is True


def test_get_me_unauthorized(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
