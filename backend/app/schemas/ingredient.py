"""Схемы ингредиента (мясо, специи, щепа, соль, добавки)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import Field

from app.schemas.common import APIModel


class IngredientTypeEnum(str, Enum):
    MEAT = "мясо"
    FAT = "жир"
    SPICE = "специя"
    SALT = "соль"
    WOOD = "щепа"
    LIQUID_SMOKE = "жидкий дым"
    ADDITIVE = "добавка"
    OTHER = "прочее"


class IngredientRead(APIModel):
    id: int
    name: str
    slug: str
    type: IngredientTypeEnum
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float
    kcal_per_100g: float
    price_per_kg: float
    unit: str
    is_allergen: bool
    allergens: list[str] = []
    gmo_flag: bool
    wood_species: str | None = None
    wood_form: str | None = None
    fraction_mm: str | None = None
    description: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class IngredientCreate(APIModel):
    name: str = Field(..., min_length=2, max_length=200)
    slug: str = Field(..., min_length=2, max_length=200, pattern=r"^[a-z0-9-]+$")
    type: IngredientTypeEnum
    protein_per_100g: float = 0
    fat_per_100g: float = 0
    carbs_per_100g: float = 0
    kcal_per_100g: float = 0
    price_per_kg: float = 0
    unit: str = "кг"
    is_allergen: bool = False
    allergens: list[str] = []
    gmo_flag: bool = False
    wood_species: str | None = None
    wood_form: str | None = None
    fraction_mm: str | None = None
    description: str | None = None


class IngredientUpdate(APIModel):
    name: str | None = None
    type: IngredientTypeEnum | None = None
    protein_per_100g: float | None = None
    fat_per_100g: float | None = None
    carbs_per_100g: float | None = None
    kcal_per_100g: float | None = None
    price_per_kg: float | None = None
    unit: str | None = None
    is_allergen: bool | None = None
    allergens: list[str] | None = None
    gmo_flag: bool | None = None
    wood_species: str | None = None
    wood_form: str | None = None
    fraction_mm: str | None = None
    description: str | None = None
