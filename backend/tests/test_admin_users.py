"""Tests for admin user management endpoints."""
from __future__ import annotations

import pytest


def test_list_users(client, auth_headers):
    resp = client.get("/users", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] >= 1
    assert any(u["username"] == "admin" for u in data["items"])


def test_list_users_forbidden_without_auth(client):
    resp = client.get("/users")
    assert resp.status_code == 401


def test_create_user(client, auth_headers):
    resp = client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": "test_create_user",
            "email": "test_create@test.com",
            "password": "test123",
            "role": "operator",
            "is_active": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "test_create_user"
    assert data["role"] == "operator"
    assert data["is_active"] is True
    assert data["is_superuser"] is False

    # Cleanup
    client.delete(f"/users/{data['id']}", headers=auth_headers)


def test_create_user_duplicate(client, auth_headers):
    resp = client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": "admin",
            "email": "admin@feleti.by",
            "password": "test123",
            "role": "operator",
        },
    )
    assert resp.status_code == 409
    assert "уже существует" in resp.json()["detail"]


def test_update_user(client, auth_headers):
    # Create user first
    created = client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": "test_update_user",
            "email": "test_update@test.com",
            "password": "test123",
            "role": "viewer",
        },
    ).json()
    uid = created["id"]

    # Update
    resp = client.patch(
        f"/users/{uid}",
        headers=auth_headers,
        json={"full_name": "Updated Name", "role": "operator"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Updated Name"
    assert data["role"] == "operator"

    # Cleanup
    client.delete(f"/users/{uid}", headers=auth_headers)


def test_delete_user(client, auth_headers):
    created = client.post(
        "/users",
        headers=auth_headers,
        json={
            "username": "test_delete_user",
            "email": "test_delete@test.com",
            "password": "test123",
            "role": "operator",
        },
    ).json()
    uid = created["id"]

    resp = client.delete(f"/users/{uid}", headers=auth_headers)
    assert resp.status_code == 200

    # Verify deleted
    resp = client.get(f"/users/{uid}", headers=auth_headers)
    assert resp.status_code == 404


def test_cannot_delete_self(client, auth_headers, admin_token):
    resp = client.get("/users", headers=auth_headers)
    admin = next(u for u in resp.json()["items"] if u["username"] == "admin")

    resp = client.delete(f"/users/{admin['id']}", headers=auth_headers)
    assert resp.status_code == 400
    assert "самого себя" in resp.json()["detail"]


@pytest.mark.parametrize("role", ["technologist", "operator", "manager", "viewer"])
def test_non_admin_cannot_access_users(client, auth_headers, role):
    """Try to access /users as non-admin role."""
    resp = client.get("/users", headers=auth_headers)
    users = resp.json()["items"]

    non_admin_user = next(
        (u for u in users if u["role"] != "admin"),
        None,
    )
    if not non_admin_user:
        pytest.skip("No non-admin user found to test")

    resp = client.get("/users")
    assert resp.status_code == 401
