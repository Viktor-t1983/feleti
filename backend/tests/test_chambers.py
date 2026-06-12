"""Chambers CRUD endpoint tests."""
from __future__ import annotations

from uuid import uuid4


def _unique_slug(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def _get_first_manufacturer_id(client, auth_headers) -> int:
    resp = client.get("/manufacturers?size=1", headers=auth_headers)
    assert resp.status_code == 200
    items = resp.json().get("items", [])
    assert len(items) > 0, "No manufacturers found — seed data required"
    return items[0]["id"]


def test_list_chambers(client, auth_headers):
    resp = client.get("/chambers?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_chamber(client, auth_headers):
    mfr_id = _get_first_manufacturer_id(client, auth_headers)
    slug = _unique_slug("test-chamber")
    resp = client.post(
        "/chambers",
        headers=auth_headers,
        json={
            "model": "Тестовая камера",
            "slug": slug,
            "type": "универсальное",
            "manufacturer_id": mfr_id,
            "max_load_kg": 100,
            "description": "Для тестов",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["model"] == "Тестовая камера"
    assert data["slug"] == slug
    assert data["type"] == "универсальное"
    return data


def test_get_chamber(client, auth_headers):
    created = test_create_chamber(client, auth_headers)
    resp = client.get(f"/chambers/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created["id"]


def test_update_chamber(client, auth_headers):
    created = test_create_chamber(client, auth_headers)
    resp = client.patch(
        f"/chambers/{created['id']}",
        headers=auth_headers,
        json={"max_load_kg": 200},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_load_kg"] == 200


def test_delete_chamber(client, auth_headers):
    created = test_create_chamber(client, auth_headers)
    resp = client.delete(f"/chambers/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/chambers/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404


def test_get_chamber_404(client, auth_headers):
    resp = client.get("/chambers/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_create_chamber_no_auth(client):
    resp = client.post("/chambers", json={"model": "x", "slug": "x", "type": "универсальное"})
    assert resp.status_code == 401
