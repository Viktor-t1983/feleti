"""Схемы продукта (изделия): Докторская, Сёмга х/к, ... """

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field, HttpUrl

from app.schemas.common import APIModel


class ProductCategoryEnum(str, Enum):
    SAUSAGE_BOILD = "колбаса вареная"
    SAUSAGE_SEMI_SMOKED = "колбаса полукопченая"
    SAUSAGE_RAW_SMOKED = "колбаса сырокопченая"
    MEAT = "мясо"
    POULTRY = "птица"
    FISH_HOT = "рыба горячего копчения"
    FISH_COLD = "рыба холодного копчения"
    FISH_ELECTRO = "рыба электростатического копчения"
    CHEESE = "сыр"
    SAUSAGE_SALAMI = "колбаса сыровяленая"
    BACON = "сало"
    BUTTER = "масло"
    SNACKS = "снеки"
    OTHER = "прочее"


class ProductRead(APIModel):
    id: int
    name: str
    slug: str
    category: ProductCategoryEnum
    description: str | None = None
    images: list[str] = []
    base_recipe_id: int | None = None
    gost: str | None = None
    shelf_life_days: int | None = None
    storage_temp_min: float | None = None
    storage_temp_max: float | None = None
    storage_humidity_min: float | None = None
    storage_humidity_max: float | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ProductCreate(APIModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200, pattern=r"^[a-z0-9-]+$")
    category: ProductCategoryEnum
    description: str | None = None
    images: list[HttpUrl] = []
    base_recipe_id: int | None = None
    gost: str | None = None
    shelf_life_days: int | None = Field(default=None, ge=0)
    storage_temp_min: float | None = None
    storage_temp_max: float | None = None
    storage_humidity_min: float | None = Field(default=None, ge=0, le=100)
    storage_humidity_max: float | None = Field(default=None, ge=0, le=100)


class ProductUpdate(APIModel):
    name: str | None = None
    category: ProductCategoryEnum | None = None
    description: str | None = None
    images: list[HttpUrl] | None = None
    base_recipe_id: int | None = None
    gost: str | None = None
    shelf_life_days: int | None = None
    storage_temp_min: float | None = None
    storage_temp_max: float | None = None
    storage_humidity_min: float | None = None
    storage_humidity_max: float | None = None
