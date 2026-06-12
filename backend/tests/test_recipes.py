"""Recipes CRUD + versions endpoint tests."""
from __future__ import annotations

from uuid import uuid4


def _unique_slug(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def _get_first_product_id(client, auth_headers) -> int:
    resp = client.get("/products?size=1", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json().get("items", [])
    assert len(items) > 0, "No products found — seed data required"
    return items[0]["id"]


def test_list_recipes(client, auth_headers):
    resp = client.get("/recipes?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_recipe(client, auth_headers):
    product_id = _get_first_product_id(client, auth_headers)
    slug = _unique_slug("test-recipe")
    resp = client.post(
        "/recipes",
        headers=auth_headers,
        json={
            "name": "Тестовый рецепт",
            "slug": slug,
            "product_id": product_id,
            "status": "draft",
            "description": "Тестовое описание",
        },
    )
    assert resp.status_code == 201, f"Create recipe failed: {resp.text}"
    data = resp.json()
    assert data["name"] == "Тестовый рецепт"
    assert data["slug"] == slug
    return data


def test_get_recipe(client, auth_headers):
    created = test_create_recipe(client, auth_headers)
    resp = client.get(f"/recipes/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Тестовый рецепт"


def test_update_recipe(client, auth_headers):
    created = test_create_recipe(client, auth_headers)
    resp = client.patch(
        f"/recipes/{created['id']}",
        headers=auth_headers,
        json={"status": "approved"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "approved"


def test_delete_recipe(client, auth_headers):
    created = test_create_recipe(client, auth_headers)
    resp = client.delete(f"/recipes/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_create_recipe_version(client, auth_headers):
    created = test_create_recipe(client, auth_headers)
    resp = client.post(
        f"/recipes/{created['id']}/versions",
        headers=auth_headers,
        json={
            "program": [
                {"name": "Сушка", "duration_min": 20, "t_chamber": 60},
            ],
            "notes": "Вторая версия",
        },
    )
    assert resp.status_code == 201, f"Create version failed: {resp.text}"
    data = resp.json()
    assert data["version_number"] >= 1


def test_list_recipe_versions(client, auth_headers):
    created = test_create_recipe(client, auth_headers)
    # Create a version first
    client.post(
        f"/recipes/{created['id']}/versions",
        headers=auth_headers,
        json={
            "program": [{"name": "Сушка", "duration_min": 20, "t_chamber": 60}],
            "notes": "Первая версия",
        },
    )
    resp = client.get(f"/recipes/{created['id']}/versions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_create_recipe_no_auth(client):
    resp = client.post("/recipes", json={"name": "x", "slug": "x", "product_id": 1})
    assert resp.status_code == 401
