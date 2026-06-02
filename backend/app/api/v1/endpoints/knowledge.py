"""CRUD базы знаний + полнотекстовый поиск.

Search стратегия (текущая):
  - ILIKE по title + body_md + excerpt + tags.
  - Скоринг: title=3, tags=2, body=1, excerpt=2.
  - Полнотекст на tsvector — план на следующую сессию (через Alembic-миграцию).
"""

from __future__ import annotations

import re
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.knowledge import (
    ArticleCategory,
    AttachmentKind,
    KnowledgeArticle,
    KnowledgeAttachment,
)
from app.schemas.common import Page, PageParams
from app.schemas.knowledge import (
    ArticleCategoryEnum,
    KnowledgeArticleCreate,
    KnowledgeArticleRead,
    KnowledgeArticleSummary,
    KnowledgeArticleUpdate,
    KnowledgeSearchResult,
)
from app.services import audit

router = APIRouter()


def _excerpt(text: str, query: str, window: int = 200) -> str:
    """Вырезать фрагмент текста вокруг первого вхождения query."""
    if not text:
        return ""
    lower = text.lower()
    pos = lower.find(query.lower())
    if pos < 0:
        return text[:window] + ("..." if len(text) > window else "")
    start = max(0, pos - window // 2)
    end = min(len(text), pos + window // 2)
    return ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")


@router.get(
    "",
    response_model=Page[KnowledgeArticleSummary],
    summary="Список статей (без body_md)",
)
async def list_articles(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()],
    category: Annotated[ArticleCategoryEnum | None, Query()] = None,
    tag: Annotated[str | None, Query()] = None,
    manufacturer_id: Annotated[int | None, Query()] = None,
    is_published: Annotated[bool | None, Query()] = None,
) -> Page[KnowledgeArticleSummary]:
    stmt = select(KnowledgeArticle)
    count_stmt = select(func.count()).select_from(KnowledgeArticle)
    if category is not None:
        stmt = stmt.where(KnowledgeArticle.category == category)
        count_stmt = count_stmt.where(KnowledgeArticle.category == category)
    if tag is not None:
        # JSON-массив: PostgreSQL оператор @> с jsonb
        stmt = stmt.where(KnowledgeArticle.tags.contains([tag]))
        count_stmt = count_stmt.where(KnowledgeArticle.tags.contains([tag]))
    if manufacturer_id is not None:
        stmt = stmt.where(KnowledgeArticle.manufacturer_id == manufacturer_id)
        count_stmt = count_stmt.where(KnowledgeArticle.manufacturer_id == manufacturer_id)
    if is_published is not None:
        stmt = stmt.where(KnowledgeArticle.is_published == is_published)
        count_stmt = count_stmt.where(KnowledgeArticle.is_published == is_published)

    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(KnowledgeArticle.updated_at.desc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[KnowledgeArticleSummary](
        items=[KnowledgeArticleSummary.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get(
    "/search",
    response_model=list[KnowledgeSearchResult],
    summary="Поиск по базе знаний (title/body/excerpt/tags)",
)
async def search_articles(
    db: DBSession,
    _user: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    category: Annotated[ArticleCategoryEnum | None, Query()] = None,
) -> list[KnowledgeSearchResult]:
    """Поиск по title, body_md, excerpt и tags с простым скорингом.

    Запрос разбивается на слова (>= 2 символов), каждое слово ищется независимо
    через ILIKE. Финальный score — сумма вкладов (title=3, tags=2, excerpt=2, body=1).
    """
    pattern = re.compile(r"[\s,.;:!?()\[\]{}\"']+")
    words = [w for w in pattern.split(q) if len(w) >= 2][:10]  # max 10 слов
    if not words:
        return []

    # Строим OR-выражение по всем словам
    word_filters = []
    for w in words:
        w_like = f"%{w}%"
        word_filters.append(
            or_(
                KnowledgeArticle.title.ilike(w_like),
                KnowledgeArticle.body_md.ilike(w_like),
                KnowledgeArticle.excerpt.ilike(w_like),
            )
        )
    where_clause = or_(*word_filters)

    stmt = select(KnowledgeArticle).where(where_clause)
    if category is not None:
        stmt = stmt.where(KnowledgeArticle.category == category)
    stmt = stmt.limit(limit * 2)  # берём с запасом, потом отсортируем

    rows = (await db.scalars(stmt)).all()

    # Считаем score для каждого результата
    results: list[KnowledgeSearchResult] = []
    for article in rows:
        score = 0
        title_lc = (article.title or "").lower()
        body_lc = (article.body_md or "").lower()
        excerpt_lc = (article.excerpt or "").lower()
        tags_lc = [t.lower() for t in (article.tags or [])]
        for w in words:
            wl = w.lower()
            if wl in title_lc:
                score += 3
            if any(wl == t or wl in t for t in tags_lc):
                score += 2
            if wl in excerpt_lc:
                score += 2
            if wl in body_lc:
                score += 1
        if score > 0:
            results.append(
                KnowledgeSearchResult(
                    article=KnowledgeArticleSummary.model_validate(article),
                    score=float(score),
                    snippet=_excerpt(article.body_md or "", w),
                )
            )
    # Сортируем по score desc, обрезаем до limit
    results.sort(key=lambda r: (-r.score, -r.article.updated_at.timestamp()))
    return results[:limit]


@router.get(
    "/{article_id}",
    response_model=KnowledgeArticleRead,
    summary="Статья по ID (с body_md и вложениями)",
)
async def get_article(
    article_id: int, db: DBSession, _user: CurrentUser
) -> KnowledgeArticleRead:
    obj = await db.scalar(
        select(KnowledgeArticle)
        .options(selectinload(KnowledgeArticle.attachments))
        .where(KnowledgeArticle.id == article_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )
    return KnowledgeArticleRead.model_validate(obj)


@router.get(
    "/by-slug/{slug}",
    response_model=KnowledgeArticleRead,
    summary="Статья по slug (для SEO/публичных ссылок)",
)
async def get_article_by_slug(
    slug: str, db: DBSession, _user: CurrentUser
) -> KnowledgeArticleRead:
    obj = await db.scalar(
        select(KnowledgeArticle)
        .options(selectinload(KnowledgeArticle.attachments))
        .where(KnowledgeArticle.slug == slug)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )
    return KnowledgeArticleRead.model_validate(obj)


@router.post(
    "",
    response_model=KnowledgeArticleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать статью (с вложениями)",
)
async def create_article(
    payload: KnowledgeArticleCreate, db: DBSession, user: CurrentUser
) -> KnowledgeArticleRead:
    obj = KnowledgeArticle(
        title=payload.title,
        slug=payload.slug,
        body_md=payload.body_md,
        body_html=payload.body_html,
        excerpt=payload.excerpt,
        category=ArticleCategory(payload.category),
        tags=payload.tags,
        manufacturer_id=payload.manufacturer_id,
        chamber_model=payload.chamber_model,
        source_url=str(payload.source_url) if payload.source_url else None,
        is_published=payload.is_published,
        version=1,
        author_id=user.id,
    )
    for att in payload.attachments:
        obj.attachments.append(
            KnowledgeAttachment(
                file_id=att.file_id,
                kind=AttachmentKind(att.kind),
                filename=att.filename,
                size_bytes=att.size_bytes,
                mime_type=att.mime_type,
                url=att.url,
            )
        )
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Статья с slug {payload.slug} уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="knowledge_article",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return KnowledgeArticleRead.model_validate(obj)


@router.patch(
    "/{article_id}",
    response_model=KnowledgeArticleRead,
    summary="Обновить статью (с авто-инкрементом version)",
)
async def update_article(
    article_id: int,
    payload: KnowledgeArticleUpdate,
    db: DBSession,
    user: CurrentUser,
) -> KnowledgeArticleRead:
    obj = await db.scalar(
        select(KnowledgeArticle)
        .options(selectinload(KnowledgeArticle.attachments))
        .where(KnowledgeArticle.id == article_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )
    data = payload.model_dump(exclude_unset=True)
    before = {c.name: getattr(obj, c.name) for c in KnowledgeArticle.__table__.columns}
    for k, v in data.items():
        if k == "category" and v is not None:
            setattr(obj, k, ArticleCategory(v))
        else:
            setattr(obj, k, v)
    obj.version = obj.version + 1
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="knowledge_article",
        entity_id=obj.id,
        before=before,
        after={**before, **data, "version": obj.version},
    )
    await db.commit()
    await db.refresh(obj)
    return KnowledgeArticleRead.model_validate(obj)


@router.delete(
    "/{article_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить статью",
)
async def delete_article(
    article_id: int, db: DBSession, user: CurrentUser
) -> None:
    obj = await db.scalar(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )
    before = {"id": obj.id, "title": obj.title, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="knowledge_article",
        entity_id=article_id,
        before=before,
    )
    await db.commit()
