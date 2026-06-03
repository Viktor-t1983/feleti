"""Pydantic-схемы для базы знаний (KnowledgeArticle + вложения)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import Field

from app.models.knowledge import ArticleCategory, AttachmentKind
from app.schemas.common import APIModel


class ArticleCategoryEnum(str, Enum):
    THEORY = "theory"
    RECIPE = "recipe"
    TROUBLESHOOTING = "troubleshooting"
    REGULATION = "regulation"
    COMPARISON = "comparison"
    REVIEW = "review"
    NEWS = "news"
    GUIDE = "guide"


class AttachmentKindEnum(str, Enum):
    PDF = "pdf"
    VIDEO = "video"
    IMAGE = "image"
    DOC = "doc"
    LINK = "link"


class KnowledgeAttachmentRead(APIModel):
    id: int
    file_id: str
    kind: AttachmentKindEnum
    filename: str
    size_bytes: int
    mime_type: str | None = None
    url: str | None = None


class KnowledgeArticleRead(APIModel):
    id: int
    title: str
    slug: str
    body_md: str
    body_html: str | None = None
    excerpt: str | None = None
    category: ArticleCategoryEnum
    tags: list[str] = []
    manufacturer_id: int | None = None
    chamber_model: str | None = None
    source_url: str | None = None
    is_published: bool
    version: int
    author_id: int | None = None
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    attachments: list[KnowledgeAttachmentRead] = []


class KnowledgeArticleSummary(APIModel):
    """Краткая карточка (без body_md — для списков)."""

    id: int
    title: str
    slug: str
    excerpt: str | None = None
    category: ArticleCategoryEnum
    tags: list[str] = []
    is_published: bool
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    manufacturer_id: int | None = None


class KnowledgeAttachmentCreate(APIModel):
    file_id: str
    kind: AttachmentKindEnum
    filename: str
    size_bytes: int = 0
    mime_type: str | None = None
    url: str | None = None


class KnowledgeArticleCreate(APIModel):
    title: Annotated[str, Field(min_length=2, max_length=500)]
    slug: Annotated[str, Field(min_length=2, max_length=500, pattern=r"^[a-z0-9-]+$")]
    body_md: str
    body_html: str | None = None
    excerpt: str | None = None
    category: ArticleCategoryEnum
    tags: list[str] = []
    manufacturer_id: int | None = None
    chamber_model: str | None = None
    source_url: str | None = None
    is_published: bool = False
    attachments: list[KnowledgeAttachmentCreate] = []


class KnowledgeArticleUpdate(APIModel):
    title: str | None = None
    body_md: str | None = None
    body_html: str | None = None
    excerpt: str | None = None
    category: ArticleCategoryEnum | None = None
    tags: list[str] | None = None
    manufacturer_id: int | None = None
    chamber_model: str | None = None
    source_url: str | None = None
    is_published: bool | None = None


class KnowledgeSearchResult(APIModel):
    """Элемент результата поиска с релевантностью (0..1)."""

    article: KnowledgeArticleSummary
    score: float
    snippet: str | None = None


class RAGAnswer(APIModel):
    """Ответ RAG: синтезированный ответ + источники."""

    answer: str
    sources: list[KnowledgeSearchResult]
    query: str


class RAGQuery(APIModel):
    """Запрос к RAG."""

    question: Annotated[str, Field(min_length=2, max_length=1000)]
    top_k: Annotated[int, Field(ge=1, le=20)] = 5


__all__ = [
    "ArticleCategoryEnum",
    "AttachmentKindEnum",
    "KnowledgeAttachmentRead",
    "KnowledgeArticleRead",
    "KnowledgeArticleSummary",
    "KnowledgeArticleCreate",
    "KnowledgeArticleUpdate",
    "KnowledgeAttachmentCreate",
    "KnowledgeSearchResult",
    "RAGAnswer",
    "RAGQuery",
]
