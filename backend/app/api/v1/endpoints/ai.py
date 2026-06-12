"""Эндпоинты AI: вопрос, анализ, настройки, тест."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_, select, text

from app.core.deps import CurrentAdmin, CurrentUser, DBSession
from app.models.ai_settings import AISettings
from app.models.knowledge import ArticleTopic, KnowledgeArticle, KnowledgeTopic
from app.schemas.knowledge import KnowledgeArticleSummary
from app.schemas.ai import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AIAskRequest,
    AIAskResponse,
    AICollectProgress,
    AICollectRequest,
    AICollectResponse,
    AISettingsRead,
    AISettingsUpdate,
    AITestResult,
)
from app.services.ai_service import AIService
from app.services.knowledge_collector import CollectionStatus, get_collector
from app.services.knowledge_pipeline import SourceType

logger = logging.getLogger("ai_router")
router = APIRouter()


def _excerpt(text: str, query: str, window: int = 300) -> str:
    if not text:
        return ""
    lower = text.lower()
    pos = lower.find(query.lower())
    if pos < 0:
        return text[:window] + ("..." if len(text) > window else "")
    start = max(0, pos - window // 2)
    end = min(len(text), pos + window // 2)
    return ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")


async def _find_relevant_topic_ids(db_session, words: list[str]) -> set[int]:
    """Найти ID узлов дерева, чьи label/description совпадают со словами вопроса."""
    if not words:
        return set()
    topic_ids: set[int] = set()
    for w in words:
        topics = (
            await db_session.scalars(
                select(KnowledgeTopic).where(
                    or_(
                        KnowledgeTopic.label.ilike(f"%{w}%"),
                        KnowledgeTopic.description.ilike(f"%{w}%"),
                    )
                )
            )
        ).all()
        topic_ids.update(t.id for t in topics)

    if not topic_ids:
        return set()

    # собираем всех потомков найденных узлов
    all_topics = (
        (await db_session.scalars(select(KnowledgeTopic))).all()
    )
    child_map: dict[int, list[int]] = {}
    for t in all_topics:
        if t.parent_id:
            child_map.setdefault(t.parent_id, []).append(t.id)

    def collect_descendants(tid: int) -> set[int]:
        result = {tid}
        for child_id in child_map.get(tid, []):
            result.update(collect_descendants(child_id))
        return result

    all_ids: set[int] = set()
    for tid in topic_ids:
        all_ids.update(collect_descendants(tid))
    return all_ids


async def _search_context(db_session, question: str, top_k: int = 5) -> str:
    """Найти релевантные статьи через дерево тем + FTS."""
    import re
    words = [w for w in re.split(r"[\s,.;:!?()\[\]{}\"']+", question.lower()) if len(w) >= 3][:10]

    # 1. Сначала пытаемся найти статьи через семантическое дерево
    topic_ids = await _find_relevant_topic_ids(db_session, words)
    if topic_ids:
        # ищем статьи, привязанные к этим темам или их потомкам
        article_ids_q = (
            select(ArticleTopic.article_id)
            .where(ArticleTopic.topic_id.in_(topic_ids))
            .limit(top_k * 3)
        )
        article_ids = (await db_session.scalars(article_ids_q)).all()
        if article_ids:
            stmt = (
                select(KnowledgeArticle)
                .where(KnowledgeArticle.id.in_(article_ids))
                .limit(top_k)
            )
            rows = (await db_session.scalars(stmt)).all()
            if rows:
                parts = []
                for a in rows:
                    snippet = _excerpt(a.body_md or "", question, window=500)
                    parts.append(f"## {a.title}\n{snippet[:2000]}")
                return "\n\n".join(parts)

    # 2. Fallback: FTS
    try:
        fts = text(
            "to_tsvector('russian', body_md || ' ' || title) @@ plainto_tsquery('russian', :q)"
        )
        stmt = (
            select(KnowledgeArticle)
            .where(fts)
            .order_by(
                text(
                    "ts_rank(to_tsvector('russian', body_md || ' ' || title), "
                    "plainto_tsquery('russian', :q)) DESC"
                )
            )
            .limit(top_k)
        )
        rows = (await db_session.execute(stmt, {"q": question})).scalars().all()
    except Exception:
        like = f"%{question}%"
        stmt = (
            select(KnowledgeArticle)
            .where(
                or_(
                    KnowledgeArticle.title.ilike(like),
                    KnowledgeArticle.body_md.ilike(like),
                )
            )
            .limit(top_k)
        )
        rows = (await db_session.scalars(stmt)).all()

    if not rows:
        stmt = select(KnowledgeArticle).order_by(KnowledgeArticle.updated_at.desc()).limit(3)
        rows = (await db_session.scalars(stmt)).all()

    parts = []
    for a in rows:
        snippet = _excerpt(a.body_md or "", question, window=500)
        parts.append(f"## {a.title}\n{snippet[:2000]}")
    return "\n\n".join(parts)


@router.post(
    "/ask",
    response_model=AIAskResponse,
    summary="Задать вопрос AI с контекстом из базы знаний",
)
async def ai_ask(
    payload: AIAskRequest,
    db: DBSession,
    _user: CurrentUser,
) -> AIAskResponse:
    settings = await AIService.get_settings(db)
    if not settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI не настроен. Укажите провайдера и API-ключ в настройках.",
        )

    service = AIService(settings)

    # Ищем контекст
    context = await _search_context(db, payload.question, payload.top_k)

    # Спрашиваем AI
    try:
        answer = await service.ask(payload.question, context=context)
    except Exception as e:
        logger.exception("AI ask error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка AI: {e}",
        )

    # Собираем источники
    sources = []
    if context:
        try:
            fts = text(
                "to_tsvector('russian', body_md || ' ' || title) @@ plainto_tsquery('russian', :q)"
            )
            stmt = (
                select(KnowledgeArticle)
                .where(fts)
                .limit(payload.top_k)
            )
            rows = (await db.execute(stmt, {"q": payload.question})).scalars().all()
            for a in rows:
                sources.append(
                    KnowledgeArticleSummary.model_validate(a)
                )
        except Exception:
            pass

    return AIAskResponse(
        answer=answer,
        sources=sources,
        query=payload.question,
        model=settings.model_name,
    )


@router.post(
    "/ask/stream",
    summary="Задать вопрос AI с потоковым ответом (SSE)",
)
async def ai_ask_stream(
    payload: AIAskRequest,
    db: DBSession,
    _user: CurrentUser,
) -> StreamingResponse:
    settings = await AIService.get_settings(db)
    if not settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI не настроен.",
        )

    service = AIService(settings)
    context = await _search_context(db, payload.question, payload.top_k)

    # Собираем источники для первого события
    source_articles = []
    if context:
        try:
            fts = text(
                "to_tsvector('russian', body_md || ' ' || title) @@ plainto_tsquery('russian', :q)"
            )
            stmt = select(KnowledgeArticle).where(fts).limit(payload.top_k)
            rows = (await db.execute(stmt, {"q": payload.question})).scalars().all()
            source_articles = [{"id": a.id, "title": a.title, "slug": a.slug} for a in rows]
        except Exception:
            pass

    async def event_stream():
        yield "data: " + json.dumps({"type": "sources", "count": len(source_articles), "articles": source_articles}) + "\n\n"
        try:
            async for token in service.ask_stream(payload.question, context=context):
                yield "data: " + json.dumps({"type": "token", "content": token}) + "\n\n"
            yield "data: " + json.dumps({"type": "done", "model": settings.model_name}) + "\n\n"
        except Exception as e:
            logger.exception("AI stream error")
            yield "data: " + json.dumps({"type": "error", "message": str(e)}) + "\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post(
    "/analyze",
    response_model=AIAnalyzeResponse,
    summary="Проанализировать текст через AI",
)
async def ai_analyze(
    payload: AIAnalyzeRequest,
    db: DBSession,
    _user: CurrentUser,
) -> AIAnalyzeResponse:
    settings = await AIService.get_settings(db)
    if not settings.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI не настроен.",
        )

    service = AIService(settings)
    try:
        result = await service.analyze(payload.text)
    except Exception as e:
        logger.exception("AI analyze error")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Ошибка AI: {e}",
        )

    return AIAnalyzeResponse(
        result=result,
        model=settings.model_name,
    )


@router.get(
    "/settings",
    response_model=AISettingsRead,
    summary="Получить настройки AI",
)
async def get_ai_settings(
    db: DBSession,
    _user: CurrentUser,
) -> AISettingsRead:
    settings = await AIService.get_settings(db)
    return AISettingsRead.model_validate(settings)


@router.put(
    "/settings",
    response_model=AISettingsRead,
    summary="Обновить настройки AI",
)
async def update_ai_settings(
    payload: AISettingsUpdate,
    db: DBSession,
    admin: CurrentAdmin,
) -> AISettingsRead:
    settings = await AIService.get_settings(db)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(settings, k, v)
    await db.flush()
    await db.commit()
    await db.refresh(settings)
    logger.info("AI settings updated by admin %s", admin.id)
    return AISettingsRead.model_validate(settings)


@router.post(
    "/test",
    response_model=AITestResult,
    summary="Проверить подключение к AI",
)
async def test_ai(
    db: DBSession,
    _user: CurrentUser,
) -> AITestResult:
    settings = await AIService.get_settings(db)
    service = AIService(settings)
    result = await service.test()
    return AITestResult(**result)


@router.post(
    "/collect",
    response_model=AICollectResponse,
    summary="Запустить сбор знаний по запросу",
)
async def ai_collect(
    payload: AICollectRequest,
    _user: CurrentUser,
) -> AICollectResponse:
    source_types = None
    if payload.source_types:
        source_types = [SourceType(st) for st in payload.source_types if st in {"web", "youtube", "telegram"}]

    collector = get_collector()
    job = await collector.collect(
        query=payload.query,
        source_types=source_types,
        topic_ids=payload.topic_ids,
        max_results=payload.max_results,
    )
    return AICollectResponse(job_id=job.id, status=job.status.value)


@router.get(
    "/collect/{job_id}",
    response_model=AICollectProgress,
    summary="Статус задачи сбора знаний",
)
async def ai_collect_status(
    job_id: str,
    _user: CurrentUser,
) -> AICollectProgress:
    collector = get_collector()
    job = collector.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return AICollectProgress(
        job_id=job.id,
        status=job.status.value,
        total=job.total,
        processed=job.processed,
        skipped=job.skipped,
        created=job.created,
        errors=job.errors,
    )


@router.get(
    "/collect/{job_id}/progress",
    summary="SSE-прогресс сбора знаний",
)
async def ai_collect_progress(
    job_id: str,
    request: Request,
    _user: CurrentUser,
) -> StreamingResponse:
    collector = get_collector()
    job = collector.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")

    async def event_stream():
        last_processed = -1
        while True:
            if await request.is_disconnected():
                break
            current = collector.get_job(job_id)
            if current is None:
                yield "data: " + json.dumps({"type": "error", "message": "Job lost"}) + "\n\n"
                break

            if current.processed != last_processed or current.status in (CollectionStatus.COMPLETED, CollectionStatus.FAILED):
                last_processed = current.processed
                yield "data: " + json.dumps({
                    "type": "progress",
                    "status": current.status.value,
                    "total": current.total,
                    "processed": current.processed,
                    "skipped": current.skipped,
                    "created": current.created,
                    "errors": current.errors,
                }) + "\n\n"

            if current.status in (CollectionStatus.COMPLETED, CollectionStatus.FAILED):
                yield "data: " + json.dumps({"type": "done", "status": current.status.value}) + "\n\n"
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
