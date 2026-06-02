# FELETI-SMOK — Архитектура системы

> **Версия:** 0.1.0 (2026-06-02)  
> **Статус:** в разработке (фаза foundation)  
> **Читать после:** `PROJECT_BOOT.md`

## 1. Цели и принципы

### 1.1. Цели
1. **Промышленная платформа** управления камерами копчения с телеметрией, рецептами, workflow-апрувом.
2. **База знаний** — структурированная: производители, рецепты, ГОСТы, физикохимия, проблемы/решения.
3. **In-app AI/чат/голосовое** — Copilot для технолога (RAG по базе знаний + рецепты + параметры камеры).
4. **PWA desktop+mobile** — единый клиент для цеха, офиса, выезда.
5. **Открытый API + Modbus TCP** — открытый протокол для интеграции с любым оборудованием.

### 1.2. Принципы
- **Domain-driven** — `domain/` — модели, сервисы, валидации; UI/API — адаптеры.
- **Скучная технология** — PostgreSQL+Redis+MinIO+Next.js+FastAPI — устоявшийся в проде стек.
- **API-first** — бэк не знает про UI; фронт общается по REST/OpenAPI.
- **Modbus-first, cloud-second** — локальное управление камерой всегда в приоритете; облако — для удалённого мониторинга/аналитики.
- **Offline PWA** — критические экраны (рецепт, текущая партия, аварии) работают без сети.
- **Версионирование рецептов** — иммутабельная история, workflow черновик→на апруве→утверждён→архив.
- **Audit trail** — все изменения фиксируются (кто, когда, что, до/после).

---

## 2. Системный контекст (C4 Level 1)

```
┌────────────────────────────────────────────────────────────────────────────┐
│  ВНЕШНИЕ АКТЁРЫ                                                            │
│  • Технолог (план/рецепты/апрув)                                           │
│  • Оператор цеха (запуск/контроль/аварии)                                  │
│  • Менеджер (отчёты/аналитика/КПЭ)                                         │
│  • Админ (настройка/пользователи/интеграции)                               │
│  • ИИ-копилот (RAG-ассистент по базе знаний)                               │
└────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │  HTTPS / WebSocket
                                    ▼
┌────────────────────────────────────────────────────────────────────────────┐
│  ПЛАТФОРМА FELETI-SMOK                                                     │
│  ┌──────────────────────┐         ┌──────────────────────┐                │
│  │   PWA-фронтенд       │ ◄─────► │   FastAPI-бэкенд     │                │
│  │   Next.js 14         │  REST   │   Python 3.11        │                │
│  │   shadcn/ui + Tail   │  WSS    │   SQLAlchemy 2 async │                │
│  │   Zustand + RHF      │         │   Pydantic v2        │                │
│  │   TanStack Query     │         │   Alembic            │                │
│  └──────────────────────┘         └──────────┬───────────┘                │
│                                                │                            │
│  ┌──────────────────────┐                     │                            │
│  │   Mobile/PWA         │                     │                            │
│  │   Service Worker     │                     │                            │
│  │   IndexedDB cache    │                     │                            │
│  └──────────────────────┘                     │                            │
└────────────────────────────────────────────────┼────────────────────────────┘
                                                │
        ┌───────────────────┬───────────────────┼───────────────────┐
        │                   │                   │                   │
        ▼                   ▼                   ▼                   ▼
   ┌─────────┐        ┌──────────┐        ┌──────────┐        ┌──────────┐
   │PostgreSQL│        │  Redis   │        │  MinIO   │        │Шлюз      │
   │  16      │        │  7       │        │  (S3)    │        │камер     │
   │  asyncpg │        │  broker  │        │ файлы/   │        │локальн.  │
   │          │        │  + cache │        │ pdf/img  │        │ModbusTCP │
   └─────────┘        └──────────┘        └──────────┘        └────┬─────┘
                                                                     │
                                                          ┌──────────┴──────────┐
                                                          │ Modbus TCP (LAN)    │
                                                          │ MQTT/HTTPS (cloud)  │
                                                          └──────────┬──────────┘
                                                                     │
                                                                     ▼
                                                              ┌──────────────┐
                                                              │ КАМЕРЫ        │
                                                              │ Ижица/Varmen  │
                                                              │ Fessmann      │
                                                              │ Kerres        │
                                                              │ Mauting       │
                                                              │ FELETI-SMOK   │
                                                              └──────────────┘
```

---

## 3. Контейнеры (C4 Level 2)

