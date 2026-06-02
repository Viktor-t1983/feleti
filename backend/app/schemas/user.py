"""Схемы пользователя."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import EmailStr, Field

from app.schemas.common import APIModel


class UserRoleEnum(str, Enum):
    ADMIN = "admin"
    TECHNOLOGIST = "technologist"
    OPERATOR = "operator"
    MANAGER = "manager"
    VIEWER = "viewer"


class UserRead(APIModel):
    id: int
    email: EmailStr
    username: str
    full_name: str | None = None
    role: UserRoleEnum
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None


class UserCreate(APIModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: str | None = None
    password: str = Field(..., min_length=6, max_length=200)
    role: UserRoleEnum = UserRoleEnum.OPERATOR
    is_active: bool = True
    is_superuser: bool = False


class UserUpdate(APIModel):
    email: EmailStr | None = None
    username: str | None = Field(default=None, min_length=3, max_length=100)
    full_name: str | None = None
    password: str | None = Field(default=None, min_length=6, max_length=200)
    role: UserRoleEnum | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
