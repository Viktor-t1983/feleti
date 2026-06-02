"""Схемы производителя коптильного оборудования."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field, HttpUrl

from app.schemas.common import APIModel


class ManufacturerRead(APIModel):
    id: int
    slug: str
    name: str
    short_name: str | None = None
    country: str | None = None
    city: str | None = None
    founded_year: int | None = None
    website: str | None = None
    description: str | None = None
    logo_url: str | None = None
    is_our_brand: bool
    is_competitor: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime | None = None


class ManufacturerCreate(APIModel):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=2, max_length=255)
    short_name: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    founded_year: int | None = Field(default=None, ge=1700, le=2100)
    website: HttpUrl | None = None
    description: str | None = None
    logo_url: HttpUrl | None = None
    is_our_brand: bool = False
    is_competitor: bool = False
    sort_order: int = 100


class ManufacturerUpdate(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    short_name: str | None = Field(default=None, max_length=100)
    country: str | None = None
    city: str | None = None
    founded_year: int | None = None
    website: HttpUrl | None = None
    description: str | None = None
    logo_url: HttpUrl | None = None
    is_our_brand: bool | None = None
    is_competitor: bool | None = None
    sort_order: int | None = None
