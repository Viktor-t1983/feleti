"""Базовые Pydantic-схемы: общие для всех эндпоинтов."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class APIModel(BaseModel):
    """Базовая модель: разрешает чтение из ORM-атрибутов."""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)


class HealthResponse(APIModel):
    status: str
    project: str
    version: str
    env: str


class MessageResponse(APIModel):
    message: str
    detail: str | None = None


class PageParams(BaseModel):
    """Параметры пагинации (query-параметры)."""

    page: int = Field(default=1, ge=1, description="Номер страницы (1..)")
    size: int = Field(default=20, ge=1, le=200, description="Размер страницы (1..200)")


class Page(APIModel, Generic[T]):
    """Универсальный ответ со списком + метаданными пагинации."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int
