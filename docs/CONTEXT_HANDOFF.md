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
