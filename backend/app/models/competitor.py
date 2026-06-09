"""Конкуренты — модели для анализа рынка."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.knowledge import KnowledgeArticle


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str | None] = mapped_column(String(100))
    founded_year: Mapped[int | None] = mapped_column(Integer)
    segment: Mapped[str | None] = mapped_column(String(100))
    is_main_competitor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    client_count: Mapped[int | None] = mapped_column(Integer)
    recipe_count: Mapped[int | None] = mapped_column(Integer)
    warranty_years: Mapped[int | None] = mapped_column(Integer)
    has_cloud: Mapped[bool | None] = mapped_column(Boolean)
    has_mobile_app: Mapped[bool | None] = mapped_column(Boolean)
    has_remote_monitoring: Mapped[bool | None] = mapped_column(Boolean)
    has_video_camera: Mapped[bool | None] = mapped_column(Boolean)
    description: Mapped[str | None] = mapped_column(Text)
    strengths: Mapped[list[str] | None] = mapped_column(JSON)
    weaknesses: Mapped[list[str] | None] = mapped_column(JSON)

    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    sitemap_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    crawl_config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    crawl_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    crawl_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    articles_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    dealers: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True, default=None)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    models: Mapped[list["CompetitorModel"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan", lazy="selectin"
    )
    problems: Mapped[list["CompetitorProblem"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan", lazy="selectin"
    )
    articles: Mapped[list["KnowledgeArticle"]] = relationship(
        back_populates="competitor", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Competitor {self.id} {self.name}>"


class CompetitorModel(Base):
    __tablename__ = "competitor_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    max_load_kg: Mapped[int | None] = mapped_column(Integer)
    power_kw: Mapped[float | None] = mapped_column(Float)
    voltage_v: Mapped[int | None] = mapped_column(Integer)
    weight_kg: Mapped[int | None] = mapped_column(Integer)
    dimensions: Mapped[str | None] = mapped_column(String(100))
    modes: Mapped[list[str] | None] = mapped_column(JSON)
    automation_level: Mapped[str | None] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)

    competitor: Mapped["Competitor"] = relationship(back_populates="models")

    def __repr__(self) -> str:
        return f"<CompetitorModel {self.id} {self.name}>"


class CompetitorProblem(Base):
    __tablename__ = "competitor_problems"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    frequency: Mapped[str | None] = mapped_column(String(100))
    source: Mapped[str | None] = mapped_column(String(500))

    competitor: Mapped["Competitor"] = relationship(back_populates="problems")

    def __repr__(self) -> str:
        return f"<CompetitorProblem {self.id} {self.title}>"
