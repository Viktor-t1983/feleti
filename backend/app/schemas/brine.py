"""Схемы посола (brine)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.common import APIModel


class BrineMethodEnum(str, Enum):
    DRY = "сухой"
    WET = "мокрый"
    INJECTION = "шприцевание"
    COMBO = "комбинированный"
    MIXED = "смешанный"


class BrineRead(APIModel):
    id: int
    name: str
    slug: str
    method: BrineMethodEnum
    salt_percent: float
    sugar_percent: float
    nitrite_ppm: float
    nitrate_ppm: float
    spices: list[str] = []
    duration_hours: float
    temp_c: float
    water_percent: float | None = None
    description: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class BrineCreate(APIModel):
    name: str = Field(..., min_length=2, max_length=300)
    slug: str = Field(..., min_length=2, max_length=300, pattern=r"^[a-z0-9-]+$")
    method: BrineMethodEnum = BrineMethodEnum.DRY
    salt_percent: float = Field(default=0, ge=0, le=100)
    sugar_percent: float = Field(default=0, ge=0, le=100)
    nitrite_ppm: float = Field(default=0, ge=0, le=200)
    nitrate_ppm: float = Field(default=0, ge=0, le=500)
    spices: list[str] = []
    duration_hours: float = Field(default=0, ge=0, le=1000)
    temp_c: float = Field(default=4, ge=-20, le=30)
    water_percent: float | None = Field(default=None, ge=0, le=100)
    description: str | None = None
    notes: str | None = None


class BrineUpdate(APIModel):
    name: str | None = None
    method: BrineMethodEnum | None = None
    salt_percent: float | None = None
    sugar_percent: float | None = None
    nitrite_ppm: float | None = None
    nitrate_ppm: float | None = None
    spices: list[str] | None = None
    duration_hours: float | None = None
    temp_c: float | None = None
    water_percent: float | None = None
    description: str | None = None
    notes: str | None = None
