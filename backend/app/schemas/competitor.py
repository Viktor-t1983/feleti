"""Схемы конкурентов."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel


class CompetitorModelRead(APIModel):
    id: int
    name: str
    max_load_kg: int | None = None
    power_kw: float | None = None
    voltage_v: int | None = None
    weight_kg: int | None = None
    dimensions: str | None = None
    modes: list[str] | None = None
    automation_level: str | None = None
    description: str | None = None


class CompetitorProblemRead(APIModel):
    id: int
    title: str
    description: str | None = None
    severity: str
    frequency: str | None = None
    source: str | None = None


class CompetitorRead(APIModel):
    id: int
    slug: str
    name: str
    country: str | None = None
    founded_year: int | None = None
    segment: str | None = None
    is_main_competitor: bool
    client_count: int | None = None
    recipe_count: int | None = None
    warranty_years: int | None = None
    has_cloud: bool | None = None
    has_mobile_app: bool | None = None
    has_remote_monitoring: bool | None = None
    has_video_camera: bool | None = None
    description: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    base_url: str | None = None
    sitemap_url: str | None = None
    crawl_config: dict | None = None
    crawl_status: str = "pending"
    crawl_error: str | None = None
    last_crawled_at: datetime | None = None
    articles_count: int = 0
    dealers: list[dict] | None = None
    models: list[CompetitorModelRead] = []
    problems: list[CompetitorProblemRead] = []
    created_at: datetime
    updated_at: datetime | None = None


class CompetitorCreate(APIModel):
    slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(..., min_length=2, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    founded_year: int | None = Field(default=None, ge=1800, le=2100)
    segment: str | None = Field(default=None, max_length=100)
    is_main_competitor: bool = False
    client_count: int | None = None
    recipe_count: int | None = None
    warranty_years: int | None = None
    has_cloud: bool | None = None
    has_mobile_app: bool | None = None
    has_remote_monitoring: bool | None = None
    has_video_camera: bool | None = None
    description: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    base_url: str | None = None
    sitemap_url: str | None = None
    crawl_config: dict | None = None
    dealers: list[dict] | None = None


class CompetitorUpdate(APIModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    country: str | None = Field(default=None, max_length=100)
    founded_year: int | None = None
    segment: str | None = Field(default=None, max_length=100)
    is_main_competitor: bool | None = None
    client_count: int | None = None
    recipe_count: int | None = None
    warranty_years: int | None = None
    has_cloud: bool | None = None
    has_mobile_app: bool | None = None
    has_remote_monitoring: bool | None = None
    has_video_camera: bool | None = None
    description: str | None = None
    strengths: list[str] | None = None
    weaknesses: list[str] | None = None
    base_url: str | None = None
    sitemap_url: str | None = None
    crawl_config: dict | None = None


class CompetitorOnboardRequest(APIModel):
    url: str = Field(..., min_length=5, max_length=500, description="URL сайта конкурента")
    name: str | None = Field(default=None, description="Название (если не указать — извлечётся из домена)")


class CompetitorDiscoveredInfo(APIModel):
    name: str
    slug: str
    base_url: str
    sitemap_url: str | None = None
    encoding: str | None = None
    title: str | None = None
    description: str | None = None
    page_count: int = 0
    error: str | None = None


class CompetitorOnboardResponse(APIModel):
    competitor: CompetitorRead
    discovery: CompetitorDiscoveredInfo
    articles_created: int = 0
    articles_skipped: int = 0
