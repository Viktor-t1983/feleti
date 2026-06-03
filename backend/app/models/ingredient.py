"""Модель ингредиента (мясо, специя, соль, щепа, прочее)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, Float, Boolean, Enum as SAEnum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class IngredientType(str, PyEnum):
    MEAT = "мясо"
    FAT = "жир"
    SPICE = "специя"
    SALT = "соль"
    WOOD = "щепа"
    LIQUID_SMOKE = "жидкий дым"
    ADDITIVE = "добавка"
    OTHER = "прочее"


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    type: Mapped[IngredientType] = mapped_column(
        SAEnum(IngredientType, name="ingredient_type"), nullable=False, index=True
    )

    protein_per_100g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    fat_per_100g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    carbs_per_100g: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    kcal_per_100g: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    price_per_kg: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="кг", nullable=False)

    is_allergen: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allergens: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    gmo_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    wood_species: Mapped[str | None] = mapped_column(String(50), nullable=True)
    wood_form: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fraction_mm: Mapped[str | None] = mapped_column(String(50), nullable=True)

    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Ingredient {self.id} {self.name} ({self.type.value})>"
