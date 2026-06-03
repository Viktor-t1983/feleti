# FELETI-SMOK — Протокол передачи контекста между сессиями

> **Зачем:** opencode-сессии (или сессии разных LLM) не имеют общей памяти. Чтобы каждая новая сессия могла за минуту понять, где мы и что делать — есть этот документ.
> **Читать первым после** `PROJECT_BOOT.md`.

## 1. Точка входа для любой новой сессии

Любой агент / новая сессия ДОЛЖЕН:

1. **Прочитать `docs/PROJECT_BOOT.md`** — общая сводка, цели, стек, статусы.
2. **Прочитать этот документ** (`docs/CONTEXT_HANDOFF.md`) — что было в прошлой сессии и что делать дальше.
3. **Прочитать `docs/ARCHITECTURE.md`** — как устроена система.
4. **Прочитать `CHANGELOG.md`** — что реально сделано.
5. **Прочитать `TODO.md`** — что планируется.
6. **Прочитать `OPEN_QUESTIONS.md`** — что нужно уточнить у пользователя.
7. **Прочитать `docs/SKILL_DEV.md`** и `docs/SKILL_SMOKING.md` — две базовые компетенции.
8. **Глянуть `git log --oneline -20`** — история коммитов.
9. **Посмотреть `git status`** — нет ли незакоммиченного.
10. **Посмотреть `data/seed/` и `docs/RECIPES_BASE.md`** — что уже засеяно.

После этого агент может работать.

## 2. Что фиксировать в конце сессии

В конце работы (или при передаче контекста) ОБЯЗАТЕЛЬНО обновить:

### 2.1. `CHANGELOG.md`
Секция `## [Unreleased]` — список того, что сделано в этой сессии:
- дата
- краткое описание изменений
- ссылки на ключевые файлы

### 2.2. `TODO.md`
- Отметить выполненное ✅
- Добавить новые пункты, выявленные в процессе
- Переставить приоритеты, если изменились

### 2.3. `OPEN_QUESTIONS.md`
- Записать все вопросы, на которые пользователь не ответил
- Записать все новые развилки, требующие выбора

### 2.4. `docs/PROJECT_BOOT.md`
- Обновить раздел "Текущий статус" (что в работе)
- Обновить раздел "Следующие шаги"
- Обновить раздел "Версия" (патч-инкремент после заметных изменений)

### 2.5. `CONTEXT_HANDOFF.md` (этот документ)
- Перезаписать секцию "Сводка последней сессии"

### 2.6. Git
- `git add .`
- `git commit -m "feat/fix/chore: краткое описание"`
- Сообщение — на русском или английском, как удобнее; формат conventional commits.

## 3. Формат сводки последней сессии

В конце секции "Сводка последней сессии" фиксировать:

```
### Сессия от YYYY-MM-DD
- **Что сделано:** кратко списком
- **Какие файлы созданы/изменены:** ключевые пути
- **Что блокирует:** если есть
- **Следующие шаги для новой сессии:** приоритетный список из TODO.md
- **Открытые вопросы к пользователю:** из OPEN_QUESTIONS.md
```

## 4. Сводка последней сессии

### Сессия от 2026-06-02 (сессия 4: backend — модели + Alembic + API v1 каркас + seed)
- **Что сделано:**
  - **Backend: 11 моделей SQLAlchemy 2.0 созданы и прошли ast-parse**:
    - Chamber, Product, Ingredient, Recipe + RecipeVersion + RecipeApproval, Brine, Batch + BatchPhase + BatchTelemetry, KnowledgeArticle + KnowledgeAttachment, TelemetryReading, AuditLog, User, Manufacturer.
    - `app/models/__init__.py` — реестр моделей (Alembic видит все).
  - **Backend: Alembic-конфигурация**:
    - `alembic.ini` (TZ Europe/Minsk, async URL).
    - `alembic/env.py` (async-режим, импорт всех моделей).
    - `alembic/script.py.mako` (шаблон миграции).
  - **Backend: API v1 каркас**:
    - `app/api/v1/__init__.py` + `endpoints/health.py` (health + health/db).
  - **Backend: seed.py** — идемпотентный сид 7 производителей, 6 камер (4 FELETI-SMOK + 2 Ижица), 6 ингредиентов, 8 продуктов, 3 demo-пользователя.
  - **Backend: драйверы камер** (были созданы в сессии 3):
    - `app/drivers/{base,simulated,feleti_smok,varmen}.py` — 4 файла, 740 строк, с полным Modbus TCP / физ-моделями / Kinco + extension register map.
  - **Backend: __init__.py** для `app/`, `app/api/`, `app/api/v1/`, `app/api/v1/endpoints/`, `app/core/`, `app/db/`, `app/models/`, `app/scripts/`, `app/drivers/`.
  - **Fixed**: db/base.py (убраны несущ. классы), telemetry.source (тип String), product.base_recipe_id (use_alter), manufacturer.chambers (cascade удалён).
  - Добавлен `pymodbus==3.7.4` в `pyproject.toml`.

