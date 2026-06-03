"""Модели базы знаний: KnowledgeArticle + KnowledgeAttachment + KnowledgeTag."""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, ForeignKey, Boolean, JSON, Enum as SAEnum, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.manufacturer import Manufacturer


class ArticleCategory(str, PyEnum):
    THEORY = "theory"
    RECIPE = "recipe"
    TROUBLESHOOTING = "troubleshooting"
    REGULATION = "regulation"
    COMPARISON = "comparison"
    REVIEW = "review"
    NEWS = "news"
    GUIDE = "guide"


class AttachmentKind(str, PyEnum):
    PDF = "pdf"
    VIDEO = "video"
    IMAGE = "image"
    DOC = "doc"
    LINK = "link"


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    excerpt: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    category: Mapped[ArticleCategory] = mapped_column(
        SAEnum(ArticleCategory, name="article_category"), nullable=False, index=True
    )
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="SET NULL"), nullable=True
    )
    chamber_model: Mapped[str | None] = mapped_column(String(200), nullable=True)

    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(nullable=True)

    author: Mapped["User | None"] = relationship(lazy="joined")
    manufacturer: Mapped["Manufacturer | None"] = relationship(lazy="joined")
    attachments: Mapped[list["KnowledgeAttachment"]] = relationship(
        back_populates="article", cascade="all, delete-orphan", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeArticle {self.id} {self.title[:50]}>"


class KnowledgeAttachment(Base):
    __tablename__ = "knowledge_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[str] = mapped_column(String(100), nullable=False)
    kind: Mapped[AttachmentKind] = mapped_column(
        SAEnum(AttachmentKind, name="attachment_kind"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    article: Mapped["KnowledgeArticle"] = relationship(back_populates="attachments")
