"""Технологический калькулятор — preview расчёта, presets."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.models.chamber import Chamber, ChamberType
from app.models.ingredient import Ingredient
from app.models.product import Product, ProductCategory
from app.schemas.calc import (
    BJUSchema,
    IngredientBreakdown,
    ProgramPhaseSummary,
    ProgramStatsSchema,
    RecipeCalcResponse,
)
from app.schemas.common import APIModel
from app.services.recipe_calc import (
    IngredientForCalc,
    ProgramStats,
    calculate_recipe,
    compute_program_stats,
    compute_total_duration_min,
)

router = APIRouter()


class CalcIngredientInput(APIModel):
    ingredient_id: int
    mass_kg: float = 0
    mass_g: float = 0


class CalcPhaseInput(APIModel):
    index: int = 1
    name: str = ""
    t_chamber: float | None = None
    t_product: float | None = None
    duration_min: int = 60
    smoke: str = "none"
    electro_voltage_kv: float = 0


class CalcPreviewRequest(APIModel):
    product_id: int
    chamber_id: int | None = None
    ingredients: list[CalcIngredientInput] = []
    program: list[CalcPhaseInput] = []
    brine_method: str | None = None


# ---- Режимы по умолчанию для комбинаций продукт × камера ----
DEFAULT_PROGRAM_PRESETS: dict[str, dict] = {
    "рыба_горячее": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 40, "t_product": 25, "duration_min": 30, "smoke": "none"},
            {"name": "Копчение", "t_chamber": 80, "t_product": 60, "duration_min": 60, "smoke": "дым"},
            {"name": "Проварка", "t_chamber": 90, "t_product": 70, "duration_min": 30, "smoke": "none"},
        ],
    },
    "рыба_холодное": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 25, "t_product": 18, "duration_min": 60, "smoke": "none"},
            {"name": "Холодное копчение", "t_chamber": 28, "t_product": 24, "duration_min": 1440, "smoke": "дым"},
        ],
    },
    "рыба_электро": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 35, "t_product": 20, "duration_min": 20, "smoke": "none"},
            {"name": "Электрокопчение", "t_chamber": 50, "t_product": 35, "duration_min": 45, "smoke": "дым", "electro_voltage_kv": 20},
        ],
    },
    "мясо_горячее": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 50, "t_product": 30, "duration_min": 40, "smoke": "none"},
            {"name": "Копчение", "t_chamber": 85, "t_product": 65, "duration_min": 90, "smoke": "дым"},
            {"name": "Запекание", "t_chamber": 100, "t_product": 75, "duration_min": 60, "smoke": "none"},
        ],
    },
    "мясо_холодное": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 22, "t_product": 15, "duration_min": 120, "smoke": "none"},
            {"name": "Холодное копчение", "t_chamber": 26, "t_product": 22, "duration_min": 2880, "smoke": "дым"},
        ],
    },
    "колбаса_полукопченая": {
        "phases": [
            {"name": "Осадка", "t_chamber": 12, "t_product": 10, "duration_min": 120, "smoke": "none"},
            {"name": "Подсушка", "t_chamber": 50, "t_product": 35, "duration_min": 60, "smoke": "none"},
            {"name": "Копчение", "t_chamber": 75, "t_product": 55, "duration_min": 120, "smoke": "дым"},
            {"name": "Варка", "t_chamber": 80, "t_product": 72, "duration_min": 60, "smoke": "none"},
            {"name": "Охлаждение", "t_chamber": 10, "t_product": 20, "duration_min": 30, "smoke": "none"},
        ],
    },
    "колбаса_сырокопченая": {
        "phases": [
            {"name": "Осадка", "t_chamber": 4, "t_product": 4, "duration_min": 2880, "smoke": "none"},
            {"name": "Холодное копчение", "t_chamber": 22, "t_product": 18, "duration_min": 4320, "smoke": "дым"},
            {"name": "Сушка", "t_chamber": 14, "t_product": 12, "duration_min": 7200, "smoke": "none"},
        ],
    },
    "птица_горячее": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 45, "t_product": 28, "duration_min": 30, "smoke": "none"},
            {"name": "Копчение", "t_chamber": 85, "t_product": 65, "duration_min": 60, "smoke": "дым"},
            {"name": "Запекание", "t_chamber": 95, "t_product": 75, "duration_min": 40, "smoke": "none"},
        ],
    },
    "сыр_холодное": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 20, "t_product": 15, "duration_min": 60, "smoke": "none"},
            {"name": "Холодное копчение", "t_chamber": 24, "t_product": 20, "duration_min": 120, "smoke": "дым"},
        ],
    },
    "сало_горячее": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 40, "t_product": 25, "duration_min": 30, "smoke": "none"},
            {"name": "Копчение", "t_chamber": 75, "t_product": 55, "duration_min": 120, "smoke": "дым"},
            {"name": "Проварка", "t_chamber": 85, "t_product": 65, "duration_min": 60, "smoke": "none"},
        ],
    },
    "снеки_горячее": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 35, "t_product": 22, "duration_min": 20, "smoke": "none"},
            {"name": "Копчение", "t_chamber": 70, "t_product": 50, "duration_min": 30, "smoke": "дым"},
        ],
    },
    "птица_горячее": {
        "phases": [
            {"name": "Подсушка", "t_chamber": 45, "t_product": 28, "duration_min": 30, "smoke": "none"},
            {"name": "Копчение", "t_chamber": 85, "t_product": 65, "duration_min": 60, "smoke": "дым"},
            {"name": "Запекание", "t_chamber": 95, "t_product": 75, "duration_min": 40, "smoke": "none"},
        ],
    },
}


def _product_category_key(cat: ProductCategory | None) -> str | None:
    if cat is None:
        return None
    mapping: dict[ProductCategory, str] = {
        ProductCategory.FISH_HOT: "рыба",
        ProductCategory.FISH_COLD: "рыба",
        ProductCategory.FISH_ELECTRO: "рыба",
        ProductCategory.MEAT: "мясо",
        ProductCategory.POULTRY: "птица",
        ProductCategory.SAUSAGE_SEMI_SMOKED: "колбаса",
        ProductCategory.SAUSAGE_RAW_SMOKED: "колбаса",
        ProductCategory.SAUSAGE_BOILD: "колбаса",
        ProductCategory.SAUSAGE_SALAMI: "колбаса",
        ProductCategory.CHEESE: "сыр",
        ProductCategory.BACON: "сало",
        ProductCategory.SNACKS: "снеки",
        ProductCategory.OTHER: "рыба",
    }
    return mapping.get(cat, None)


def _smoke_type_key(chamber: Chamber | None) -> str:
    if chamber is None:
        return "горячее"
    return {
        ChamberType.HOT: "горячее",
        ChamberType.COLD: "холодное",
        ChamberType.ELECTRO: "электро",
        ChamberType.UNIVERSAL: "горячее",
        ChamberType.SEMI_HOT: "горячее",
    }.get(chamber.type, "горячее")


@router.post(
    "/preview",
    response_model=RecipeCalcResponse,
    summary="Предварительный расчёт техкарты",
)
async def calc_preview(
    body: CalcPreviewRequest,
    db: DBSession,
    _user: CurrentUser,
) -> RecipeCalcResponse:
    """Рассчитать yield, БЖУ, себестоимость по произвольным параметрам."""
    # Load ingredients
    ings_for_calc: list[IngredientForCalc] = []
    for entry in body.ingredients:
        ing = await db.get(Ingredient, entry.ingredient_id)
        if ing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ingredient {entry.ingredient_id} not found")
        mass_kg = entry.mass_kg or (entry.mass_g / 1000.0)
        if mass_kg > 0:
            ings_for_calc.append(IngredientForCalc(
                id=ing.id, name=ing.name,
                protein_per_100g=ing.protein_per_100g,
                fat_per_100g=ing.fat_per_100g,
                carbs_per_100g=ing.carbs_per_100g,
                kcal_per_100g=ing.kcal_per_100g,
                price_per_kg=ing.price_per_kg,
                mass_kg=mass_kg,
            ))

    program = [p.model_dump() for p in body.program]

    result = calculate_recipe(
        ingredients=ings_for_calc,
        program=program,
        brine_method=body.brine_method,
    )

    return RecipeCalcResponse(
        recipe_id=0,
        recipe_version_id=0,
        total_mass_kg=result.total_mass_kg,
        finished_mass_kg=result.finished_mass_kg,
        losses_percent=result.losses_percent,
        cost_per_kg_raw=result.cost_per_kg_raw,
        cost_per_kg_finished=result.cost_per_kg_finished,
        total_cost=result.total_cost,
        bju_per_100g=result.bju_per_100g.__dict__,
        program={
            "total_duration_min": result.program.total_duration_min,
            "phases_count": result.program.phases_count,
            "phases_summary": result.program.phases_summary,
        },
        breakdown=result.breakdown,
    )


@router.get(
    "/presets",
    summary="Рекомендованные режимы копчения",
)
async def calc_presets(
    db: DBSession,
    _user: CurrentUser,
    product_id: Annotated[int | None, Query()] = None,
    chamber_id: Annotated[int | None, Query()] = None,
) -> dict:
    """Вернуть рекомендованную программу копчения для продукта и камеры."""
    product = None
    chamber = None
    if product_id:
        product = await db.get(Product, product_id)
    if chamber_id:
        chamber = await db.get(Chamber, chamber_id)

    # Try to find matching preset
    if product and chamber:
        pcat = _product_category_key(product.category)
        stype = _smoke_type_key(chamber)
        key = f"{pcat}_{stype}" if pcat else None
        if key and key in DEFAULT_PROGRAM_PRESETS:
            return {
                "preset_key": key,
                "product_name": product.name,
                "chamber_model": chamber.model,
                "recommended_program": DEFAULT_PROGRAM_PRESETS[key]["phases"],
                "warning": None,
            }

    # Fallback: return all presets for the product category
    if product:
        pcat = _product_category_key(product.category)
        if pcat:
            relevant = {k: v for k, v in DEFAULT_PROGRAM_PRESETS.items() if k.startswith(pcat)}
            if relevant:
                return {
                    "preset_key": list(relevant.keys())[0],
                    "product_name": product.name,
                    "chamber_model": chamber.model if chamber else None,
                    "recommended_program": list(relevant.values())[0]["phases"],
                    "warning": "Камера не учтена — показан базовый режим для продукта",
                }

    # Default fallback
    return {
        "preset_key": "универсальное",
        "product_name": product.name if product else None,
        "chamber_model": chamber.model if chamber else None,
        "recommended_program": DEFAULT_PROGRAM_PRESETS["рыба_горячее"]["phases"],
        "warning": "Не удалось подобрать точный режим — показан базовый режим горячего копчения рыбы",
    }