| Контейнер | Технология | Назначение |
|---|---|---|
| **frontend** | Next.js 14 + shadcn/ui + Tailwind | UI/PWA (desktop+mobile) |
| **backend** | FastAPI + SQLAlchemy 2.0 async | API + бизнес-логика + WebSocket |
| **postgres** | PostgreSQL 16 | Данные (OLTP) |
| **redis** | Redis 7 | Кеш + WebSocket-брокер + Celery broker |
| **minio** | MinIO (S3-совместимый) | Файлы (PDF, изображения, видео-туториалы) |
| **adminer** | Adminer 4 | Менеджер БД (только dev) |
| **chamber-gateway** | Python-сервис | Modbus TCP ↔ камеры, телеметрия → бэкенд |
| **telegram-parser** | Python (Telethon) | Парсинг TG-каналов → база знаний |
| **nginx** | nginx 1.27 | Reverse proxy, static, TLS |

---

## 4. Архитектура бэкенда (внутри контейнера `backend`)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, lifespan, CORS, exception handlers
│   ├── api/                    # HTTP-роуты (по доменам)
│   │   ├── v1/
│   │   │   ├── auth.py        # /login, /refresh, /me
│   │   │   ├── users.py
│   │   │   ├── manufacturers.py
│   │   │   ├── chambers.py
│   │   │   ├── products.py
│   │   │   ├── ingredients.py
│   │   │   ├── recipes.py     # + версионирование, workflow
│   │   │   ├── brines.py
│   │   │   ├── batches.py     # запуски партий
│   │   │   ├── telemetry.py   # WS-эндпоинт для дашборда
│   │   │   ├── chat.py        # in-app chat + AI/RAG
│   │   │   ├── knowledge.py   # база знаний
│   │   │   └── reports.py
│   ├── core/
│   │   ├── config.py          # Pydantic Settings
│   │   ├── security.py        # bcrypt + JWT
│   │   ├── deps.py            # FastAPI Depends (current_user, db, rbac)
│   │   ├── logging.py         # loguru, JSON-логи
│   │   └── errors.py
│   ├── db/
│   │   ├── base.py            # SQLAlchemy DeclarativeBase
│   │   ├── session.py         # async engine, sessionmaker
│   │   └── migrations/        # Alembic
│   ├── models/                # SQLAlchemy ORM (1 файл = 1 агрегат)
│   │   ├── user.py
│   │   ├── manufacturer.py
│   │   ├── chamber.py
│   │   ├── product.py
│   │   ├── ingredient.py
│   │   ├── recipe.py          # + RecipeVersion, RecipeApproval
│   │   ├── brine.py
│   │   ├── batch.py
│   │   ├── telemetry.py
│   │   ├── knowledge.py       # статьи, теги
│   │   └── audit.py           # audit log
│   ├── schemas/               # Pydantic v2 DTO (request/response)
│   │   └── (зеркало models/)
│   ├── services/              # бизнес-логика
│   │   ├── auth.py
│   │   ├── recipe_workflow.py # черновик→на апруве→утверждён→архив
│   │   ├── recipe_calc.py     # расчёт БЖУ, себестоимости, соли
│   │   ├── chamber_gateway.py # абстракция камеры
│   │   ├── telemetry.py       # буферизация, batch insert
│   │   ├── knowledge.py       # поиск, тегирование
│   │   ├── chat.py            # RAG/AI
│   │   ├── pdf_parser.py
│   │   ├── telegram_parser.py
│   │   └── report.py
│   ├── drivers/               # драйверы камер (плагины)
│   │   ├── base.py            # интерфейс ChamberDriver
│   │   ├── simulated.py       # мок для dev
│   │   ├── varmen.py          # Ижица Varmen (Modbus TCP)
│   │   ├── fessmann.py        # OPC UA
│   │   ├── kerres.py          # HTTP API
│   │   ├── mauting.py         # Modbus TCP
│   │   └── feleti_smok.py     # наша камера
│   ├── workers/               # Celery (фоновые задачи)
│   │   ├── celery_app.py
│   │   ├── tasks/
│   │   │   ├── parse_telegram.py
│   │   │   ├── parse_pdf.py
│   │   │   └── send_report.py
│   └── utils/
│       ├── pagination.py
│       ├── filters.py
│       └── i18n.py            # ru/en
├── alembic.ini
├── pyproject.toml
└── Dockerfile
```

### 4.1. Слои (Clean Architecture lite)
```
api (роутеры)
  ↓ depends on
services (сценарии использования)
  ↓ depends on
models (ORM)  +  db (session)
  ↑
