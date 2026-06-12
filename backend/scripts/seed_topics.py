"""Seed семантического дерева знаний (knowledge_topics)."""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import asyncio
import logging
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.knowledge import KnowledgeTopic

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TREE = [
    {
        "slug": "technologies",
        "label": "Технологии",
        "children": [
            {
                "slug": "zasol",
                "label": "Засол",
                "children": [
                    {"slug": "suchoj-zasol", "label": "Сухой посол"},
                    {"slug": "mokryj-zasol", "label": "Мокрый посол"},
                    {"slug": "shpricevanie", "label": "Шприцевание"},
                ],
            },
            {
                "slug": "termoobrabotka",
                "label": "Термообработка",
                "children": [
                    {"slug": "holodnoe-kopchenie", "label": "Холодное копчение (t<30°C)"},
                    {"slug": "goryachee-kopchenie", "label": "Горячее копчение (t>80°C)"},
                    {"slug": "polugoryachee-kopchenie", "label": "Полугорячее копчение (30-80°C)"},
                    {"slug": "sushka", "label": "Сушка"},
                    {"slug": "varka", "label": "Варка"},
                ],
            },
            {
                "slug": "ohlazhdenie-i-hranenie",
                "label": "Охлаждение и хранение",
            },
            {
                "slug": "upakovka",
                "label": "Упаковка",
                "children": [
                    {"slug": "vakuumnaya-upakovka", "label": "Вакуумная упаковка"},
                    {"slug": "gaz-mod-sreda", "label": "Газ-модифицированная среда"},
                ],
            },
        ],
    },
    {
        "slug": "syrio",
        "label": "Сырьё",
        "children": [
            {
                "slug": "ryba",
                "label": "Рыба",
                "children": [
                    {"slug": "osetr", "label": "Осётр"},
                    {"slug": "losos-forel", "label": "Лосось / Форель"},
                    {"slug": "skumbriya", "label": "Скумбрия"},
                    {"slug": "ugor", "label": "Угорь"},
                    {"slug": "sig-ryapushka", "label": "Сиг / Ряпушка"},
                ],
            },
            {
                "slug": "myaso",
                "label": "Мясо",
                "children": [
                    {"slug": "svinina", "label": "Свинина"},
                    {"slug": "govyadina", "label": "Говядина"},
                    {"slug": "ptica", "label": "Птица"},
                ],
            },
            {"slug": "moreprodukty", "label": "Морепродукты"},
            {"slug": "obolochki", "label": "Оболочки"},
        ],
    },
    {
        "slug": "oborudovanie",
        "label": "Оборудование",
        "children": [
            {
                "slug": "kamery-koptilnye",
                "label": "Камеры коптильные",
                "children": [
                    {"slug": "feleti-smok", "label": "FELETI-SMOK"},
                    {"slug": "mid", "label": "МИД"},
                    {"slug": "izhitsa", "label": "Ижица"},
                ],
            },
            {"slug": "dymogeneratory", "label": "Дымогенераторы"},
            {"slug": "kompressory-klimat", "label": "Компрессоры и климат"},
            {"slug": "mojka-defrostaciya", "label": "Мойка и дефростация"},
        ],
    },
    {
        "slug": "recepty",
        "label": "Рецепты",
        "children": [
            {"slug": "rybnye", "label": "Рыбные"},
            {"slug": "myasnye", "label": "Мясные"},
            {"slug": "moreproduktov", "label": "Морепродукты"},
        ],
    },
    {
        "slug": "problemy-i-resheniya",
        "label": "Проблемы и решения",
        "children": [
            {"slug": "gorech", "label": "Горечь"},
            {"slug": "peresol", "label": "Пересол"},
            {"slug": "nedosol", "label": "Недосол"},
            {"slug": "plesen", "label": "Плесень"},
            {"slug": "textura", "label": "Текстура и консистенция"},
        ],
    },
    {
        "slug": "konkurenty",
        "label": "Конкуренты",
        "children": [
            {"slug": "otechestvennye", "label": "Отечественные"},
            {"slug": "importnye", "label": "Импортные"},
        ],
    },
]


def _create_recursive(items, parent_id, parent_path, level, sort_start, all_topics):
    """Рекурсивно создаёт темы в all_topics, возвращает список созданных."""
    result = []
    for i, item in enumerate(items):
        slug = item["slug"]
        path = f"{parent_path}/{slug}" if parent_path else f"/{slug}"
        children = item.get("children", [])
        topic = KnowledgeTopic(
            slug=slug,
            label=item["label"],
            path=path,
            parent_id=parent_id,
            level=level,
            sort_order=sort_start + i,
        )
        result.append(topic)
        all_topics.append(topic)

        if children:
            child_topics = _create_recursive(
                children, None, path, level + 1, 0, all_topics
            )
            result.extend(child_topics)

    return result


async def seed_topics():
    async with AsyncSessionLocal() as session:
        existing = await session.scalar(
            select(KnowledgeTopic).limit(1)
        )
        if existing is not None:
            logger.info("Темы уже посеяны, пропускаем")
            return

        all_topics = []
        root_topics = _create_recursive(TREE, None, "", 0, 0, all_topics)
        session.add_all(all_topics)
        await session.flush()

        # проставляем parent_id для детей
        # сперва мапим slug → id
        slug_id = {t.slug: t.id for t in all_topics}

        def link_parents(items, parent_slug):
            for item in items:
                item_id = slug_id[item["slug"]]
                children = item.get("children", [])
                if children:
                    for child in children:
                        child_id = slug_id[child["slug"]]
                        # находим объект и обновляем parent_id
                        for t in all_topics:
                            if t.id == child_id:
                                t.parent_id = item_id
                                break
                    link_parents(children, item["slug"])

        link_parents(TREE, None)
        await session.commit()
        logger.info("Посеяно %d тем", len(all_topics))


async def main():
    async with AsyncSessionLocal() as session:
        try:
            await seed_topics()
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())
