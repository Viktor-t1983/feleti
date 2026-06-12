"""Матрица совместимости: продукт ↔ камера ↔ посол (rule-based)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.chamber import Chamber, ChamberType
from app.models.product import Product, ProductCategory

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# ── ProductCategory ↔ ChamberType compatibility ──
PRODUCT_CHAMBER_MAP: dict[ProductCategory, set[ChamberType]] = {
    ProductCategory.FISH_HOT: {ChamberType.HOT, ChamberType.UNIVERSAL, ChamberType.SEMI_HOT},
    ProductCategory.FISH_COLD: {ChamberType.COLD, ChamberType.UNIVERSAL},
    ProductCategory.FISH_ELECTRO: {ChamberType.ELECTRO, ChamberType.UNIVERSAL},
    ProductCategory.MEAT: {ChamberType.HOT, ChamberType.UNIVERSAL, ChamberType.SEMI_HOT},
    ProductCategory.POULTRY: {ChamberType.HOT, ChamberType.UNIVERSAL},
    ProductCategory.SAUSAGE_SEMI_SMOKED: {ChamberType.HOT, ChamberType.UNIVERSAL, ChamberType.SEMI_HOT},
    ProductCategory.SAUSAGE_RAW_SMOKED: {ChamberType.COLD, ChamberType.UNIVERSAL},
    ProductCategory.SAUSAGE_BOILD: {ChamberType.HOT, ChamberType.UNIVERSAL},
    ProductCategory.SAUSAGE_SALAMI: {ChamberType.COLD, ChamberType.UNIVERSAL},
    ProductCategory.CHEESE: {ChamberType.COLD, ChamberType.SMOKE},
    ProductCategory.BACON: {ChamberType.HOT, ChamberType.COLD, ChamberType.UNIVERSAL},
    ProductCategory.SNACKS: {ChamberType.HOT, ChamberType.UNIVERSAL},
    ProductCategory.BUTTER: {ChamberType.COLD, ChamberType.SMOKE},
    ProductCategory.OTHER: {ChamberType.UNIVERSAL},
}

# ── ProductCategory ↔ preferred brine methods ──
PRODUCT_BRINE_MAP: dict[ProductCategory, list[str]] = {
    ProductCategory.FISH_HOT: ["сухой", "мокрый"],
    ProductCategory.FISH_COLD: ["сухой", "мокрый"],
    ProductCategory.FISH_ELECTRO: ["сухой"],
    ProductCategory.MEAT: ["шприцевание", "мокрый", "сухой"],
    ProductCategory.POULTRY: ["мокрый", "шприцевание", "сухой"],
    ProductCategory.SAUSAGE_SEMI_SMOKED: ["мокрый", "шприцевание"],
    ProductCategory.SAUSAGE_RAW_SMOKED: ["сухой"],
    ProductCategory.SAUSAGE_BOILD: ["шприцевание", "мокрый"],
    ProductCategory.SAUSAGE_SALAMI: ["сухой"],
    ProductCategory.CHEESE: [],
    ProductCategory.BACON: ["сухой", "мокрый"],
    ProductCategory.SNACKS: ["сухой"],
    ProductCategory.BUTTER: [],
    ProductCategory.OTHER: ["сухой"],
}

# ── ChamberType → recommended temperature range ──
CHAMBER_TEMP_RANGE: dict[ChamberType, tuple[float, float]] = {
    ChamberType.HOT: (60, 120),
    ChamberType.COLD: (15, 30),
    ChamberType.ELECTRO: (30, 60),
    ChamberType.UNIVERSAL: (15, 120),
    ChamberType.SEMI_HOT: (40, 80),
    ChamberType.SMOKE: (15, 40),
    ChamberType.UNKNOWN: (0, 120),
}


def is_chamber_compatible(category: ProductCategory, chamber_type: ChamberType) -> bool:
    return chamber_type in PRODUCT_CHAMBER_MAP.get(category, set())


def recommended_brine_methods(category: ProductCategory) -> list[str]:
    return PRODUCT_BRINE_MAP.get(category, [])


def chamber_temp_range(chamber_type: ChamberType) -> tuple[float, float]:
    return CHAMBER_TEMP_RANGE.get(chamber_type, (0, 120))


# ── Data-driven lookups ──

async def get_reference_recipes(
    db: AsyncSession,
    product_id: int | None = None,
    chamber_id: int | None = None,
    limit: int = 10,
) -> list[dict]:
    """Найти схожие рецепты/версии для reference."""
    from app.models.recipe import Recipe, RecipeVersion

    stmt = (
        select(Recipe)
        .options(selectinload(Recipe.current_version))
        .where(Recipe.status != "archived")
    )
    if product_id is not None:
        stmt = stmt.where(Recipe.product_id == product_id)
    stmt = stmt.limit(limit)
    rows = (await db.scalars(stmt)).all()

    results: list[dict] = []
    for r in rows:
        v = r.current_version
        if v is None:
            continue
        results.append({
            "recipe_id": r.id,
            "recipe_name": r.name,
            "product_id": r.product_id,
            "phases_count": len(v.program or []),
            "total_duration_min": sum(p.get("duration_min", 0) for p in (v.program or [])),
            "brine_method": (v.brine or {}).get("method"),
            "yield_percent": v.yield_percent,
            "losses_percent": v.losses_percent,
        })
    return results


async def get_compatible_chambers(db: AsyncSession, category: ProductCategory) -> list[Chamber]:
    """Найти все камеры, совместимые с категорией продукта."""
    allowed_types = PRODUCT_CHAMBER_MAP.get(category, set())
    rows = (await db.scalars(
        select(Chamber).where(Chamber.type.in_([t.value for t in allowed_types]))
    )).all()
    return list(rows)


async def get_compatible_chambers_for_product(db: AsyncSession, product_id: int) -> dict:
    """Для продукта: какие камеры совместимы, какие нет."""
    product = await db.get(Product, product_id)
    if product is None:
        return {"product_id": product_id, "compatible": [], "incompatible": []}

    all_chambers = (await db.scalars(select(Chamber))).all()
    compatible = []
    incompatible = []
    for ch in all_chambers:
        entry = {
            "id": ch.id,
            "model": ch.model,
            "type": ch.type.value,
            "manufacturer": ch.manufacturer.name if ch.manufacturer else None,
        }
        if is_chamber_compatible(product.category, ch.type):
            compatible.append(entry)
        else:
            incompatible.append(entry)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "product_category": product.category.value,
        "compatible": compatible,
        "incompatible": incompatible,
    }


async def get_compatible_brines_for_product(db: AsyncSession, product_id: int) -> dict:
    """Для продукта: какие рассолы совместимы по методу."""
    from app.models.brine import Brine

    product = await db.get(Product, product_id)
    if product is None:
        return {"product_id": product_id, "recommended": [], "other": []}

    preferred_methods = recommended_brine_methods(product.category)
    all_brines = (await db.scalars(select(Brine))).all()

    recommended = []
    other = []
    for b in all_brines:
        entry = {
            "id": b.id,
            "name": b.name,
            "method": b.method.value,
            "salt_percent": b.salt_percent,
            "duration_hours": b.duration_hours,
        }
        if b.method.value in preferred_methods:
            recommended.append(entry)
        else:
            other.append(entry)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "product_category": product.category.value,
        "preferred_methods": preferred_methods,
        "recommended": recommended,
        "other": other,
    }
