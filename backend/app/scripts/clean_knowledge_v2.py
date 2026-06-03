"""Вторая чистка: агрессивное удаление SEO-лендингов + очистка заголовков.

Запуск: docker compose exec backend python -m app.scripts.clean_knowledge_v2
"""

import asyncio
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("clean_v2")

# Статьи-категории (списки ссылок, без полезного контента) — удалить
CATEGORY_PAGES = {5, 6, 7, 8, 10, 11, 12, 15, 22, 25, 26, 30, 42}

# Статьи с технической информацией — оставить, почистить заголовок
KEEP_TECH = {
    9: "Как выбрать парогенератор для коптильни",
    16: "Рецепты копчения деликатесов",
    18: "Как выбрать коптильню для рыбы",
    27: "Панель управления термокамеры: повышение эффективности копчения",
    36: "Точный контроль температуры при холодном копчении",
    37: "Копчение мяса диких животных",
    38: "Основные виды копчёных сыров",
    39: "Копчение в контейнере",
    40: "Рецептуры копчёностей из оленины",
    44: "Говядина копчёно-запечённая: рецептура",
    45: "Сравнение Ижицы с низкотехнологичными конкурентами",
    48: "Преимущества коптилен Ижицы",
    49: "Засол свинины перед копчением",
    54: "Хранение рыбы холодного копчения: ГОСТ",
}

# Страницы каталогов — проверить, есть ли таблицы с ТТХ
CATALOG_PAGES = {13, 17, 19, 20, 21, 23, 24, 28, 32, 35, 41, 43, 46, 47, 51, 53}


def clean_title(title: str) -> str:
    """Убрать SEO из заголовка."""
    patterns = [
        r"купить.*?в Санкт-Петербурге.*",
        r"Купить.*?в Санкт-Петербурге.*",
        r"с доставкой.*",
        r"цена от производителя",
        r"цены на.*",
        r"по России и СНГ",
        r"от прямого производителя",
        r"в Москву, по России и СНГ",
        r"по России и страны СНГ",
        r"из Санкт-Петербурга с доставкой",
        r"с доставкой по России и СНГ",
        r"с доставкой в Москву.*",
        r"по доступной цене.*",
        r" \|.*",  # всё после |
    ]
    for pat in patterns:
        title = re.sub(pat, "", title, flags=re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title).strip().rstrip(",").rstrip(" ").rstrip("-").strip()
    return title or "(без названия)"


def has_tech_content(body: str) -> bool:
    """Проверить, есть ли техническая информация в тексте."""
    tech_keywords = [
        "температур", "мм", "кг", "градус", "режим", "дым",
        "мощност", "напряжени", "электро", "вольт", "квт",
        "модел", "комплект", "технологи", "таблиц", "характеристик",
    ]
    body_lower = body.lower()
    matches = sum(1 for kw in tech_keywords if kw in body_lower)
    return matches >= 3


async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.knowledge import KnowledgeArticle
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        articles = result.scalars().all()

        deleted = 0
        renamed = 0
        saved_catalog = 0

        for a in articles:
            # Удаляем категории
            if a.id in CATEGORY_PAGES:
                await session.delete(a)
                deleted += 1
                logger.info(f"  УДАЛЕНО ID:{a.id}: {a.title[:60]}")
                continue

            # Чистим заголовок
            if a.id in KEEP_TECH:
                new_title = KEEP_TECH[a.id]
                if a.title != new_title:
                    old = a.title[:50]
                    a.title = new_title
                    renamed += 1
                    logger.info(f"  ЗАГОЛОВОК ID:{a.id}: {old}… → {new_title}")
            else:
                new_title = clean_title(a.title)
                if new_title and new_title != a.title:
                    a.title = new_title
                    renamed += 1

            # Страницы каталогов
            if a.id in CATALOG_PAGES:
                if has_tech_content(a.body_md or ""):
                    saved_catalog += 1
                    if a.category.value == "review":
                        a.category = type(a.category)("guide")  # переключаем
                    logger.info(f"  ОСТАВЛЕНО ID:{a.id} (каталог, есть ТТХ): {a.title[:60]}")
                else:
                    await session.delete(a)
                    deleted += 1
                    logger.info(f"  УДАЛЕНО ID:{a.id} (каталог, нет ТТХ): {a.title[:60]}")

        await session.commit()

        # Итог
        final = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        final_list = final.scalars().all()
        logger.info(f"\n=== ИТОГ ===")
        logger.info(f"Удалено: {deleted}")
        logger.info(f"Переименовано: {renamed}")
        logger.info(f"Сохранено каталогов с ТТХ: {saved_catalog}")
        logger.info(f"Осталось: {len(final_list)}")
        for a in final_list:
            bl = len(a.body_md or "")
            logger.info(f"  ID:{a.id:2d} | {a.category.value:12s} | {bl:5d} б | {a.title[:70]}")


if __name__ == "__main__":
    asyncio.run(main())
