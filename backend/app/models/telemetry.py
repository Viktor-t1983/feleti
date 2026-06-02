"""Модели телеметрии: TelemetryReading (поток от камер) + агрегаты."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Integer, ForeignKey, Float, Boolean, JSON, Index, String,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class TelemetryReading(Base):
    """Сырая телеметрия от камер (партиционирование по ts в миграции).

    7 дней raw → агрегаты 1 мин / 1 ч / 1 день → архив 1 год.
    """

    __tablename__ = "telemetry_readings"
    __table_args__ = (
        Index("ix_telemetry_chamber_ts", "chamber_id", "ts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chamber_id: Mapped[int] = mapped_column(
        ForeignKey("chambers.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[datetime] = mapped_column(nullable=False, index=True)
    t_chamber: Mapped[float | None] = mapped_column(Float, nullable=True)
    t_product: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    smoke_density: Mapped[float | None] = mapped_column(Float, nullable=True)
    electro_voltage: Mapped[float | None] = mapped_column(Float, nullable=True)
    electro_current: Mapped[float | None] = mapped_column(Float, nullable=True)
    fan_rpm: Mapped[float | None] = mapped_column(Float, nullable=True)
    door_open: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    current_phase: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phase_progress: Mapped[float | None] = mapped_column(Float, nullable=True)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    raw: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
