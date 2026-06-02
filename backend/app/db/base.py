"""Import all models here so Alembic can detect them."""
from app.db.session import Base  # noqa: F401

# Import all model modules so they register with Base.metadata
from app.models.user import User  # noqa: F401, E402
from app.models.manufacturer import Manufacturer  # noqa: F401, E402
from app.models.chamber import Chamber, ChamberFeature  # noqa: F401, E402
from app.models.product import Product  # noqa: F401, E402
from app.models.ingredient import Ingredient  # noqa: F401, E402
from app.models.recipe import Recipe, RecipeStep, RecipeIngredient  # noqa: F401, E402
from app.models.brine import Brine, BrineIngredient  # noqa: F401, E402
from app.models.batch import Batch, BatchReading  # noqa: F401, E402
from app.models.knowledge import KnowledgeArticle, Gost, TelegramChannel, Video  # noqa: F401, E402
