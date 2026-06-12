"""Knowledge base CRUD + search endpoint tests."""
from __future__ import annotations

from uuid import uuid4


def _unique_slug(base: str) -> str:
    return f"{base}-{uuid4().hex[:8]}"


def _create_article(client, auth_headers) -> dict:
    slug = _unique_slug("test-article")
    resp = client.post(
        "/knowledge",
        headers=auth_headers,
        json={
            "title": "Тестовая статья",
            "slug": slug,
            "body_md": "# Тест\n\nЭто тестовая статья.",
            "category": "theory",
            "tags": ["тест"],
        },
    )
    assert resp.status_code == 201
    return resp.json()


def test_list_knowledge(client, auth_headers):
    resp = client.get("/knowledge?size=200", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("items"), list)


def test_create_article(client, auth_headers):
    article = _create_article(client, auth_headers)
    assert article["title"] == "Тестовая статья"
    assert article["category"] == "theory"


def test_get_article(client, auth_headers):
    created = _create_article(client, auth_headers)
    resp = client.get(f"/knowledge/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == created["id"]
    assert "body_md" in data


def test_update_article(client, auth_headers):
    created = _create_article(client, auth_headers)
    resp = client.patch(
        f"/knowledge/{created['id']}",
        headers=auth_headers,
        json={"title": "Обновлённая статья"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Обновлённая статья"


def test_delete_article(client, auth_headers):
    created = _create_article(client, auth_headers)
    resp = client.delete(f"/knowledge/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/knowledge/{created['id']}", headers=auth_headers)
    assert resp.status_code == 404


def test_search_knowledge(client, auth_headers):
    slug = _unique_slug("searchable-article")
    client.post(
        "/knowledge",
        headers=auth_headers,
        json={
            "title": "UniqueSearchTermArticle",
            "slug": slug,
            "body_md": "This article contains a unique search term for testing.",
            "category": "theory",
        },
    )
    resp = client.get("/knowledge/search?q=UniqueSearchTerm", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_knowledge_tree(client, auth_headers):
    resp = client.get("/knowledge/tree", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_get_article_404(client, auth_headers):
    resp = client.get("/knowledge/999999", headers=auth_headers)
    assert resp.status_code == 404


def test_create_article_no_auth(client):
    resp = client.post(
        "/knowledge",
        json={"title": "x", "slug": "x", "body_md": "x", "category": "theory"},
    )
    assert resp.status_code == 401
