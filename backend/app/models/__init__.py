"""SQLAlchemy-модели FELETI-SMOK.

Импорт всех моделей для регистрации в Base.metadata (нужно Alembic'у).
"""

from app.db.base import Base  # noqa: F401, E402

# ВАЖНО: импортируем ВСЕ модули моделей, иначе Alembic не увидит таблицы.
# (см. также app/db/base.py — там то же самое, двойной импорт не вредит)
from app.models.audit import AuditLog  # noqa: F401, E402
from app.models.batch import Batch, BatchPhase, BatchTelemetry  # noqa: F401, E402
from app.models.brine import Brine  # noqa: F401, E402
from app.models.chamber import Chamber  # noqa: F401, E402
from app.models.chat import ChatSession, ChatMessage  # noqa: F401, E402
from app.models.ingredient import Ingredient  # noqa: F401, E402
from app.models.knowledge import KnowledgeArticle, KnowledgeAttachment, ArticleAnalysis, KnowledgeTopic, ArticleTopic  # noqa: F401, E402
from app.models.manufacturer import Manufacturer  # noqa: F401, E402
from app.models.product import Product  # noqa: F401, E402
from app.models.recipe import Recipe, RecipeApproval, RecipeVersion  # noqa: F401, E402
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem  # noqa: F401, E402
from app.models.telemetry import TelemetryReading  # noqa: F401, E402
from app.models.user import User  # noqa: F401, E402
from app.models.ai_settings import AISettings  # noqa: F401, E402
from app.models.source_reputation import SourceReputation  # noqa: F401, E402
from app.models.knowledge_fact import KnowledgeFact, KnowledgeChunk  # noqa: F401, E402  # noqa: F401, E402

__all__ = [
    "Base",
    "User",
    "Manufacturer",
    "Chamber",
    "Product",
    "Ingredient",
    "Recipe",
    "RecipeVersion",
    "RecipeApproval",
    "Brine",
    "Batch",
    "BatchPhase",
    "BatchTelemetry",
    "KnowledgeArticle",
    "KnowledgeAttachment",
    "TelemetryReading",
    "AuditLog",
    "AISettings",
    "ArticleAnalysis",
    "KnowledgeTopic",
    "ArticleTopic",
    "ChatSession",
    "ChatMessage",
    "SourceReputation",
]
