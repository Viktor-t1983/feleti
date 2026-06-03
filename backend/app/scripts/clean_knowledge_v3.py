"""Финальная чистка: доочистить заголовки каталогов + извлечь ТТХ → CompetitorModel.

Запуск: docker compose exec backend python -m app.scripts.clean_knowledge_v3
"""

import asyncio
import logging
import re
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("clean_v3")

CATALOG_TITLES = {
    13: "Автоматические коптильни горячего и холодного копчения",
    17: "Коптильные камеры для малого бизнеса",
    19: "Камеры для вяления мяса и рыбы",
    20: "Коптильные шкафы",
    21: "Универсальные коптильные камеры",
    23: "Коптильный шкаф для горячего копчения",
    24: "Промышленные коптильные камеры для рыбы и мяса",
    28: "Профессиональные коптильные камеры",
    32: "Оборудование для копчения мяса",
    35: "Оборудование для холодного копчения",
    41: "Коптильное оборудование для коптилен и цехов",
    43: "Термокамера для колбасного производства",
    46: "Камера холодного электростатического копчения Ижица-1200М4-А",
    47: "Мини-коптильня горячего копчения",
    51: "Коптильни для сала: профессиональное оборудование",
    53: "Коптильные камеры холодного и горячего копчения",
}


def extract_model_rows(text: str) -> list[dict[str, str]]:
    """Извлечь строки ТТХ из Markdown-таблиц."""
    rows = []
    table_pattern = re.compile(
        r"\|[^\n]+\|\n\|[-| ]+\|\n(?:\|[^\n]+\|\n?)+",
        re.MULTILINE,
    )
    for table_match in table_pattern.finditer(text):
        lines = table_match.group(0).strip().split("\n")
        if len(lines) < 3:
            continue
        headers = [h.strip().lower() for h in lines[0].strip("|").split("|")]
        if len(headers) < 2:
            continue
        for line in lines[2:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) != len(headers):
                continue
            row = dict(zip(headers, cells))
            tech_count = sum(
                1 for v in row.values()
                if re.search(r"\d+", v) and re.search(r"(мм|кг|°c|квт|в|л|м3|шт|г|час|мин)", v, re.I)
            )
            if tech_count >= 2:
                rows.append(row)
    return rows


def parse_value(val: str) -> Optional[str]:
    """Очистить значение."""
    if not val:
        return None
    val = re.sub(r"\s+", " ", val).strip()
    return val if val and val != "-" else None


async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.knowledge import KnowledgeArticle, ArticleCategory
    from app.models.competitor import Competitor, CompetitorModel
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        # Находим конкурента Ижица
        result = await session.execute(
            select(Competitor).where(Competitor.slug == "ijiza")
        )
        ijiza: Optional[Competitor] = result.scalar_one_or_none()
        if not ijiza:
            logger.error("Конкурент 'ijiza' не найден в БД!")
            return
        logger.info(f"Конкурент Ижица: id={ijiza.id}")

        # Читаем все статьи
        result = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        articles = result.scalars().all()

        fixed_titles = 0
        new_models = 0
        chunks_removed = 0

        for a in articles:
            # 1. Фикс заголовков
            if a.id in CATALOG_TITLES:
                new_title = CATALOG_TITLES[a.id]
                if a.title != new_title:
                    logger.info(f"  ЗАГОЛОВОК ID:{a.id}: было → {new_title}")
                    a.title = new_title
                    fixed_titles += 1
                    if a.category and a.category.value == "review":
                        a.category = ArticleCategory("guide")

            # 2. Удаление SEO-блоков из body
            body = a.body_md or ""
            old_body = body
            body = re.sub(
                r"Наверх\s*\n.*?Оборудование для копчения.*?(?:\n|$)",
                "", body, flags=re.IGNORECASE | re.DOTALL
            )
            body = re.sub(
                r"Купить.*?(?:в Санкт-Петербурге|в Москве).*?(?:доставк|цен).*?(?:\n|$)",
                "", body, flags=re.IGNORECASE | re.DOTALL
            )
            body = re.sub(
                r"Оборудование для копчения:.*?(?:СНГ|России).*?(?:\n|$)",
                "", body, flags=re.IGNORECASE | re.DOTALL
            )
            body = re.sub(
                r"Ижица[—\-–]\s*оборудование для копчения.*?(?:\n|$)",
                "", body, flags=re.IGNORECASE | re.DOTALL
            )
            if body != old_body:
                a.body_md = body
                chunks_removed += 1

        await session.flush()

        # 3. Извлечение ТТХ из каталогов → CompetitorModel
        for a in articles:
            if a.id not in CATALOG_TITLES:
                continue
            body = a.body_md or ""
            model_rows = extract_model_rows(body)
            if not model_rows:
                continue

            logger.info(f"  ТТХ ID:{a.id}: найдено {len(model_rows)} строк")
            for row in model_rows:
                model_name = parse_value(row.get("модель", ""))
                if not model_name:
                    continue

                # Проверяем дубликат
                existing = await session.execute(
                    select(CompetitorModel).where(
                        CompetitorModel.name == model_name,
                        CompetitorModel.competitor_id == ijiza.id,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                # Парсим параметры
                def int_val(key: str) -> Optional[int]:
                    v = parse_value(row.get(key, ""))
                    if v:
                        m = re.search(r"\d+", v)
                        if m:
                            return int(m.group())
                    return None

                def float_val(key: str) -> Optional[float]:
                    v = parse_value(row.get(key, ""))
                    if v:
                        m = re.search(r"[\d.]+", v)
                        if m:
                            return float(m.group())
                    return None

                cm = CompetitorModel(
                    competitor_id=ijiza.id,
                    name=model_name,
                    max_load_kg=int_val("загрузка"),
                    power_kw=float_val("мощность"),
                    voltage_v=int_val("напряжение"),
                    weight_kg=int_val("вес"),
                    dimensions=parse_value(row.get("габариты", "")),
                )
                session.add(cm)
                new_models += 1
                logger.info(f"    + {model_name}")

        await session.commit()

        # Итог
        final = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        final_list = final.scalars().all()
        models = await session.execute(
            select(CompetitorModel).where(CompetitorModel.competitor_id == ijiza.id)
        )
        model_count = len(models.scalars().all())

        logger.info(f"\n=== ИТОГ ===")
        logger.info(f"Заголовков исправлено: {fixed_titles}")
        logger.info(f"SEO-блоков удалено: {chunks_removed}")
        logger.info(f"Новых моделей CompetitorModel: {new_models}")
        logger.info(f"Всего моделей Ижицы в БД: {model_count}")
        logger.info(f"Статей после чистки: {len(final_list)}")
        for a in final_list:
            bl = len(a.body_md or "")
            logger.info(f"  ID:{a.id:2d} | {a.category.value:12s} | {bl:5d} б | {a.title[:70]}")


if __name__ == "__main__":
    asyncio.run(main())
