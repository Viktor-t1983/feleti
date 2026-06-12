"""Экспорт технологической карты (PDF)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession
from app.models.product import Product
from app.models.recipe import Recipe, RecipeVersion
from app.services.recipe_calc import IngredientForCalc, calculate_recipe
from app.services.tech_card_pdf import build_tech_card

router = APIRouter()


@router.get(
    "/recipes/{recipe_id}/tech-card",
    summary="Экспорт техкарты рецепта (PDF)",
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF технологической карты",
        },
        404: {"description": "Рецепт не найден"},
    },
)
async def export_tech_card(
    recipe_id: int,
    db: DBSession,
    _user: CurrentUser,
) -> Response:
    """Сгенерировать PDF технологической карты для рецепта."""
    recipe = await db.scalar(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(selectinload(Recipe.current_version))
    )
    if not recipe:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден")

    product = await db.get(Product, recipe.product_id)

    version: RecipeVersion | None = recipe.current_version
    calc_result = None
    ingredients_data = []
    program_data = []

    if version:
        program_data = version.program

        # Load ingredients for calculation
        ings_for_calc = []
        for entry in version.ingredients:
            from app.models.ingredient import Ingredient
            ing_id = entry.get("ingredient_id")
            mass_kg = entry.get("mass_kg") or (entry.get("mass_g", 0) / 1000.0)
            if ing_id and mass_kg:
                ing = await db.get(Ingredient, ing_id)
                if ing:
                    ings_for_calc.append(IngredientForCalc(
                        id=ing.id, name=ing.name,
                        protein_per_100g=ing.protein_per_100g,
                        fat_per_100g=ing.fat_per_100g,
                        carbs_per_100g=ing.carbs_per_100g,
                        kcal_per_100g=ing.kcal_per_100g,
                        price_per_kg=ing.price_per_kg,
                        mass_kg=mass_kg,
                    ))

        if ings_for_calc:
            calc_result = calculate_recipe(
                ings_for_calc,
                version.program,
                brine_method=version.brine.get("method") if version.brine else None,
            )
            ingredients_data = calc_result.breakdown

    # Build data for PDF
    data = {
        "product_name": product.name if product else recipe.name,
        "recipe_number": f"РЦ-{recipe.id:04d}",
        "meta": {
            "product_name": product.name if product else recipe.name,
            "gost": version.gost if version else "",
            "recipe_number": f"РЦ-{recipe.id:04d}",
            "date": recipe.updated_at.strftime("%d.%m.%Y") if recipe.updated_at else "",
            "developer": "FELETI-SMOK",
        },
        "ingredients": ingredients_data,
        "program": program_data,
        "calculation": {
            "total_mass_kg": calc_result.total_mass_kg if calc_result else None,
            "finished_mass_kg": calc_result.finished_mass_kg if calc_result else None,
            "losses_percent": calc_result.losses_percent if calc_result else None,
            "cost_per_kg_raw": calc_result.cost_per_kg_raw if calc_result else None,
            "cost_per_kg_finished": calc_result.cost_per_kg_finished if calc_result else None,
            "total_cost": calc_result.total_cost if calc_result else None,
            "bju_per_100g": {
                "protein": calc_result.bju_per_100g.protein,
                "fat": calc_result.bju_per_100g.fat,
                "carbs": calc_result.bju_per_100g.carbs,
                "kcal": calc_result.bju_per_100g.kcal,
            } if calc_result else None,
        },
        "storage": {
            "shelf_life_days": product.shelf_life_days if product else None,
            "storage_temp": f"{product.storage_temp_min}…{product.storage_temp_max}" if product and (product.storage_temp_min or product.storage_temp_max) else None,
            "storage_humidity": f"{product.storage_humidity_min}…{product.storage_humidity_max}" if product and (product.storage_humidity_min or product.storage_humidity_max) else None,
        } if product else {},
        "notes": version.notes if version else "",
    }

    pdf_bytes = build_tech_card(data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tech-card-{recipe.slug}.pdf"',
        },
    )
