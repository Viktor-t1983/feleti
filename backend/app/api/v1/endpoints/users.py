"""CRUD пользователей (только для админов)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.deps import CurrentAdmin, DBSession
from app.core.security import hash_password
from app.models.audit import AuditAction
from app.models.user import User
from app.schemas.common import Page
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import audit

router = APIRouter()


@router.get("", response_model=Page[UserRead], summary="Список пользователей")
async def list_users(
    db: DBSession,
    _admin: CurrentAdmin,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
) -> Page[UserRead]:
    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)
    total = await db.scalar(count_stmt) or 0
    stmt = stmt.order_by(User.id.asc()).offset((page - 1) * size).limit(size)
    rows = (await db.scalars(stmt)).all()
    pages = (total + size - 1) // size if total else 0
    return Page[UserRead](
        items=[UserRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@router.get("/{user_id}", response_model=UserRead, summary="Пользователь по ID")
async def get_user(user_id: int, db: DBSession, _admin: CurrentAdmin) -> UserRead:
    obj = await db.scalar(select(User).where(User.id == user_id))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserRead.model_validate(obj)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED, summary="Создать пользователя")
async def create_user(payload: UserCreate, db: DBSession, admin: CurrentAdmin) -> UserRead:
    data = payload.model_dump(exclude={"password"})
    obj = User(**data, hashed_password=hash_password(payload.password))
    db.add(obj)
    try:
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email или username уже существует",
        ) from e
    await audit.record(
        db, actor_id=admin.id, action=AuditAction.CREATE,
        entity_type="user", entity_id=obj.id,
        after=data,
    )
    await db.commit()
    await db.refresh(obj)
    return UserRead.model_validate(obj)


@router.patch("/{user_id}", response_model=UserRead, summary="Обновить пользователя")
async def update_user(
    user_id: int, payload: UserUpdate, db: DBSession, admin: CurrentAdmin
) -> UserRead:
    obj = await db.scalar(select(User).where(User.id == user_id))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    before = {c.name: getattr(obj, c.name) for c in User.__table__.columns}
    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        data["hashed_password"] = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(obj, k, v)
    await db.flush()
    await audit.record(
        db, actor_id=admin.id, action=AuditAction.UPDATE,
        entity_type="user", entity_id=obj.id,
        before=before, after={**before, **data},
    )
    await db.commit()
    await db.refresh(obj)
    return UserRead.model_validate(obj)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK, summary="Удалить пользователя")
async def delete_user(user_id: int, db: DBSession, admin: CurrentAdmin) -> None:
    obj = await db.scalar(select(User).where(User.id == user_id))
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if obj.id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")
    before = {"id": obj.id, "username": obj.username, "email": obj.email}
    await db.delete(obj)
    await audit.record(
        db, actor_id=admin.id, action=AuditAction.DELETE,
        entity_type="user", entity_id=user_id, before=before,
    )
    await db.commit()
