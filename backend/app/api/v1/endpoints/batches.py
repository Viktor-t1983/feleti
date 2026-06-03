"""CRUD партий + жизненный цикл (start/pause/resume/cancel/complete).

Партия — конкретный запуск программы рецепта в конкретной камере.
Логика:
  - PLANNED → RUNNING через POST /batches/{id}/start
    (загружает программу в камеру через ChamberGateway и стартует)
  - RUNNING ⇄ PAUSED через /pause и /resume
  - RUNNING/PAUSED → COMPLETED через /complete (или авто по завершении программы)
  - любое → CANCELLED через /cancel
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from app.core.deps import CurrentUser, DBSession
from app.models.audit import AuditAction
from app.models.batch import Batch, BatchStatus
from app.models.chamber import Chamber
from app.models.recipe import RecipeStatus, RecipeVersion
from app.schemas.batch import (
    BatchCreate,
    BatchDetail,
    BatchRead,
    BatchStatusChange,
    BatchUpdate,
)
from app.schemas.common import Page, PageParams
from app.services import audit
from app.services.chamber_gateway import (
    ChamberConnectionError,
    ChamberGateway,
    get_chamber_gateway,
)

router = APIRouter()


def _utcnow() -> datetime:
    """Единая точка получения UTC now (для тестируемости)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("", response_model=Page[BatchRead], summary="Список партий")
async def list_batches(
    db: DBSession,
    _user: CurrentUser,
    params: Annotated[PageParams, Query()],
    chamber_id: Annotated[int | None, Query()] = None,
    recipe_id: Annotated[int | None, Query()] = None,
    status_: Annotated[BatchStatus | None, Query(alias="status")] = None,
) -> Page[BatchRead]:
    stmt = select(Batch)
    count_stmt = select(func.count()).select_from(Batch)
    if chamber_id is not None:
        stmt = stmt.where(Batch.chamber_id == chamber_id)
        count_stmt = count_stmt.where(Batch.chamber_id == chamber_id)
    if recipe_id is not None:
        stmt = stmt.where(Batch.recipe_version_id.in_(
            select(RecipeVersion.id).where(RecipeVersion.recipe_id == recipe_id)
        ))
        count_stmt = count_stmt.where(Batch.recipe_version_id.in_(
            select(RecipeVersion.id).where(RecipeVersion.recipe_id == recipe_id)
        ))
    if status_ is not None:
        stmt = stmt.where(Batch.status == status_)
        count_stmt = count_stmt.where(Batch.status == status_)

    total = await db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(Batch.id.desc())
        .offset((params.page - 1) * params.size)
        .limit(params.size)
    )
    rows = (await db.scalars(stmt)).all()
    pages = (total + params.size - 1) // params.size if total else 0
    return Page[BatchRead](
        items=[BatchRead.model_validate(r) for r in rows],
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )


@router.get(
    "/{batch_id}",
    response_model=BatchDetail,
    summary="Детальная информация о партии (с фазами)",
)
async def get_batch(
    batch_id: int, db: DBSession, _user: CurrentUser
) -> BatchDetail:
    obj = await db.scalar(
        select(Batch)
        .options(
            selectinload(Batch.phases),
            selectinload(Batch.recipe_version),
            selectinload(Batch.chamber),
            selectinload(Batch.operator),
        )
        .where(Batch.id == batch_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    return BatchDetail.model_validate(obj)


@router.post(
    "",
    response_model=BatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать партию (в статусе PLANNED, без запуска)",
)
async def create_batch(
    payload: BatchCreate, db: DBSession, user: CurrentUser
) -> BatchRead:
    rv = await db.scalar(
        select(RecipeVersion).where(RecipeVersion.id == payload.recipe_version_id)
    )
    if rv is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Версия рецепта {payload.recipe_version_id} не найдена",
        )
    if rv.status not in (RecipeStatus.APPROVED, RecipeStatus.PENDING):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Версия рецепта в статусе {rv.status.value}; "
                "для запуска нужна APPROVED или PENDING"
            ),
        )
    chamber = await db.scalar(
        select(Chamber).where(Chamber.id == payload.chamber_id)
    )
    if chamber is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Камера {payload.chamber_id} не найдена",
        )
    obj = Batch(
        recipe_version_id=payload.recipe_version_id,
        chamber_id=payload.chamber_id,
        operator_id=payload.operator_id or user.id,
        batch_number=payload.batch_number,
        status=BatchStatus.PLANNED,
        product_weight_kg=payload.product_weight_kg,
        planned_start=payload.planned_start,
        notes=payload.notes,
    )
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Партия с номером {payload.batch_number} уже существует",
        ) from e
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CREATE,
        entity_type="batch",
        entity_id=obj.id,
        after=payload.model_dump(mode="json"),
    )
    await db.commit()
    await db.refresh(obj)
    return BatchRead.model_validate(obj)


