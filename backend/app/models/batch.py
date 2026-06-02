"""Модели партий (запусков): Batch + BatchPhase + BatchTelemetry."""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    String, ForeignKey, Integer, Float, Boolean, JSON, Enum as SAEnum, Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.recipe import RecipeVersion
    from app.models.chamber import Chamber
    from app.models.user import User


class BatchStatus(str, PyEnum):
    PLANNED = "planned"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_version_id: Mapped[int] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    chamber_id: Mapped[int] = mapped_column(
        ForeignKey("chambers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    operator_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    batch_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    status: Mapped[BatchStatus] = mapped_column(
        SAEnum(BatchStatus, name="batch_status"),
        default=BatchStatus.PLANNED, nullable=False, index=True,
    )

    product_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    yield_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    losses_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    planned_start: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    errors: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    recipe_version: Mapped["RecipeVersion"] = relationship(lazy="joined")
    chamber: Mapped["Chamber"] = relationship(back_populates="batches", lazy="joined")
    operator: Mapped["User | None"] = relationship(lazy="joined")
    phases: Mapped[list["BatchPhase"]] = relationship(
        back_populates="batch", order_by="BatchPhase.phase_index", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Batch {self.id} {self.batch_number} {self.status.value}>"


class BatchPhase(Base):
    __tablename__ = "batch_phases"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    phase_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    planned_duration_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_duration_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_start: Mapped[datetime | None] = mapped_column(nullable=True)
    actual_end: Mapped[datetime | None] = mapped_column(nullable=True)

    set_t_chamber: Mapped[float | None] = mapped_column(Float, nullable=True)
    set_humidity: Mapped[float | None] = mapped_column(Float, nullable=True)
    set_smoke: Mapped[str | None] = mapped_column(String(50), nullable=True)
    set_electro_voltage_kv: Mapped[float | None] = mapped_column(Float, nullable=True)
    set_fan_speed_percent: Mapped[int | None] = mapped_column(nullable=True)

    avg_t_chamber: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_t_product: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_humidity: Mapped[float | None] = mapped_column(Float, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    batch: Mapped["Batch"] = relationship(back_populates="phases")

    def __repr__(self) -> str:
        return f"<BatchPhase {self.id} batch={self.batch_id} #{self.phase_index} {self.name}>"


class BatchTelemetry(Base):
    """Сырая телеметрия конкретной партии (партиционирование по ts в миграции)."""

    __tablename__ = "batch_telemetry"
    __table_args__ = (
        Index("ix_batch_telemetry_batch_ts", "batch_id", "ts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey("batches.id", ondelete="CASCADE"), nullable=False
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
