"""Brine CRUD endpoint tests."""
from __future__ import annotations

from uuid import uuid4


def _unique_slug(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def test_list_brines(client, auth_headers):
    resp = client.get("/brines?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_brine(client, auth_headers):
    slug = _unique_slug("test-brine")
    resp = client.post(
        "/brines",
        headers=auth_headers,
        json={
            "name": "Тестовый посол",
            "slug": slug,
            "method": "сухой",
            "salt_percent": 3.5,
            "sugar_percent": 1.0,
            "nitrite_ppm": 80,
            "nitrate_ppm": 0,
            "duration_hours": 24,
            "temp_c": 4,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Тестовый посол"
    assert data["slug"] == slug
    return data


def test_get_brine(client, auth_headers):
    created = test_create_brine(client, auth_headers)
    resp = client.get(f"/brines/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Тестовый посол"


def test_update_brine(client, auth_headers):
    created = test_create_brine(client, auth_headers)
    resp = client.patch(
        f"/brines/{created['id']}",
        headers=auth_headers,
        json={"description": "Обновлённое описание"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Обновлённое описание"


def test_delete_brine(client, auth_headers):
    created = test_create_brine(client, auth_headers)
    resp = client.delete(f"/brines/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_get_brine_404(client, auth_headers):
    resp = client.get("/brines/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_filter_by_method(client, auth_headers):
    resp = client.get("/brines?method=сухой&size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["method"] == "сухой"


def test_create_brine_no_auth(client):
    resp = client.post(
        "/brines",
        json={
            "name": "x",
            "slug": "x",
            "salt_percent": 0,
            "sugar_percent": 0,
            "nitrite_ppm": 0,
            "nitrate_ppm": 0,
            "duration_hours": 0,
            "temp_c": 4,
        },
    )
    assert resp.status_code == 401
