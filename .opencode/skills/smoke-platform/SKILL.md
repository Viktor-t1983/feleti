# SKILL: smoke-platform (главный)

> Базовый скилл для FELETI-SMOK. Загружай при ЛЮБОЙ задаче по проекту.

## 1. Что это

**FELETI-SMOK** — fullstack-платформа (hardware + software) для управления коптильным производством. Бренд FELETI (Беларусь, Брест) входит на рынок коптильного оборудования с собственной линейкой камер + софтверной платформой, конкурент Ижицы/Varmen.

**Hardware-стратегия (зафиксировано 2026-06-02):**
- **Profi H** (горячее): 100/150/200/250 кг.
- **Profi C** (холодное + охлаждение, NEW): 100/200/250 кг + холодильный агрегат R404A/R290 (-5…+25°C).
- **Profi U** (универсал, NEW): 200/250 кг — горячее + холодное + электро + охлаждение в одной камере.
- **C-Ultra / U-Frost** (опция): заморозка полуфабриката (-18…-25°C, шоковая).
- **Контроллер**: Kinco HMI/PLC (Китай, MT 4514 HMI + K7 PLC) + **свой модуль расширения** (RPi CM4, Modbus TCP port 503, электростатика, edge-AI, MQTT-мост).
- **Электростатика 10–30 кВ** — опция (апгрейд-модуль).
- **Дымогенератор свой**: щепа + фрикционный (диск ⌀300мм) + атомайзер.
- **Датчики — всегда максимальная комплектация**: Pt100×2 + Pt100×1-3 (продукт), влажность, дым, ΔP, ток ТЭН, опц. газоанализатор/весы/pH.

**Software-стратегия:**
- **Стек:** Next.js 14 + FastAPI + PostgreSQL + Redis + MinIO + Docker Compose.
- **Ключевые фичи:** версионирование рецептов, workflow-апрув, offline PWA, in-app чат+AI, голосовое управление, Modbus TCP + cloud гибрид.
- **Стиль:** современный, информативный, FELETI-бренд (ч/б + красный `#E30613`).

## 2. Точка входа

Перед началом работы прочитай:
1. `docs/PROJECT_BOOT.md`
2. `docs/CONTEXT_HANDOFF.md` (сводка последней сессии)
3. `CHANGELOG.md`, `TODO.md`, `OPEN_QUESTIONS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SKILL_DEV.md`, `docs/SKILL_SMOKING.md`
6. `docs/CAMERA_DRIVER.md`
7. `docs/COMPETITORS.md`, `docs/RECIPES_BASE.md`, `docs/FELETI_BRAND.md`

После прочтения — `git status` и `git log --oneline -10`.

## 3. Специализированные скиллы

| Скилл | Когда загружать |
|---|---|
| `smoke-platform` | Всегда первым (этот файл) |
| `add-recipe` | Создание/редактирование рецепта + /calc |
| `add-chamber` | Добавление камеры (модель, ТТХ, драйвер) |
| `camera-driver` | Работа с драйверами камер + ChamberGateway |
| `batches-lifecycle` | Создание/запуск партий, интеграция с камерой |
| `telemetry-websocket` | Live-стрим телеметрии (WS + REST) |
| `knowledge-search` | CRUD базы знаний + полнотекстовый поиск |
| `seed-data` | Сидирование начальных данных |
| `design-system` | Брендирование UI (FELETI Red, dark/light) |
| `research-competitor` | Парсинг сайта/каталога конкурента |

**Правило:** если задача подходит под скилл — загрузи его ПЕРЕД началом.

## 4. Принципы разработки

### 4.1. Стек
- **Frontend:** Next.js 14 (App Router, TS strict), shadcn/ui, Tailwind, Recharts, Zustand, RHF+Zod, TanStack Query, Workbox (PWA), Dexie (offline), next-intl (i18n).
- **Backend:** FastAPI 0.115+, SQLAlchemy 2.0 async, Alembic, Pydantic v2, asyncpg, redis-py, pymodbus, asyncua (OPC UA), Celery, loguru, prometheus_client.
- **Infra:** PostgreSQL 16, Redis 7, MinIO, Mosquitto (MQTT), Adminer, Nginx, Docker Compose.

