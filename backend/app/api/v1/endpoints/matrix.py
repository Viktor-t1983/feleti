"""Матрица совместимости: продукт ↔ камера ↔ посол."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.models.chamber import Chamber
from app.models.product import Product
from app.schemas.common import APIModel
from app.services.compatibility_matrix import (
    chamber_temp_range,
    get_compatible_brines_for_product,
    get_reference_recipes,
    is_chamber_compatible,
    recommended_brine_methods,
)

router = APIRouter()


class ChamberCompatibilityOut(APIModel):
    id: int
    model: str
    type: str
    manufacturer: str | None = None
    compatible: bool
    temp_range: tuple[float, float] | None = None


class BrineCompatibilityOut(APIModel):
    id: int
    name: str
    method: str
    salt_percent: float
    duration_hours: float
    recommended: bool


class ProductAnalysis(APIModel):
    product_id: int
    product_name: str | None = None
    product_category: str | None = None
    preferred_brine_methods: list[str] = []
    chambers: list[ChamberCompatibilityOut] = []
    brines: list[BrineCompatibilityOut] = []
    reference_recipes: list[dict] = []


@router.get(
    "/compatibility",
    response_model=ProductAnalysis,
    summary="Анализ совместимости продукта, камеры и рассолов",
)
async def compatibility_analysis(
    db: DBSession,
    _user: CurrentUser,
    product_id: Annotated[int, Query(ge=1)],
    chamber_id: Annotated[int | None, Query(ge=1)] = None,
    limit_refs: Annotated[int, Query(alias="refs", ge=0, le=50)] = 5,
) -> ProductAnalysis:
    """Полный анализ совместимости для заданного продукта."""
    product = await db.get(Product, product_id)
    product_name = product.name if product else None
    category = product.category if product else None
    preferred_methods = recommended_brine_methods(category) if category else []

    # All chambers with compatibility
    chambers_out: list[ChamberCompatibilityOut] = []
    all_chambers = (await db.scalars(select(Chamber))).all()
    for ch in all_chambers:
        compatible = is_chamber_compatible(category, ch.type) if category else False
        tr = chamber_temp_range(ch.type)
        chambers_out.append(ChamberCompatibilityOut(
            id=ch.id,
            model=ch.model,
            type=ch.type.value,
            manufacturer=ch.manufacturer.name if ch.manufacturer else None,
            compatible=compatible,
            temp_range=(tr[0], tr[1]) if tr else None,
        ))

    # Brines
    brines_out: list[BrineCompatibilityOut] = []
    if category:
        brine_data = await get_compatible_brines_for_product(db, product_id)
        for b in brine_data.get("recommended", []):
            brines_out.append(BrineCompatibilityOut(**b, recommended=True))
        for b in brine_data.get("other", []):
            brines_out.append(BrineCompatibilityOut(**b, recommended=False))

    # Reference recipes
    refs = await get_reference_recipes(
        db, product_id=product_id, chamber_id=chamber_id, limit=limit_refs
    )

    return ProductAnalysis(
        product_id=product_id,
        product_name=product_name,
        product_category=category.value if category else None,
        preferred_brine_methods=preferred_methods,
        chambers=chambers_out,
        brines=brines_out,
        reference_recipes=refs,
    )
