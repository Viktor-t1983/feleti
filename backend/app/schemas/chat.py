"""Pydantic-схемы для диалогов с AI-ассистентом."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field
from typing import Annotated

from app.schemas.common import APIModel


class MessageSource(APIModel):
    id: int
    title: str
    slug: str


class ChatMessageRead(APIModel):
    id: int
    session_id: int
    seq: int
    role: str
    content: str
    sources: list[dict] | None = None
    model: str | None = None
    created_at: datetime


class ChatSessionRead(APIModel):
    id: int
    user_id: int
    title: str
    page_context: str | None = None
    message_count: int
    created_at: datetime
    updated_at: datetime
    messages: list[ChatMessageRead] = []


class ChatSessionSummary(APIModel):
    """Сессия без сообщений (для списка)."""

    id: int
    title: str
    page_context: str | None = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class ChatSessionCreate(APIModel):
    title: str = "Новый диалог"
    page_context: str | None = None


class ChatSessionUpdate(APIModel):
    title: str | None = None
    page_context: str | None = None


class ChatMessageCreate(APIModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: Annotated[str, Field(min_length=1, max_length=50000)]
    sources: list[dict] | None = None
    model: str | None = None


__all__ = [
    "ChatSessionRead",
    "ChatSessionSummary",
    "ChatSessionCreate",
    "ChatMessageRead",
    "ChatMessageCreate",
    "ChatSessionUpdate",
    "MessageSource",
]
