"""FastAPI dependencies: DB session, current user, RBAC."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db as _get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True,
)

DBSession = Annotated[AsyncSession, Depends(_get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DBSession,
) -> User:
    """Получить текущего пользователя по JWT access token."""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный токен (нет sub)",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный sub в токене",
        )

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден или заблокирован",
        )
    return user


def require_roles(*allowed: UserRole):
    """Зависимость: пользователь должен иметь одну из перечисленных ролей (или быть superuser)."""
    allowed_set = set(allowed)

    async def _checker(user: CurrentUser) -> User:
        if user.is_superuser or user.role in allowed_set:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Недостаточно прав. Нужна одна из ролей: {[r.value for r in allowed]}",
        )

    return _checker


CurrentUser = Annotated[User, Depends(get_current_user)]


async def _require_admin(user: CurrentUser) -> User:
    if user.is_superuser or user.role == UserRole.ADMIN:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Требуются права администратора",
    )


CurrentAdmin = Annotated[User, Depends(_require_admin)]