@router.patch("/{batch_id}", response_model=BatchRead, summary="Обновить партию")
async def update_batch(
    batch_id: int, payload: BatchUpdate, db: DBSession, user: CurrentUser
) -> BatchRead:
    obj = await db.scalar(select(Batch).where(Batch.id == batch_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    data = payload.model_dump(exclude_unset=True)
    before = {c.name: getattr(obj, c.name) for c in Batch.__table__.columns}
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.UPDATE,
        entity_type="batch",
        entity_id=obj.id,
        before=before,
        after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return BatchRead.model_validate(obj)


@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить партию (только в PLANNED/CANCELLED)",
)
async def delete_batch(batch_id: int, db: DBSession, user: CurrentUser) -> None:
    obj = await db.scalar(select(Batch).where(Batch.id == batch_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    if obj.status not in (BatchStatus.PLANNED, BatchStatus.CANCELLED, BatchStatus.COMPLETED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Нельзя удалить партию в статусе {obj.status.value}. "
                "Сначала отмените (/cancel) или завершите (/complete)."
            ),
        )
    before = {"id": obj.id, "batch_number": obj.batch_number, "status": obj.status.value}
    await db.delete(obj)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.DELETE,
        entity_type="batch",
        entity_id=batch_id,
        before=before,
    )
    await db.commit()


@router.post(
    "/{batch_id}/start",
    response_model=BatchRead,
    summary="Запустить партию: загрузить программу в камеру и стартовать",
)
async def start_batch(
    batch_id: int,
    db: DBSession,
    user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
) -> BatchRead:
    obj = await db.scalar(
        select(Batch)
        .options(
            selectinload(Batch.recipe_version),
            selectinload(Batch.chamber),
        )
        .where(Batch.id == batch_id)
    )
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    if obj.status not in (BatchStatus.PLANNED, BatchStatus.PAUSED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Нельзя запустить партию в статусе {obj.status.value}",
        )
    if obj.chamber is None or obj.recipe_version is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Партия без камеры или версии рецепта (битые FK)",
        )
    program = obj.recipe_version.program or []
    if not program:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У версии рецепта пустая программа (program=[])",
        )
    try:
        await gateway.start_batch(
            chamber_id=obj.chamber_id,
            driver_class=obj.chamber.driver_class,
            connection=obj.chamber.default_driver_config or {},
            recipe_program=program,
        )
    except ChamberConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Не удалось подключиться к камере: {e}",
        ) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка запуска: {e}",
        ) from e

    obj.status = BatchStatus.RUNNING
    obj.actual_start = obj.actual_start or _utcnow()
    if obj.operator_id is None:
        obj.operator_id = user.id
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.START,
        entity_type="batch",
        entity_id=obj.id,
        after={"status": obj.status.value, "actual_start": obj.actual_start.isoformat()},
    )
    await db.commit()
    await db.refresh(obj)
    return BatchRead.model_validate(obj)


