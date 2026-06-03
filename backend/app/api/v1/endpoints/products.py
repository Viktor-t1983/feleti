"""CRUD продуктов (изделий)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.product import Product
from app.schemas.common import Page, PageParams
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import audit

router = APIRouter()


@router.get("", response_model=Page[ProductRead], summary="Список продуктов")
async def list_products(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()],
    category: Annotated[str | None, Query()] = None,
) -> Page[ProductRead]:
    stmt = select(Product)
    count_stmt = select(func.count()).select_from(Product)
    if category is not None:
        stmt = stmt.where(Product.category == category)
        count_stmt = count_stmt.where(Product.category == category)
    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Product.id.asc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[ProductRead](
        items=[ProductRead.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get("/{product_id}", response_model=ProductRead, summary="Продукт по ID")
async def get_product(product_id: int, db: DBSession, _user: CurrentUser) -> ProductRead:
    obj = await db.scalar(select(Product).where(Product.id == product_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден"
        )
    return ProductRead.model_validate(obj)


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать продукт",
)
async def create_product(
    payload: ProductCreate, db: DBSession, user: CurrentUser
) -> ProductRead:
    data = payload.model_dump()
    data["images"] = [str(u) for u in data.get("images", [])]
    obj = Product(**data)
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Продукт с таким slug уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="product",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return ProductRead.model_validate(obj)


@router.patch("/{product_id}", response_model=ProductRead, summary="Обновить продукт")
async def update_product(
    product_id: int, payload: ProductUpdate, db: DBSession, user: CurrentUser
) -> ProductRead:
    obj = await db.scalar(select(Product).where(Product.id == product_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден"
        )
    data = payload.model_dump(exclude_unset=True)
    if "images" in data and data["images"] is not None:
        data["images"] = [str(u) for u in data["images"]]
    before = {c.name: getattr(obj, c.name) for c in Product.__table__.columns}
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="product",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return ProductRead.model_validate(obj)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить продукт",
)
async def delete_product(product_id: int, db: DBSession, user: CurrentUser) -> None:
    obj = await db.scalar(select(Product).where(Product.id == product_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден"
        )
    before = {"id": obj.id, "name": obj.name, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="product",
        entity_id=product_id,
        before=before,
    )
    await db.commit()
