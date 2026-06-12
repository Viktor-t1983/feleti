"""CRUD базы знаний + полнотекстовый поиск + RAG.

Search: PostgreSQL FTS (tsvector) с fallback на ILIKE.
RAG: вопрос → поиск релевантных статей → синтезированный ответ.
"""

from __future__ import annotations

import logging
import re
from typing import Annotated

from enum import Enum

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.entity_link import EntityLink
from app.models.knowledge import (
    ArticleAnalysis,
    ArticleCategory,
    ArticleTopic,
    AttachmentKind,
    KnowledgeArticle,
    KnowledgeAttachment,
    KnowledgeTopic,
)
from app.schemas.common import Page, PageParams
from app.schemas.knowledge import (
    ArticleCategoryEnum,
    KnowledgeArticleCreate,
    KnowledgeArticleRead,
    KnowledgeArticleSummary,
    KnowledgeArticleUpdate,
    KnowledgeSearchResult,
    RAGAnswer,
    RAGQuery,
    ArticleAnalysisRead,
    ArticleAnalysisTriggerResponse,
    ArticleAnalysisBatchResponse,
    TopicCreate,
    TopicRead,
    TopicTreeNode,
    TopicUpdate,
)
from app.services import audit
from app.services.article_analyzer import ArticleAnalyzer


