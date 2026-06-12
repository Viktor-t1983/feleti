"""Products CRUD endpoint tests."""
from __future__ import annotations

from uuid import uuid4


def _unique_slug(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def test_list_products(client, auth_headers):
    resp = client.get("/products?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_product(client, auth_headers):
    slug = _unique_slug("test-product")
    resp = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Тестовый продукт",
            "slug": slug,
            "category": "мясо",
            "description": "Тестовое описание",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Тестовый продукт"
    assert data["slug"] == slug
    assert data["category"] == "мясо"
    return data


def test_get_product_by_slug(client, auth_headers):
    created = test_create_product(client, auth_headers)
    resp = client.get(f"/products/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == created["slug"]


def test_get_product(client, auth_headers):
    created = test_create_product(client, auth_headers)
    resp = client.get(f"/products/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Тестовый продукт"


def test_update_product(client, auth_headers):
    created = test_create_product(client, auth_headers)
    resp = client.patch(
        f"/products/{created['id']}",
        headers=auth_headers,
        json={"description": "Обновлённое описание"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Обновлённое описание"


def test_delete_product(client, auth_headers):
    created = test_create_product(client, auth_headers)
    resp = client.delete(f"/products/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_get_product_404(client, auth_headers):
    resp = client.get("/products/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_create_product_no_auth(client):
    resp = client.post("/products", json={"name": "x", "slug": "x", "category": "мясо"})
    assert resp.status_code == 401
