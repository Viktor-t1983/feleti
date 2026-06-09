"""Tests for admin manufacturer management endpoints."""
from __future__ import annotations


def test_list_manufacturers(client, auth_headers):
    resp = client.get("/manufacturers", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) > 0


def test_get_manufacturer(client, auth_headers):
    resp = client.get("/manufacturers", headers=auth_headers)
    mfgs = resp.json()["items"]
    mfg_id = mfgs[0]["id"]

    resp = client.get(f"/manufacturers/{mfg_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == mfg_id


def test_create_manufacturer(client, auth_headers):
    resp = client.post(
        "/manufacturers",
        headers=auth_headers,
        json={
            "slug": "test-mfg",
            "name": "Test Manufacturer",
            "country": "Testland",
            "is_our_brand": False,
            "is_competitor": False,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Manufacturer"

    # Cleanup
    client.delete(f"/manufacturers/{data['id']}", headers=auth_headers)


def test_create_manufacturer_duplicate_slug(client, auth_headers):
    resp = client.post(
        "/manufacturers",
        headers=auth_headers,
        json={
            "slug": "feleti",
            "name": "Duplicate Slug",
            "country": "Test",
        },
    )
    assert resp.status_code == 409


def test_create_manufacturer_forbidden_without_auth(client):
    resp = client.post(
        "/manufacturers",
        json={"slug": "test-mfg2", "name": "Test"},
    )
    assert resp.status_code == 401


def test_update_manufacturer(client, auth_headers):
    resp = client.get("/manufacturers", headers=auth_headers)
    mfgs = resp.json()["items"]
    mfg_id = mfgs[0]["id"]

    resp = client.patch(
        f"/manufacturers/{mfg_id}",
        headers=auth_headers,
        json={"name": "Updated MFG Name via Test"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated MFG Name via Test"

    # Restore
    client.patch(
        f"/manufacturers/{mfg_id}",
        headers=auth_headers,
        json={"name": resp.json()["name"].replace(" via Test", "")},
    )


def test_delete_manufacturer(client, auth_headers):
    created = client.post(
        "/manufacturers",
        headers=auth_headers,
        json={
            "slug": "test-delete-mfg",
            "name": "Test Delete MFG",
            "country": "Testland",
        },
    ).json()
    mfg_id = created["id"]

    resp = client.delete(f"/manufacturers/{mfg_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_manufacturer_404(client, auth_headers):
    resp = client.get("/manufacturers/99999", headers=auth_headers)
    assert resp.status_code == 404
