"""CRUD для управления репутацией источников знаний."""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUser, DBSession
from app.models.source_reputation import SourceReputation
from app.schemas.source_reputation import (
    SourceReputationCreate,
    SourceReputationRead,
    SourceReputationUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=list[SourceReputationRead])
async def list_sources(
    db: DBSession,
    _user: CurrentUser,
    blacklisted: bool | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Список всех источников."""
    stmt = select(SourceReputation).order_by(
        SourceReputation.is_blacklisted,
        SourceReputation.score.desc(),
        SourceReputation.domain,
    )
    if blacklisted is not None:
        stmt = stmt.where(SourceReputation.is_blacklisted == blacklisted)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=SourceReputationRead, status_code=201)
async def create_source(
    body: SourceReputationCreate,
    db: DBSession,
    _user: CurrentUser,
):
    """Добавить новый источник."""
    source = SourceReputation(**body.model_dump())
    db.add(source)
    try:
        await db.commit()
        await db.refresh(source)
        return source
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Источник с таким доменом уже существует")


@router.get("/{source_id}", response_model=SourceReputationRead)
async def get_source(source_id: int, db: DBSession, _user: CurrentUser):
    """Получить источник по ID."""
    source = await db.get(SourceReputation, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    return source


@router.put("/{source_id}", response_model=SourceReputationRead)
async def update_source(
    source_id: int,
    body: SourceReputationUpdate,
    db: DBSession,
    _user: CurrentUser,
):
    """Обновить источник."""
    source = await db.get(SourceReputation, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(source, field, value)
    try:
        await db.commit()
        await db.refresh(source)
        return source
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Домен уже существует")


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: DBSession, _user: CurrentUser):
    """Удалить источник."""
    source = await db.get(SourceReputation, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Источник не найден")
    await db.delete(source)
    await db.commit()
