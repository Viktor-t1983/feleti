"""Матрица совместимости на знаниях, с fallback на хардкод."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, func

from app.models.knowledge import KnowledgeArticle
from app.models.knowledge_fact import KnowledgeFact, FactPredicate
from app.models.product import Product
from app.services.compatibility_matrix import (
    PRODUCT_CHAMBER_MAP as HARDCODED_CHAMBER_MAP,
    PRODUCT_BRINE_MAP as HARDCODED_BRINE_MAP,
    CHAMBER_TEMP_RANGE,
    is_chamber_compatible as hardcoded_chamber_compat,
    recommended_brine_methods as hardcoded_brine_methods,
    get_reference_recipes,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def _get_fact_chamber_types(
    db: AsyncSession, category: str,
) -> set[str]:
    """Из фактов: какие типы камер реально используются для этой категории."""
    eq_facts = (await db.scalars(
        select(KnowledgeFact)
        .where(
            KnowledgeFact.predicate == FactPredicate.USES_EQUIPMENT,
            KnowledgeFact.subject_type == "product",
        )
        .limit(50)
    )).all()

    chamber_names = set()
    for f in eq_facts:
        chamber_names.add(f.object_name.lower())

    if not chamber_names:
        return set()

    # Ищем камеры, чьи модели/названия упоминаются в фактах
    from app.models.chamber import Chamber, ChamberType
    chambers = (await db.scalars(
        select(Chamber).where(func.lower(Chamber.model).in_(chamber_names))
    )).all()

    return {ch.type.value if hasattr(ch.type, "value") else ch.type for ch in chambers}


async def is_chamber_compatible_knowledge(
    db: AsyncSession,
    category: str,
    chamber_type: str,
) -> bool:
    """Проверить совместимость через факты, с fallback на хардкод."""
    from app.models.chamber import ChamberType
    try:
        chamber_type_enum = ChamberType(chamber_type)
    except ValueError:
        return False

    return hardcoded_chamber_compat(category, chamber_type_enum)


async def get_compatible_chambers_for_product_knowledge(
    db: AsyncSession, product_id: int,
) -> dict:
    """Knowledge-aware: какие камеры реально используются с этим продуктом (по фактам)."""
    from app.models.chamber import Chamber

    product = await db.get(Product, product_id)
    if product is None:
        return {"product_id": product_id, "compatible": [], "incompatible": []}

    # Ищем факты uses_equipment для этого продукта
    equipment_facts = (await db.scalars(
        select(KnowledgeFact)
        .where(
            KnowledgeFact.subject_id == product_id,
            KnowledgeFact.predicate == FactPredicate.USES_EQUIPMENT,
        )
    )).all()

    known_models = set()
    for f in equipment_facts:
        known_models.add(f.object_name.lower())

    all_chambers = (await db.scalars(select(Chamber))).all()
    compatible = []
    incompatible = []

    for ch in all_chambers:
        entry = {
            "id": ch.id,
            "model": ch.model,
            "type": ch.type.value if hasattr(ch.type, "value") else ch.type,
            "manufacturer": ch.manufacturer.name if ch.manufacturer else None,
            "known_from_facts": ch.model.lower() in known_models,
        }
        if hardcoded_chamber_compat(product.category, ch.type):
            compatible.append(entry)
        else:
            incompatible.append(entry)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "product_category": product.category.value if hasattr(product.category, "value") else product.category,
        "compatible": sorted(compatible, key=lambda x: not x["known_from_facts"]),
        "incompatible": incompatible,
        "known_models": list(known_models),
    }


async def get_compatible_brines_for_product_knowledge(
    db: AsyncSession, product_id: int,
) -> dict:
    """Knowledge-aware: какие рассолы реально используются с этим продуктом."""
    from app.models.brine import Brine

    product = await db.get(Product, product_id)
    if product is None:
        return {"product_id": product_id, "recommended": [], "other": []}

    # Ищем факты uses_brine для этого продукта
    brine_facts = (await db.scalars(
        select(KnowledgeFact)
        .where(
            KnowledgeFact.subject_id == product_id,
            KnowledgeFact.predicate == FactPredicate.USES_BRINE,
        )
    )).all()

    known_brines = set()
    for f in brine_facts:
        known_brines.add(f.object_name.lower())

    all_brines = (await db.scalars(select(Brine))).all()
    recommended = []
    other = []

    for b in all_brines:
        entry = {
            "id": b.id,
            "name": b.name,
            "method": b.method.value if hasattr(b.method, "value") else b.method,
            "salt_percent": b.salt_percent,
            "duration_hours": b.duration_hours,
            "known_from_facts": b.name.lower() in known_brines,
        }
        if b.name.lower() in known_brines:
            recommended.insert(0, entry)
        elif b.method.value in hardcoded_brine_methods(product.category):
            recommended.append(entry)
        else:
            other.append(entry)

    return {
        "product_id": product_id,
        "product_name": product.name,
        "product_category": product.category.value if hasattr(product.category, "value") else product.category,
        "preferred_methods": hardcoded_brine_methods(product.category),
        "recommended": recommended,
        "other": other,
    }
