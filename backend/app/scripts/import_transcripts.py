"""Импорт структурированных данных из YouTube-транскриптов в БД.

Запуск: docker compose exec backend python -m app.scripts.import_transcripts
"""

import asyncio
import json
import logging
import os
import re

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("import_transcripts")

SUMMARY_PATH = "/app/summary.json"


def make_slug(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"[^a-zа-яё0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug)[:200]
    return slug or "video"


def build_body(vid: dict) -> str:
    parts = []
    title = vid.get("title", "")
    parts.append(f"# {title}\n")

    products = vid.get("products_mentioned", [])
    if products:
        parts.append("## Продукты\n" + ", ".join(products) + "\n")

    techs = vid.get("technologies_mentioned", [])
    if techs:
        parts.append("## Технологии\n" + ", ".join(techs) + "\n")

    equipment = vid.get("equipment_mentioned", [])
    if equipment:
        parts.append("## Оборудование\n" + ", ".join(equipment) + "\n")

    problems = vid.get("problems_mentioned", [])
    if problems:
        parts.append("## Проблемы\n" + ", ".join(problems) + "\n")

    return "\n".join(parts)


async def main():
    from app.db.session import AsyncSessionLocal
    from app.models.knowledge import KnowledgeArticle, ArticleCategory
    from app.models.competitor import Competitor, CompetitorProblem
    from sqlalchemy import select

    if not os.path.exists(SUMMARY_PATH):
        logger.error(f"Файл {SUMMARY_PATH} не найден!")
        return

    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        videos: list[dict] = json.load(f)

    problem_counter: dict[str, int] = {}

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Competitor).where(Competitor.slug == "ijiza")
        )
        ijiza = result.scalar_one_or_none()

        new_articles = 0

        for vid in videos:
            vid_id = vid["video_id"]
            has_content = (
                vid.get("has_recipe_details")
                or vid.get("has_program_details")
                or vid.get("has_problem_details")
            )
            if not has_content:
                continue

            existing = await session.execute(
                select(KnowledgeArticle).where(
                    KnowledgeArticle.source_url.ilike(f"%youtube.com/watch?v={vid_id}%")
                )
            )
            if existing.scalar_one_or_none():
                continue

            if vid.get("has_recipe_details"):
                category = ArticleCategory("recipe")
            elif vid.get("has_problem_details"):
                category = ArticleCategory("troubleshooting")
            else:
                category = ArticleCategory("guide")

            title = vid.get("title", f"Видео {vid_id}").strip()
            url = f"https://www.youtube.com/watch?v={vid_id}"
            body = build_body(vid)
            slug = make_slug(title)
            if slug != make_slug(title):
                slug = f"{slug}-{vid_id[:8]}"

            tags = []
            if vid.get("has_recipe_details"):
                tags.append("recipe")
            if vid.get("has_program_details"):
                tags.append("program")
            if vid.get("has_problem_details"):
                tags.append("problems")
            if vid.get("has_business_info"):
                tags.append("business")

            article = KnowledgeArticle(
                title=title,
                slug=slug,
                body_md=body,
                category=category,
                source_url=url,
                tags=tags,
                is_published=True,
            )
            session.add(article)
            await session.flush()
            new_articles += 1

            for prob in vid.get("problems_mentioned", []):
                p = prob.lower().strip()
                if p:
                    problem_counter[p] = problem_counter.get(p, 0) + 1

            if new_articles % 20 == 0:
                logger.info(f"  Прогресс: {new_articles} статей")

        if ijiza:
            for prob_name, count in sorted(
                problem_counter.items(), key=lambda x: -x[1]
            ):
                if count < 3:
                    continue
                existing = await session.execute(
                    select(CompetitorProblem).where(
                        CompetitorProblem.competitor_id == ijiza.id,
                        CompetitorProblem.title == prob_name,
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                severity = "high" if count >= 10 else ("medium" if count >= 5 else "low")
                cp = CompetitorProblem(
                    competitor_id=ijiza.id,
                    title=prob_name,
                    description=f"Упоминается в {count} видео на YouTube",
                    severity=severity,
                    frequency=f"{count} упоминаний",
                    source="YouTube",
                )
                session.add(cp)

        await session.commit()

        final = await session.execute(
            select(KnowledgeArticle).where(
                KnowledgeArticle.source_url.like("%youtube.com%")
            )
        )
        yt_articles = final.scalars().all()
        all_articles = await session.execute(
            select(KnowledgeArticle).order_by(KnowledgeArticle.id)
        )
        all_list = all_articles.scalars().all()

        logger.info(f"\n=== ИТОГ ===")
        logger.info(f"Новых статей из YouTube: {new_articles}")
        logger.info(f"Всего YouTube-статей в БД: {len(yt_articles)}")
        logger.info(f"Всего статей в БД: {len(all_list)}")
        logger.info(f"\n--- Топ-10 проблем ---")
        for prob_name, count in sorted(
            problem_counter.items(), key=lambda x: -x[1]
        )[:10]:
            logger.info(f"  {prob_name}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
