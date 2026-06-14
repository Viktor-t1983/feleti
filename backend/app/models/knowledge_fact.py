"""KnowledgeFact + KnowledgeChunk — нормализованные факты с происхождением."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, ForeignKey, Integer, Float, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class FactSubjectType(str, PyEnum):
    PRODUCT = "product"
    BRINE = "brine"
    CHAMBER = "chamber"
    TECHNOLOGY = "technology"
    INGREDIENT = "ingredient"
    REGULATION = "regulation"
    ARTICLE = "article"


class FactPredicate(str, PyEnum):
    USES_BRINE = "uses_brine"
    USES_EQUIPMENT = "uses_equipment"
    USES_TECHNOLOGY = "uses_technology"
    HAS_PARAMETER = "has_parameter"
    REGULATED_BY = "regulated_by"
    HAS_CATEGORY = "has_category"
    CONTAINS = "contains"
    DERIVED_FROM = "derived_from"
    SHELF_LIFE = "shelf_life"
    STORAGE_CONDITION = "storage_condition"
    PROCESS_STEP = "process_step"
    MENTIONS = "mentions"


class FactObjectType(str, PyEnum):
    PRODUCT = "product"
    BRINE = "brine"
    CHAMBER = "chamber"
    TECHNOLOGY = "technology"
    REGULATION = "regulation"
    INGREDIENT = "ingredient"
    LITERAL = "literal"


class FactStatus(str, PyEnum):
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    DEPRECATED = "deprecated"


class KnowledgeChunk(Base):
    """Фрагмент статьи — минимальная единица анализа."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_offset_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    char_offset_end: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False,
    )

    def __repr__(self) -> str:
        return f"<KnowledgeChunk {self.id} article={self.article_id} #{self.chunk_index}>"


class KnowledgeFact(Base):
    """Один факт, извлечённый AI из чанка статьи.

    Схема: subject --predicate--> object
    Пример: Скумбрия г/к --uses_brine--> Тузлук классический
    """

    __tablename__ = "knowledge_facts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    chunk_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_chunks.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    article_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_articles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    subject_type: Mapped[FactSubjectType] = mapped_column(
        SAEnum(FactSubjectType, name="fact_subject_type"),
        nullable=False, index=True,
    )
    subject_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    subject_name: Mapped[str] = mapped_column(String(200), nullable=False)

    predicate: Mapped[FactPredicate] = mapped_column(
        SAEnum(FactPredicate, name="fact_predicate"),
        nullable=False, index=True,
    )

    object_type: Mapped[FactObjectType] = mapped_column(
        SAEnum(FactObjectType, name="fact_object_type"),
        nullable=False,
    )
    object_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    object_name: Mapped[str] = mapped_column(String(500), nullable=False)

    params: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.3, nullable=False)

    status: Mapped[FactStatus] = mapped_column(
        SAEnum(FactStatus, name="fact_status"),
        default=FactStatus.CANDIDATE,
        nullable=False,
    )

    source_hash: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeFact {self.id} "
            f"{self.subject_name} --{self.predicate.value}--> {self.object_name}>"
        )
