"""Ingredient CRUD endpoint tests."""
from __future__ import annotations

from uuid import uuid4


def _unique_slug(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def test_list_ingredients(client, auth_headers):
    resp = client.get("/ingredients?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_ingredient(client, auth_headers):
    slug = _unique_slug("test-ingredient")
    resp = client.post(
        "/ingredients",
        headers=auth_headers,
        json={
            "name": "Тестовый ингредиент",
            "slug": slug,
            "type": "мясо",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Тестовый ингредиент"
    assert data["slug"] == slug
    assert data["type"] == "мясо"
    return data


def test_get_ingredient(client, auth_headers):
    created = test_create_ingredient(client, auth_headers)
    resp = client.get(f"/ingredients/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Тестовый ингредиент"


def test_update_ingredient(client, auth_headers):
    created = test_create_ingredient(client, auth_headers)
    resp = client.patch(
        f"/ingredients/{created['id']}",
        headers=auth_headers,
        json={"description": "Обновлённое описание"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Обновлённое описание"


def test_delete_ingredient(client, auth_headers):
    created = test_create_ingredient(client, auth_headers)
    resp = client.delete(f"/ingredients/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_get_ingredient_404(client, auth_headers):
    resp = client.get("/ingredients/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_filter_by_type(client, auth_headers):
    resp = client.get("/ingredients?type=мясо&size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["type"] == "мясо"


def test_create_ingredient_no_auth(client):
    resp = client.post("/ingredients", json={"name": "x", "slug": "x", "type": "мясо"})
    assert resp.status_code == 401
