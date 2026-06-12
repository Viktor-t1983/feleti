"""Competitor CRUD endpoint tests."""
from __future__ import annotations

from uuid import uuid4


def _unique_slug(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def test_list_competitors(client, auth_headers):
    resp = client.get("/competitors?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_competitor(client, auth_headers):
    slug = _unique_slug("test-competitor")
    resp = client.post(
        "/competitors",
        headers=auth_headers,
        json={
            "name": "Тестовый конкурент",
            "slug": slug,
            "country": "Россия",
            "segment": "middle",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Тестовый конкурент"
    assert data["slug"] == slug
    return data


def test_get_competitor(client, auth_headers):
    created = test_create_competitor(client, auth_headers)
    resp = client.get(f"/competitors/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Тестовый конкурент"


def test_update_competitor(client, auth_headers):
    created = test_create_competitor(client, auth_headers)
    resp = client.patch(
        f"/competitors/{created['id']}",
        headers=auth_headers,
        json={"description": "Обновлённое описание"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["description"] == "Обновлённое описание"


def test_delete_competitor(client, auth_headers):
    created = test_create_competitor(client, auth_headers)
    resp = client.delete(f"/competitors/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204


def test_get_competitor_404(client, auth_headers):
    resp = client.get("/competitors/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_filter_competitors(client, auth_headers):
    resp = client.get("/competitors?segment=middle&size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    items_with_segment = [item for item in data["items"] if item.get("segment")]
    assert len(items_with_segment) > 0
    for item in items_with_segment:
        assert "middle" in item["segment"].lower()


def test_create_competitor_no_auth(client):
    resp = client.post(
        "/competitors",
        json={"name": "x", "slug": "x"},
    )
    assert resp.status_code == 401
