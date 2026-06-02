"""Схемы рецепта: Recipe + RecipeVersion + workflow."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.common import APIModel


class RecipeStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class RecipeApprovalDecisionEnum(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class RecipeVersionRead(APIModel):
    id: int
    recipe_id: int
    version_number: int
    parent_version_id: int | None = None
    program: list[dict] = []
    brine: dict | None = None
    ingredients: list[dict] = []
    yield_percent: float | None = None
    losses_percent: float | None = None
    bju_per_100g: dict | None = None
    cost_per_kg: float | None = None
    notes: str | None = None
    gost: str | None = None
    source: str | None = None
    verified: bool
    status: RecipeStatusEnum
    created_by_id: int | None = None
    created_at: datetime


class RecipeVersionCreate(APIModel):
    parent_version_id: int | None = None
    program: list[dict] = []
    brine: dict | None = None
    ingredients: list[dict] = []
    yield_percent: float | None = Field(default=None, ge=0, le=100)
    losses_percent: float | None = Field(default=None, ge=0, le=100)
    bju_per_100g: dict | None = None
    cost_per_kg: float | None = None
    notes: str | None = None
    gost: str | None = None
    source: str | None = None


class RecipeRead(APIModel):
    id: int
    product_id: int
    name: str
    slug: str
    status: RecipeStatusEnum
    current_version_id: int | None = None
    description: str | None = None
    tags: list[str] = []
    created_by_id: int | None = None
    created_at: datetime
    updated_at: datetime | None = None
    current_version: RecipeVersionRead | None = None


class RecipeCreate(APIModel):
    product_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=2, max_length=300)
    slug: str = Field(..., min_length=2, max_length=300, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    tags: list[str] = []
    initial_version: RecipeVersionCreate | None = Field(
        default=None,
        description="Первая иммутабельная версия рецепта (опционально).",
    )


class RecipeUpdate(APIModel):
    name: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    status: RecipeStatusEnum | None = None
    current_version_id: int | None = None
