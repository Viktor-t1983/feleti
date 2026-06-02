# SKILL: smoke-platform (главный)

> Базовый скилл для FELETI-SMOK. Загружай при ЛЮБОЙ задаче по проекту.

## 1. Что это

**FELETI-SMOK** — fullstack-платформа (hardware + software) для управления коптильным производством. Бренд FELETI (Беларусь, Брест) входит на рынок коптильного оборудования с собственной линейкой камер + софтверной платформой, конкурент Ижицы/Varmen.

**Hardware-стратегия (зафиксировано 2026-06-02):**
- Profi/Industrial B2B (100–250+ кг).
- Контроллер: **Kinco HMI/PLC** (Китай) + **свой модуль расширения**.
- Электростатика — **опция** (апгрейд-модуль).
- Датчики — **всегда максимальная комплектация**.
- Дымогенератор — **свой** (щепа + фрикционный + атомайзер).

**Software-стратегия:**
- **Стек:** Next.js 14 + FastAPI + PostgreSQL + Redis + MinIO + Docker Compose.
- **Ключевые фичи:** версионирование рецептов, workflow-апрув, offline PWA, in-app чат+AI, голосовое управление, Modbus TCP + cloud гибрид.
- **Стиль:** современный, информативный, FELETI-бренд (ч/б + красный `#E30613`).

## 2. Точка входа

Перед началом работы прочитай:
1. `docs/PROJECT_BOOT.md`
2. `docs/CONTEXT_HANDOFF.md`
3. `CHANGELOG.md`, `TODO.md`, `OPEN_QUESTIONS.md`
4. `docs/ARCHITECTURE.md`
5. `docs/SKILL_DEV.md`, `docs/SKILL_SMOKING.md`
6. `docs/CAMERA_DRIVER.md`
7. `docs/COMPETITORS.md`, `docs/RECIPES_BASE.md`, `docs/FELETI_BRAND.md`

После прочтения — `git status` и `git log --oneline -10`.

## 3. Специализированные скиллы

| Скилл | Когда загружать |
|---|---|
| `add-recipe` | Создание/редактирование рецепта |
| `add-chamber` | Добавление камеры (модель, ТТХ, драйвер) |
| `camera-driver` | Работа с драйверами камер (Kinco, Varmen, ...) |
| `seed-data` | Сидирование начальных данных |
| `design-system` | Брендирование UI |
| `research-competitor` | Парсинг сайта/каталога конкурента |

**Правило:** если задача подходит под скилл — загрузи его ПЕРЕД началом.

## 4. Принципы разработки

### 4.1. Стек
- **Frontend:** Next.js 14 (App Router, TS strict), shadcn/ui, Tailwind, Recharts, Zustand, RHF+Zod, TanStack Query, Workbox (PWA), Dexie (offline), next-intl (i18n).
- **Backend:** FastAPI 0.115+, SQLAlchemy 2.0 async, Alembic, Pydantic v2, asyncpg, redis-py, pymodbus, asyncua (OPC UA), Celery, loguru, prometheus_client.
- **Infra:** PostgreSQL 16, Redis 7, MinIO, Mosquitto (MQTT), Adminer, Nginx, Docker Compose.

### 4.2. Стиль кода
- **Python:** type hints везде, async где I/O, snake_case, Pydantic v2.
- **TypeScript:** strict mode, no `any` без причины, camelCase, RHF+Zod.
- **Без комментариев в коде** (если пользователь не просил).
- **Идемпотентные миграции.**

### 4.3. Архитектура
- **API-first**, REST + WebSocket.
- **Domain-driven** — модели, сервисы, валидации; UI/API — адаптеры.
- **Modbus-first, cloud-second** — локальный канал приоритет.
- **Версионирование рецептов** — иммутабельная история.
- **Audit trail** — все мутации логируются.