repositories (CRUD-обёртки, опционально)
```

**Правила:**
- `api/` не лезет в `db/` напрямую — только через `services/`.
- `services/` не возвращает ORM — только DTO (`schemas/`) или доменные объекты.
- `models/` — без бизнес-логики (только поля, constraints, relationships).

---

## 5. Архитектура фронтенда (контейнер `frontend`)

```
frontend/
├── app/                       # Next.js 14 App Router
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── (dashboard)/
│   │   ├── layout.tsx        # sidebar + header
│   │   ├── page.tsx          # обзор
│   │   ├── chambers/         # список/детали камер, телеметрия live
│   │   ├── recipes/          # список, создание, версионирование, апрув
│   │   ├── batches/          # партии: создание, запуск, мониторинг
│   │   ├── products/         # продукты (изделия)
│   │   ├── ingredients/      # ингредиенты + щёпа
│   │   ├── manufacturers/    # справочник
│   │   ├── knowledge/        # база знаний, статьи
│   │   ├── chat/             # in-app чат + AI-копилот
│   │   ├── reports/          # отчёты
│   │   └── settings/
│   ├── api/                   # API-роуты (прокси, если нужно)
│   ├── manifest.json         # PWA manifest
│   └── sw.ts                 # service worker (Workbox)
├── components/
│   ├── ui/                   # shadcn-примитивы
│   ├── chambers/
│   ├── recipes/
│   ├── telemetry/            # live-графики (Recharts), WS-клиент
│   ├── chat/
│   └── layout/
├── lib/
│   ├── api/                  # fetch-клиенты (axios/fetch + react-query)
│   ├── ws/                   # WebSocket-менеджер
│   ├── stores/               # Zustand stores (auth, ui)
│   ├── offline/              # IndexedDB (Dexie) + sync-логика
│   └── utils/
├── hooks/
├── public/
│   ├── icons/                # PWA-иконки 192/512/maskable
│   └── locales/              # ru.json, en.json (next-intl)
├── styles/
│   └── globals.css
├── next.config.mjs
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

### 5.1. Ключевые фичи фронта
- **shadcn/ui** — без библиотечного бойлерплейта, копируем код.
- **TanStack Query** — кеш, рефетч, optimistic updates, offline-aware.
- **Zustand** — UI-state (модалки, выбранные фильтры, online/offline).
- **React Hook Form + Zod** — формы + валидация (тип-безопасно с бэком).
- **Recharts** — графики телеметрии (температура, влажность, дым, Δt).
- **next-pwa / Workbox** — manifest + service worker + offline-shell.
- **Dexie** — IndexedDB-обёртка для оффлайн-рецептов и справочников.

---

## 6. Модель данных (ключевые сущности)

### 6.1. Пользователь и роли
- `User`: id, email, hashed_password, full_name, role, is_active, created_at.
- `UserRole` (enum): `admin`, `technologist`, `operator`, `manager`, `viewer`.
- **RBAC**-матрица: `admin` всё; `technologist` — recipes/brines/knowledge write; `operator` — batches read+write start/pause/stop; `manager` — reports read; `viewer` — только read.

### 6.2. Справочники
- `Manufacturer`: id, name, country, website, contacts, notes.
- `Chamber`: id, manufacturer_id, model, type (горячее/холодное/электро), max_load_kg, volume_m3, power_kw, voltage_v, supports_static_smoke, supports_electro, supports_joint, supported_protocols (jsonb), driver_class, default_driver_config (jsonb), images (jsonb), description.
- `Product`: id, name (например, "Докторская ГОСТ"), category (колбаса/рыба/птица/сыр/прочее), base_recipe_id?, images, description.
- `Ingredient`: id, name, type (мясо/специя/соль/щёпа/другое), unit, default_nutrition, default_price_per_unit, allergens, is_allergen, gmo_flag.

### 6.3. Рецепты и версионирование
- `Recipe`: id, product_id, name, slug, current_version_id, status (draft|pending|approved|archived), created_by, created_at.
- `RecipeVersion` (иммутабельный): id, recipe_id, version_number, parent_version_id?, parameters (jsonb — программа копчения: фазы, температуры, времена, влажность, дым, щепа, эл.поле), brine (jsonb), ingredients (jsonb — с весами), yield_percent, losses_percent, notes, created_by, created_at, status.
- `RecipeApproval`: id, recipe_version_id, approver_id, decision (approved|rejected|changes_requested), comment, decided_at.

### 6.4. Партии (запуски)
- `Batch`: id, recipe_version_id, chamber_id, operator_id, planned_start, actual_start, actual_end, status (planned|queued|running|paused|completed|cancelled|failed), yield_kg, notes.
- `BatchPhase` (факт): batch_id, phase_index, name, planned_at, actual_start, actual_end, set_temperature, measured_temperature, smoke_on, electro_voltage, notes.
- `BatchTelemetry` (поток): id, batch_id, ts, t_chamber, t_product, humidity, smoke_density, electro_voltage, electro_current, fan_rpm, door_open, errors. Партиционирование по `ts` (месяц).

