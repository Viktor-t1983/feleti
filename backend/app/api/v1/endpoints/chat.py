"""Эндпоинты для диалогов с AI-ассистентом."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select

from app.core.deps import CurrentUser, DBSession
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionRead,
    ChatSessionSummary,
    ChatSessionUpdate,
)
from app.schemas.common import Page, PageParams

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/sessions",
    response_model=Page[ChatSessionSummary],
    summary="Список диалогов пользователя",
)
async def list_sessions(
    db: DBSession,
    user: CurrentUser,
    params: Annotated[PageParams, Depends()],
) -> Page[ChatSessionSummary]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    count_stmt = (
        select(func.count())
        .select_from(ChatSession)
        .where(ChatSession.user_id == user.id)
    )
    total = await db.scalar(count_stmt) or 0
    rows = (
        await db.scalars(
            stmt.offset((params.page - 1) * params.size).limit(params.size)
        )
    ).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[ChatSessionSummary](
        items=[ChatSessionSummary.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.post(
    "/sessions",
    response_model=ChatSessionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый диалог",
)
async def create_session(
    payload: ChatSessionCreate,
    db: DBSession,
    user: CurrentUser,
) -> ChatSessionRead:
    session = ChatSession(
        user_id=user.id,
        title=payload.title,
        page_context=payload.page_context,
    )
    db.add(session)
    await db.flush()
    await db.commit()
    await db.refresh(session)
    return ChatSessionRead.model_validate(session)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionRead,
    summary="Получить диалог с сообщениями",
)
async def get_session(
    session_id: int,
    db: DBSession,
    user: CurrentUser,
) -> ChatSessionRead:
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )
    return ChatSessionRead.model_validate(session)


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionRead,
    summary="Обновить заголовок/контекст диалога",
)
async def update_session(
    session_id: int,
    payload: ChatSessionUpdate,
    db: DBSession,
    user: CurrentUser,
) -> ChatSessionRead:
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(session, k, v)
    await db.flush()
    await db.commit()
    await db.refresh(session)
    return ChatSessionRead.model_validate(session)


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    summary="Удалить диалог",
)
async def delete_session(
    session_id: int,
    db: DBSession,
    user: CurrentUser,
) -> None:
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )
    await db.delete(session)
    await db.commit()


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить сообщение в диалог",
)
async def add_message(
    session_id: int,
    payload: ChatMessageCreate,
    db: DBSession,
    user: CurrentUser,
) -> ChatMessageRead:
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    # определяем следующий seq
    max_seq = await db.scalar(
        select(func.coalesce(func.max(ChatMessage.seq), 0)).where(
            ChatMessage.session_id == session_id
        )
    ) or 0

    msg = ChatMessage(
        session_id=session_id,
        seq=max_seq + 1,
        role=payload.role,
        content=payload.content,
        sources=payload.sources,
        model=payload.model,
    )
    db.add(msg)

    session.message_count = (await db.scalar(
        select(func.count()).where(ChatMessage.session_id == session_id)
    )) + 1
    await db.flush()
    await db.commit()
    await db.refresh(msg)
    return ChatMessageRead.model_validate(msg)


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[ChatMessageRead],
    summary="Сообщения диалога",
)
async def list_messages(
    session_id: int,
    db: DBSession,
    user: CurrentUser,
) -> list[ChatMessageRead]:
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user.id,
        )
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Диалог не найден",
        )

    rows = (
        await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.seq)
        )
    ).all()
    return [ChatMessageRead.model_validate(r) for r in rows]
