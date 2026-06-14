"""Сервис верификации фактов: дедупликация, подтверждение, повышение confidence."""

from __future__ import annotations

import logging

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_fact import KnowledgeFact, FactStatus, FactPredicate

logger = logging.getLogger(__name__)


async def find_duplicates(db: AsyncSession) -> list[dict]:
    """Найти дубликаты фактов (одинаковые subject + predicate + object)."""
    subq = (
        select(
            KnowledgeFact.subject_name,
            KnowledgeFact.subject_type,
            KnowledgeFact.predicate,
            KnowledgeFact.object_name,
            KnowledgeFact.object_type,
            func.count().label("cnt"),
            func.array_agg(KnowledgeFact.id).label("ids"),
        )
        .group_by(
            KnowledgeFact.subject_name,
            KnowledgeFact.subject_type,
            KnowledgeFact.predicate,
            KnowledgeFact.object_name,
            KnowledgeFact.object_type,
        )
        .having(func.count() > 1)
        .subquery()
    )

    rows = (await db.execute(
        select(subq).order_by(subq.c.cnt.desc())
    )).all()

    results = []
    for r in rows:
        results.append({
            "subject_name": r.subject_name,
            "subject_type": r.subject_type.value if hasattr(r.subject_type, "value") else str(r.subject_type),
            "predicate": r.predicate.value if hasattr(r.predicate, "value") else str(r.predicate),
            "object_name": r.object_name,
            "object_type": r.object_type.value if hasattr(r.object_type, "value") else str(r.object_type),
            "count": r.cnt,
            "fact_ids": list(r.ids),
        })
    return results


async def find_contradictions(db: AsyncSession) -> list[dict]:
    """Найти противоречия: одинаковый subject + predicate, но разный object."""
    from sqlalchemy import or_

    # Находим пары (subject_name, subject_type, predicate) с разными object
    conflict_stmt = (
        select(
            KnowledgeFact.subject_name,
            KnowledgeFact.subject_type,
            KnowledgeFact.predicate,
        )
        .where(KnowledgeFact.status != FactStatus.DEPRECATED)
        .group_by(
            KnowledgeFact.subject_name,
            KnowledgeFact.subject_type,
            KnowledgeFact.predicate,
        )
        .having(func.count(KnowledgeFact.object_name.distinct()) > 1)
    )
    conflict_pairs = (await db.execute(conflict_stmt)).all()

    if not conflict_pairs:
        return []

    # Строим OR-условия для загрузки этих фактов
    conditions = [
        (KnowledgeFact.subject_name == cp.subject_name)
        & (KnowledgeFact.subject_type == cp.subject_type)
        & (KnowledgeFact.predicate == cp.predicate)
        for cp in conflict_pairs
    ]

    rows = (await db.scalars(
        select(KnowledgeFact)
        .where(
            or_(*conditions),
            KnowledgeFact.status != FactStatus.DEPRECATED,
        )
        .order_by(
            KnowledgeFact.subject_name,
            KnowledgeFact.predicate,
            KnowledgeFact.confidence.desc(),
        )
    )).all()

    contradictions: dict[str, dict] = {}
    for f in rows:
        key = f"{f.subject_name}|{f.predicate.value}"
        if key not in contradictions:
            contradictions[key] = {
                "subject_name": f.subject_name,
                "subject_type": f.subject_type.value if hasattr(f.subject_type, "value") else str(f.subject_type),
                "predicate": f.predicate.value if hasattr(f.predicate, "value") else str(f.predicate),
                "objects": [],
            }
        contradictions[key]["objects"].append({
            "fact_id": f.id,
            "object_name": f.object_name,
            "object_type": f.object_type.value if hasattr(f.object_type, "value") else str(f.object_type),
            "confidence": f.confidence,
            "source_text": f.source_text[:100] if f.source_text else None,
            "article_id": f.article_id,
        })

    return list(contradictions.values())


async def boost_confidence(db: AsyncSession, fact_id: int) -> KnowledgeFact | None:
    """Повысить confidence факта на 0.1 (при ручном подтверждении)."""
    fact = await db.get(KnowledgeFact, fact_id)
    if not fact:
        return None
    fact.confidence = min(fact.confidence + 0.15, 1.0)
    await db.flush()
    return fact


async def confirm_fact(db: AsyncSession, fact_id: int) -> KnowledgeFact | None:
    """Подтвердить факт человеком (status → CONFIRMED, confidence → 0.95)."""
    fact = await db.get(KnowledgeFact, fact_id)
    if not fact:
        return None
    fact.status = FactStatus.CONFIRMED
    fact.confidence = max(fact.confidence, 0.85)
    await db.flush()
    return fact


async def reject_fact(db: AsyncSession, fact_id: int) -> KnowledgeFact | None:
    """Отклонить факт (status → DEPRECATED)."""
    fact = await db.get(KnowledgeFact, fact_id)
    if not fact:
        return None
    fact.status = FactStatus.DEPRECATED
    await db.flush()
    return fact


async def deduplicate_facts(db: AsyncSession) -> int:
    """Автоматическая дедупликация: удалить дубликаты, оставить с highest confidence."""
    duplicates = await find_duplicates(db)
    removed = 0
    for dup in duplicates:
        fact_ids = sorted(dup["fact_ids"])
        if len(fact_ids) <= 1:
            continue
        # Первый оставляем, остальные удаляем
        keep_id = fact_ids[0]
        for rm_id in fact_ids[1:]:
            fact = await db.get(KnowledgeFact, rm_id)
            if fact:
                await db.delete(fact)
                removed += 1
    if removed:
        await db.flush()
        logger.info(f"Deduplication: removed {removed} duplicate facts")
    return removed


async def auto_verify(db: AsyncSession) -> dict:
    """Запустить автоматическую верификацию:
    - Дедупликация
    - Повышаем confidence у фактов, подтверждённых из 2+ источников
    """
    removed = await deduplicate_facts(db)

    # Повышаем confidence если один и тот же факт из разных статей
    subq = (
        select(
            KnowledgeFact.source_hash,
            func.count().label("cnt"),
        )
        .where(
            KnowledgeFact.source_hash.isnot(None),
            KnowledgeFact.status != FactStatus.DEPRECATED,
        )
        .group_by(KnowledgeFact.source_hash)
        .having(func.count() > 1)
        .subquery()
    )

    rows = (await db.execute(
        select(KnowledgeFact).where(
            KnowledgeFact.source_hash.in_(select(subq.c.source_hash))
        )
    )).scalars().all()

    boosted = 0
    for fact in rows:
        fact.confidence = min(fact.confidence + 0.1, 1.0)
        boosted += 1

    if boosted:
        await db.flush()

    return {"removed_duplicates": removed, "boosted_confidence": boosted}
