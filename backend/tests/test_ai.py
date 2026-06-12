"""AI settings endpoint tests."""
from __future__ import annotations


def test_get_ai_settings(client, auth_headers):
    resp = client.get("/ai/settings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)


def test_get_ai_settings_no_auth(client):
    resp = client.get("/ai/settings")
    assert resp.status_code == 401
