# CHANGELOG — FELETI-SMOK

> Все значимые изменения в проекте. Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).

---

## [Unreleased]

### В работе
- Backend: API v1: telemetry WebSocket (Redis pub/sub)
- Backend: API v1: knowledge CRUD + search
- Backend: services: recipe_workflow, recipe_calc, telemetry, knowledge
- Backend: workers (Celery): parse_telegram, parse_pdf, send_report
- Frontend: init Next.js 14 + shadcn/ui + PWA
- Реальный стенд FELETI-SMOK (R&D)
- Парсинг Ижицы: сайт + каталог + TG + YouTube (сессия 2+)

### Added (сессия 5, 2026-06-02 — backend API v1, часть 2: batches + gateway)
- **API v1: batches** (`backend/app/api/v1/endpoints/batches.py`):
  - `GET /batches` — пагинация + фильтры по `chamber_id`, `recipe_id`, `status`.
  - `GET /batches/{id}` — детальная карточка с фазами.
  - `POST /batches` — создание в PLANNED (с проверкой версии рецепта и камеры; версия рецепта должна быть APPROVED/PENDING).
  - `PATCH /batches/{id}` — обновление метаданных.
  - `DELETE /batches/{id}` — только для PLANNED/CANCELLED/COMPLETED.
  - `POST /batches/{id}/start` — загрузить программу в камеру через ChamberGateway и стартовать.
  - `POST /batches/{id}/pause` — пауза.
  - `POST /batches/{id}/resume` — снять с паузы.
  - `POST /batches/{id}/cancel` — остановить камеру + CANCELLED (с опциональной note).
  - `POST /batches/{id}/complete` — остановить камеру + COMPLETED.
- **ChamberGateway** (`backend/app/services/chamber_gateway.py`):
  - Singleton с пулом драйверов по `chamber_id` (lazy init + auto-reconnect).
  - Кольцевой буфер телеметрии на камеру (3600 точек ≈ 1 час @ 1 Hz).
  - Подписки (fan-out) для будущего WebSocket.
  - `start_batch(chamber_id, driver_class, connection, recipe_program)` — главный метод запуска.
  - Защита от двойного подключения (per-chamber asyncio.Lock).
- **Pydantic v2: schemas/batch.py**:
  - `BatchRead`, `BatchDetail`, `BatchCreate`, `BatchUpdate`, `BatchStatusChange`, `BatchPhaseRead`.
- **AuditAction**: добавлены `CANCEL`, `COMPLETE` (раньше не было).
- Все 56 Python-файлов проходят `ast.parse` и `py_compile`.

### Notes
- Жизненный цикл партии: `PLANNED → RUNNING → PAUSED ⇄ RUNNING → COMPLETED | CANCELLED`.
- Удаление разрешено только для финальных статусов (PLANNED/CANCELLED/COMPLETED).
- При недоступности камеры (502) партия НЕ стартует и остаётся в прежнем статусе; cancel/complete работают даже при недоступной камере.
- ChamberGateway.shutdown() — не вызывается автоматически; добавить в lifespan при старте FastAPI (следующая сессия).

---

## [Unreleased] (предыдущая сессия)

### В работе (на момент завершения сессии 4)
- Backend: API v1 для всех сущностей
- Frontend: init Next.js 14 + shadcn/ui + PWA
- Реальный стенд FELETI-SMOK (R&D)

### Added (сессия 5, 2026-06-02 — backend API v1)
- **API v1: auth** (`backend/app/api/v1/endpoints/auth.py`):
  - `POST /auth/login` (OAuth2 password flow, для Swagger UI).
  - `POST /auth/login/json` (JSON-вариант для PWA).
  - `POST /auth/refresh` (refresh-токены, 7× access TTL).
  - `GET /auth/me` (текущий пользователь, с аудит-логом).
- **API v1: manufacturers CRUD** (пагинация, фильтры `is_our_brand`/`is_competitor`, аудит).
- **API v1: chambers CRUD** (фильтры по типу, поддержке электро/холода, verified; валидация `driver_class` через реестр; `GET /chambers/drivers` для списка драйверов).
- **API v1: products CRUD** (фильтр по категории).
- **API v1: ingredients CRUD** (фильтры по `type` и `wood_species` для щепы).
- **API v1: brines CRUD** (фильтр по `method`).
- **API v1: recipes CRUD + версионирование**:
  - Создание рецепта с опциональной первой иммутабельной версией.
  - `GET /recipes/{id}/versions` — список версий.
  - `POST /recipes/{id}/versions` — создание новой версии (авто-инкремент version_number).
