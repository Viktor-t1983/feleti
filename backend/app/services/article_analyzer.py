"""Сервис AI-анализа статей: категоризация, извлечение ТТХ, продуктов, технологий."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge import ArticleAnalysis, AnalysisStatus, KnowledgeArticle
from app.services.ai_service import AIService

logger = logging.getLogger("article_analyzer")


class ArticleAnalyzer:
    """Запускает AI-анализ статьи и сохраняет результат."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def analyze(self, article_id: int) -> ArticleAnalysis:
        article = await self.db.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.id == article_id)
        )
        if not article:
            raise ValueError(f"Статья {article_id} не найдена")

        analysis = await self.db.scalar(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article_id)
        )
        if not analysis:
            analysis = ArticleAnalysis(article_id=article_id)
            self.db.add(analysis)

        analysis.status = AnalysisStatus.RUNNING
        await self.db.flush()

        try:
            settings = await AIService.get_settings(self.db)
            ai = AIService(settings)

            text = f"{article.title}\n\n{article.body_md or ''}"
            result = await ai.analyze(text)

            analysis.products = result.get("products", [])
            analysis.technologies = result.get("technologies", [])
            problems_raw = result.get("problems", [])
            analysis.problems = [
                {
                    "title": p.get("title", ""),
                    "description": p.get("description", ""),
                    "severity": p.get("severity", "medium"),
                }
                for p in problems_raw
            ]
            equipment_raw = result.get("equipment", [])
            analysis.equipment = [
                {
                    "name": e.get("name", ""),
                    "specs": e.get("specs", {}),
                }
                for e in equipment_raw
            ]
            analysis.key_insights = result.get("key_insights", [])
            mentions_raw = result.get("competitor_mentions", [])
            analysis.competitor_mentions = [
                {
                    "name": m.get("name", ""),
                    "products": m.get("products", []),
                    "pricing": m.get("pricing"),
                }
                for m in mentions_raw
            ]
            analysis.target_markets = result.get("target_markets", [])
            analysis.ai_category = result.get("category")
            analysis.topic_path = result.get("topic_path")
            analysis.raw_response = result
            analysis.model_used = settings.model_name
            analysis.status = AnalysisStatus.DONE
            analysis.error = None
            analysis.analyzed_at = datetime.utcnow()

        except Exception as exc:
            logger.exception("AI-анализ статьи %d провалился", article_id)
            analysis.status = AnalysisStatus.ERROR
            analysis.error = str(exc)

        await self.db.flush()
        return analysis

    async def get_analysis(self, article_id: int) -> ArticleAnalysis | None:
        return await self.db.scalar(
            select(ArticleAnalysis).where(ArticleAnalysis.article_id == article_id)
        )

    async def get_unanalyzed_ids(self, limit: int = 50) -> list[int]:
        analyzed = select(ArticleAnalysis.article_id)
        stmt = (
            select(KnowledgeArticle.id)
            .where(
                ~KnowledgeArticle.id.in_(analyzed),
            )
            .limit(limit)
        )
        rows = (await self.db.scalars(stmt)).all()
        return list(rows)
