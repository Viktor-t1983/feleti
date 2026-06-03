"""Импорт всех моделей для регистрации в Base.metadata (нужно Alembic'у)."""

from app.db.session import Base  # noqa: F401

# Импортируем все модули моделей, чтобы они зарегистрировались в Base.metadata
from app.models.user import User  # noqa: F401, E402
from app.models.manufacturer import Manufacturer  # noqa: F401, E402
from app.models.chamber import Chamber  # noqa: F401, E402
from app.models.product import Product  # noqa: F401, E402
from app.models.ingredient import Ingredient  # noqa: F401, E402
from app.models.recipe import Recipe, RecipeVersion, RecipeApproval  # noqa: F401, E402
from app.models.brine import Brine  # noqa: F401, E402
from app.models.batch import Batch, BatchPhase, BatchTelemetry  # noqa: F401, E402
from app.models.knowledge import KnowledgeArticle, KnowledgeAttachment  # noqa: F401, E402
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem  # noqa: F401, E402
from app.models.telemetry import TelemetryReading  # noqa: F401, E402
from app.models.audit import AuditLog  # noqa: F401, E402

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
]
