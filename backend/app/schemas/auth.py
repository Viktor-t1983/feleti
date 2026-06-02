"""Схемы аутентификации: login, refresh, me."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel


class LoginRequest(APIModel):
    username: str = Field(..., min_length=1, max_length=100, description="Имя пользователя или email")
    password: str = Field(..., min_length=1, max_length=200, description="Пароль")


class RefreshRequest(APIModel):
    refresh_token: str = Field(..., min_length=10)


class Token(APIModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Время жизни access_token в секундах")


class TokenPayload(APIModel):
    sub: str
    exp: datetime
    iat: datetime | None = None
    role: str | None = None
