"""Ingredients CRUD endpoint tests."""
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
    slug = _unique_slug("kurinaya-grudka")
    resp = client.post(
        "/ingredients",
        headers=auth_headers,
        json={
            "name": "Куриная грудка",
            "slug": slug,
            "type": "мясо",
            "protein_per_100g": 23.0,
            "fat_per_100g": 1.5,
            "carbs_per_100g": 0.0,
            "kcal_per_100g": 110.0,
            "price_per_kg": 450.0,
            "unit": "кг",
            "is_allergen": False,
            "allergens": [],
            "gmo_flag": False,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Куриная грудка"
    assert data["slug"] == slug
    assert data["type"] == "мясо"
    assert data["id"] > 0


def test_list_ingredients_with_data(client, auth_headers):
    slug = _unique_slug("govyadina")
    client.post(
        "/ingredients",
        headers=auth_headers,
        json={
            "name": "Говядина",
            "slug": slug,
            "type": "мясо",
            "protein_per_100g": 20.0,
            "fat_per_100g": 10.0,
            "carbs_per_100g": 0.0,
            "kcal_per_100g": 170.0,
            "price_per_kg": 600.0,
            "unit": "кг",
            "is_allergen": False,
            "allergens": [],
            "gmo_flag": False,
        },
    )
    resp = client.get("/ingredients?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1


def test_get_ingredient(client, auth_headers):
    slug = _unique_slug("sol-povarennaya")
    create_resp = client.post(
        "/ingredients",
        headers=auth_headers,
        json={
            "name": "Соль поваренная",
            "slug": slug,
            "type": "соль",
            "protein_per_100g": 0.0,
            "fat_per_100g": 0.0,
            "carbs_per_100g": 0.0,
            "kcal_per_100g": 0.0,
            "price_per_kg": 30.0,
            "unit": "кг",
            "is_allergen": False,
            "allergens": [],
            "gmo_flag": False,
        },
    )
    ing_id = create_resp.json()["id"]

    resp = client.get(f"/ingredients/{ing_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Соль поваренная"


def test_update_ingredient(client, auth_headers):
    slug = _unique_slug("perec-chernyy")
    create_resp = client.post(
        "/ingredients",
        headers=auth_headers,
        json={
            "name": "Перец чёрный",
            "slug": slug,
            "type": "специя",
            "protein_per_100g": 10.0,
            "fat_per_100g": 3.0,
            "carbs_per_100g": 38.0,
            "kcal_per_100g": 250.0,
            "price_per_kg": 800.0,
            "unit": "кг",
            "is_allergen": False,
            "allergens": [],
            "gmo_flag": False,
        },
    )
    ing_id = create_resp.json()["id"]

    resp = client.patch(
        f"/ingredients/{ing_id}",
        headers=auth_headers,
        json={"price_per_kg": 900.0},
    )
    assert resp.status_code == 200
    assert resp.json()["price_per_kg"] == 900.0


def test_delete_ingredient(client, auth_headers):
    slug = _unique_slug("oregano")
    create_resp = client.post(
        "/ingredients",
        headers=auth_headers,
        json={
            "name": "Орегано",
            "slug": slug,
            "type": "специя",
            "protein_per_100g": 9.0,
            "fat_per_100g": 4.0,
            "carbs_per_100g": 50.0,
            "kcal_per_100g": 260.0,
            "price_per_kg": 1200.0,
            "unit": "кг",
            "is_allergen": False,
            "allergens": [],
            "gmo_flag": False,
        },
    )
    ing_id = create_resp.json()["id"]

    resp = client.delete(f"/ingredients/{ing_id}", headers=auth_headers)
    assert resp.status_code == 200

    resp = client.get(f"/ingredients/{ing_id}", headers=auth_headers)
    assert resp.status_code == 404
