"""User CRUD endpoint tests (admin-only)."""
from __future__ import annotations

from uuid import uuid4


def _unique_username(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def test_list_users(client, auth_headers):
    resp = client.get("/users?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_user(client, auth_headers):
    username = _unique_username("testuser")
    resp = client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": username,
            "email": f"{username}@test.com",
            "password": "testpass123",
            "full_name": "Тестовый пользователь",
            "role": "operator",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == username
    assert data["email"] == f"{username}@test.com"
    return data


def test_get_user(client, auth_headers):
    created = test_create_user(client, auth_headers)
    resp = client.get(f"/users/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == created["username"]


def test_update_user(client, auth_headers):
    created = test_create_user(client, auth_headers)
    resp = client.patch(
        f"/users/{created['id']}",
        headers=auth_headers,
        json={"full_name": "Обновлённое имя"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Обновлённое имя"


def test_delete_user(client, auth_headers):
    created = test_create_user(client, auth_headers)
    resp = client.delete(f"/users/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_get_user_404(client, auth_headers):
    resp = client.get("/users/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_cannot_delete_self(client, auth_headers):
    resp = client.delete("/users/1", headers=auth_headers)
    assert resp.status_code == 400
    assert "Нельзя удалить самого себя" in resp.text


def test_create_user_no_auth(client):
    resp = client.post(
        "/users",
        json={
            "username": "noauth",
            "email": "noauth@test.com",
            "password": "testpass123",
        },
    )
    assert resp.status_code == 401
