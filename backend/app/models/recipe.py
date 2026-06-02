"""Модели рецептов: Recipe + RecipeVersion + RecipeApproval.

Recipe — общий заголовок, ссылается на current_version_id.
RecipeVersion — иммутабельная версия (программа копчения, ингредиенты, посол).
RecipeApproval — workflow апрува (draft → pending → approved → archived).
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    String, ForeignKey, Integer, Boolean, JSON, Enum as SAEnum, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class RecipeStatus(str, PyEnum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ApprovalDecision(str, PyEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), unique=True, nullable=False, index=True)
    status: Mapped[RecipeStatus] = mapped_column(
        SAEnum(RecipeStatus, name="recipe_status"),
        default=RecipeStatus.DRAFT, nullable=False, index=True,
    )
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="SET NULL", use_alter=True),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    product: Mapped["Product"] = relationship(foreign_keys=[product_id], lazy="joined")
    versions: Mapped[list["RecipeVersion"]] = relationship(
        back_populates="recipe",
        foreign_keys="RecipeVersion.recipe_id",
        order_by="RecipeVersion.version_number.desc()",
        lazy="selectin",
    )
    current_version: Mapped["RecipeVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True, lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<Recipe {self.id} {self.name} ({self.status.value})>"


class RecipeVersion(Base):
    __tablename__ = "recipe_versions"
    __table_args__ = (
        UniqueConstraint("recipe_id", "version_number", name="uq_recipe_version_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    parent_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="SET NULL"), nullable=True
    )

    program: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    brine: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ingredients: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)

    yield_percent: Mapped[float | None] = mapped_column(nullable=True)
    losses_percent: Mapped[float | None] = mapped_column(nullable=True)
    bju_per_100g: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    cost_per_kg: Mapped[float | None] = mapped_column(nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    gost: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(nullable=True)

    status: Mapped[RecipeStatus] = mapped_column(
        SAEnum(RecipeStatus, name="recipe_version_status"),
        default=RecipeStatus.DRAFT, nullable=False, index=True,
    )

    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    recipe: Mapped["Recipe"] = relationship(
        back_populates="versions", foreign_keys=[recipe_id]
    )
    approvals: Mapped[list["RecipeApproval"]] = relationship(
        back_populates="version", order_by="RecipeApproval.decided_at", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<RecipeVersion {self.id} recipe={self.recipe_id} v{self.version_number} {self.status.value}>"


class RecipeApproval(Base):
    __tablename__ = "recipe_approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipe_version_id: Mapped[int] = mapped_column(
        ForeignKey("recipe_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    approver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    decision: Mapped[ApprovalDecision] = mapped_column(
        SAEnum(ApprovalDecision, name="approval_decision"), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    version: Mapped["RecipeVersion"] = relationship(back_populates="approvals")
    approver: Mapped["User"] = relationship(lazy="joined")
