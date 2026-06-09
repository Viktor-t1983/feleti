"""Health endpoint tests."""
from __future__ import annotations


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


def test_health_db(client):
    resp = client.get("/health/db")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
