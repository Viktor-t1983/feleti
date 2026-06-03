# FELETI-SMOK

**Платформа управления коптильным производством + база знаний + HMI камер**

Fullstack-платформа (PWA-десктоп + мобильная) для технологов, операторов коптильных камер и владельцев производств. Замена Ижице и Fessmann: современный стек, live-телеметрия, база знаний с конкурентной разведкой, умные драйверы оборудования.

---

## Возможности

| Модуль | Описание | Статус |
|--------|----------|--------|
| **Dashboard** | KPI камер, графики партий, быстрые действия | ✅ |
| **Камеры** | Каталог + HMI с WebSocket live-телеметрией | ✅ |
| **Рецепты** | Конструктор фаз, версионирование, расчёт БЖУ/себестоимости | ✅ |
| **Партии** | Журнал, создание, управление (start/pause/resume/cancel) | ✅ |
| **База знаний** | Статьи, поиск, категории, markdown | ✅ |
| **Конкуренты** | Матрица сравнения, 18+ моделей Ижицы, проблемы | ✅ |
| **HMI камеры** | 3D-интерфейс, WebSocket, клавиатура, fullscreen | ✅ |
| **Knowledge Pipeline** | Сбор знаний с сайтов/YouTube/PDF/TG | ✅ |
| **Настройки** | Профиль, роли, о системе | ✅ |

## Архитектура

```
┌─────────────────────────────────────────────────────┐
│                   Frontend (Next.js 14)              │
│  Dashboard │ Chambers │ HMI │ Recipes │ Batches      │
│  Knowledge │ Competitors │ Settings │ PWA            │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP REST + WebSocket
┌──────────────────▼──────────────────────────────────┐
│                Backend (FastAPI)                      │
│  Auth │ CRUD │ Telemetry WS │ Pipeline API │ Audit   │
│  ┌──────────────────────────────────────────────┐   │
│  │              Services Layer                   │   │
│  │  ChamberGateway │ RecipeCalc │ KnowledgeSaver │   │
│  │  WebCrawler │ YouTubeTranscriber │ PdfParser  │   │
│  └──────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │           Models (SQLAlchemy 2.0)             │   │
│  │  Chamber │ Batch │ Recipe │ KnowledgeArticle  │   │
│  │  Competitor │ User │ Audit │ Telemetry        │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────────┘
                   │ asyncpg │ redis │ celery
┌──────────────────▼──────────────────────────────────┐
│    PostgreSQL 16 │ Redis 7 │ MinIO │ Mosquitto MQTT │
└─────────────────────────────────────────────────────┘
```

## Стек

**Frontend:**
Next.js 14 (App Router) · TypeScript · shadcn/ui · Tailwind CSS · Recharts · Zustand · TanStack Query · React Hook Form · Zod · Framer Motion · PWA (next-pwa)

**Backend:**
FastAPI · SQLAlchemy 2.0 (async) · Alembic · Pydantic v2 · Celery · Redis · httpx · WebSocket

**Хранилище:**
PostgreSQL 16 · Redis 7 · MinIO (S3)

**Инфраструктура:**
Docker Compose · Mosquitto MQTT · Adminer

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/Viktor-t1983/feleti.git
cd feleti

# 2. Настроить окружение
cp .env.example .env

# 3. Запустить
docker compose up -d --build

# 4. Накатить миграции + seed
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed
```

**Открыть:**
- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/api/v1/docs
- Adminer (БД): http://localhost:8080
- MinIO Console: http://localhost:9001

## Структура проекта

```
feleti/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/   # REST роутеры (14 endpoint-файлов)
│   │   ├── core/               # config, security, deps, celery
│   │   ├── db/                 # session, base, migrations
│   │   ├── drivers/            # chamber drivers (Modbus, simulated)
│   │   ├── models/             # SQLAlchemy 2.0 (13 моделей)
│   │   ├── schemas/            # Pydantic v2
│   │   ├── services/           # бизнес-логика (9 сервисов)
│   │   ├── tasks/              # Celery задачи (knowledge pipeline)
│   │   ├── scripts/            # seed, утилиты
│   │   └── main.py
│   ├── alembic/                # миграции (4 шт.)
│   └── pyproject.toml
├── frontend/
│   ├── app/                    # Next.js App Router страницы
│   ├── components/             # UI + chamber HMI (9 комп.)
│   ├── hooks/                  # WebSocket + data hooks
│   ├── lib/                    # API клиент, types, utils
│   ├── stores/                 # Zustand (auth)
│   └── public/                 # PWA manifest, icons
├── docs/                       # Исследования, спецификации
│   └── research/ijiza/         # HMI анализ, транскрипты (118 видео)
├── scripts/                    # Парсеры, транскрибация
├── docker-compose.yml
├── .env.example
├── README.md
├── CHANGELOG.md
└── TODO.md
```

## API Endpoints

- `GET/POST/PATCH/DELETE /api/v1/*` — CRUD всех сущностей
- `WS /api/v1/chambers/{id}/telemetry/ws` — live телеметрия
- `POST /api/v1/pipeline/crawl/*` — запуск сбора знаний
- `GET /api/v1/pipeline/tasks/{id}` — статус задачи
- `POST /api/v1/auth/login` — JWT аутентификация

## Конкурентная разведка

Глубоко исследованы и загружены в БД:
- **Ижица** (Z115, Z380, UTR-C, UTR-F и др.) — 18+ моделей, 30+ рецептов, 7 проблем, HMI-анализ, 118 YouTube-видео транскрибировано
- **Mauting** — 6+ моделей туннелей
- **Fessmann** — 6+ моделей + FES.APP
- **Kerres** — Jet Smoke, Hybrid Airflow

## Knowledge Pipeline (сбор знаний)

Автоматический сбор информации о продуктах/технологиях копчения:

1. **WebCrawler** — парсинг сайтов конкурентов (httpx + bs4)
2. **YouTubeTranscriber** — yt-dlp + faster-whisper
3. **PdfParser** — pdfplumber (каталоги, техпаспорта)
4. **TelegramParser** — Telethon (нужен API_ID/HASH)
5. **LlmExtractor** — Ollama/OpenAI → структурированные данные
6. **KnowledgeSaver** → БД (KnowledgeArticle, CompetitorModel)

---

**© FELETI-SMOK, 2026. Внутренний проект.**
