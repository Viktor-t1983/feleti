"""Pydantic-схемы для AI-эндпоинтов."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Annotated

from pydantic import Field

from app.schemas.common import APIModel
from app.schemas.knowledge import KnowledgeArticleSummary


class AIAskRequest(APIModel):
    question: Annotated[str, Field(min_length=2, max_length=2000)]
    top_k: Annotated[int, Field(ge=1, le=20)] = 5


class AIAskResponse(APIModel):
    answer: str
    sources: list[KnowledgeArticleSummary] = []
    query: str
    model: str = ""


class AIAnalyzeRequest(APIModel):
    text: Annotated[str, Field(min_length=10, max_length=50000)]


class AIAnalyzeResponse(APIModel):
    result: dict[str, Any]
    model: str = ""


class AISettingsRead(APIModel):
    provider: str = "ollama"
    endpoint: str = "http://host.docker.internal:11434/v1"
    api_key: str | None = None
    model_name: str = "qwen2.5:7b"
    temperature: float = 0.3
    max_tokens: int = 2048
    system_prompt: str = ""
    enabled: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AISettingsUpdate(APIModel):
    provider: str | None = None
    endpoint: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    system_prompt: str | None = None
    enabled: bool | None = None


class AITestResult(APIModel):
    success: bool
    model: str | None = None
    latency_ms: int | None = None
    error: str | None = None


class AICollectRequest(APIModel):
    query: Annotated[str, Field(min_length=2, max_length=500)]
    source_types: list[str] | None = None
    topic_ids: list[int] | None = None
    max_results: int = 10


class AICollectResponse(APIModel):
    job_id: str
    status: str


class AICollectProgress(APIModel):
    job_id: str
    status: str
    total: int = 0
    processed: int = 0
    skipped: int = 0
    created: list[int] = []
    errors: list[str] = []


__all__ = [
    "AIAskRequest",
    "AIAskResponse",
    "AIAnalyzeRequest",
    "AIAnalyzeResponse",
    "AISettingsRead",
    "AISettingsUpdate",
    "AITestResult",
    "AICollectRequest",
    "AICollectResponse",
    "AICollectProgress",
]
