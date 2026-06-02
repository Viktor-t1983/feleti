"""Сервис расчёта характеристик рецепта: БЖУ, себестоимость, yield, время.

Использует чистые функции: на вход — данные (RecipeVersion + связанные
Ingredient и Brine), на выход — структурированный результат. Без обращений к БД,
без побочных эффектов. Это упрощает юнит-тестирование.

Формат ingredients в RecipeVersion:
    [
        {"ingredient_id": 1, "mass_kg": 5.0},
        {"ingredient_id": 2, "mass_g": 250.0, "name": "Перец чёрный"},  # опц.
    ]
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


# Стандартные (отраслевые) коэффициенты потерь при копчении по типу копчения.
# hot/cold/electro/semi_hot/universal — по умолчанию используется в расчёте yield.
DEFAULT_LOSSES_PERCENT: dict[str, float] = {
    "горячее": 32.0,        # колбасы в/к, мясо, птица: ужарка + варка
    "полугорячее": 25.0,    # сосиски, сардельки
    "холодное": 12.0,       # рыба, мясо х/к: только подсушка
    "электро": 8.0,         # минимум потерь (быстрая обработка)
    "универсальное": 25.0,  # среднее между горячим и холодным
    "неизвестно": 25.0,
}

# Потери при посоле (поглощение соли, выравнивание влаги).
SALT_LOSS_PERCENT: dict[str, float] = {
    "сухой": 4.0,
    "мокрый": 2.0,
    "шприцевание": 1.0,
    "комбинированный": 3.0,
    "смешанный": 3.0,
}


@dataclass(frozen=True)
class IngredientForCalc:
    """Минимальный набор полей ингредиента, нужный для расчёта."""

    id: int
    name: str
    protein_per_100g: float
    fat_per_100g: float
    carbs_per_100g: float
    kcal_per_100g: float
    price_per_kg: float
    mass_kg: float          # масса в рецепте (в кг)


@dataclass(frozen=True)
class BJU:
    """Белки/Жиры/Углеводы и калорийность на 100 г готового продукта."""

    protein: float
    fat: float
    carbs: float
    kcal: float


@dataclass(frozen=True)
class ProgramStats:
    """Статистика по программе (фазам копчения)."""

    total_duration_min: float
    phases_count: int
    phases_summary: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class RecipeCalcResult:
    """Итог расчёта рецепта."""

    total_mass_kg: float
    finished_mass_kg: float
    losses_percent: float
    cost_per_kg_raw: float
    cost_per_kg_finished: float
    total_cost: float
    bju_per_100g: BJU
    program: ProgramStats
    breakdown: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def _mass_from_entry(entry: dict[str, Any]) -> float:
    """Извлечь массу в кг из записи ингредиента в рецепте."""
    if "mass_kg" in entry and entry["mass_kg"] is not None:
        return float(entry["mass_kg"])
    if "mass_g" in entry and entry["mass_g"] is not None:
        return float(entry["mass_g"]) / 1000.0
    if "percent" in entry and entry["percent"] is not None:
        # percent — доля от общей массы фарша (например, соль 2% = 0.02).
        # Для абсолютного расчёта требуется total_mass_kg снаружи.
        # Здесь трактуем как 1 кг по умолчанию — недостаточно, помечаем 0.
        return 0.0
    return 0.0


def _percent_entries_with_total(
    entries: Iterable[dict[str, Any]], total_mass_kg: float
) -> list[float]:
    """Если entries в % от общей массы — перевести в кг (по total_mass_kg)."""
    out: list[float] = []
    for e in entries:
        if "percent" in e and e["percent"] is not None and "mass_kg" not in e and "mass_g" not in e:
            out.append(float(e["percent"]) / 100.0 * total_mass_kg)
        else:
            out.append(0.0)
    return out


def _infer_smoke_type(program: list[dict[str, Any]]) -> str:
    """Грубое определение типа копчения по фазам (для коэф. потерь)."""
    if not program:
        return "неизвестно"
    temps = [float(p.get("t_chamber") or 0.0) for p in program if p.get("t_chamber")]
    if not temps:
        return "неизвестно"
    avg = sum(temps) / len(temps)
    max_t = max(temps)
    electro = any((p.get("electro_voltage_kv") or 0) > 0 for p in program)
    if electro:
        return "электро"
    if max_t < 30:
        return "холодное"
    if 30 <= avg < 60:
        return "полугорячее"
    if avg >= 60:
        return "горячее"
    return "неизвестно"


def compute_total_duration_min(program: list[dict[str, Any]]) -> float:
    """Сумма длительностей всех фаз в минутах."""
    return sum(float(p.get("duration_min") or 0) for p in program)


def compute_program_stats(program: list[dict[str, Any]]) -> ProgramStats:
    """Полная статистика по программе."""
    summary: list[dict[str, Any]] = []
    for p in program:
        summary.append(
            {
                "index": p.get("index") or p.get("phase_index"),
                "name": p.get("name") or p.get("phase") or "",
                "duration_min": float(p.get("duration_min") or 0),
                "t_chamber": p.get("t_chamber"),
                "t_product": p.get("t_product"),
                "smoke": p.get("smoke", "none"),
                "electro_voltage_kv": p.get("electro_voltage_kv", 0),
            }
        )
    return ProgramStats(
        total_duration_min=compute_total_duration_min(program),
        phases_count=len(program),
        phases_summary=summary,
    )


def compute_bju(ingredients: list[IngredientForCalc]) -> BJU:
    """БЖУ готового продукта (на 100 г) с учётом потерь массы.

    По простой модели: суммируем БЖУ всех ингредиентов и нормируем на total_mass_kg.
    Это даёт БЖУ «сырья». Для точного БЖУ готового продукта нужно знать потери
    конкретных фракций (жир вытапливается, белок частично уходит в бульон) —
    упрощённо считаем, что БЖУ готового = БЖУ сырья с поправкой на потерю влаги.
    Здесь возвращаем БЖУ сырья (для точного — нужна лаборатория, не калькулятор).
    """
    if not ingredients:
        return BJU(0, 0, 0, 0)
    total_mass = sum(i.mass_kg for i in ingredients)
    if total_mass <= 0:
        return BJU(0, 0, 0, 0)
    protein = sum(i.protein_per_100g * (i.mass_kg * 1000) / 100 for i in ingredients)
    fat = sum(i.fat_per_100g * (i.mass_kg * 1000) / 100 for i in ingredients)
    carbs = sum(i.carbs_per_100g * (i.mass_kg * 1000) / 100 for i in ingredients)
    kcal = sum(i.kcal_per_100g * (i.mass_kg * 1000) / 100 for i in ingredients)
    return BJU(
        protein=round(protein / (total_mass * 10), 2),    # г на 100 г
        fat=round(fat / (total_mass * 10), 2),
        carbs=round(carbs / (total_mass * 10), 2),
        kcal=round(kcal / (total_mass * 10), 1),
    )


def compute_cost(ingredients: list[IngredientForCalc]) -> tuple[float, float]:
    """Возвращает (total_cost, cost_per_kg_raw)."""
    total = sum(i.price_per_kg * i.mass_kg for i in ingredients)
    mass = sum(i.mass_kg for i in ingredients)
    if mass <= 0:
        return total, 0.0
    return round(total, 2), round(total / mass, 2)


def compute_yield(
    ingredients: list[IngredientForCalc],
    program: list[dict[str, Any]],
    brine_method: str | None = None,
) -> tuple[float, float, float]:
    """Возвращает (raw_mass_kg, finished_mass_kg, losses_percent).

    finished = raw * (1 - losses/100)
    losses = копчение (по типу) + посол (если задан).
    """
    raw = sum(i.mass_kg for i in ingredients)
    if raw <= 0:
        return 0.0, 0.0, 0.0
    smoke_type = _infer_smoke_type(program)
    smoke_loss = DEFAULT_LOSSES_PERCENT.get(smoke_type, 25.0)
    salt_loss = SALT_LOSS_PERCENT.get(brine_method, 0.0) if brine_method else 0.0
    total_loss_pct = min(smoke_loss + salt_loss, 60.0)  # защита от абсурда
    finished = raw * (1.0 - total_loss_pct / 100.0)
    return round(raw, 3), round(finished, 3), round(total_loss_pct, 1)


def calculate_recipe(
    ingredients: list[IngredientForCalc],
    program: list[dict[str, Any]],
    brine_method: str | None = None,
) -> RecipeCalcResult:
    """Главная точка входа: посчитать всё, что можно, по рецепту."""
    raw, finished, losses = compute_yield(ingredients, program, brine_method)
    total_cost, cost_per_kg_raw = compute_cost(ingredients)
    cost_per_kg_finished = round(total_cost / finished, 2) if finished > 0 else 0.0
    bju = compute_bju(ingredients)
    stats = compute_program_stats(program)
    breakdown: list[dict[str, Any]] = []
    for ing in ingredients:
        breakdown.append(
            {
                "ingredient_id": ing.id,
                "name": ing.name,
                "mass_kg": ing.mass_kg,
                "cost": round(ing.price_per_kg * ing.mass_kg, 2),
                "protein": ing.protein_per_100g,
                "fat": ing.fat_per_100g,
                "carbs": ing.carbs_per_100g,
                "kcal": ing.kcal_per_100g,
            }
        )
    return RecipeCalcResult(
        total_mass_kg=raw,
        finished_mass_kg=finished,
        losses_percent=losses,
        cost_per_kg_raw=cost_per_kg_raw,
        cost_per_kg_finished=cost_per_kg_finished,
        total_cost=total_cost,
        bju_per_100g=bju,
        program=stats,
        breakdown=breakdown,
    )


__all__ = [
    "IngredientForCalc",
    "BJU",
    "ProgramStats",
    "RecipeCalcResult",
    "calculate_recipe",
    "compute_bju",
    "compute_cost",
    "compute_yield",
    "compute_total_duration_min",
    "compute_program_stats",
    "DEFAULT_LOSSES_PERCENT",
    "SALT_LOSS_PERCENT",
]