class SortField(str, Enum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    TITLE = "title"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

router = APIRouter()
logger = logging.getLogger(__name__)


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
    params: Annotated[PageParams, Depends()],
    category: Annotated[ArticleCategoryEnum | None, Query()] = None,
    tag: Annotated[str | None, Query()] = None,
    manufacturer_id: Annotated[int | None, Query()] = None,
    competitor_id: Annotated[int | None, Query()] = None,
    is_published: Annotated[bool | None, Query()] = None,
    topic_path: Annotated[str | None, Query()] = None,
    topic_id: Annotated[int | None, Query()] = None,
    sort_by: Annotated[SortField, Query()] = SortField.UPDATED_AT,
    sort_order: Annotated[SortOrder, Query()] = SortOrder.DESC,
) -> Page[KnowledgeArticleSummary]:
    stmt = select(KnowledgeArticle).options(selectinload(KnowledgeArticle.analysis))
    count_stmt = select(func.count()).select_from(KnowledgeArticle)
    if category is not None:
        stmt = stmt.where(KnowledgeArticle.category == category)
        count_stmt = count_stmt.where(KnowledgeArticle.category == category)
    if tag is not None:
        stmt = stmt.where(KnowledgeArticle.tags.contains([tag]))
        count_stmt = count_stmt.where(KnowledgeArticle.tags.contains([tag]))
    if manufacturer_id is not None:
        stmt = stmt.where(KnowledgeArticle.manufacturer_id == manufacturer_id)
        count_stmt = count_stmt.where(KnowledgeArticle.manufacturer_id == manufacturer_id)
    if competitor_id is not None:
        stmt = stmt.where(KnowledgeArticle.competitor_id == competitor_id)
        count_stmt = count_stmt.where(KnowledgeArticle.competitor_id == competitor_id)
    if is_published is not None:
        stmt = stmt.where(KnowledgeArticle.is_published == is_published)
        count_stmt = count_stmt.where(KnowledgeArticle.is_published == is_published)
    if topic_path is not None:
        stmt = stmt.join(ArticleAnalysis, ArticleAnalysis.article_id == KnowledgeArticle.id)
        if topic_path.endswith("/%"):
            stmt = stmt.where(ArticleAnalysis.topic_path.like(topic_path))
            count_stmt = count_stmt.join(ArticleAnalysis, ArticleAnalysis.article_id == KnowledgeArticle.id).where(ArticleAnalysis.topic_path.like(topic_path))
        else:
            stmt = stmt.where(ArticleAnalysis.topic_path == topic_path)
            count_stmt = count_stmt.join(ArticleAnalysis, ArticleAnalysis.article_id == KnowledgeArticle.id).where(ArticleAnalysis.topic_path == topic_path)
    if topic_id is not None:
        stmt = stmt.join(ArticleTopic, ArticleTopic.article_id == KnowledgeArticle.id).where(ArticleTopic.topic_id == topic_id)
        count_stmt = count_stmt.join(ArticleTopic, ArticleTopic.article_id == KnowledgeArticle.id).where(ArticleTopic.topic_id == topic_id)

    total = await db.scalar(count_stmt) or 0
    sort_column = getattr(KnowledgeArticle, sort_by.value)
    order = sort_column.asc() if sort_order == SortOrder.ASC else sort_column.desc()
    stmt = (
        stmt.order_by(order)
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0

    # enrich with topic_path from analysis
    items = []
    for r in rows:
        d = KnowledgeArticleSummary.model_validate(r)
        if r.analysis:
            d.topic_path = r.analysis.topic_path
            d.ai_category = r.analysis.ai_category
        items.append(d)

    return Page[KnowledgeArticleSummary](
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get(
    "/search",
    response_model=list[KnowledgeSearchResult],
    summary="Полнотекстовый поиск (FTS) по базе знаний",
)
async def search_articles(
    db: DBSession,
    _user: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    category: Annotated[ArticleCategoryEnum | None, Query()] = None,
) -> list[KnowledgeSearchResult]:
    """Поиск через PostgreSQL FTS (tsvector) по body_md + title.

    Возвращает статьи + подсвеченные фрагменты (snippet).
    """
    pattern = re.compile(r"[\s,.;:!?()\[\]{}\"']+")
    words = [w for w in pattern.split(q) if len(w) >= 2][:10]
    if not words:
        return []

    # Пробуем FTS
    try:
        ts_query = " & ".join(words)
        fts_condition = text(
            "to_tsvector('russian', body_md || ' ' || title) @@ plainto_tsquery('russian', :q)"
        )
        headline = text(
            "ts_headline('russian', body_md, plainto_tsquery('russian', :q), "
            "'MaxWords=50, MinWords=20, StartSel=<mark>, StopSel=</mark>')"
        )

        stmt = select(KnowledgeArticle, headline.label("_snippet")).where(
            fts_condition
        )
        if category is not None:
            stmt = stmt.where(KnowledgeArticle.category == category)

        # ranking
        stmt = stmt.order_by(
            text("ts_rank(to_tsvector('russian', body_md || ' ' || title), plainto_tsquery('russian', :q)) DESC")
        ).limit(limit)

        rows = (await db.execute(stmt, {"q": q})).all()
        results = []
        for article, snippet in rows:
            snippet_str = (snippet or "") if snippet else _excerpt(article.body_md or "", q)
            snippet_clean = re.sub(r"<[^>]+>", "", snippet_str)[:300]
            results.append(
                KnowledgeSearchResult(
                    article=KnowledgeArticleSummary.model_validate(article),
                    score=1.0,
                    snippet=snippet_clean,
                )
            )
        return results
    except Exception:
        # FTS недоступен — fallback на ILIKE
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
        stmt = stmt.limit(limit * 2)

        rows = (await db.scalars(stmt)).all()
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
        results.sort(key=lambda r: (-r.score, -r.article.updated_at.timestamp()))
        return results[:limit]


@router.get(
    "/tree",
    response_model=list[TopicTreeNode],
    summary="Дерево папок (topic_path) с количеством статей",
)
async def get_topic_tree(
    db: DBSession,
    _user: CurrentUser,
) -> list[TopicTreeNode]:
    """Возвращает иерархическое дерево тем на основе topic_path из AI-анализа."""
    from sqlalchemy import func as sa_func

    rows = (await db.execute(
        select(ArticleAnalysis.topic_path, sa_func.count().label("cnt"))
        .where(ArticleAnalysis.status == "DONE", ArticleAnalysis.topic_path.isnot(None))
        .group_by(ArticleAnalysis.topic_path)
        .order_by(ArticleAnalysis.topic_path)
    )).all()

    # Build tree from flat paths
    root: dict[str, TopicTreeNode] = {}
    for path, cnt in rows:
        parts = path.strip("/").split("/")
        full = ""
        for i, part in enumerate(parts):
            full = f"{full}/{part}" if full else f"/{part}"
            if full not in root:
                root[full] = TopicTreeNode(path=full, label=part, article_count=0)
            root[full].article_count += cnt

    # Nest children
    tree: list[TopicTreeNode] = []
    node_map: dict[str, TopicTreeNode] = {}
    for full, node in sorted(root.items(), key=lambda x: (x[0].count("/"), x[0])):
        node_map[full] = node
        if "/" in full.lstrip("/"):
            parent = full.rsplit("/", 1)[0]
            if parent in node_map:
                node_map[parent].children.append(node)
        else:
            tree.append(node)

    return tree


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
    response_model=None,
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


@router.get(
    "/{article_id}/analysis",
    response_model=ArticleAnalysisRead | None,
    summary="Результат AI-анализа статьи",
)
async def get_article_analysis(
    article_id: int, db: DBSession, _user: CurrentUser
) -> ArticleAnalysisRead | None:
    obj = await ArticleAnalyzer(db).get_analysis(article_id)
    if obj is None:
        return None
    return ArticleAnalysisRead.model_validate(obj)


@router.post(
    "/{article_id}/analyze",
    response_model=ArticleAnalysisTriggerResponse,
    summary="Запустить AI-анализ статьи",
)
async def analyze_article(
    article_id: int,
    db: DBSession,
    _user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> ArticleAnalysisTriggerResponse:
    article = await db.scalar(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )

    analyzer = ArticleAnalyzer(db)
    result = await analyzer.analyze(article_id)
    await db.commit()
    return ArticleAnalysisTriggerResponse(
        message="Анализ завершён",
        article_id=article_id,
    )


@router.post(
    "/analyze/batch",
    response_model=ArticleAnalysisBatchResponse,
    summary="Запустить AI-анализ всех необработанных статей",
)
async def analyze_all_articles(
    db: DBSession,
    _user: CurrentUser,
    background_tasks: BackgroundTasks,
) -> ArticleAnalysisBatchResponse:
    analyzer = ArticleAnalyzer(db)
    unanalyzed = await analyzer.get_unanalyzed_ids(limit=50)
    queued = 0
    for aid in unanalyzed:
        try:
            await analyzer.analyze(aid)
            queued += 1
        except Exception:
            logger.exception("Batch-анализ статьи %d провалился", aid)
    await db.commit()
    return ArticleAnalysisBatchResponse(
        message="Пакетный анализ запущен",
        queued=queued,
        skipped=len(unanalyzed) - queued,
    )


@router.post(
    "/ask",
    response_model=RAGAnswer,
    summary="RAG: задать вопрос по базе знаний",
)
async def ask_question(
    payload: RAGQuery,
    db: DBSession,
    _user: CurrentUser,
) -> RAGAnswer:
    """Поиск релевантных статей по вопросу + синтез ответа.

    Поиск — через FTS. Синтез — через выделение ключевых фрагментов.
    При наличии Ollama/OpenAI будет использована LLM.
    """
    q = payload.question

    # 1. Ищем релевантные статьи через FTS
    try:
        fts_condition = text(
            "to_tsvector('russian', body_md || ' ' || title) @@ plainto_tsquery('russian', :q)"
        )
        stmt = (
            select(KnowledgeArticle)
            .where(fts_condition)
            .order_by(
                text(
                    "ts_rank(to_tsvector('russian', body_md || ' ' || title), "
                    "plainto_tsquery('russian', :q)) DESC"
                )
            )
            .limit(payload.top_k)
        )
        rows = (await db.execute(stmt, {"q": q})).scalars().all()
    except Exception:
        # Fallback: ILIKE
        like = f"%{q}%"
        stmt = (
            select(KnowledgeArticle)
            .where(
                or_(
                    KnowledgeArticle.title.ilike(like),
                    KnowledgeArticle.body_md.ilike(like),
                )
            )
            .limit(payload.top_k)
        )
        rows = (await db.scalars(stmt)).all()

    if not rows:
        return RAGAnswer(
            answer="По вашему вопросу ничего не найдено в базе знаний.",
            sources=[],
            query=q,
        )

    # 2. Собираем источники со сниппетами
    sources = []
    context_parts = []
    for article in rows:
        snippet = _excerpt(article.body_md or "", q, window=300)
        sources.append(
            KnowledgeSearchResult(
                article=KnowledgeArticleSummary.model_validate(article),
                score=1.0,
                snippet=snippet,
            )
        )
        context_parts.append(
            f"## {article.title}\n{snippet}"
        )

    # 3. Синтезируем ответ (rule-based, пока нет LLM)
    context = "\n\n".join(context_parts)

    # Группируем источники по категориям для ответа
    recipes = [a for a in rows if a.category.value == "recipe"]
    guides = [a for a in rows if a.category.value == "guide"]
    troubleshooting = [a for a in rows if a.category.value == "troubleshooting"]

    answer_parts = [f"По запросу «{q}» найдено {len(rows)} релевантных статей."]

    if recipes:
        answer_parts.append(
            f"\nРецепты: {', '.join(r.title for r in recipes[:3])}."
        )
    if guides:
        answer_parts.append(
            f"\nРуководства: {', '.join(g.title for g in guides[:3])}."
        )
    if troubleshooting:
        answer_parts.append(
            f"\nРешение проблем: {', '.join(t.title for t in troubleshooting[:3])}."
        )

    # Добавляем фрагменты из топ-2 статей
    for article in rows[:2]:
        snippet = _excerpt(article.body_md or "", q, window=400)
        if snippet:
            answer_parts.append(f"\n\nИз статьи «{article.title}»:\n{snippet[:500]}")

    answer_parts.append(
        "\n\nДля более точного ответа настройте Ollama или OpenAI в переменных окружения."
    )

    return RAGAnswer(
        answer="".join(answer_parts),
        sources=sources,
        query=q,
    )


# ─── Knowledge Topic (семантическое дерево) ──────────────────────────────────


@router.get(
    "/topics/tree",
    response_model=list[TopicTreeNode],
    summary="Дерево тем (семантическая таксономия)",
)
async def get_topic_tree(
    db: DBSession,
    _user: CurrentUser,
) -> list[TopicTreeNode]:
    """Возвращает иерархическое дерево тем KnowledgeTopic."""
    all_topics = (
        (await db.scalars(
            select(KnowledgeTopic).order_by(KnowledgeTopic.level, KnowledgeTopic.sort_order)
        ))
        .all()
    )

    # считаем статьи в каждом узле
    topic_counts: dict[int, int] = {}
    if all_topics:
        rows = (
            await db.execute(
                select(
                    ArticleTopic.topic_id,
                    func.count().label("cnt"),
                ).group_by(ArticleTopic.topic_id)
            )
        ).all()
        for topic_id, cnt in rows:
            topic_counts[topic_id] = cnt

    # мапим id → node
    node_map: dict[int, TopicTreeNode] = {}
    for t in all_topics:
        node_map[t.id] = TopicTreeNode(
            id=t.id,
            slug=t.slug,
            label=t.label,
            description=t.description,
            path=t.path,
            level=t.level,
            sort_order=t.sort_order,
            icon=t.icon,
            article_count=topic_counts.get(t.id, 0),
            children=[],
        )

    # строим дерево
    tree: list[TopicTreeNode] = []
    for t in all_topics:
        node = node_map[t.id]
        if t.parent_id and t.parent_id in node_map:
            node_map[t.parent_id].children.append(node)
        else:
            tree.append(node)

    return tree


@router.get(
    "/topics",
    response_model=list[TopicRead],
    summary="Все темы (плоский список)",
)
async def list_topics(
    db: DBSession,
    _user: CurrentUser,
    parent_id: Annotated[int | None, Query()] = None,
) -> list[TopicRead]:
    stmt = select(KnowledgeTopic).order_by(KnowledgeTopic.level, KnowledgeTopic.sort_order)
    if parent_id is not None:
        stmt = stmt.where(KnowledgeTopic.parent_id == parent_id)
    rows = (await db.scalars(stmt)).all()

    # считаем статьи
    topic_counts: dict[int, int] = {}
    if rows:
        counts = (
            await db.execute(
                select(
                    ArticleTopic.topic_id,
                    func.count().label("cnt"),
                ).group_by(ArticleTopic.topic_id)
            )
        ).all()
        for tid, cnt in counts:
            topic_counts[tid] = cnt

    return [
        TopicRead(
            id=t.id,
            slug=t.slug,
            label=t.label,
            description=t.description,
            path=t.path,
            parent_id=t.parent_id,
            level=t.level,
            sort_order=t.sort_order,
            icon=t.icon,
            article_count=topic_counts.get(t.id, 0),
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in rows
    ]


@router.get(
    "/topics/{topic_id}",
    response_model=TopicRead,
    summary="Тема по ID",
)
async def get_topic(topic_id: int, db: DBSession, _user: CurrentUser) -> TopicRead:
    t = await db.scalar(select(KnowledgeTopic).where(KnowledgeTopic.id == topic_id))
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")

    # считаем статьи
    cnt = await db.scalar(
        select(func.count()).where(ArticleTopic.topic_id == topic_id)
    ) or 0

    return TopicRead(
        id=t.id,
        slug=t.slug,
        label=t.label,
        description=t.description,
        path=t.path,
        parent_id=t.parent_id,
        level=t.level,
        sort_order=t.sort_order,
        icon=t.icon,
        article_count=cnt,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.post(
    "/topics",
    response_model=TopicRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать тему",
)
async def create_topic(
    payload: TopicCreate,
    db: DBSession,
    user: CurrentUser,
) -> TopicRead:
    parent_path = ""
    parent_level = -1
    if payload.parent_id:
        parent = await db.scalar(
            select(KnowledgeTopic).where(KnowledgeTopic.id == payload.parent_id)
        )
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Родительская тема не найдена",
            )
        parent_path = parent.path
        parent_level = parent.level

    new_path = f"{parent_path}/{payload.slug}" if parent_path else f"/{payload.slug}"

    # проверяем уникальность slug
    existing = await db.scalar(
        select(KnowledgeTopic).where(KnowledgeTopic.slug == payload.slug)
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Тема со slug '{payload.slug}' уже существует",
        )

    t = KnowledgeTopic(
        slug=payload.slug,
        label=payload.label,
        description=payload.description,
        path=new_path,
        parent_id=payload.parent_id,
        level=parent_level + 1,
        sort_order=payload.sort_order,
        icon=payload.icon,
    )
    db.add(t)
    await db.flush()
    await db.commit()
    await db.refresh(t)

    return TopicRead(
        id=t.id,
        slug=t.slug,
        label=t.label,
        description=t.description,
        path=t.path,
        parent_id=t.parent_id,
        level=t.level,
        sort_order=t.sort_order,
        icon=t.icon,
        article_count=0,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.patch(
    "/topics/{topic_id}",
    response_model=TopicRead,
    summary="Обновить тему",
)
async def update_topic(
    topic_id: int,
    payload: TopicUpdate,
    db: DBSession,
    _user: CurrentUser,
) -> TopicRead:
    t = await db.scalar(select(KnowledgeTopic).where(KnowledgeTopic.id == topic_id))
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)

    await db.flush()
    await db.commit()
    await db.refresh(t)

    cnt = await db.scalar(
        select(func.count()).where(ArticleTopic.topic_id == topic_id)
    ) or 0

    return TopicRead(
        id=t.id,
        slug=t.slug,
        label=t.label,
        description=t.description,
        path=t.path,
        parent_id=t.parent_id,
        level=t.level,
        sort_order=t.sort_order,
        icon=t.icon,
        article_count=cnt,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.delete(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_topic(
    topic_id: int,
    db: DBSession,
    _user: CurrentUser,
) -> None:
    t = await db.scalar(select(KnowledgeTopic).where(KnowledgeTopic.id == topic_id))
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тема не найдена")

    await db.delete(t)
    await db.commit()


@router.get(
    "/{article_id}/topics",
    response_model=list[int],
    summary="ID тем, привязанных к статье",
)
async def get_article_topics(
    article_id: int,
    db: DBSession,
    _user: CurrentUser,
) -> list[int]:
    rows = (
        await db.execute(
            select(ArticleTopic.topic_id).where(ArticleTopic.article_id == article_id)
        )
    ).scalars().all()
    return list(rows)


@router.post(
    "/{article_id}/topics",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Привязать статью к темам",
)
async def set_article_topics(
    article_id: int,
    topic_ids: list[int],
    db: DBSession,
    _user: CurrentUser,
) -> None:
    article = await db.scalar(
        select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
    )
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Статья не найдена"
        )

    # удаляем старые связи
    await db.execute(
        ArticleTopic.__table__.delete().where(ArticleTopic.article_id == article_id)
    )

    # добавляем новые
    for tid in topic_ids:
        topic = await db.scalar(
            select(KnowledgeTopic).where(KnowledgeTopic.id == tid)
        )
        if topic is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Тема {tid} не найдена",
            )
        db.add(ArticleTopic(article_id=article_id, topic_id=tid))

    await db.commit()


@router.get(
    "/{article_id}/graph",
    response_model=list[dict],
    summary="Граф знаний статьи — связанные сущности",
)
async def get_article_graph(
    article_id: int,
    db: DBSession,
    _user: CurrentUser,
) -> list[dict]:
    """Вернуть все EntityLink для статьи + резолвить имена target-сущностей."""
    rows = (
        await db.execute(
            select(EntityLink).where(
                EntityLink.source_type == "article",
                EntityLink.source_id == article_id,
            )
        )
    ).scalars().all()

    result = []
    for link in rows:
        target_name = None
        if link.target_type == "product":
            from app.models.product import Product
            obj = await db.get(Product, link.target_id)
            target_name = obj.name if obj else None
        elif link.target_type == "competitor":
            from app.models.competitor import Competitor
            obj = await db.get(Competitor, link.target_id)
            target_name = obj.name if obj else None
        elif link.target_type == "manufacturer":
            from app.models.manufacturer import Manufacturer
            obj = await db.get(Manufacturer, link.target_id)
            target_name = obj.name if obj else None

        result.append({
            "id": link.id,
            "target_type": link.target_type,
            "target_id": link.target_id,
            "target_name": target_name,
            "relation": link.relation,
            "created_at": link.created_at.isoformat(),
        })

    return result
