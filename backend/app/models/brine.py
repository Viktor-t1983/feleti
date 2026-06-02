"""Модель посола (brine) — отдельная сущность для переиспользования между рецептами."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, Integer, JSON, Enum as SAEnum, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class BrineMethod(str, PyEnum):
    DRY = "сухой"
    WET = "мокрый"
    INJECTION = "шприцевание"
    COMBO = "комбинированный"
    MIXED = "смешанный"


class Brine(Base):
    __tablename__ = "brines"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), unique=True, nullable=False, index=True)
    method: Mapped[BrineMethod] = mapped_column(
        SAEnum(BrineMethod, name="brine_method"), default=BrineMethod.DRY, nullable=False
    )

    salt_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    sugar_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    nitrite_ppm: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    nitrate_ppm: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    spices: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    duration_hours: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    temp_c: Mapped[float] = mapped_column(Float, default=4, nullable=False)
    water_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Brine {self.id} {self.name} ({self.method.value})>"
