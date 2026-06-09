"""CRUD конкурентов + онбординг."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.core.deps import CurrentAdmin, CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem
from app.schemas.common import Page
from app.schemas.competitor import (
    CompetitorCreate,
    CompetitorOnboardRequest,
    CompetitorOnboardResponse,
    CompetitorRead,
    CompetitorUpdate,
)
from app.services import audit
from app.services.competitor_onboarder import CompetitorOnboarder

router = APIRouter()


@router.get("", response_model=Page[CompetitorRead], summary="Список конкурентов")
async def list_competitors(
    db: DBSession,
    _user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    is_main: bool | None = Query(None),
    segment: str | None = Query(None),
) -> Page[CompetitorRead]:
    stmt = select(Competitor).options(
        joinedload(Competitor.models),
        joinedload(Competitor.problems),
    )
    count_stmt = select(func.count()).select_from(Competitor)
    if is_main is not None:
        stmt = stmt.where(Competitor.is_main_competitor == is_main)
        count_stmt = count_stmt.where(Competitor.is_main_competitor == is_main)
    if segment:
        stmt = stmt.where(Competitor.segment.ilike(f"%{segment}%"))
        count_stmt = count_stmt.where(Competitor.segment.ilike(f"%{segment}%"))

    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Competitor.is_main_competitor.desc(), Competitor.id.asc())
        .offset((page - 1) * size)
        .limit(size)
    )
    rows = (await db.scalars(stmt)).unique().all()
    pages = (total + size - 1) // size if total else 0
    return Page[CompetitorRead](
        items=[CompetitorRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{competitor_id}", response_model=CompetitorRead, summary="Конкурент по ID")
async def get_competitor(
    competitor_id: int, db: DBSession, _user: CurrentUser
) -> CompetitorRead:
    obj = await db.scalar(
        select(Competitor)
        .where(Competitor.id == competitor_id)
        .options(joinedload(Competitor.models), joinedload(Competitor.problems))
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Конкурент не найден"
        )
    return CompetitorRead.model_validate(obj)


@router.post(
    "",
    response_model=CompetitorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать конкурента",
)
async def create_competitor(
    payload: CompetitorCreate, db: DBSession, user: CurrentAdmin
) -> CompetitorRead:
    data = payload.model_dump()
    obj = Competitor(**data)
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Конкурент с таким slug уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="competitor",
        entity_id=obj.id,
        after=data,
    )
    await db.commit()
    await db.refresh(obj)
    return CompetitorRead.model_validate(obj)


@router.patch("/{competitor_id}", response_model=CompetitorRead, summary="Обновить конкурента")
async def update_competitor(
    competitor_id: int,
    payload: CompetitorUpdate,
    db: DBSession,
    user: CurrentAdmin,
) -> CompetitorRead:
    obj = await db.scalar(
        select(Competitor)
        .where(Competitor.id == competitor_id)
        .options(joinedload(Competitor.models), joinedload(Competitor.problems))
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Конкурент не найден"
        )
    before = {c.name: getattr(obj, c.name) for c in Competitor.__table__.columns}
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="competitor",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return CompetitorRead.model_validate(obj)


@router.post(
    "/onboard",
    response_model=CompetitorOnboardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Запустить онбординг нового конкурента",
)
async def onboard_competitor(
    payload: CompetitorOnboardRequest, db: DBSession, _user: CurrentUser
) -> CompetitorOnboardResponse:
    """URL → разведка → краулинг → сохранение в БД."""
    onboarder = CompetitorOnboarder(db)
    try:
        result = await onboarder.onboard(url=payload.url, name=payload.name)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    finally:
        await onboarder.close()
    return result


@router.delete(
    "/{competitor_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить конкурента",
)
async def delete_competitor(
    competitor_id: int, db: DBSession, user: CurrentAdmin
) -> None:
    obj = await db.scalar(select(Competitor).where(Competitor.id == competitor_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Конкурент не найден"
        )
    before = {"id": obj.id, "name": obj.name, "slug": obj.slug}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="competitor",
        entity_id=competitor_id,
        before=before,
    )
    await db.commit()