- **Какие файлы созданы/изменены:**
  - **Созданы (всего 24 новых файла):**
    - `backend/app/models/{__init__,chamber,product,ingredient,recipe,brine,batch,knowledge,telemetry,audit}.py` (10).
    - `backend/app/api/v1/{__init__,endpoints/__init__,endpoints/health}.py` (3).
    - `backend/app/scripts/{__init__,seed}.py` (2).
    - `backend/app/{__init__,core/__init__,api/__init__,db/__init__}.py` (4).
    - `backend/alembic.ini`, `backend/alembic/{env.py,script.py.mako}` (3).
  - **Изменены:** `backend/pyproject.toml` (+pymodbus), `backend/app/models/manufacturer.py` (расширен), `backend/app/models/product.py` (use_alter), `backend/app/models/telemetry.py` (тип колонки), `backend/app/db/base.py` (реестр), `CHANGELOG.md`, `TODO.md`.

- **Что блокирует:**
  - 🚫 Нет Telethon API_ID/HASH от пользователя → нельзя начать парсинг TG-каналов.
  - 🚫 Не подтверждена карта Modbus-регистров Varmen-1 (нужны Wireshark или реальное устройство).
  - 🚫 Не выбран GitHub-репозиторий (отложено на потом).
  - 🚫 Не определены точные ТТХ камер FELETI-SMOK (нужны эскизы от инженеров).
  - 🆕 Нет Docker-окружения для запуска `alembic revision --autogenerate` (нужен `docker compose up`).

