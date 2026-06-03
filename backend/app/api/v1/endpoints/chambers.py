"""CRUD коптильных камер."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession
from app.drivers import list_drivers
from app.models.audit import AuditAction
from app.models.chamber import Chamber
from app.models.manufacturer import Manufacturer
from app.schemas.chamber import ChamberCreate, ChamberRead, ChamberUpdate
from app.schemas.common import Page, PageParams
from app.services import audit

router = APIRouter()


def _to_read(obj: Chamber) -> ChamberRead:
    data = ChamberRead.model_validate(obj)
    if obj.manufacturer is not None:
        data.manufacturer_name = obj.manufacturer.name
    return data


@router.get("", response_model=Page[ChamberRead], summary="Список камер")
async def list_chambers(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()],
    manufacturer_id: Annotated[int | None, Query()] = None,
    type: Annotated[str | None, Query(description="ChamberType")] = None,
    supports_electro: Annotated[bool | None, Query()] = None,
    supports_cold_smoke: Annotated[bool | None, Query()] = None,
    verified: Annotated[bool | None, Query()] = None,
) -> Page[ChamberRead]:
    stmt = select(Chamber).options(selectinload(Chamber.manufacturer))
    count_stmt = select(func.count()).select_from(Chamber)
    if manufacturer_id is not None:
        stmt = stmt.where(Chamber.manufacturer_id == manufacturer_id)
        count_stmt = count_stmt.where(Chamber.manufacturer_id == manufacturer_id)
    if type is not None:
        stmt = stmt.where(Chamber.type == type)
        count_stmt = count_stmt.where(Chamber.type == type)
    if supports_electro is not None:
        stmt = stmt.where(Chamber.supports_electro == supports_electro)
        count_stmt = count_stmt.where(Chamber.supports_electro == supports_electro)
    if supports_cold_smoke is not None:
        stmt = stmt.where(Chamber.supports_cold_smoke == supports_cold_smoke)
        count_stmt = count_stmt.where(Chamber.supports_cold_smoke == supports_cold_smoke)
    if verified is not None:
        stmt = stmt.where(Chamber.verified == verified)
        count_stmt = count_stmt.where(Chamber.verified == verified)

    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Chamber.id.asc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[ChamberRead](
        items=[_to_read(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get("/drivers", summary="Список доступных драйверов")
async def drivers_list(_user: CurrentUser) -> dict:
    return {"drivers": list_drivers()}


@router.get("/{chamber_id}", response_model=ChamberRead, summary="Камера по ID")
async def get_chamber(chamber_id: int, db: DBSession, _user: CurrentUser) -> ChamberRead:
    obj = await db.scalar(
        select(Chamber).options(selectinload(Chamber.manufacturer)).where(Chamber.id == chamber_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Камера не найдена"
        )
    return _to_read(obj)


@router.post(
    "",
    response_model=ChamberRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать камеру",
)
async def create_chamber(
    payload: ChamberCreate, db: DBSession, user: CurrentUser
) -> ChamberRead:
    if payload.driver_class not in list_drivers():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестный driver_class: {payload.driver_class}. Доступные: {list_drivers()}",
        )
    manuf = await db.scalar(
        select(Manufacturer).where(Manufacturer.id == payload.manufacturer_id)
    )
    if manuf is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Производитель не найден"
        )
    data = payload.model_dump()
    data["images"] = [str(u) for u in data.get("images", [])]
    data["source_url"] = str(data["source_url"]) if data.get("source_url") else None
    obj = Chamber(**data)
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Камера с таким slug уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="chamber",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return _to_read(obj)


@router.patch("/{chamber_id}", response_model=ChamberRead, summary="Обновить камеру")
async def update_chamber(
    chamber_id: int, payload: ChamberUpdate, db: DBSession, user: CurrentUser
) -> ChamberRead:
    obj = await db.scalar(
        select(Chamber).options(selectinload(Chamber.manufacturer)).where(Chamber.id == chamber_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Камера не найдена"
        )
    data = payload.model_dump(exclude_unset=True)
    if "driver_class" in data and data["driver_class"] not in list_drivers():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Неизвестный driver_class: {data['driver_class']}",
        )
    if "images" in data and data["images"] is not None:
        data["images"] = [str(u) for u in data["images"]]
    if "source_url" in data and data["source_url"] is not None:
        data["source_url"] = str(data["source_url"])
    before = {
        c.name: getattr(obj, c.name) for c in Chamber.__table__.columns
    }
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="chamber",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return _to_read(obj)


@router.delete(
    "/{chamber_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить камеру",
)
async def delete_chamber(chamber_id: int, db: DBSession, user: CurrentUser) -> None:
    obj = await db.scalar(select(Chamber).where(Chamber.id == chamber_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Камера не найдена"
        )
    before = {"id": obj.id, "model": obj.model, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="chamber",
        entity_id=chamber_id,
        before=before,
    )
    await db.commit()
