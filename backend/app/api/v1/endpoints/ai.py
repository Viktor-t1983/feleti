"""Эндпоинты AI: вопрос, анализ, настройки, тест."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import or_, select, text

from app.core.deps import CurrentUser, DBSession
from app.models.ai_settings import AISettings
from app.models.knowledge import KnowledgeArticle
from app.schemas.knowledge import KnowledgeArticleSummary
from app.schemas.ai import (
    AIAnalyzeRequest,
    AIAnalyzeResponse,
    AIAskRequest,
    AIAskResponse,
    AISettingsRead,
    AISettingsUpdate,
    AITestResult,
)

from app.services.ai_service import AIService

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


async def _search_context(db_session, question: str, top_k: int = 5) -> str:
    """Найти релевантные статьи и вернуть контекст."""
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
        # Если ничего не нашли — возвращаем топ статей
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
    user: CurrentUser,
) -> AISettingsRead:
    settings = await AIService.get_settings(db)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(settings, k, v)
    await db.flush()
    await db.commit()
    await db.refresh(settings)
    logger.info("AI settings updated by user %s", user.id)
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
