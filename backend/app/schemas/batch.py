"""Pydantic v2 schemas для партий (Batch)."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import Field

from app.models.batch import BatchStatus
from app.schemas.common import APIModel


class BatchPhaseRead(APIModel):
    id: int
    phase_index: int
    name: str
    planned_duration_min: float | None = None
    actual_duration_min: float | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    set_t_chamber: float | None = None
    set_humidity: float | None = None
    set_smoke: str | None = None
    set_electro_voltage_kv: float | None = None
    set_fan_speed_percent: int | None = None
    avg_t_chamber: float | None = None
    avg_t_product: float | None = None
    avg_humidity: float | None = None
    notes: str | None = None


class BatchRead(APIModel):
    id: int
    recipe_version_id: int
    chamber_id: int
    operator_id: int | None = None
    batch_number: str
    status: BatchStatus
    product_weight_kg: float | None = None
    yield_kg: float | None = None
    losses_percent: float | None = None
    planned_start: datetime | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    notes: str | None = None
    errors: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class BatchDetail(BatchRead):
    phases: list[BatchPhaseRead] = Field(default_factory=list)


class BatchCreate(APIModel):
    recipe_version_id: int
    chamber_id: int
    operator_id: int | None = None
    batch_number: Annotated[str, Field(min_length=1, max_length=50)]
    product_weight_kg: float | None = None
    planned_start: datetime | None = None
    notes: str | None = None


class BatchUpdate(APIModel):
    operator_id: int | None = None
    product_weight_kg: float | None = None
    yield_kg: float | None = None
    losses_percent: float | None = None
    notes: str | None = None
    status: BatchStatus | None = None


class BatchStatusChange(APIModel):
    """Запрос на смену статуса (start/pause/resume/cancel)."""

    note: str | None = None


__all__ = [
    "BatchPhaseRead",
    "BatchRead",
    "BatchDetail",
    "BatchCreate",
    "BatchUpdate",
    "BatchStatusChange",
]
