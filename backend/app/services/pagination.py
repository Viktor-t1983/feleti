"""Утилиты для пагинированных SQLAlchemy-запросов (DRY для list-эндпоинтов)."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.schemas.common import Page, PageParams

M = TypeVar("M")
R = TypeVar("R")


async def paginate(
    db: AsyncSession,
    stmt: Select,
    params: PageParams,
    map_func: type[R] | callable = None,
    *,
    order_by=None,
    unique: bool = False,
) -> Page[R]:
    """Выполнить пагинированный запрос и вернуть Page[R].

    Parameters
    ----------
    db : AsyncSession
    stmt : Select
        SELECT-запрос к модели (уже с JOIN/where-фильтрами).
    params : PageParams
        page / size.
    map_func : type[R] | callable | None
        Чем сериализовать строки. Если None — возвращаются ORM-объекты как есть.
    order_by
        Если задан, перезаписывает ORDER BY в stmt.
    unique : bool
        Если True, вызывает `.unique().all()` (нужно для joinedload).

    Returns
    -------
    Page[R]
    """
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = await db.scalar(count_stmt) or 0

    if order_by is not None:
        stmt = stmt.order_by(order_by)
    stmt = stmt.offset((params.page - 1) * params.size).limit(params.size)

    if unique:
        rows = (await db.scalars(stmt)).unique().all()
    else:
        rows = (await db.scalars(stmt)).all()

    pages = (total + params.size - 1) // params.size if total else 0

    if map_func is None:
        items = list(rows)
    elif isinstance(map_func, type):
        items = [map_func.model_validate(r) for r in rows]
    else:
        items = [map_func(r) for r in rows]

    return Page[R](
        items=items,
        total=total,
        page=params.page,
        size=params.size,
        pages=pages,
    )