@router.post(
    "/{batch_id}/pause",
    response_model=BatchRead,
    summary="Поставить партию на паузу",
)
async def pause_batch(
    batch_id: int,
    db: DBSession,
    user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
) -> BatchRead:
    obj = await db.scalar(select(Batch).where(Batch.id == batch_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    if obj.status != BatchStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Пауза доступна только из RUNNING, текущий: {obj.status.value}",
        )
    try:
        await gateway.pause_batch(obj.chamber_id)
    except ChamberConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Камера недоступна: {e}",
        ) from e
    obj.status = BatchStatus.PAUSED
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.PAUSE,
        entity_type="batch",
        entity_id=obj.id,
        after={"status": obj.status.value},
    )
    await db.commit()
    await db.refresh(obj)
    return BatchRead.model_validate(obj)


@router.post(
    "/{batch_id}/resume",
    response_model=BatchRead,
    summary="Снять партию с паузы",
)
async def resume_batch(
    batch_id: int,
    db: DBSession,
    user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
) -> BatchRead:
    obj = await db.scalar(select(Batch).where(Batch.id == batch_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    if obj.status != BatchStatus.PAUSED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Resume доступен только из PAUSED, текущий: {obj.status.value}",
        )
    try:
        await gateway.resume_batch(obj.chamber_id)
    except ChamberConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Камера недоступна: {e}",
        ) from e
    obj.status = BatchStatus.RUNNING
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.RESUME,
        entity_type="batch",
        entity_id=obj.id,
        after={"status": obj.status.value},
    )
    await db.commit()
    await db.refresh(obj)
    return BatchRead.model_validate(obj)


@router.post(
    "/{batch_id}/cancel",
    response_model=BatchRead,
    summary="Отменить партию (остановить камеру, статус CANCELLED)",
)
async def cancel_batch(
    batch_id: int,
    db: DBSession,
    user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
    payload: Annotated[BatchStatusChange | None, Body()] = None,
) -> BatchRead:
    obj = await db.scalar(select(Batch).where(Batch.id == batch_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    if obj.status in (BatchStatus.COMPLETED, BatchStatus.CANCELLED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Партия уже в финальном статусе: {obj.status.value}",
        )
    try:
        await gateway.stop_batch(obj.chamber_id)
    except ChamberConnectionError:
        # Камера может быть недоступна, но партию всё равно отменяем
        pass
    obj.status = BatchStatus.CANCELLED
    obj.actual_end = _utcnow()
    if payload and payload.note:
        obj.notes = (obj.notes or "") + f"\n[Отмена] {payload.note}"
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.CANCEL,
        entity_type="batch",
        entity_id=obj.id,
        after={"status": obj.status.value, "note": payload.note if payload else None},
    )
    await db.commit()
    await db.refresh(obj)
    return BatchRead.model_validate(obj)


@router.post(
    "/{batch_id}/complete",
    response_model=BatchRead,
    summary="Завершить партию (остановить камеру, статус COMPLETED)",
)
async def complete_batch(
    batch_id: int,
    db: DBSession,
    user: CurrentUser,
    gateway: Annotated[ChamberGateway, Depends(get_chamber_gateway)],
    payload: Annotated[BatchStatusChange | None, Body()] = None,
) -> BatchRead:
    obj = await db.scalar(select(Batch).where(Batch.id == batch_id))
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Партия не найдена"
        )
    if obj.status not in (BatchStatus.RUNNING, BatchStatus.PAUSED):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Завершить можно только из RUNNING/PAUSED, "
                f"текущий: {obj.status.value}"
            ),
        )
    try:
        await gateway.stop_batch(obj.chamber_id)
    except ChamberConnectionError:
        pass
    obj.status = BatchStatus.COMPLETED
    obj.actual_end = _utcnow()
    if payload and payload.note:
        obj.notes = (obj.notes or "") + f"\n[Завершение] {payload.note}"
    await db.flush()
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.COMPLETE,
        entity_type="batch",
        entity_id=obj.id,
        after={"status": obj.status.value, "actual_end": obj.actual_end.isoformat()},
    )
    await db.commit()
    await db.refresh(obj)
    return BatchRead.model_validate(obj)