### 4.2. Стиль кода
- **Python:** type hints везде, async где I/O, snake_case, Pydantic v2 (`T | None` вместо `Optional[T]`).
- **TypeScript:** strict mode, no `any` без причины, camelCase, RHF+Zod.
- **Без комментариев в коде** (если пользователь не просил).
- **Идемпотентные миграции** (Alembic).
- **UTC** во всех датах (`datetime.now(timezone.utc).replace(tzinfo=None)`).

### 4.3. Архитектура
- **API-first**, REST + WebSocket.
- **Domain-driven** — модели, сервисы, валидации; UI/API — адаптеры.
- **Modbus-first, cloud-second** — локальный канал приоритет.
- **Версионирование рецептов** — иммутабельная история.
- **Audit trail** — все мутации логируются через `services/audit.py`.
- **ChamberGateway pattern**: singleton, пул драйверов, кольцевой буфер 3600 точек, fan-out подписки.

### 4.4. Безопасность
- HTTPS everywhere, CORS whitelist, JWT (httpOnly cookie).
- RBAC: admin / technologist / operator / manager / viewer.
- Audit log всех изменений (`AuditAction` enum: CREATE/UPDATE/DELETE/APPROVE/REJECT/LOGIN/LOGOUT/START/PAUSE/RESUME/STOP/CANCEL/COMPLETE/EXPORT/IMPORT/OTHER).
- Только ORM (без сырого SQL).
- PII в БД, бэкапы зашифрованы.

## 5. Структура репозитория

```
koptilnya-platform/
├── docs/                          # Документация
│   ├── PROJECT_BOOT.md
│   ├── ARCHITECTURE.md
│   ├── CAMERA_DRIVER.md
│   ├── CONTEXT_HANDOFF.md
│   ├── COMPETITORS.md
│   ├── RECIPES_BASE.md
│   ├── FELETI_BRAND.md
│   ├── SKILL_DEV.md
│   ├── SKILL_SMOKING.md
│   ├── cameras/<manufacturer>/    # Спецификации камер
│   └── research/                  # Сырые данные парсинга
├── .opencode/
│   ├── AGENTS.md                  # ← читается агентом первым
│   └── skills/<name>/SKILL.md     # 10 специализированных скиллов
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── __init__.py        # api_router (агрегатор)
│   │   │   └── endpoints/         # health, auth, manufacturers, chambers,
│   │   │                          # products, ingredients, brines, recipes,
│   │   │                          # batches, telemetry, knowledge
│   │   ├── core/                  # config, security, deps (get_db, get_current_user, require_roles)
│   │   ├── db/                    # session (engine), base (DeclarativeBase)
│   │   ├── models/                # 11 SQLAlchemy 2.0 моделей + __init__.py (реестр)
│   │   ├── schemas/               # Pydantic v2 DTO
│   │   ├── services/              # audit, auth, chamber_gateway, recipe_calc
│   │   ├── drivers/               # Плагины камер (base + simulated + feleti_smok + varmen)
│   │   ├── scripts/               # seed.py (идемпотентный)
│   │   ├── workers/               # Celery (TODO)
│   │   └── main.py                # FastAPI app + lifespan
│   ├── alembic/
│   │   ├── env.py                 # async, импорт app.db.base
│   │   └── script.py.mako
│   ├── alembic.ini
│   ├── tests/                     # TODO
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                      # TODO: Next.js 14
│   ├── app/                       # App Router
│   ├── components/
│   ├── lib/                       # api/, ws/, stores/, offline/, utils/
│   ├── public/                    # PWA-манифест, иконки
│   └── package.json
├── nginx/                         # конфиги
├── data/                          # Тома (не в git)
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   └── uploads/
├── .env.example
├── docker-compose.yml
├── README.md
├── CHANGELOG.md
├── TODO.md
├── OPEN_QUESTIONS.md
└── RECOMMENDATIONS.md             # рекомендации по развитию
```

## 6. Реальные эндпоинты (backend MVP, сессия 5)

> Все пути под префиксом `/api/v1`. Auth через JWT (Bearer), кроме `/auth/*` и `/health`.

### Auth
- `POST /auth/login` — OAuth2 password flow (Swagger UI)
- `POST /auth/login/json` — JSON-вариант для PWA
- `POST /auth/refresh` — refresh access token
- `GET /auth/me` — текущий пользователь