- **Pydantic v2 schemas** (`backend/app/schemas/`):
  - `common.py` (APIModel, Page[T], PageParams, HealthResponse, MessageResponse).
  - `auth.py` (LoginRequest, RefreshRequest, Token, TokenPayload).
  - `user.py` (UserRead, UserCreate, UserUpdate, UserRoleEnum).
  - `manufacturer.py`, `chamber.py`, `product.py`, `ingredient.py`, `brine.py`, `recipe.py` — Read/Create/Update + Enum-ы.
  - Все схемы: `from_attributes=True`, `use_enum_values=True` (корректная сериализация enum в JSON).
- **Backend: services/**
  - `audit.py` — запись событий в AuditLog.
  - `auth.py` — аутентификация (login по username/email, выдача access+refresh, обновление last_login_at, регистрация).
- **Backend: deps**
  - `app/core/deps.py` — `oauth2_scheme`, `DBSession`, `CurrentUser`, `require_roles(...)` (RBAC dependency factory).
- **Alembic/Backend fixes**:
  - `chamber.py` — `manufacturer_id` теперь `ondelete="RESTRICT"` (раньше был CASCADE; удаление производителя больше не уничтожает историю партий).
  - `user.py` — добавлен `__repr__`.
  - `main.py` — убран дубль `/api/v1/health` (был конфликт с `api_router`).
  - `pyproject.toml` — добавлен `pydantic[email]==2.10.3` (для `EmailStr`).

### Fixed
- **Конфликт маршрутов**: `main.py:41` объявлял `@app.get("/api/v1/health")` и `api_router.health` тоже на `/health` → FastAPI выдавал 409. Удалён дубль.
- **EmailStr без зависимости**: в `pydantic` v2 `EmailStr` требует `pydantic[email]`. Добавлено в `pyproject.toml`.
- **PageParams как query**: исправлено на `params: Annotated[PageParams, Query()]` во всех эндпоинтах (иначе FastAPI ожидал body).
- **recipes.create race**: `RecipeVersion.recipe=obj` создавался ДО flush `obj` (когда `obj.id=None`). Теперь сначала flush, потом version с явным `recipe_id=obj.id`.

### Notes
- **53 файла проходят `ast.parse`** без ошибок.
- API v1 endpoints требуют **JWT-аутентификации** (кроме `/health`, `/auth/login`, `/auth/login/json`, `/auth/refresh`). Все остальные endpoints используют `CurrentUser` dependency.
- Все мутации (CREATE/UPDATE/DELETE) пишут в `audit_logs` с actor_id, before/after, ip, user_agent.
- Идемпотентность API не реализована (Idempotency-Key) — это для следующей сессии.

---

## [Unreleased] (предыдущая сессия)

### В работе (на момент завершения сессии 4)
- Backend: API v1 для всех сущностей
- Frontend: init Next.js 14 + shadcn/ui + PWA
- Реальный стенд FELETI-SMOK (R&D)

### Added (сессия 4, 2026-06-02 — модели + Alembic + каркас)
  - `app/models/__init__.py` — реестр моделей.
  - `app/models/chamber.py` — Chamber (FELETI-SMOK Profi H/C/U, Ижица, ...) + ChamberType enum.
  - `app/models/product.py` — Product (Докторская, Сёмга х/к, ...) + ProductCategory enum (14 категорий).
  - `app/models/ingredient.py` — Ingredient (мясо, щёпа по породам, соль, специи) + IngredientType enum + БЖУ/аллергены.
  - `app/models/recipe.py` — Recipe (заголовок) + RecipeVersion (иммутабельная версия с программой фаз, посолом, ingredients, БЖУ, себестоимостью) + RecipeApproval (workflow: draft → pending → approved → archived).
  - `app/models/brine.py` — Brine (отдельная сущность для переиспользования: dry/wet/injection/combo, salt%, sugar%, нитрит/нитрат ppm, специи).
  - `app/models/batch.py` — Batch (партия) + BatchPhase (фаза с planned/actual) + BatchTelemetry (сырая телеметрия по партии).
  - `app/models/knowledge.py` — KnowledgeArticle (база знаний, markdown/html) + KnowledgeAttachment (PDF/видео/изображения) + ArticleCategory enum (9 категорий).
  - `app/models/telemetry.py` — TelemetryReading (поток от камер, 7 дней raw → агрегаты → архив 1 год).
  - `app/models/audit.py` — AuditLog (все мутации: actor, action, entity, before/after, ip, ua, extra).
- **Backend: Alembic-конфигурация:**
  - `backend/alembic.ini` — настройки Alembic (async, TZ Europe/Minsk, формат имени файла).
  - `backend/alembic/env.py` — async-режим, импорт всех моделей через `app.db.base`.
  - `backend/alembic/script.py.mako` — шаблон миграции.
- **Backend: API v1 каркас:**
  - `app/api/v1/__init__.py` — api_router (агрегатор).
  - `app/api/v1/endpoints/__init__.py` + `health.py` — health-check + health/db.
- **Backend: scripts/seed.py:**
  - Идемпотентный сид: 7 производителей (feleti, ijiza, mauting, fessmann, kerres, agros, reich), 6 камер (4 FELETI-SMOK + 2 Ижица), 6 ингредиентов (3 мяса + 2 щёпы + 2 соли), 8 продуктов, 3 demo-пользователя (admin/tech/operator).
- **Backend: драйверы камер** (ранее):
  - `app/drivers/base.py` — ChamberDriver (abstract) + ChamberCapabilities + ChamberTelemetry + ChamberProgramPhase.
  - `app/drivers/__init__.py` — реестр через `@register("name")`.
  - `app/drivers/simulated.py` — мок с физ-моделью (T_chamber, T_product, инерция, фазы).
  - `app/drivers/feleti_smok.py` — FELETI-SMOK driver (Kinco :502 + свой модуль :503, полная карта регистров).
  - `app/drivers/varmen.py` — Ижица Varmen-1 (Modbus TCP, DRAFT register map).
- `backend/pyproject.toml` — добавлен `pymodbus==3.7.4` для Varmen/FELETI-SMOK драйверов.
- `backend/app/models/manufacturer.py` — расширен: is_our_brand, is_competitor, sort_order (нужны для бренда FELETI + сортировки в каталоге).
- `backend/app/core/config.py`, `security.py`, `db/session.py`, `db/base.py` — ранее созданы.
- `docs/research/{README,ijiza,mauting,fessmann,kerres,dilers}/README.md` — план глубокого парсинга (ранее).
- `docs/cameras/feleti-smok/SPEC.md` — спецификация камер FELETI-SMOK Profi H/C/U (ранее).
- `docs/RECIPES_BASE.md` — 80+ рецептов (ранее).
- `docs/SKILL_SMOKING.md` — расширен холодным копчением, охлаждением, заморозкой (ранее).

### Fixed
- `db/base.py` — убраны несуществующие импорты (ChamberFeature, RecipeStep, RecipeIngredient, BrineIngredient, BatchReading, Gost, TelegramChannel, Video). Теперь импортируются реальные классы.
- `telemetry.py` — у колонки `source` указан тип `String(50)` (раньше был без типа + неправильный `server_default=func.now()`).
- `product.py` — FK `base_recipe_id → recipes.id` теперь с `use_alter=True` (избегаем циклической зависимости с `Recipe.product_id`).
- `manufacturer.py` — убран опасный `cascade="all, delete-orphan"` на chambers (иначе удаление производителя = удаление всех камер с потерей истории партий).

### Notes
- Backend не запускается локально без `pip install -e .` (SQLAlchemy 1.4 → 2.0, asyncpg, pymodbus). Проверка — только в Docker-окружении (`docker compose up backend`).
- Все 28 Python-файлов проходят `ast.parse` без ошибок.
- Модели готовы к autogenerate миграции: `docker compose exec backend alembic revision --autogenerate -m "initial"` (после запуска контейнера).
- Seed-скрипт идемпотентен: повторный запуск не дублирует записи (по slug/email).
- **Линейка FELETI-SMOK расширена** (сессия 3, по запросу пользователя):
  - Profi H (горячее): 100/150/200/250 кг.
  - **Profi C (холодное + охлаждение, новинка):** 100/200/250 кг с холодильным агрегатом.
  - **Profi U (универсал, новинка):** 200/250 кг — горячее + холодное + электро + охлаждение в одной камере.
- `docs/cameras/feleti-smok/SPEC.md` — добавлены секции:
  - **Холодное копчение** (Profi C): программы для сёмги, форели, скумбрии, сыра, сала, балыка.
  - **Охлаждение готовой продукции** (Profi C/U): соответствие СанПиН.
  - **Заморозка полуфабриката** (Profi C-Ultra / U-Frost, опция).
  - **Полугорячее копчение** (Profi H, расширенный режим).
  - **Холодильный агрегат**: R404A/R290, T -5…+25°C, инверторный компрессор, оттайка.
  - **Таблица электрики** для H/C/U линеек.
- `docs/research/README.md` — общий план парсинга (Ижица P0, Mauting/Fessmann/Kerres P1, остальные P2-P3).
- `docs/research/ijiza/README.md` — детальный план парсинга Ижицы (сайт, каталоги, TG, YouTube, дилеры).
- `docs/research/mauting/README.md` — план по Mauting.
- `docs/research/fessmann/README.md` — план по Fessmann + FES.APP.
- `docs/research/kerres/README.md` — план по Kerres + Jet Smoke + Hybrid Airflow.
- `docs/research/dilers/README.md` — план по дилерам в РФ/СНГ.
- `docs/RECIPES_BASE.md` — расширена база рецептов: **80+** стартовых (было 50+).
  - **Холодное копчение + охлаждение (17 рецептов)**: сёмга, форель, скумбрия, палтус, сиг, осётр, балык, грудинка, корейка, сало, сыры, масло, сырокопчёные колбасы.
  - **Полугорячее копчение (5 рецептов)**: сельдь, скумбрия, треска, курица, свинина.
  - **Охлаждение (4 рецепта)**: после г/к, после п/к, подсушка, хранение.
  - **Сыры/прочее (8 рецептов)**: сыр, сало, масло, орехи, чеснок, перец, соль.
- `docs/SKILL_SMOKING.md` — расширены разделы:
  - **Холодное копчение — подробно** (Profi C-линейка): применение, параметры, технологические нюансы, оборудование, Ижица UTR-C.
  - **Охлаждение готовой продукции** (Profi C/U): СанПиН 2.3/2.4.3590-20, ТР ТС 021/2011, преимущества.
  - **Заморозка полуфабриката** (Profi C-Ultra / U-Frost): шоковая заморозка, Ижица UTR-F.

### Changed
- `docs/cameras/feleti-smok/SPEC.md` — добавлены Profi C и Profi U линейки с холодным копчением, охлаждением и заморозкой (по запросу пользователя).
- `docs/RECIPES_BASE.md` — расширена секция «Типы копчения» (добавлены C, U, F, ELE линейки FELETI-SMOK).
- `docs/SKILL_SMOKING.md` — таблица видов копчения дополнена колонкой «Камера FELETI-SMOK».

### Решено (продолжение)
- **По запросу пользователя:** FELETI-SMOK Profi C (холодное + охлаждение) и Profi U (универсал) добавлены в линейку. Источники: холодное копчение и охлаждение у Ижицы (UTR-C, UTR-F), Mauting (туннели), Fessmann (Turbomat с предварит. охлаждением).
- **Создана структура для глубокого парсинга** (`docs/research/`): Ижица — приоритет P0, остальные — P1-P3.

---

## [0.1.0] — 2026-06-02 (foundation)

### Added
- Инициализирован проект `koptilnya-platform` (Git, README, .gitignore, .env.example, docker-compose).
- Backend skeleton: `Dockerfile`, `pyproject.toml` (FastAPI 0.115, SQLAlchemy 2.0 async, asyncpg, alembic, pymodbus, asyncua, reportlab, loguru).
- `app/main.py` — FastAPI app, lifespan, CORS, healthcheck.
- `app/core/config.py` — Pydantic Settings.
- `app/core/security.py` — bcrypt + JWT.
- `app/db/base.py` — SQLAlchemy DeclarativeBase, модель-реестр для Alembic.
- `app/db/session.py` — async engine, sessionmaker.
- `app/models/user.py` — User + UserRole enum (admin/technologist/operator/manager/viewer).
- `app/models/manufacturer.py` — Manufacturer.
- Структура `.opencode/skills/` с 6 каталогами: smoke-platform, add-recipe, add-chamber, camera-driver, seed-data, design-system.
- `docs/PROJECT_BOOT.md` — главная точка входа.
- `docs/CAMERA_DRIVER.md` — универсальный драйвер (Modbus TCP + cloud).
- `docs/SKILL_DEV.md` — стек и конвенции разработки.
- `docs/SKILL_SMOKING.md` — база знаний технолога.
- `docs/ARCHITECTURE.md` — C4-архитектура.
- `docs/CONTEXT_HANDOFF.md` — протокол передачи контекста.
- `docs/COMPETITORS.md` — детальная матрица конкурентов.
- `docs/RECIPES_BASE.md` — структура базы рецептов (50+ стартовых).
- `docs/FELETI_BRAND.md` — айдентика (цвета, типографика, компоненты).
- `БАЗА_ЗНАНИЙ_КОПЧЕНИЕ.md` (в родительской папке) — общая база знаний о копчении.
- `docker-compose.yml` — 6 сервисов: postgres, redis, backend, frontend, adminer, minio.

### Changed
- (none — первый релиз)

### Fixed
- (none — первый релиз)

### Removed
- (none — первый релиз)

### Notes
- Проект находится в фазе **foundation** (документация + скелет backend).
- Hardware-стратегия FELETI-SMOK зафиксирована: Kinco + свой модуль, Profi/Industrial B2B, свой дымогенератор, электростатика как опция.
- GitHub-репозиторий — отложен (по запросу пользователя "потом").

---

## Шаблон для следующих версий

```markdown
## [X.Y.Z] — YYYY-MM-DD

### Added
- Что добавлено (фичи, файлы, API).

### Changed
- Что изменилось (рефакторинг, улучшения).

### Fixed
- Что исправлено (баги).

### Removed
- Что удалено.

### Notes
- Важные заметки для следующих сессий.
```