### 4.4. Безопасность
- HTTPS everywhere, CORS whitelist, JWT (httpOnly cookie).
- RBAC: admin / technologist / operator / manager / viewer.
- Audit log всех изменений.
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
│   ├── AGENTS.md
│   └── skills/<name>/SKILL.md
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── drivers/                # Плагины камер
│   │   └── workers/                # Celery
│   ├── alembic/
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/                        # App Router
│   ├── components/
│   ├── lib/                        # api/, ws/, stores/, offline/, utils/
│   ├── public/                     # PWA-манифест, иконки
│   └── package.json
├── nginx/
├── data/                           # Тома (не в git)
│   ├── postgres/
│   ├── redis/
│   ├── minio/
│   └── uploads/
├── .env.example
├── docker-compose.yml
├── README.md
├── CHANGELOG.md
├── TODO.md
└── OPEN_QUESTIONS.md
```

## 6. Ключевые эндпоинты (план)

| Метод | URL | Назначение |
|---|---|---|
| POST | `/api/v1/auth/login` | Логин (JWT) |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Текущий пользователь |
| GET | `/api/v1/manufacturers` | Список производителей |
| GET | `/api/v1/chambers` | Список камер |
| GET | `/api/v1/chambers/{id}` | Детали камеры |
| GET | `/api/v1/recipes` | Список рецептов |
| POST | `/api/v1/recipes` | Создать рецепт (draft) |
| GET | `/api/v1/recipes/{id}/versions` | Версии рецепта |
| POST | `/api/v1/recipes/{id}/versions` | Новая версия |
| POST | `/api/v1/recipes/{id}/versions/{v}/approve` | Апрув |
| GET | `/api/v1/recipes/{id}/diff?v1=2&v2=3` | Diff версий |
| POST | `/api/v1/batches` | Создать партию |
| POST | `/api/v1/batches/{id}/start` | Запустить |
| POST | `/api/v1/batches/{id}/pause` | Пауза |
| POST | `/api/v1/batches/{id}/resume` | Продолжить |
| POST | `/api/v1/batches/{id}/stop` | Стоп |
| GET | `/api/v1/batches/{id}/telemetry` | История телеметрии |
| WS | `/api/v1/telemetry/ws?chamber_id=...` | Live-телеметрия |
| GET | `/api/v1/knowledge` | База знаний (с пагинацией, поиском, тегами) |
| POST | `/api/v1/chat/messages` | Отправить сообщение в чат |
| GET | `/api/v1/chat/history` | История чата |
| GET | `/api/v1/reports/batch/{id}/pdf` | PDF партии |

## 7. Workflow апрува рецепта

```
[Технолог]  draft  ──Отправить на апрув──►  pending
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
                        archived
```

**Ключевые правила:**
- `Recipe` — общий заголовок, ссылается на `current_version`.
- `RecipeVersion` — **иммутабельный**, содержит всю программу.
- Создание новой версии: `parent_version_id` указывает на предыдущую.
- Апрув — отдельная сущность `RecipeApproval` с комментарием.
- Diff версий — endpoint `/diff?v1=X&v2=Y`.

## 8. Гибридный доступ к камере

| Сценарий | Канал | Задержка | Поведение |
|---|---|---|---|
| Камера в цехе, LAN OK | Modbus TCP (LAN) | <100 мс | Приоритет |
| Камера в цехе, LAN down | MQTT (облако) | 0.5–2 с | Fallback |
| Удалённый мониторинг | MQTT (облако) | 0.5–2 с | Основной |
| Оффлайн (PWA без сети) | Кеш (IndexedDB) | — | Read-only |

**Команды** (start/pause/stop) идут **только по Modbus TCP** для надёжности.
**Телеметрия** зеркалируется в оба канала (дедупликация по `ts+chamber_id`).

## 9. Связь с другими скиллами

- `add-recipe` — для создания рецептов и рецепт-калькулятора.
- `add-chamber` — для добавления камер в каталог.
- `camera-driver` — для работы с драйверами камер.
- `seed-data` — для сидирования начальных данных.
- `design-system` — для брендирования UI.
- `research-competitor` — для парсинга конкурентов.

## 10. Частые ошибки

1. ❌ Забыл обновить `CHANGELOG.md` после изменений.
2. ❌ Забыл добавить модель в `db/base.py` — Alembic не увидит.
3. ❌ Использовал `Optional` вместо `T | None` (Pydantic v2 style).
4. ❌ Сделал миграцию без данных — `alembic upgrade head` упадёт на prod.
5. ❌ Использовал `datetime.now()` без tz — нужна UTC.
6. ❌ Забыл `await` в async-SQLAlchemy — TypeError.
7. ❌ Положил секрет в Git — `git filter-branch` или перевыпуск.
8. ❌ Использовал `print()` вместо `loguru` — не попадёт в JSON-логи.
9. ❌ Сделал UI без `prefers-reduced-motion` — нарушил a11y.
10. ❌ Использовал больше 5% красного на экране — нарушил бренд.

## 11. Полезные команды

```bash
# Backend
cd backend && uv run uvicorn app.main:app --reload --port 8000
cd backend && alembic revision --autogenerate -m "msg"
cd backend && alembic upgrade head
cd backend && ruff check .
cd backend && mypy app/

# Frontend
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
git add -A && git commit -m "feat: ..."
```

---

**Версия:** 0.1.0
**Загружай:** при ЛЮБОЙ задаче по FELETI-SMOK.
