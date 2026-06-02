"""Модель продукта (изделия)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import String, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.recipe import Recipe


class ProductCategory(str, PyEnum):
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


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    category: Mapped[ProductCategory] = mapped_column(
        SAEnum(ProductCategory, name="product_category"), nullable=False, index=True
    )

    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    images: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    base_recipe_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL", use_alter=True), nullable=True
    )

    gost: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shelf_life_days: Mapped[int | None] = mapped_column(nullable=True)
    storage_temp_min: Mapped[float | None] = mapped_column(nullable=True)
    storage_temp_max: Mapped[float | None] = mapped_column(nullable=True)
    storage_humidity_min: Mapped[float | None] = mapped_column(nullable=True)
    storage_humidity_max: Mapped[float | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    base_recipe: Mapped["Recipe | None"] = relationship(foreign_keys=[base_recipe_id])

    def __repr__(self) -> str:
        return f"<Product {self.id} {self.name}>"