### 6.5. Телеметрия (отдельный поток, горячие данные)
- `TelemetryReading`: id, chamber_id, ts, payload (jsonb). TimescaleDB / партиции по месяцам.
- Ретенция: 7 дней raw → архив 1 год по агрегатам (1 мин / 1 час / 1 день).

### 6.6. Знания
- `KnowledgeArticle`: id, title, slug, body_md, body_html, category (theory/recipe/troubleshooting/regulation/comparison), tags (array), manufacturer_id?, chamber_model?, author_id, created_at, updated_at, version, is_published.
- `KnowledgeAttachment`: id, article_id, file_id (MinIO), kind (pdf|video|image|doc).
- `KnowledgeTag`: tag, count (денормализация).

### 6.7. Аудит
- `AuditLog`: id, actor_id, action, entity_type, entity_id, before (jsonb), after (jsonb), ts, ip, user_agent.

---

## 7. Камера: гибридный доступ (ключевая фича)

### 7.1. Два режима работы
| Режим | Протокол | Задержка | Когда |
|---|---|---|---|
| **Локальный Modbus TCP** | Modbus TCP (Ethernet, LAN) | <100 мс | Онлайн в цехе, offline-устойчиво |
| **Облако MQTT/HTTPS** | MQTT (бинарный) или HTTPS REST | 0.5–2 с | Удалённый мониторинг, аналитика |

### 7.2. Graceful degradation
- Бэкенд всегда **сначала пробует Modbus TCP** (быстрее, offline-safe).
- Если LAN недоступен — переключается на cloud-канал.
- Телеметрия **зеркалируется** в оба канала (для отказоустойчивости), дедупликация по `ts + chamber_id`.
- Команды (start/pause/stop) идут **по локальному каналу приоритетно**; облако — fallback.

### 7.3. Архитектура `ChamberGateway`
```
        ┌──────────────┐
        │   Бэкенд     │  (FastAPI-сервис)
        │  chamber_gw  │
        └──────┬───────┘
               │ внутренний API (gRPC/REST)
               │
        ┌──────▼────────────┐
        │  ChamberGateway   │  (отдельный Python-сервис или in-process)
        │  + DriverRegistry │
        └──┬───────┬────────┘
           │       │
   ┌───────▼─┐  ┌──▼────────┐
   │ Driver: │  │ Driver:   │
   │ Varmen  │  │ Simulated │
   │ (Modbus)│  │           │
   └────┬────┘  └───────────┘
        │
        │ Modbus TCP (порт 502, JSON-конфиг)
        ▼
   ┌─────────────┐         ┌──────────────┐
   │  Varmen-1   │ ◄──────►│  Varmen Cloud │ (опционально)
   │  (камера)   │         │  (HTTPS/MQTT) │
   └─────────────┘         └──────────────┘
```

Подробности — `docs/CAMERA_DRIVER.md`.

---

## 8. Дизайн API

### 8.1. Стиль
- **REST + JSON**, версионирование в URL (`/api/v1/...`).
- **OpenAPI** — генерируется автоматически, доступен по `/docs` (Swagger UI) и `/redoc`.
- **Идемпотентность** команд камеры: заголовок `Idempotency-Key`.
- **Pagination**: `?page=1&size=20&sort=created_at:desc` (cursor-based для телеметрии).
- **Модель ошибки**:
  ```json
  { "error": { "code": "RECIPE_NOT_APPROVED", "message": "...", "details": {...} } }
  ```

### 8.2. Авторизация
- **JWT** (HS256, 15 мин access + 7 дней refresh в httpOnly cookie).
- `Authorization: Bearer <access_token>`.
- RBAC через `Depends(require_role("admin"))`.

### 8.3. WebSocket
- `/api/v1/telemetry/ws?chamber_id=...` — live-поток.
- `/api/v1/chat/ws` — in-app чат с typing-индикатором.
- Reconnect с exponential backoff, очередь offline-команд.

---

## 9. Real-time и фон

### 9.1. WebSocket-менеджер
- Бэкенд: `FastAPI WebSocket` + Redis pub/sub для fan-out.
- Клиент: `WebSocketManager` (reconnect, queue, типизированные события).

