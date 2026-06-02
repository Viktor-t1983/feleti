"""CRUD рецептов: Recipe + RecipeVersion + workflow (заглушка)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.ingredient import Ingredient
from app.models.recipe import Recipe, RecipeStatus, RecipeVersion
from app.schemas.calc import RecipeCalcResponse
from app.schemas.common import Page, PageParams
from app.schemas.recipe import (
    RecipeCreate,
    RecipeRead,
    RecipeUpdate,
    RecipeVersionCreate,
    RecipeVersionRead,
)
from app.services import audit
from app.services.recipe_calc import IngredientForCalc, calculate_recipe

router = APIRouter()


@router.get("", response_model=Page[RecipeRead], summary="Список рецептов")
async def list_recipes(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()],
    product_id: Annotated[int | None, Query()] = None,
    status_: Annotated[str | None, Query(alias="status")] = None,
) -> Page[RecipeRead]:
    stmt = select(Recipe)
    count_stmt = select(func.count()).select_from(Recipe)
    if product_id is not None:
        stmt = stmt.where(Recipe.product_id == product_id)
        count_stmt = count_stmt.where(Recipe.product_id == product_id)
    if status_ is not None:
        stmt = stmt.where(Recipe.status == status_)
        count_stmt = count_stmt.where(Recipe.status == status_)
    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Recipe.id.asc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[RecipeRead](
        items=[RecipeRead.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get("/{recipe_id}", response_model=RecipeRead, summary="Рецепт по ID")
async def get_recipe(recipe_id: int, db: DBSession, _user: CurrentUser) -> RecipeRead:
    obj = await db.scalar(
        select(Recipe)
        .options(selectinload(Recipe.current_version))
        .where(Recipe.id == recipe_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден"
        )
    return RecipeRead.model_validate(obj)


@router.post(
    "",
    response_model=RecipeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать рецепт (с первой версией, если передана)",
)
async def create_recipe(
    payload: RecipeCreate, db: DBSession, user: CurrentUser
) -> RecipeRead:
    obj = Recipe(
        product_id=payload.product_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        tags=payload.tags,
        status=RecipeStatus.DRAFT,
        created_by_id=user.id,
    )
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Рецепт с таким slug уже существует",
        ) from e

    if payload.initial_version is not None:
        version = RecipeVersion(
            recipe_id=obj.id,
            version_number=1,
            program=payload.initial_version.program,
            brine=payload.initial_version.brine,
            ingredients=payload.initial_version.ingredients,
            yield_percent=payload.initial_version.yield_percent,
            losses_percent=payload.initial_version.losses_percent,
            bju_per_100g=payload.initial_version.bju_per_100g,
            cost_per_kg=payload.initial_version.cost_per_kg,
            notes=payload.initial_version.notes,
            gost=payload.initial_version.gost,
            source=payload.initial_version.source,
            status=RecipeStatus.DRAFT,
            created_by_id=user.id,
        )
        db.add(version)
        await db.flush()
        obj.current_version_id = version.id
        await db.flush()

    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="recipe",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return RecipeRead.model_validate(obj)


@router.patch("/{recipe_id}", response_model=RecipeRead, summary="Обновить рецепт (метаданные)")
async def update_recipe(
    recipe_id: int, payload: RecipeUpdate, db: DBSession, user: CurrentUser
) -> RecipeRead:
    obj = await db.scalar(select(Recipe).where(Recipe.id == recipe_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден"
        )
    data = payload.model_dump(exclude_unset=True)
    before = {c.name: getattr(obj, c.name) for c in Recipe.__table__.columns}
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="recipe",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return RecipeRead.model_validate(obj)


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить рецепт",
)
async def delete_recipe(recipe_id: int, db: DBSession, user: CurrentUser) -> None:
    obj = await db.scalar(select(Recipe).where(Recipe.id == recipe_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден"
        )
    before = {"id": obj.id, "name": obj.name, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="recipe",
        entity_id=recipe_id,
        before=before,
    )
    await db.commit()


@router.get(
    "/{recipe_id}/versions",
    response_model=list[RecipeVersionRead],
    summary="Список версий рецепта",
)
async def list_versions(
    recipe_id: int, db: DBSession, _user: CurrentUser
) -> list[RecipeVersionRead]:
    rows = (
        await db.scalars(
            select(RecipeVersion)
            .where(RecipeVersion.recipe_id == recipe_id)
            .order_by(RecipeVersion.version_number.desc())
        )
    ).all()
    return [RecipeVersionRead.model_validate(r) for r in rows]


@router.post(
    "/{recipe_id}/versions",
    response_model=RecipeVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новую иммутабельную версию рецепта",
)
async def create_version(
    recipe_id: int,
    payload: RecipeVersionCreate,
    db: DBSession,
    user: CurrentUser,
) -> RecipeVersionRead:
    obj = await db.scalar(select(Recipe).where(Recipe.id == recipe_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден"
        )
    last_v = await db.scalar(
        select(func.max(RecipeVersion.version_number)).where(
            RecipeVersion.recipe_id == recipe_id
        )
    )
    next_number = (last_v or 0) + 1
    version = RecipeVersion(
        recipe_id=recipe_id,
        version_number=next_number,
        parent_version_id=payload.parent_version_id,
        program=payload.program,
        brine=payload.brine,
        ingredients=payload.ingredients,
        yield_percent=payload.yield_percent,
        losses_percent=payload.losses_percent,
        bju_per_100g=payload.bju_per_100g,
        cost_per_kg=payload.cost_per_kg,
        notes=payload.notes,
        gost=payload.gost,
        source=payload.source,
        status=RecipeStatus.DRAFT,
        created_by_id=user.id,
    )
    db.add(version)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="recipe_version",
        entity_id=version.id,
        after={"recipe_id": recipe_id, "version_number": next_number},
    )
    await db.commit()
    await db.refresh(version)
    return RecipeVersionRead.model_validate(version)


async def _calc_for_version(
    db: DBSession, recipe_id: int, version: RecipeVersion
) -> RecipeCalcResponse:
    """Посчитать БЖУ/себестоимость/yield для конкретной версии рецепта."""
    ingredients_raw: list[dict] = version.ingredients or []
    if not ingredients_raw:
        return RecipeCalcResponse(
            recipe_id=recipe_id,
            recipe_version_id=version.id,
            total_mass_kg=0.0,
            finished_mass_kg=0.0,
            losses_percent=0.0,
            cost_per_kg_raw=0.0,
            cost_per_kg_finished=0.0,
            total_cost=0.0,
            bju_per_100g={"protein": 0, "fat": 0, "carbs": 0, "kcal": 0},
            program={
                "total_duration_min": 0.0,
                "phases_count": 0,
                "phases_summary": [],
            },
            breakdown=[],
        )

    # Собираем ID ингредиентов, тянем из БД батчем.
    ingredient_ids: list[int] = []
    for entry in ingredients_raw:
        iid = entry.get("ingredient_id") or entry.get("id")
        if isinstance(iid, int):
            ingredient_ids.append(iid)
    unique_ids = list(set(ingredient_ids))
    rows = (
        await db.scalars(select(Ingredient).where(Ingredient.id.in_(unique_ids)))
    ).all() if unique_ids else []
    by_id: dict[int, Ingredient] = {r.id: r for r in rows}

    parsed: list[IngredientForCalc] = []
    for entry in ingredients_raw:
        iid = entry.get("ingredient_id") or entry.get("id")
        if not isinstance(iid, int) or iid not in by_id:
            continue
        ing = by_id[iid]
        mass_kg = 0.0
        if entry.get("mass_kg") is not None:
            mass_kg = float(entry["mass_kg"])
        elif entry.get("mass_g") is not None:
            mass_kg = float(entry["mass_g"]) / 1000.0
        elif entry.get("percent") is not None:
            # Доля от общей массы — нужно знать total, считаем от суммы остальных mass_kg.
            # Упрощённо: пока 0, обработаем после.
            mass_kg = 0.0
        if mass_kg > 0:
            parsed.append(
                IngredientForCalc(
                    id=ing.id,
                    name=ing.name,
                    protein_per_100g=ing.protein_per_100g,
                    fat_per_100g=ing.fat_per_100g,
                    carbs_per_100g=ing.carbs_per_100g,
                    kcal_per_100g=ing.kcal_per_100g,
                    price_per_kg=ing.price_per_kg,
                    mass_kg=mass_kg,
                )
            )

    brine_method: str | None = None
    if version.brine and isinstance(version.brine, dict):
        brine_method = version.brine.get("method")

    result = calculate_recipe(
        ingredients=parsed,
        program=version.program or [],
        brine_method=brine_method,
    )
    return RecipeCalcResponse(
        recipe_id=recipe_id,
        recipe_version_id=version.id,
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
    "/{recipe_id}/calc",
    response_model=RecipeCalcResponse,
    summary="Расчёт для текущей (current) версии рецепта",
)
async def calc_current_version(
    recipe_id: int, db: DBSession, _user: CurrentUser
) -> RecipeCalcResponse:
    recipe = await db.scalar(
        select(Recipe)
        .options(selectinload(Recipe.current_version))
        .where(Recipe.id == recipe_id)
    )
    if recipe is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Рецепт не найден"
        )
    if recipe.current_version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У рецепта нет current_version_id (создайте первую версию)",
        )
    return await _calc_for_version(db, recipe_id, recipe.current_version)


@router.get(
    "/{recipe_id}/versions/{version_id}/calc",
    response_model=RecipeCalcResponse,
    summary="Расчёт для конкретной версии рецепта",
)
async def calc_version(
    recipe_id: int,
    version_id: int,
    db: DBSession,
    _user: CurrentUser,
) -> RecipeCalcResponse:
    version = await db.scalar(
        select(RecipeVersion).where(
            RecipeVersion.id == version_id,
            RecipeVersion.recipe_id == recipe_id,
        )
    )
    if version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Версия {version_id} рецепта {recipe_id} не найдена",
        )
    return await _calc_for_version(db, recipe_id, version)
