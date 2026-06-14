"""Бэкфилл: резолвинг subject_name → subject_id для старых фактов.

Запуск: python -m app.scripts.resolve_subject_ids
"""
from __future__ import annotations

import asyncio
import logging
import sys

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.knowledge_fact import KnowledgeFact, FactSubjectType
from app.models.product import Product
from app.models.chamber import Chamber
from app.models.brine import Brine

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("resolve_subject_ids")

BATCH_SIZE = 200


async def resolve_products(db: AsyncSession) -> int:
    """Привязать subject_name → subject_id для типа product."""
    names = (await db.scalars(
        select(KnowledgeFact.subject_name)
        .where(
            KnowledgeFact.subject_type == FactSubjectType.PRODUCT,
            KnowledgeFact.subject_id.is_(None),
        )
        .distinct()
    )).all()

    products = (await db.scalars(select(Product))).all()
    name_map = {}
    for p in products:
        name_map[p.name.lower()] = p.id

    resolved = 0
    for name in names:
        pid = name_map.get(name.lower())
        if pid is None:
            continue
        rows = (await db.scalars(
            select(KnowledgeFact).where(
                KnowledgeFact.subject_name == name,
                KnowledgeFact.subject_type == FactSubjectType.PRODUCT,
                KnowledgeFact.subject_id.is_(None),
            )
        )).all()
        for f in rows:
            f.subject_id = pid
            resolved += 1

    if resolved:
        await db.flush()
        logger.info(f"Resolved {resolved} product facts → {len([v for v in name_map.values()])} products")
    return resolved


async def resolve_chambers(db: AsyncSession) -> int:
    """Привязать subject_name → subject_id для типа chamber."""
    names = (await db.scalars(
        select(KnowledgeFact.subject_name)
        .where(
            KnowledgeFact.subject_type == FactSubjectType.CHAMBER,
            KnowledgeFact.subject_id.is_(None),
        )
        .distinct()
    )).all()

    chambers = (await db.scalars(select(Chamber))).all()
    name_map = {}
    for c in chambers:
        name_map[c.model.lower()] = c.id

    resolved = 0
    for name in names:
        cid = name_map.get(name.lower())
        if cid is None:
            continue
        rows = (await db.scalars(
            select(KnowledgeFact).where(
                KnowledgeFact.subject_name == name,
                KnowledgeFact.subject_type == FactSubjectType.CHAMBER,
                KnowledgeFact.subject_id.is_(None),
            )
        )).all()
        for f in rows:
            f.subject_id = cid
            resolved += 1

    if resolved:
        await db.flush()
        logger.info(f"Resolved {resolved} chamber facts")
    return resolved


async def resolve_brines(db: AsyncSession) -> int:
    """Привязать subject_name → subject_id для типа brine."""
    names = (await db.scalars(
        select(KnowledgeFact.subject_name)
        .where(
            KnowledgeFact.subject_type == FactSubjectType.BRINE,
            KnowledgeFact.subject_id.is_(None),
        )
        .distinct()
    )).all()

    brines = (await db.scalars(select(Brine))).all()
    name_map = {}
    for b in brines:
        name_map[b.name.lower()] = b.id

    resolved = 0
    for name in names:
        bid = name_map.get(name.lower())
        if bid is None:
            continue
        rows = (await db.scalars(
            select(KnowledgeFact).where(
                KnowledgeFact.subject_name == name,
                KnowledgeFact.subject_type == FactSubjectType.BRINE,
                KnowledgeFact.subject_id.is_(None),
            )
        )).all()
        for f in rows:
            f.subject_id = bid
            resolved += 1

    if resolved:
        await db.flush()
        logger.info(f"Resolved {resolved} brine facts")
    return resolved


async def main():
    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count(KnowledgeFact.id)))
        null_subject = await db.scalar(
            select(func.count(KnowledgeFact.id)).where(KnowledgeFact.subject_id.is_(None))
        )
        logger.info(f"Total facts: {total}, null subject_id: {null_subject}")

        r1 = await resolve_products(db)
        r2 = await resolve_chambers(db)
        r3 = await resolve_brines(db)

        await db.commit()
        logger.info(f"Done: {r1 + r2 + r3} facts resolved")


if __name__ == "__main__":
    asyncio.run(main())
