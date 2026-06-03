"""Очистка спарсенных статей: удалить рекламу, SEO-мусор, дубликаты.

Запуск: docker compose exec backend python -m app.scripts.clean_knowledge
"""

import asyncio
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("clean_knowledge")

# Фразы, по которым статьи — мусор (удаляем целиком)
TRASH_TITLES = [
    "пользовательское соглашение",
    "выбрать город доставки",
    "контакты",
    "станьте дилером",
    "поддон для",
    "комплект крючков",
    "щелочное моющее средство",
    "пресс для приготовления рыбного фарша",
]

# SEO-фразы, которые нужно вырезать из body_md
SEO_PATTERNS = [
    r"Наверх\s*Оборудование для копчения.*?(?=\n|$)",
    r"Оборудование для промышленного копчения",
    r"Доставляем в.*?стран(?:ы|\.)",  # "Доставляем в 50 стран"
    r"Ижица . оборудование для копчения и коптильных цехов",
    r"Оборудование для копчения:.*?СНГ",
    r"Купить.*?в Санкт-Петербурге.*?доставкой.*?(?=\n|$)",
    r"цены на коптильные.*?производителя",
    r"доставка в Москву, по России и СНГ",
    r"от прямого производителя",
    r"по России и страны СНГ",
    r"из Санкт-Петербурга с доставкой",
    r"с доставкой по России и СНГ",
    r"купить.*?оборудование для копчения",
    r"цена от производителя",
    r"\n{3,}",  # множественные переносы
    r" {2,}",  # множественные пробелы
]

# Отображение URL → категория
URL_CATEGORY_MAP: dict[str, str] = {}

# Статьи, которые нужно перекатегоризировать
CATEGORY_FIXES: dict[int, str] = {
    # articles about technology
    9: "guide",      # выбор парогенератора
    16: "recipe",    # рецепты
    18: "guide",     # как выбрать коптильню
    27: "guide",     # панель управления
    36: "theory",    # температура х/к
    37: "recipe",    # дичь
    38: "recipe",    # сыры
    39: "guide",     # контейнер
    40: "recipe",    # оленина
    44: "recipe",    # говядина
    45: "comparison", # сравнение
    48: "review",     # преимущества
    49: "guide",      # засол
    54: "guide",      # хранение рыбы
}


def clean_body(text: str) -> str:
    """Очистить body от SEO-мусора."""
    if not text:
        return ""
    for pattern in SEO_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


def is_trash(title: str) -> bool:
    """Проверить, мусорная ли статья."""
    t = title.lower()
    for phrase in TRASH_TITLES:
        if phrase in t:
            return True
    return False


async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.knowledge import KnowledgeArticle, ArticleCategory
    from sqlalchemy import select, delete

    async with AsyncSessionLocal() as session:
        # 1. Получаем все статьи
        result = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        articles = result.scalars().all()
        logger.info(f"Всего статей: {len(articles)}")

        # 2. Удаляем дубликаты по source_url
        seen_urls: dict[str, int] = {}
        to_delete_ids: list[int] = []
        for a in articles:
            if a.source_url and a.source_url in seen_urls:
                to_delete_ids.append(a.id)
                logger.info(f"  ДУБЛИКАТ ID:{a.id}: {a.title[:60]}")
            elif a.source_url:
                seen_urls[a.source_url] = a.id

        # 3. Удаляем мусор
        for a in articles:
            if is_trash(a.title):
                to_delete_ids.append(a.id)
                logger.info(f"  МУСОР ID:{a.id}: {a.title[:60]}")

        # Удаляем найденное
        if to_delete_ids:
            for aid in set(to_delete_ids):
                obj = await session.get(KnowledgeArticle, aid)
                if obj:
                    await session.delete(obj)
            await session.flush()
            logger.info(f"  Удалено: {len(set(to_delete_ids))} статей")

        # 4. Чистим body у оставшихся
        remaining = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        cleaned = 0
        for a in remaining.scalars().all():
            new_body = clean_body(a.body_md or "")
            if new_body != a.body_md:
                a.body_md = new_body
                cleaned += 1

            # Перекатегоризация
            if a.id in CATEGORY_FIXES:
                new_cat = ArticleCategory(CATEGORY_FIXES[a.id])
                if a.category != new_cat:
                    old_cat = a.category.value
                    a.category = new_cat
                    logger.info(f"  КАТ ID:{a.id}: {old_cat} → {new_cat.value}")

        await session.commit()

        # 5. Итог
        final = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        final_articles = final.scalars().all()
        logger.info(f"\n=== ИТОГ ===")
        logger.info(f"Статей после чистки: {len(final_articles)}")
        for a in final_articles:
            bl = len(a.body_md or "")
            logger.info(f"  ID:{a.id:2d} | {a.category.value:15s} | {bl:5d} б | {a.title[:70]}")


if __name__ == "__main__":
    asyncio.run(main())
