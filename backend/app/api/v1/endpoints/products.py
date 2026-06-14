"""CRUD продуктов (изделий) + Product Profile."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.product import Product
from app.schemas.common import Page, PageParams
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services import audit
from app.services.pagination import paginate
from app.services.product_profile import build_profile_facts

router = APIRouter()


class FactItem(BaseModel):
    object_name: str
    object_type: str
    predicate: str
    article_id: int
    source_text: str | None = None
    confidence: float = 0.0
    params: dict = Field(default_factory=dict)
    inherited_from: str | None = None
    chunk_id: int | None = None


class FactGroup(BaseModel):
    predicate: str
    label: str
    facts: list[FactItem]


class ProductProfile(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    gost: str | None = None
    parent: ProductRead | None = None
    children: list[ProductRead] = []
    fact_groups: list[FactGroup] = []


@router.get(
    "/{product_id}/profile",
    response_model=ProductProfile,
    summary="Product Profile — агрегированные факты",
)
async def product_profile(product_id: int, db: DBSession, _user: CurrentUser) -> ProductProfile:
    obj = await db.scalar(select(Product).where(Product.id == product_id))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден")

    parent: ProductRead | None = None
    if obj.parent_id:
        p = await db.get(Product, obj.parent_id)
        if p:
            parent = ProductRead.model_validate(p)

    children: list[ProductRead] = []
    for c in (await db.scalars(select(Product).where(Product.parent_id == product_id))).all():
        children.append(ProductRead.model_validate(c))

    groups = await build_profile_facts(product_id, db)

    return ProductProfile(
        id=obj.id,
        name=obj.name,
        slug=obj.slug,
        category=obj.category.value if hasattr(obj.category, "value") else str(obj.category),
        gost=obj.gost,
        parent=parent,
        children=children,
        fact_groups=[
            FactGroup.model_validate(g.to_dict()) for g in groups
        ],
    )


@router.get("", response_model=Page[ProductRead], summary="Список продуктов")
async def list_products(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()] = PageParams(),
    category: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> Page[ProductRead]:
    stmt = select(Product)
    if category is not None:
        stmt = stmt.where(Product.category == category)
    if q is not None:
        pattern = f"%{q}%"
        stmt = stmt.where(
            or_(Product.name.ilike(pattern), Product.description.ilike(pattern))
        )
    return await paginate(db, stmt, params, ProductRead, order_by=Product.id.asc())


@router.get("/by-slug/{slug}", response_model=ProductRead, summary="Продукт по slug")
async def get_product_by_slug(slug: str, db: DBSession, _user: CurrentUser) -> ProductRead:
    obj = await db.scalar(select(Product).where(Product.slug == slug))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Продукт не найден"
        )
    return ProductRead.model_validate(obj)


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
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
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
