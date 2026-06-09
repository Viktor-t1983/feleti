"""Сервис аудит-логирования мутаций."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditAction, AuditLog


def _json_safe(val: Any) -> Any:
    """Convert non-serializable types to JSON-safe equivalents."""
    if isinstance(val, datetime):
        return val.isoformat()
    return val


def _prepare(d: dict[str, Any] | None) -> dict[str, Any] | None:
    if d is None:
        return None
    return {k: _json_safe(v) for k, v in d.items()}


async def record(
    db: AsyncSession,
    *,
    actor_id: int | None,
    action: AuditAction,
    entity_type: str,
    entity_id: int | None = None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
    extra: dict[str, Any] | None = None,
) -> AuditLog:
    """Записать событие в аудит-лог. Не коммитит — вызывающий код решает."""
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=_prepare(before),
        after=_prepare(after),
        ip=ip,
        user_agent=user_agent,
        extra=_prepare(extra) or {},
    )
    db.add(log)
    return log
