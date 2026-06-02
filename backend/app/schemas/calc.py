"""Pydantic-схемы для расчёта рецепта (preview)."""

from __future__ import annotations

from app.schemas.common import APIModel


class BJUSchema(APIModel):
    protein: float
    fat: float
    carbs: float
    kcal: float


class ProgramPhaseSummary(APIModel):
    index: int | None = None
    name: str = ""
    duration_min: float
    t_chamber: float | None = None
    t_product: float | None = None
    smoke: str = "none"
    electro_voltage_kv: float = 0.0


class ProgramStatsSchema(APIModel):
    total_duration_min: float
    phases_count: int
    phases_summary: list[ProgramPhaseSummary]


class IngredientBreakdown(APIModel):
    ingredient_id: int
    name: str
    mass_kg: float
    cost: float
    protein: float
    fat: float
    carbs: float
    kcal: float


class RecipeCalcResponse(APIModel):
    recipe_id: int
    recipe_version_id: int
    total_mass_kg: float
    finished_mass_kg: float
    losses_percent: float
    cost_per_kg_raw: float
    cost_per_kg_finished: float
    total_cost: float
    bju_per_100g: BJUSchema
    program: ProgramStatsSchema
    breakdown: list[IngredientBreakdown]


__all__ = ["RecipeCalcResponse"]
