"""Модели базы знаний: KnowledgeArticle + KnowledgeAttachment + KnowledgeTag."""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, ForeignKey, Boolean, Enum as SAEnum, Text, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.manufacturer import Manufacturer
    from app.models.competitor import Competitor


class AnalysisStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


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
    tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    manufacturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("manufacturers.id", ondelete="SET NULL"), nullable=True
    )
    chamber_model: Mapped[str | None] = mapped_column(String(200), nullable=True)

    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    competitor_id: Mapped[int | None] = mapped_column(
        ForeignKey("competitors.id", ondelete="SET NULL"), nullable=True, index=True
    )
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
    competitor: Mapped["Competitor | None"] = relationship(
        back_populates="articles", lazy="joined"
    )
    attachments: Mapped[list["KnowledgeAttachment"]] = relationship(
        back_populates="article", cascade="all, delete-orphan", lazy="selectin"
    )
    analysis: Mapped["ArticleAnalysis | None"] = relationship(
        back_populates="article", uselist=False, lazy="joined"
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


class ArticleAnalysis(Base):
    """Результат AI-анализа статьи конкурента."""

    __tablename__ = "article_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    products: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    technologies: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    problems: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    equipment: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    key_insights: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    competitor_mentions: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    target_markets: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    ai_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    topic_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[AnalysisStatus] = mapped_column(
        SAEnum(AnalysisStatus, name="analysis_status"),
        default=AnalysisStatus.PENDING,
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    article: Mapped["KnowledgeArticle"] = relationship(back_populates="analysis")

    def __repr__(self) -> str:
        return f"<ArticleAnalysis {self.id} article={self.article_id} status={self.status}>"
