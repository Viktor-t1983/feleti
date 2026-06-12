"""Manufacturers public endpoint tests (non-admin)."""
from __future__ import annotations


def test_list_manufacturers(client, auth_headers):
    resp = client.get("/manufacturers?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)
    assert data["total"] >= 1
    assert len(data["items"]) > 0
    item = data["items"][0]
    assert "name" in item
    assert "country" in item


def test_list_manufacturers_paginated(client, auth_headers):
    resp = client.get("/manufacturers?page=1&size=20", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == data["size"]
    assert data["page"] == 1
    assert data["size"] == 20


def test_get_manufacturer(client, auth_headers):
    resp = client.get("/manufacturers?size=1", headers=auth_headers)
    first_id = resp.json()["items"][0]["id"]

    resp = client.get(f"/manufacturers/{first_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == first_id
    assert "name" in data


def test_get_manufacturer_404(client, auth_headers):
    resp = client.get("/manufacturers/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_filter_our_brands(client, auth_headers):
    resp = client.get("/manufacturers?is_our_brand=true&size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["is_our_brand"] is True


def test_filter_competitors(client, auth_headers):
    resp = client.get("/manufacturers?is_competitor=true&size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    for item in data["items"]:
        assert item["is_competitor"] is True