### System
- `GET /health` — статус сервиса
- `GET /health/db` — проверка подключения к БД

### CRUD ресурсы
| Ресурс | Endpoints |
|---|---|
| `manufacturers` | `GET/POST /`, `GET/PATCH/DELETE /{id}` |
| `chambers` | `GET/POST /`, `GET /drivers`, `GET/PATCH/DELETE /{id}` |
| `products` | `GET/POST /`, `GET/PATCH/DELETE /{id}` |
| `ingredients` | `GET/POST /`, `GET/PATCH/DELETE /{id}` |
| `brines` | `GET/POST /`, `GET/PATCH/DELETE /{id}` |
| `recipes` | `GET/POST /`, `GET/PATCH/DELETE /{id}`, `GET /{id}/versions`, `POST /{id}/versions`, `GET /{id}/calc`, `GET /{id}/versions/{vid}/calc` |
| `batches` | `GET/POST /`, `GET/PATCH/DELETE /{id}`, `POST /{id}/start\|pause\|resume\|cancel\|complete` |

### Telemetry (live + REST)
- `GET /chambers/{id}/status` — running/paused/phase
- `GET /chambers/{id}/telemetry/latest` — последний сэмпл из буфера
- `GET /chambers/{id}/telemetry/history?limit=600` — последние N точек
- `GET /chambers/{id}/active-batch` — текущая RUNNING/PAUSED партия
- `WS /chambers/{id}/telemetry/ws?token=...` — live-стрим

### Knowledge
- `GET/POST /knowledge` — список с пагинацией / создание
- `GET /knowledge/{id}` — детальная карточка
- `GET /knowledge/by-slug/{slug}` — для SEO
- `GET /knowledge/search?q=...` — поиск (title=3, tags=2, excerpt=2, body=1)
- `PATCH /knowledge/{id}` — обновление (с авто-инкрементом version)
- `DELETE /knowledge/{id}`

## 7. Workflow апрува рецепта

```
[Технолог]  draft  ──submit_for_approval──►  pending        ← TODO endpoint
                                               │
                                               ▼
[Старший технолог / Админ]
                                               │
                             ┌─────────────────┼─────────────────┐
                             ▼                 ▼                 ▼
                         approved          rejected    changes_requested
                             │                 │                 │
                             ▼                 ▼                 ▼
                        (current)           (архив)        (→ draft)
                             │
                             ▼ (через время/правки)
                         archived            ← TODO автоматический переход
```

**Ключевые правила:**
- `Recipe` — общий заголовок, ссылается на `current_version`.
- `RecipeVersion` — **иммутабельный**, содержит всю программу.
- Создание новой версии: `parent_version_id` указывает на предыдущую.
- Апрув — отдельная сущность `RecipeApproval` с комментарием.
- Создание партии требует `APPROVED` или `PENDING` версию.
- **TODO**: endpoint `/recipes/{id}/versions/{vid}/approve` + `/reject` + авто-архивация старых версий.

## 8. Гибридный доступ к камере

| Сценарий | Канал | Задержка | Поведение |
|---|---|---|---|
| Камера в цехе, LAN OK | Modbus TCP (LAN) | <100 мс | Приоритет |
| Камера в цехе, LAN down | MQTT (облако) | 0.5–2 с | Fallback |
| Удалённый мониторинг | MQTT (облако) | 0.5–2 с | Основной |
| Оффлайн (PWA без сети) | Кеш (IndexedDB) | — | Read-only |

**Команды** (start/pause/stop/cancel/complete) идут **только по Modbus TCP** для надёжности.
**Телеметрия** зеркалируется в оба канала (дедупликация по `ts+chamber_id`).
**ChamberGateway** — singleton, абстрагирует канал от драйвера, поддерживает:
- Пул инстансов драйверов (lazy init, per-chamber Lock)
- Кольцевой буфер 3600 точек на камеру
- Fan-out подписки (для WebSocket)
- Auto-reconnect при обрыве

## 9. Связь с другими скиллами

- `add-recipe` — для создания рецептов и /calc.
- `add-chamber` — для добавления камер в каталог.
- `camera-driver` — для работы с драйверами камер и ChamberGateway.
- `batches-lifecycle` — для создания и запуска партий.
- `telemetry-websocket` — для live-телеметрии.
- `knowledge-search` — для базы знаний.
- `seed-data` — для сидирования начальных данных.
- `design-system` — для брендирования UI.
- `research-competitor` — для парсинга конкурентов.

