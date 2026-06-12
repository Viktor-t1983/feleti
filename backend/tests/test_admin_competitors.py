"""Tests for admin competitor management endpoints."""
from __future__ import annotations


def test_list_competitors(client, auth_headers):
    resp = client.get("/competitors", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) > 0


def test_get_competitor(client, auth_headers):
    resp = client.get("/competitors", headers=auth_headers)
    items = resp.json()["items"]
    competitor_id = items[0]["id"]

    resp = client.get(f"/competitors/{competitor_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == competitor_id


def test_create_competitor(client, auth_headers):
    resp = client.post(
        "/competitors",
        headers=auth_headers,
        json={
            "slug": "test-comp",
            "name": "Test Competitor",
            "country": "Testland",
            "segment": "Horeca",
            "is_main_competitor": False,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Competitor"
    assert data["slug"] == "test-comp"

    # Cleanup
    client.delete(f"/competitors/{data['id']}", headers=auth_headers)


def test_create_competitor_forbidden_for_non_admin(client):
    resp = client.post(
        "/competitors",
        json={"slug": "test-comp2", "name": "Test"},
    )
    assert resp.status_code == 401


def test_update_competitor(client, auth_headers):
    resp = client.get("/competitors", headers=auth_headers)
    competitor_id = resp.json()["items"][0]["id"]

    resp = client.patch(
        f"/competitors/{competitor_id}",
        headers=auth_headers,
        json={"name": "Updated Name via Test"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name via Test"

    # Restore
    client.patch(
        f"/competitors/{competitor_id}",
        headers=auth_headers,
        json={"name": resp.json()["name"].replace(" via Test", "")},
    )


def test_delete_competitor(client, auth_headers):
    created = client.post(
        "/competitors",
        headers=auth_headers,
        json={
            "slug": "test-delete-comp",
            "name": "Test Delete Competitor",
            "country": "Testland",
        },
    ).json()
    cid = created["id"]

    resp = client.delete(f"/competitors/{cid}", headers=auth_headers)
    assert resp.status_code == 204


def test_competitor_404(client, auth_headers):
    resp = client.get("/competitors/99999", headers=auth_headers)
    assert resp.status_code == 404
