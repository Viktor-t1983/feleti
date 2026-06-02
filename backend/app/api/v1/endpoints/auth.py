"""Auth endpoints: login, refresh, me."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.deps import CurrentUser, DBSession
from app.core.security import decode_access_token
from app.models.audit import AuditAction
from app.models.user import User
from app.schemas.auth import LoginRequest, RefreshRequest, Token
from app.schemas.user import UserRead
from app.services import audit, auth as auth_service

router = APIRouter()


@router.post("/login", response_model=Token, summary="Вход (OAuth2 password flow)")
async def login(
    request: Request,
    db: DBSession,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await auth_service.authenticate(db, form.username, form.password)
    access, refresh, expires_in = await auth_service.issue_tokens(
        db,
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/login/json", response_model=Token, summary="Вход (JSON-вариант)")
async def login_json(payload: LoginRequest, request: Request, db: DBSession) -> Token:
    user = await auth_service.authenticate(db, payload.username, payload.password)
    access, refresh, expires_in = await auth_service.issue_tokens(
        db,
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return Token(access_token=access, refresh_token=refresh, expires_in=expires_in)


@router.post("/refresh", response_model=Token, summary="Обновить токены")
async def refresh(payload: RefreshRequest, request: Request, db: DBSession) -> Token:
    data = decode_access_token(payload.refresh_token)
    if not data or data.get("typ") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный refresh token",
        )
    sub = data.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token без sub",
        )
    user: User | None = None
    try:
        user_id = int(sub)
        user = await db.scalar(select(User).where(User.id == user_id))
    except (TypeError, ValueError):
        user = await auth_service.get_user_by_login(db, sub)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    access, new_refresh, expires_in = await auth_service.issue_tokens(
        db,
        user,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return Token(access_token=access, refresh_token=new_refresh, expires_in=expires_in)


@router.get("/me", response_model=UserRead, summary="Текущий пользователь")
async def me(current: CurrentUser, db: DBSession) -> UserRead:
    await audit.record(
        db,
        actor_id=current.id,
        action=AuditAction.OTHER,
        entity_type="user",
        entity_id=current.id,
        extra={"event": "me_check"},
    )
    await db.commit()
    return UserRead.model_validate(current)