## 10. Частые ошибки

1. Забыл обновить `CHANGELOG.md` после изменений.
2. Забыл добавить модель в `models/__init__.py` — Alembic не увидит.
3. Использовал `Optional` вместо `T | None` (Pydantic v2 style).
4. Сделал миграцию без данных — `alembic upgrade head` упадёт на prod.
5. Использовал `datetime.now()` без tz — нужна UTC (`datetime.now(timezone.utc).replace(tzinfo=None)`).
6. Забыл `await` в async-SQLAlchemy — TypeError.
7. Положил секрет в Git — `git filter-branch` или перевыпуск.
8. Использовал `print()` вместо `logging` — не попадёт в JSON-логи.
9. Сделал UI без `prefers-reduced-motion` — нарушил a11y.
10. Использовал больше 5% красного на экране — нарушил бренд.
11. Забыл `Annotated[PageParams, Query()]` для query-параметров в FastAPI 0.115+.
12. `EmailStr` без `pydantic[email]` — ImportError.
13. `recipe_version.recipe=obj` создан ДО `flush(obj)` — `obj.id=None`, FK не работает.
14. `cascade="all, delete-orphan"` на `Manufacturer.chambers` — удалит камеры с историей партий.
15. Забыл `gateway.start_batch` для партий — драйвер не получит команду.

## 11. Полезные команды

```bash
# Backend
cd backend && python -m uvicorn app.main:app --reload --port 8000
cd backend && alembic revision --autogenerate -m "msg"
cd backend && alembic upgrade head
cd backend && python -m app.scripts.seed
cd backend && ruff check .  # TODO
cd backend && mypy app/      # TODO

# Frontend (после init)
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run lint
cd frontend && npm run type-check

# Docker
docker compose up -d
docker compose ps
docker compose logs -f backend
docker compose down
docker compose exec backend bash

# Git
git status
git log --oneline -10
git diff
git add -A && git commit -m "feat(scope): ..."
```

## 12. Зарегистрированные драйверы камер

| Имя | Класс | Протокол | Контроллер |
|---|---|---|---|
| `SimulatedDriver` | `app/drivers/simulated.py` | — (мок с физ-моделью) | — |
| `FELETI_SMOKDriver` | `app/drivers/feleti_smok.py` | Modbus TCP :503 | Kinco + свой модуль |
| `VarmenDriver` | `app/drivers/varmen.py` | Modbus TCP :502 | Varmen-1 (Ижица) |
| `FessmannDriver` | TODO | OPC UA | FOOD.CON 2 |
| `KerresDriver` | TODO | HTTP/REST | собственный |
| `MautingDriver` | TODO | Modbus TCP | Siemens S7 |
| `AGROSDriver` | TODO | Modbus TCP | собственный |
| `ReichDriver` | TODO | Modbus/Profinet | собственный |

**Регистрация**: `@register("Name")` декоратор, импорт в `app/drivers/__init__.py`.

## 13. Модели данных (11)

| Модель | Назначение |
|---|---|
| `User` | Пользователи (admin/technologist/operator/manager/viewer + is_superuser) |
| `Manufacturer` | Производители камер (с is_our_brand, is_competitor, sort_order) |
| `Chamber` | Камеры (с driver_class, default_driver_config) |
| `Product` | Продукты (колбасы, мясо, рыба, сыр, ...) |
| `Ingredient` | Ингредиенты (с БЖУ и ценой) |
| `Brine` | Посолы (переиспользуемые между рецептами) |
| `Recipe` + `RecipeVersion` + `RecipeApproval` | Рецепты с иммутабельным версионированием |
| `Batch` + `BatchPhase` + `BatchTelemetry` | Партии (запуски) с фазами и сырой телеметрией |
| `KnowledgeArticle` + `KnowledgeAttachment` | База знаний (8 категорий, 5 типов вложений) |
| `TelemetryReading` | Сырая телеметрия вне партий (для мониторинга) |
| `AuditLog` | Лог всех мутаций (15 AuditAction) |

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при ЛЮБОЙ задаче по FELETI-SMOK.
