"""CRUD ингредиентов."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.ingredient import Ingredient
from app.schemas.common import Page, PageParams
from app.schemas.ingredient import IngredientCreate, IngredientRead, IngredientUpdate
from app.services import audit

router = APIRouter()


@router.get("", response_model=Page[IngredientRead], summary="Список ингредиентов")
async def list_ingredients(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()] = PageParams(),
    type: Annotated[str | None, Query(description="IngredientType")] = None,
    wood_species: Annotated[str | None, Query(description="Для type=wood")] = None,
) -> Page[IngredientRead]:
    stmt = select(Ingredient)
    count_stmt = select(func.count()).select_from(Ingredient)
    if type is not None:
        stmt = stmt.where(Ingredient.type == type)
        count_stmt = count_stmt.where(Ingredient.type == type)
    if wood_species is not None:
        stmt = stmt.where(Ingredient.wood_species == wood_species)
        count_stmt = count_stmt.where(Ingredient.wood_species == wood_species)
    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Ingredient.type.asc(), Ingredient.id.asc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[IngredientRead](
        items=[IngredientRead.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get("/{ingredient_id}", response_model=IngredientRead, summary="Ингредиент по ID")
async def get_ingredient(
    ingredient_id: int, db: DBSession, _user: CurrentUser
) -> IngredientRead:
    obj = await db.scalar(select(Ingredient).where(Ingredient.id == ingredient_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ингредиент не найден"
        )
    return IngredientRead.model_validate(obj)


@router.post(
    "",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать ингредиент",
)
async def create_ingredient(
    payload: IngredientCreate, db: DBSession, user: CurrentUser
) -> IngredientRead:
    obj = Ingredient(**payload.model_dump())
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ингредиент с таким slug уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="ingredient",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return IngredientRead.model_validate(obj)


@router.patch(
    "/{ingredient_id}", response_model=IngredientRead, summary="Обновить ингредиент"
)
async def update_ingredient(
    ingredient_id: int,
    payload: IngredientUpdate,
    db: DBSession,
    user: CurrentUser,
) -> IngredientRead:
    obj = await db.scalar(select(Ingredient).where(Ingredient.id == ingredient_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ингредиент не найден"
        )
    data = payload.model_dump(exclude_unset=True)
    before = {c.name: getattr(obj, c.name) for c in Ingredient.__table__.columns}
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="ingredient",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return IngredientRead.model_validate(obj)


@router.delete(
    "/{ingredient_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить ингредиент",
)
async def delete_ingredient(
    ingredient_id: int, db: DBSession, user: CurrentUser
) -> None:
    obj = await db.scalar(select(Ingredient).where(Ingredient.id == ingredient_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ингредиент не найден"
        )
    before = {"id": obj.id, "name": obj.name, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="ingredient",
        entity_id=ingredient_id,
        before=before,
    )
    await db.commit()
