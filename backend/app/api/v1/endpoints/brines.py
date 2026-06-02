"""CRUD посолов (brine)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.brine import Brine
from app.schemas.brine import BrineCreate, BrineRead, BrineUpdate
from app.schemas.common import Page, PageParams
from app.services import audit

router = APIRouter()


@router.get("", response_model=Page[BrineRead], summary="Список посолов")
async def list_brines(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()],
    method: Annotated[str | None, Query()] = None,
) -> Page[BrineRead]:
    stmt = select(Brine)
    count_stmt = select(func.count()).select_from(Brine)
    if method is not None:
        stmt = stmt.where(Brine.method == method)
        count_stmt = count_stmt.where(Brine.method == method)
    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Brine.method.asc(), Brine.id.asc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[BrineRead](
        items=[BrineRead.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get("/{brine_id}", response_model=BrineRead, summary="Посол по ID")
async def get_brine(brine_id: int, db: DBSession, _user: CurrentUser) -> BrineRead:
    obj = await db.scalar(select(Brine).where(Brine.id == brine_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Посол не найден"
        )
    return BrineRead.model_validate(obj)


@router.post(
    "",
    response_model=BrineRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать посол",
)
async def create_brine(
    payload: BrineCreate, db: DBSession, user: CurrentUser
) -> BrineRead:
    obj = Brine(**payload.model_dump())
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Посол с таким slug уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="brine",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return BrineRead.model_validate(obj)


@router.patch("/{brine_id}", response_model=BrineRead, summary="Обновить посол")
async def update_brine(
    brine_id: int, payload: BrineUpdate, db: DBSession, user: CurrentUser
) -> BrineRead:
    obj = await db.scalar(select(Brine).where(Brine.id == brine_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Посол не найден"
        )
    data = payload.model_dump(exclude_unset=True)
    before = {c.name: getattr(obj, c.name) for c in Brine.__table__.columns}
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="brine",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return BrineRead.model_validate(obj)


@router.delete(
    "/{brine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить посол",
)
async def delete_brine(brine_id: int, db: DBSession, user: CurrentUser) -> None:
    obj = await db.scalar(select(Brine).where(Brine.id == brine_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Посол не найден"
        )
    before = {"id": obj.id, "name": obj.name, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="brine",
        entity_id=brine_id,
        before=before,
    )
    await db.commit()
