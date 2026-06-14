"""Сервис агрегации фактов для Product Profile с наследованием по parent_id."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_fact import KnowledgeFact
from app.models.product import Product

PREDICATE_LABELS: dict[str, str] = {
    "uses_brine": "Рассолы",
    "uses_equipment": "Оборудование",
    "uses_technology": "Технологии",
    "has_parameter": "Параметры",
    "regulated_by": "ГОСТы / ТУ",
    "has_category": "Категоризация",
    "contains": "Состав",
    "derived_from": "Сырьё",
    "shelf_life": "Срок хранения",
    "storage_condition": "Условия хранения",
    "process_step": "Техпроцесс",
    "mentions": "Упоминания",
}


class FactItem:
    def __init__(
        self,
        object_name: str,
        object_type: str,
        predicate: str,
        article_id: int,
        source_text: str | None = None,
        confidence: float = 0.0,
        params: dict | None = None,
        inherited_from: str | None = None,
        chunk_id: int | None = None,
    ):
        self.object_name = object_name
        self.object_type = object_type
        self.predicate = predicate
        self.article_id = article_id
        self.source_text = source_text
        self.confidence = confidence
        self.params = params or {}
        self.inherited_from = inherited_from
        self.chunk_id = chunk_id

    def to_dict(self) -> dict:
        return {
            "object_name": self.object_name,
            "object_type": self.object_type,
            "predicate": self.predicate,
            "article_id": self.article_id,
            "source_text": self.source_text,
            "confidence": self.confidence,
            "params": self.params,
            "inherited_from": self.inherited_from,
            "chunk_id": self.chunk_id,
        }


class FactGroup:
    def __init__(self, predicate: str, label: str, facts: list[FactItem]):
        self.predicate = predicate
        self.label = label
        self.facts = facts

    def to_dict(self) -> dict:
        return {
            "predicate": self.predicate,
            "label": self.label,
            "facts": [f.to_dict() for f in self.facts],
        }


async def _fetch_fact_items(
    product_id: int,
    db: AsyncSession,
    inherited_from: str | None = None,
) -> list[FactItem]:
    """Получить факты для одного product_id."""
    facts = (await db.scalars(
        select(KnowledgeFact)
        .where(
            KnowledgeFact.subject_id == product_id,
            KnowledgeFact.subject_type == "product",
        )
        .order_by(KnowledgeFact.predicate, KnowledgeFact.confidence.desc())
    )).all()

    items = []
    for f in facts:
        pred = f.predicate.value if hasattr(f.predicate, "value") else str(f.predicate)
        items.append(FactItem(
            object_name=f.object_name,
            object_type=f.object_type.value if hasattr(f.object_type, "value") else str(f.object_type),
            predicate=pred,
            article_id=f.article_id,
            source_text=f.source_text,
            confidence=f.confidence,
            params=f.params or {},
            inherited_from=inherited_from,
            chunk_id=f.chunk_id,
        ))
    return items


async def build_profile_facts(
    product_id: int,
    db: AsyncSession,
) -> list[FactGroup]:
    """Собрать факты для продукта + унаследованные от родителя."""
    # Факты самого продукта
    own_facts = await _fetch_fact_items(product_id, db)

    # Восхождение по цепочке parent_id
    inherited: list[FactItem] = []
    seen_predicates: set[tuple[str, str, str]] = set()
    for f in own_facts:
        seen_predicates.add((f.predicate, f.object_name, f.object_type))

    product = await db.get(Product, product_id)
    visited = {product_id}
    while product and product.parent_id and product.parent_id not in visited:
        visited.add(product.parent_id)
        parent = await db.get(Product, product.parent_id)
        if not parent:
            break

        parent_facts = await _fetch_fact_items(parent.id, db, inherited_from=parent.name)
        for pf in parent_facts:
            key = (pf.predicate, pf.object_name, pf.object_type)
            if key not in seen_predicates:
                seen_predicates.add(key)
                inherited.append(pf)

        product = parent

    # Собираем в группы
    all_items = own_facts + inherited
    groups_map: dict[str, list[FactItem]] = {}
    for item in all_items:
        groups_map.setdefault(item.predicate, []).append(item)

    return [
        FactGroup(
            predicate=pred,
            label=PREDICATE_LABELS.get(pred, pred),
            facts=items,
        )
        for pred, items in groups_map.items()
    ]
