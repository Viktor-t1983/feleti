"""Сервис аутентификации: выдача и валидация токенов."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.models.audit import AuditAction
from app.services import audit


async def get_user_by_login(db: AsyncSession, login: str) -> User | None:
    """Найти пользователя по username ИЛИ email."""
    return await db.scalar(
        select(User).where(or_(User.username == login, User.email == login))
    )


async def authenticate(db: AsyncSession, login: str, password: str) -> User:
    user = await get_user_by_login(db, login)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь заблокирован",
        )
    return user


async def issue_tokens(
    db: AsyncSession,
    user: User,
    *,
    ip: str | None = None,
    user_agent: str | None = None,
) -> tuple[str, str, int]:
    """Выдать access+refresh токены и записать аудит-событие login."""
    expires_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    access = create_access_token(
        subject=user.id,
        expires_minutes=expires_minutes,
        role=user.role.value,
    )
    refresh = create_access_token(
        subject=user.id,
        expires_minutes=expires_minutes * 7,
        typ="refresh",
    )
    user.last_login_at = datetime.now(tz=timezone.utc)
    db.add(user)
    await audit.record(
        db,
        actor_id=user.id,
        action=AuditAction.LOGIN,
        entity_type="user",
        entity_id=user.id,
        ip=ip,
        user_agent=user_agent,
    )
    return access, refresh, expires_minutes * 60


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    password: str,
    full_name: str | None = None,
    role: UserRole = UserRole.OPERATOR,
    is_superuser: bool = False,
    actor_id: int | None = None,
) -> User:
    """Регистрация нового пользователя (admin)."""
    existing = await db.scalar(
        select(User).where(or_(User.email == email, User.username == username))
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email или username уже существует",
        )
    user = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    await audit.record(
        db,
        actor_id=actor_id,
        action=AuditAction.CREATE,
        entity_type="user",
        entity_id=user.id,
        after={"email": email, "username": username, "role": role.value},
    )
    return user