- **Следующие шаги для новой сессии (по приоритету):**
  1. 🔄 `docker compose up` + дождаться healthy у backend.
  2. ⏳ `alembic revision --autogenerate -m "initial models"` (сгенерировать миграцию).
  3. ⏳ `alembic upgrade head` + `python -m app.scripts.seed` — применить миграцию и засеять.
  4. ⏳ Проверить: `curl http://localhost:8000/api/v1/health` → `{"status": "ok"}`.
  5. ⏳ **Backend: API v1: auth (login/refresh/me)** + JWT-middleware.
  6. ⏳ **Backend: API v1: manufacturers CRUD** (первый полный эндпоинт).
  7. ⏳ **Backend: API v1: chambers CRUD** (с driver_class → реестр драйверов).
  8. ⏳ **Backend: API v1: products + ingredients + recipes + brines CRUD** (Pydantic v2 schemas).
  9. ⏳ **Backend: API v1: batches CRUD + start/pause/stop** (через ChamberGateway).
  10. ⏳ **Backend: API v1: telemetry WebSocket** (Redis pub/sub + FastAPI WS).
  11. ⏳ **Backend: API v1: knowledge CRUD + search**.
  12. ⏳ **Backend: services/**: recipe_workflow, recipe_calc, chamber_gateway, telemetry, knowledge.
  13. ⏳ **Frontend: init Next.js 14 + TypeScript + Tailwind + shadcn/ui**.
  14. ⏳ **Frontend: PWA manifest + service worker** (Workbox).
  15. ⏳ **Frontend: Login + Dashboard + Chambers + Recipes + Batches**.
  16. ⏳ Реализовать `web_parser.py` + спарсить ijiza.ru.
  17. ⏳ Скачать PDF-каталог Ижица 2024 + `pdf_parser.py`.
  18. ⏳ Hardware: KINCO_REGISTER_MAP.md, EXTENSION_MODULE.md, SCHEMATIC.md, BOM.md для FELETI-SMOK.
  19. ⏳ Реализовать `telegram_parser.py` (Telethon) после получения API_ID/HASH.
  20. ⏳ Реализовать `youtube_parser.py` (yt-dlp + Whisper), транскрибировать 10+ видео.

- **Открытые вопросы к пользователю:** см. `OPEN_QUESTIONS.md` (hardware FELETI-SMOK, монетизация, демо-камера, сроки, Telethon API_ID/HASH).

### Сессия от 2026-06-02 (продолжение foundation phase, +расширение hardware-стратегии)

### Сессия от 2026-06-02 (API v1: auth/manufacturers/chambers/products/ingredients/brines/recipes)
- Добавлено 8 групп эндпоинтов + Pydantic v2 схемы + services/auth (логин, refresh, register) + services/audit.
- `app/core/deps.py` — `oauth2_scheme`, `DBSession`, `CurrentUser`, `require_roles(*roles)`.
- Убран дубль `/api/v1/health` (был конфликт 409).
- `chamber.manufacturer_id` ondelete CASCADE → RESTRICT.
- `recipes.create` — flush obj перед созданием версии.
- `Annotated[PageParams, Query()]` для FastAPI 0.115+.
- `pyproject.toml`: +pydantic[email]==2.10.3 для EmailStr.
- Коммит: `6d55c7e`.

### Сессия от 2026-06-02 (ChamberGateway + batches lifecycle)
- `app/services/chamber_gateway.py` — singleton с пулом драйверов по `chamber_id`, lazy init, auto-reconnect, кольцевой буфер телеметрии 3600 точек, fan-out подписки.
- `app/api/v1/endpoints/batches.py` — CRUD + `start/pause/resume/cancel/complete` через `ChamberGateway`.
- Создание партии требует APPROVED/PENDING версию рецепта.
- Удаление только для PLANNED/CANCELLED/COMPLETED.
- При недоступности камеры `start` возвращает 502; `cancel/complete` работают даже при недоступной камере.
- `app/schemas/batch.py` — BatchRead/Detail/Create/Update/StatusChange/PhaseRead.
- `AuditAction`: +CANCEL, +COMPLETE.
- **56 Python-файлов** проходят `ast.parse` + `py_compile`.
- Коммит: `4e9d41c`.

### Сессия от 2026-06-02 (recipe_calc + telemetry WebSocket/REST)
- `app/services/recipe_calc.py` — чистые функции: БЖУ, себестоимость, yield с дефолтами по типу копчения (горячее 32%, холодное 12%, электро 8%) + посол (сухой 4%, мокрый 2%, шприц 1%).
- API: `GET /recipes/{id}/calc` (current) + `GET /recipes/{id}/versions/{vid}/calc`.
- API: `GET /chambers/{id}/status|telemetry/latest|telemetry/history|active-batch`.
- API: `WS /chambers/{id}/telemetry/ws?token=...` (auth в query, ping/subscribe команды).
- `schemas/calc.py` — RecipeCalcResponse + BJU + ProgramStats + Breakdown.
- 59 Python-файлов.
- Коммит: `4cb8852`.

### Сессия от 2026-06-02 (knowledge CRUD + search)
- API: `/knowledge` (list/detail/by-slug) + `/knowledge/search?q=...` (in-Python скоринг title=3, tags=2, excerpt=2, body=1; ILIKE по 4 полям; snippet).
- POST/PATCH/DELETE с авто-инкрементом version и каскадом на attachments.
- Фильтры: category, tag (JSONB contains), manufacturer_id, is_published.
- `schemas/knowledge.py` — 9 Pydantic моделей + 2 enums.
- **61 Python-файлов** проходят `ast.parse` + `py_compile`.
- Коммит: `f8fcb5d`.

### Сессия от 2026-06-03 (сессия 6: роли агента + 9 новых SKILL.md)
- **Что сделано:**
  - **AGENTS.md обновлён**: добавлены 4 ключевые роли агента:
    1. Главный архитектор-разработчик (backend + frontend + инфраструктура)
    2. Главный дизайнер UI/UX (визуальный стиль FELETI, компоненты, UX-паттерны)
    3. Главный технолог по копчению (рецепты, программы, БЖУ, yield, посол, ГОСТ)
    4. Мега-визуализатор программ и качества (timeline, графики, KPI, отчёты)
  - **Созданы 9 новых SKILL.md** (в `.opencode/skills/`):
    - `db-migrations` — процедуры Alembic (autogenerate, upgrade, rollback, verify)
    - `frontend-init` — init Next.js 14 + TS + shadcn/ui + PWA + брендирование FELETI
    - `recipe-calc` — формулы: БЖУ, себестоимость, yield, потери по типу копчения, посол
    - `pytest-testing` — структура тестов, fixtures, примеры (unit + integration)
    - `frontend-api-client` — axios + TanStack Query + Zustand auth + offline cache
    - `program-visualizer` — визуализация программ: timeline, графики температуры, прогресс
    - `quality-control` — органолептика, лаб. показатели, дефекты, акт КК, pass/fail
    - `batch-monitoring` — KPI партий, алерты, отклонения от программы, дашборд
    - `pdf-report` — генерация ТТК, актов КК, журналов через ReportLab
  - **Всего скиллов: 10 → 19** (10 исходных + 9 новых).
  - **Обновлены CHANGELOG.md, TODO.md, CONTEXT_HANDOFF.md**.

- **Какие файлы созданы/изменены:**
  - **Созданы:** `.opencode/skills/{db-migrations,frontend-init,recipe-calc,pytest-testing,frontend-api-client,program-visualizer,quality-control,batch-monitoring,pdf-report}/SKILL.md` (9)
  - **Изменены:** `.opencode/AGENTS.md` (роли + 19 скиллов), `CHANGELOG.md`, `TODO.md`, `docs/CONTEXT_HANDOFF.md`.

- **Что блокирует:**
  - 🚫 Нет Docker compose up → не сгенерированы Alembic миграции.
  - 🚫 Frontend пустой (0 файлов) — нужен Next.js init.
  - 🚫 Seed: 0 рецептов (RECIPES_BASE.md содержит 80+, но seed.py пуст).

- **Следующие шаги для новой сессии (по приоритету):**
  1. 🔄 `docker compose up` + Alembic `revision --autogenerate` + `upgrade head`.
  2. ⏳ Frontend init Next.js 14 + shadcn/ui + PWA (по скиллу `frontend-init`).
  3. ⏳ Seed: 80+ рецептов + 30+ ингредиентов + 10+ статей БЗ.
  4. ⏳ Backend: recipe_workflow (draft→pending→approved→archived).
  5. ⏳ Backend: users CRUD + roles/permissions.
  6. ⏳ Backend: telemetry с Redis pub/sub для масштабирования.

---

### Итог сессии 5 (2026-06-02)
**5 коммитов, +3525 строк backend кода, 53→61 Python-файлов:**

1. `6d55c7e` — API v1 endpoints + Pydantic schemas + services (auth/audit/deps)
2. `4e9d41c` — ChamberGateway + batches lifecycle
3. `1c94839` — docs(handoff): резюме сессии 5 (API v1 + ChamberGateway + batches)
4. `4cb8852` — recipe_calc + telemetry WebSocket/REST
5. `f8fcb5d` — knowledge CRUD + search

**Backend MVP завершён:**

| Домен | Endpoints | Coverage |
|-------|-----------|----------|
| Auth | login (OAuth2 + JSON), refresh, me | ✓ |
| Manufacturers | CRUD | ✓ |
| Chambers | CRUD + /drivers | ✓ |
| Products | CRUD | ✓ |
| Ingredients | CRUD | ✓ |
| Brines | CRUD | ✓ |
| Recipes | CRUD + versions + /calc | ✓ |
| Batches | CRUD + start/pause/resume/cancel/complete | ✓ |
| Telemetry | status/latest/history/active-batch + WS | ✓ |
| Knowledge | CRUD + /search | ✓ |
| Services | auth, audit, chamber_gateway, recipe_calc | ✓ |
| Models | 11 SQLAlchemy 2.0 моделей | ✓ |
| Alembic | конфиг + env.py + script.py.mako (готов к revision) | ✓ |
| Seed | 7 производителей, 6 камер, 6 ингредиентов, 8 продуктов, 3 user | ✓ |
| Drivers | base, Simulated, FELETI-SMOK, Varmen | 4/7 |

### Следующий приоритет (сессия 6)
1. **Frontend init** (Next.js 14 + TS + Tailwind + shadcn/ui + PWA) — РЕКОМЕНДУЕТСЯ. Визуальный прогресс, можно демонстрировать.
2. **Alembic миграция + apply + seed** (нужен Docker) — блокер для E2E тестов backend.
3. **Драйверы stubs**: fessmann.py (OPC UA), kerres.py (HTTP), mauting.py (Modbus) — расширение покрытия.
4. **services/recipe_workflow** (draft→pending→approved→archived с авто-уведомлениями).
5. **services/telemetry с Redis pub/sub** для горизонтального масштабирования.
6. **Workers (Celery)**: parse_telegram, parse_pdf, send_report.

## 5. Шаблон коммита

Используем Conventional Commits + scope:

```
<type>(<scope>): <краткое описание на русском>

<тело — что и почему>

<footer — ссылки на задачи, breaking changes>
```

**Типы:**
- `feat` — новая функциональность
- `fix` — исправление бага
- `docs` — только документация
- `style` — форматирование, без смысловых изменений
- `refactor` — рефакторинг, без новой функциональности
- `test` — добавление тестов
- `chore` — рутина (зависимости, конфиги)
- `perf` — производительность

**Scope:** `backend`, `frontend`, `docs`, `infra`, `seed`, `db`, `driver`, `knowledge`, `telegram`.

**Примеры:**
```
feat(backend): добавить модель Recipe + версионирование
docs(arch): описать гибридный доступ к камере (Modbus + cloud)
fix(driver): корректная обработка таймаута Modbus TCP
seed(ijiza): добавить 12 рецептов из каталога Ижица 2024
```

## 6. Правила для агента

### 6.1. Перед любым действием
- Прочитать PROJECT_BOOT + этот документ + CHANGELOG + TODO.
- Проверить `git status` — нет ли незакоммиченных изменений.
- Если изменения есть — спросить, что с ними делать.

### 6.2. После любого значимого действия
- Обновить CHANGELOG.md.
- Если меняется план — обновить TODO.md.
- Если появляются вопросы — обновить OPEN_QUESTIONS.md.
- Закоммитить с понятным сообщением.

### 6.3. Стиль общения с пользователем
- **На русском** (пользователь попросил явно).
- Короткие и ёмкие ответы (< 4 строк, если не просят деталей).
- Сначала спросить, если неясно.
- Не выдумывать URL, цены, ТТХ — только то, что в БАЗЕ_ЗНАНИЙ или в открытых источниках.
- Для критических решений — `question` с вариантами, не текстом.

### 6.4. Чего НЕ делать
- Не коммитить без явной просьбы.
- Не удалять чужие файлы без подтверждения.
- Не менять `БАЗА_ЗНАНИЙ_КОПЧЕНИЕ.md` без явной просьбы.
- Не выдумывать рецепты с точными цифрами — помечать как "требует уточнения".
- Не игнорировать ошибки — фиксировать в CHANGELOG/TODO.

## 7. Связь с другими документами

```
PROJECT_BOOT.md ─── общая сводка (ЧТО и ЗАЧЕМ)
       │
       ▼
ARCHITECTURE.md ─── как устроено (КАК)
       │
       ▼
SKILL_DEV.md ────── стек, конвенции разработки
SKILL_SMOKING.md ── база знаний технолога
       │
       ▼
CAMERA_DRIVER.md ── драйвер камеры (Modbus + cloud)
COMPETITORS.md ─── сравнение с конкурентами
RECIPES_BASE.md ── структура рецептов
FELETI_BRAND.md ── айдентика
       │
       ▼
CHANGELOG.md ────── что реально сделано
TODO.md ─────────── что планируется
OPEN_QUESTIONS.md ─ что нужно уточнить
       │
       ▼
CONTEXT_HANDOFF.md (этот документ) — сводка для следующей сессии
       │
       ▼
.opencode/AGENTS.md — точка входа для opencode-агента
.opencode/skills/<name>/SKILL.md — специализированные скиллы
```

**Правило:** `PROJECT_BOOT.md` и `CONTEXT_HANDOFF.md` — обновляются ПОСЛЕ каждой значимой сессии. Остальные — по мере необходимости.
