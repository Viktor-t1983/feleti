"""Матрица совместимости: продукт ↔ камера ↔ посол."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query

from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.models.product import Product
from app.schemas.common import APIModel
from app.models.chamber import Chamber, ChamberType
from app.services.compatibility_knowledge import (
    get_compatible_brines_for_product_knowledge,
    get_compatible_chambers_for_product_knowledge,
    get_reference_recipes,
)
from app.services.compatibility_matrix import (
    chamber_temp_range,
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
    known_from_facts: bool = False


class BrineCompatibilityOut(APIModel):
    id: int
    name: str
    method: str
    salt_percent: float
    duration_hours: float
    recommended: bool
    known_from_facts: bool = False


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

    # Chambers — knowledge-aware
    chambers_out: list[ChamberCompatibilityOut] = []
    ch_data = await get_compatible_chambers_for_product_knowledge(db, product_id)
    for ch in ch_data.get("compatible", []):
        tr = None
        try:
            ct = ChamberType(ch["type"])
            tr_raw = chamber_temp_range(ct)
            tr = (tr_raw[0], tr_raw[1])
        except (ValueError, KeyError):
            pass
        chambers_out.append(ChamberCompatibilityOut(
            id=ch["id"],
            model=ch["model"],
            type=ch["type"],
            manufacturer=ch["manufacturer"],
            compatible=True,
            temp_range=tr,
            known_from_facts=ch.get("known_from_facts", False),
        ))
    for ch in ch_data.get("incompatible", []):
        chambers_out.append(ChamberCompatibilityOut(
            id=ch["id"],
            model=ch["model"],
            type=ch["type"],
            manufacturer=ch["manufacturer"],
            compatible=False,
            temp_range=None,
            known_from_facts=False,
        ))

    # Brines — knowledge-aware
    brines_out: list[BrineCompatibilityOut] = []
    if category:
        brine_data = await get_compatible_brines_for_product_knowledge(db, product_id)
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
