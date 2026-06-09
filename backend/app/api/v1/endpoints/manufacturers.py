"""CRUD производителей коптильного оборудования."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentAdmin, CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.manufacturer import Manufacturer
from app.schemas.common import Page, PageParams
from app.schemas.manufacturer import ManufacturerCreate, ManufacturerRead, ManufacturerUpdate
from app.services import audit

router = APIRouter()


@router.get("", response_model=Page[ManufacturerRead], summary="Список производителей")
async def list_manufacturers(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()] = PageParams(),
    is_our_brand: Annotated[bool | None, Query()] = None,
    is_competitor: Annotated[bool | None, Query()] = None,
) -> Page[ManufacturerRead]:
    stmt = select(Manufacturer)
    count_stmt = select(func.count()).select_from(Manufacturer)
    if is_our_brand is not None:
        stmt = stmt.where(Manufacturer.is_our_brand == is_our_brand)
        count_stmt = count_stmt.where(Manufacturer.is_our_brand == is_our_brand)
    if is_competitor is not None:
        stmt = stmt.where(Manufacturer.is_competitor == is_competitor)
        count_stmt = count_stmt.where(Manufacturer.is_competitor == is_competitor)

    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Manufacturer.sort_order.asc(), Manufacturer.id.asc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[ManufacturerRead](
        items=[ManufacturerRead.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get("/{manufacturer_id}", response_model=ManufacturerRead, summary="Производитель по ID")
async def get_manufacturer(
    manufacturer_id: int, db: DBSession, _user: CurrentUser
) -> ManufacturerRead:
    obj = await db.scalar(select(Manufacturer).where(Manufacturer.id == manufacturer_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Производитель не найден"
        )
    return ManufacturerRead.model_validate(obj)


@router.post(
    "",
    response_model=ManufacturerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать производителя",
)
async def create_manufacturer(
    payload: ManufacturerCreate, db: DBSession, user: CurrentAdmin
) -> ManufacturerRead:
    obj = Manufacturer(**payload.model_dump())
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Производитель с таким slug уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="manufacturer",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return ManufacturerRead.model_validate(obj)


@router.patch(
    "/{manufacturer_id}", response_model=ManufacturerRead, summary="Обновить производителя"
)
async def update_manufacturer(
    manufacturer_id: int,
    payload: ManufacturerUpdate,
    db: DBSession,
    user: CurrentAdmin,
) -> ManufacturerRead:
    obj = await db.scalar(select(Manufacturer).where(Manufacturer.id == manufacturer_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Производитель не найден"
        )
    before = {
        c.name: getattr(obj, c.name) for c in Manufacturer.__table__.columns
    }
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="manufacturer",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return ManufacturerRead.model_validate(obj)


@router.delete(
    "/{manufacturer_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить производителя",
)
async def delete_manufacturer(
    manufacturer_id: int, db: DBSession, user: CurrentAdmin
) -> None:
    obj = await db.scalar(select(Manufacturer).where(Manufacturer.id == manufacturer_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Производитель не найден"
        )
    before = {"id": obj.id, "name": obj.name, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="manufacturer",
        entity_id=manufacturer_id,
        before=before,
    )
    await db.commit()
