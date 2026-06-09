"""Test fixtures: HTTP client against running Docker backend."""
from __future__ import annotations

import httpx
import pytest

API_BASE = "http://localhost:8000/api/v1"


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=10)


@pytest.fixture
def auth_headers(client: httpx.Client) -> dict[str, str]:
    """Get auth token by logging in as admin."""
    resp = client.post(
        "/auth/login/json",
        json={"username": "admin", "password": "admin"},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token(auth_headers: dict[str, str]) -> str:
    return auth_headers["Authorization"].split(" ", 1)[1]
