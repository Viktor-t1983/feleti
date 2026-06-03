# SKILL: pytest-testing

> Написание тестов для backend (FastAPI + SQLAlchemy async). Используй при создании тестового покрытия.

## 1. Структура тестов

```
backend/tests/
├── conftest.py              # Fixtures: event_loop, db_session, client, auth_headers
├── test_recipe_calc.py      # Юнит-тесты калькулятора (чистые функции)
├── test_auth.py             # Интеграционные: login, refresh, me
├── test_recipes.py          # Интеграционные: CRUD recipes + versions
├── test_batches.py          # Интеграционные: lifecycle партий
├── test_chambers.py         # Интеграционные: CRUD chambers + drivers
├── test_telemetry.py        # Интеграционные: REST telemetry
├── test_knowledge.py        # Интеграционные: CRUD + search
└── test_seed.py             # Проверка idempotентности seed
```

## 2. conftest.py

```python
import pytest_asyncio
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, UserRole

TEST_DATABASE_URL = "postgresql+asyncpg://feleti:feleti_dev_password@localhost:5432/feleti_smok_test"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_headers(db_session):
    user = User(
        email="test@feleti.by",
        username="testuser",
        hashed_password=hash_password("testpass"),
        role=UserRole.TECHNOLOGIST,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    
    from app.core.security import create_access_token
    token = create_access_token({"sub": user.username})
    return {"Authorization": f"Bearer {token}"}
```

## 3. Юнит-тесты (recipe_calc)

```python
# tests/test_recipe_calc.py
import pytest
from app.services.recipe_calc import (
    calculate_recipe,
    compute_bju,
    compute_yield,
    IngredientForCalc,
)

@pytest.fixture
def sample_ingredients():
    return [
        IngredientForCalc(id=1, name="Свинина", protein_per_100g=16, fat_per_100g=27, carbs_per_100g=0, kcal_per_100g=305, price_per_kg=650, mass_kg=5.0),
        IngredientForCalc(id=2, name="Соль", protein_per_100g=0, fat_per_100g=0, carbs_per_100g=0, kcal_per_100g=0, price_per_kg=25, mass_kg=0.15),
    ]


def test_compute_yield_hot(sample_ingredients):
    program = [{"t_chamber": 80, "duration_min": 60}]
    raw, finished, losses = compute_yield(sample_ingredients, program, brine_method="сухой")
    assert losses == 36.0  # 32% hot + 4% dry salt
    assert finished == pytest.approx(5.15 * 0.64, 0.01)


def test_compute_yield_cold(sample_ingredients):
    program = [{"t_chamber": 20, "duration_min": 720}]
    raw, finished, losses = compute_yield(sample_ingredients, program, brine_method="мокрый")
    assert losses == 14.0  # 12% cold + 2% wet salt


def test_compute_yield_electro(sample_ingredients):
    program = [{"t_chamber": 25, "duration_min": 90, "electro_voltage_kv": 20}]
    raw, finished, losses = compute_yield(sample_ingredients, program)
    assert losses == 8.0  # electro only


def test_compute_bju(sample_ingredients):
    bju = compute_bju(sample_ingredients)
    assert bju.protein > 0
    assert bju.fat > 0
    assert bju.kcal > 0


def test_losses_capped_at_60():
    # Абсурдный сценарий: горячее + сухой + ещё что-то не должно превысить 60%
    ingredients = [IngredientForCalc(id=1, name="Тест", protein_per_100g=0, fat_per_100g=0, carbs_per_100g=0, kcal_per_100g=0, price_per_kg=1, mass_kg=1.0)]
    program = [{"t_chamber": 80, "duration_min": 60}]
    raw, finished, losses = compute_yield(ingredients, program, brine_method="сухой")
    assert losses <= 60.0
```

## 4. Интеграционные тесты (recipes)

```python
# tests/test_recipes.py
import pytest

@pytest.mark.asyncio
async def test_create_recipe(client, auth_headers):
    response = await client.post("/api/v1/recipes", json={
        "name": "Тестовый рецепт",
        "slug": "test-recipe",
        "product_id": 1,
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Тестовый рецепт"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_calc_recipe(client, auth_headers):
    # Сначала создать рецепт с версией
    response = await client.get("/api/v1/recipes/1/calc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "bju_per_100g" in data
    assert "cost_per_kg_finished" in data
    assert "losses_percent" in data
```

## 5. Запуск тестов

```bash
# Все тесты
cd backend && pytest -v

# С покрытием
cd backend && pytest --cov=app --cov-report=html

# Конкретный файл
cd backend && pytest tests/test_recipe_calc.py -v

# С дебагом
cd backend && pytest tests/test_recipes.py -v --tb=short
```

## 6. Чек-лист

- [ ] `conftest.py` с fixtures для db, client, auth
- [ ] Юнит-тесты для `recipe_calc.py` (все типы копчения)
- [ ] Интеграционные тесты для auth
- [ ] Интеграционные тесты для recipes CRUD
- [ ] Интеграционные тесты для batches lifecycle
- [ ] Интеграционные тесты для telemetry REST
- [ ] Тест seed на idempotентность
- [ ] Покрытие > 60% для `services/`

## 7. Связь с другими скиллами

- `smoke-platform` — общие правила
- `recipe-calc` — тестируемый модуль
- `db-migrations` — тестовая БД должна быть актуальной

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при написании или запуске тестов.
