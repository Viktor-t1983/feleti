"""Pydantic-схемы для SourceReputation."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from app.schemas.common import APIModel


class SourceReputationCreate(APIModel):
    domain: str
    score: int = 1
    is_blacklisted: bool = False
    label: Optional[str] = None
    notes: Optional[str] = None


class SourceReputationUpdate(APIModel):
    domain: Optional[str] = None
    score: Optional[int] = None
    is_blacklisted: Optional[bool] = None
    label: Optional[str] = None
    notes: Optional[str] = None


class SourceReputationRead(APIModel):
    id: int
    domain: str
    score: int
    is_blacklisted: bool
    label: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