### 9.2. Фоновые воркеры (Celery)
- `parse_telegram_channel` — периодический парсинг TG.
- `parse_pdf_catalog` — загрузка каталога → извлечение текста/таблиц.
- `aggregate_telemetry` — скользящие окна 1м/1ч/1д.
- `send_email_report` — ежедневный отчёт менеджеру.
- `ml_reindex` — переиндексация базы знаний для RAG (позже).

### 9.3. Телеметрия: буферизация и запись
- Камеры шлют данные с частотой 1 Гц (типично).
- In-memory буфер в chamber-gateway, батч 5 сек → бэкенд.
- Бэкенд: bulk insert в `telemetry_readings` (партиция по месяцам).
- Алерты (правила): превышение ΔT, отклонение от программы > N%, дверь открыта > 30 с → push/email.

---

## 10. Безопасность

- **HTTPS** везде (Nginx + Let's Encrypt).
- **CORS** — whitelist фронтенд-доменов.
- **Rate limit** — Redis-based, на login и sensitive endpoints.
- **Управление секретами** — `.env` локально, Docker secrets / Vault в проде.
- **Audit log** — все мутации.
- **SQL injection** — только ORM.
- **PII** — `email/phone` хранятся в БД, бэкапы шифруются.
- **CSP** — strict policy, nonce-based scripts.
- **CSRF** — double-submit cookie для state-changing запросов.
- **Зависимости** — `pip-audit`, `npm audit` в CI.

---

## 11. Наблюдаемость (Observability)

- **Логи** — `loguru`, JSON-формат, stdout → `docker logs` → Loki (позже).
- **Метрики** — `prometheus_client` на бэке (`/metrics`).
- **Трейсы** — OpenTelemetry (FastAPI + SQLAlchemy + requests), экспорт в Jaeger/Tempo.
- **Health** — `/health` (liveness), `/ready` (readiness: DB+Redis+MinIO).
- **Дашборды** — Grafana (камеры live, error rate, batch throughput, latency p95).

---

## 12. Деплой

### 12.1. Dev
```bash
docker compose up -d
# backend: http://localhost:8000
# frontend: http://localhost:3000
# adminer: http://localhost:8080
# minio: http://localhost:9001
```

### 12.2. Prod (roadmap)
- **VPS** (Hetzner/Timeweb) или собственный сервер.
- `docker compose -f docker-compose.prod.yml up -d`.
- TLS — Caddy или Nginx + Let's Encrypt.
- Backup: `pg_dump` ежедневно + MinIO bucket replication.
- CI/CD: GitHub Actions → build → push images → deploy.

---

## 13. Расширения (Roadmap)

| Версия | Что | Цель |
|---|---|---|
| v0.1 (сейчас) | Foundation, docs, models, drivers, seed | Каркас для разработки |
| v0.2 | UI: chambers live + recipes CRUD | Демонстрация концепта |
| v0.3 | Workflow approval + версионирование | Готово к пилоту |
| v0.4 | Offline PWA + IndexedDB | Полевой сценарий |
| v0.5 | In-app chat + RAG (база знаний) | AI-копилот |
| v0.6 | Голосовое управление (Whisper + intent) | Hands-free в цеху |
| v0.7 | Отчёты + email/PDF | Менеджмент |
| v0.8 | ML: авто-подбор программы, anomaly detection | Конкурент. преимущество |
| v1.0 | Промышленный пилот + Ижица-парсер в проде | Первый клиент |

---

## 14. Открытые архитектурные вопросы

- Multi-tenancy: один FELETI-SMOK для нескольких заводов? Пока — single-tenant.
- WebSocket transport: native WS vs Socket.IO — пока native, проще.
- Telemetry storage: vanilla Postgres partitions vs TimescaleDB — решаем по нагрузке.
- RAG: pgvector vs Qdrant — начнём с pgvector (меньше сервисов).
- Mobile app: нативное vs PWA-only — PWA-only (TWA/Capacitor как escape hatch).
- Голос: Whisper API vs локальный Whisper.cpp — локально (offline + privacy).

См. `OPEN_QUESTIONS.md` для деталей.

---

**Связанные документы:**
- `docs/PROJECT_BOOT.md` — общая сводка, что делаем
- `docs/CAMERA_DRIVER.md` — драйвер камеры (Modbus TCP + облако)
- `docs/SKILL_DEV.md` — стек и конвенции разработки
- `docs/SKILL_SMOKING.md` — база знаний технолога
- `docs/COMPETITORS.md` — сравнение с конкурентами
- `docs/RECIPES_BASE.md` — структура рецептов
- `docs/FELETI_BRAND.md` — айдентика
- `docs/CONTEXT_HANDOFF.md` — протокол передачи контекста между сессиями
