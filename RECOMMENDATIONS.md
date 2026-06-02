# RECOMMENDATIONS — приоритеты на Сессию 6

> Финал сессии 5 (2026-06-02). Backend MVP завершён, фронтенд не начат. Документ — приоритеты на следующую сессию.
> Согласовано с пользователем: пользователь — chief developer, я решаю приоритеты.

## TL;DR

**Сессия 6 = Frontend init + первая вертикаль (Login → Dashboard → Batches).**  
Backend API готов и валиден, можно параллельно с Docker-окружением поднимать фронт.

## 1. P0 (сделать в первую очередь)

### 1.1. Docker-окружение + миграция + сид
- `docker compose up -d` (PostgreSQL 16, Redis 7, MinIO, Mosquitto, Adminer).
- `alembic revision --autogenerate -m "init"`.
- `alembic upgrade head`.
- `python -m app.scripts.seed` → проверка в БД.
- **Блокирует всё остальное** (без БД endpoint'ы падают на импортах/запросах).

### 1.2. Frontend init
- `npx create-next-app@14 frontend --typescript --app --src-dir --tailwind --eslint --import-alias "@/*"`.
- `frontend/package.json` добавить: `@tanstack/react-query`, `zustand`, `react-hook-form`, `zod`, `@hookform/resolvers`, `lucide-react`, `recharts`, `axios`, `next-pwa`, `dayjs`, `clsx`, `tailwind-merge`.
- `npx shadcn-ui@latest init` (style: default, baseColor: black, cssVariables: yes).
- `npx shadcn-ui@latest add button card input label form dialog sheet sidebar tabs badge`.
- `frontend/tailwind.config.ts` → скопировать `design-system/SKILL.md` секцию 2.1.
- `frontend/src/app/layout.tsx` → тёмная тема, Inter, base styles.
- `frontend/src/app/manifest.json` + `next-pwa` конфиг.
- `frontend/.env.local` → `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1`, `NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1`.
- `frontend/src/lib/api/client.ts` → axios instance с interceptor для JWT.
- `frontend/src/lib/api/auth.ts` → `login(email, password)`, `refresh()`, `logout()`.

### 1.3. Login + Auth flow
- Страница `/login` (email/password, форма на RHF + Zod).
- Zustand `useAuthStore`: `user`, `accessToken`, `refreshToken`, `setAuth`, `clearAuth`.
- Middleware `middleware.ts` → redirect to `/login` если нет токена.
- Страница `/dashboard` (заглушка с `user.email` + logout).

## 2. P1 (сделать во вторую очередь)

### 2.1. Frontend: основные страницы
- `/chambers` — список камер (карточки с статусом, текущая партия, кнопка "Открыть").
- `/chambers/[id]` — дашборд камеры (статус + графики телеметрии через WS).
- `/recipes` — список рецептов (фильтры по статусу, типу продукта).
- `/recipes/[id]` — карточка рецепта + список версий + кнопка "Создать версию".
- `/batches` — список партий (фильтры по статусу, камере).
- `/batches/[id]` — детали партии (timeline фаз + live телеметрия).
- `/knowledge` — список статей + поиск.
- `/knowledge/[slug]` — рендер Markdown статьи.

### 2.2. Frontend: WebSocket-интеграция
- `frontend/src/lib/ws/use-chamber-telemetry.ts` (хук из `telemetry-websocket/SKILL.md` секция 6).
- `frontend/src/components/chamber/TelemetryChart.tsx` (recharts LineChart).
- `frontend/src/components/chamber/StatusBadge.tsx`.

### 2.3. Драйверы stubs
- `backend/app/drivers/fessmann.py` (OPC UA через `opcua`).
- `backend/app/drivers/kerres.py` (HTTP через `httpx` + basic auth).
- `backend/app/drivers/mauting.py` (Modbus TCP, аналог varmen.py с другой картой регистров).
- `backend/app/drivers/agros.py` + `reich.py` — заглушки с заявленным протоколом.

## 3. P2 (сделать, если останется время)

### 3.1. Backend: рецепт workflow
- `backend/app/services/recipe_workflow.py` — авто-переход draft → pending при submit, approval-эндпоинт.
- `POST /api/v1/recipes/{id}/versions/{vid}/approve` (admin/technologist).
- `POST /api/v1/recipes/{id}/versions/{vid}/reject` (с reason).
- `GET /api/v1/recipes/{id}/versions/{vid}/diff?from={parent_vid}` — JSON-diff для UI.
- Авто-архивация `current_version` при approve новой.

### 3.2. Backend: persist телеметрии
- В `chamber_gateway._telemetry_loop` батчевая запись `BatchTelemetry`/`TelemetryReading` каждые 10 сек.
- Фоновый таск `persist_telemetry()` собирает буфер и делает batch insert.

### 3.3. Backend: Alembic миграция tsvector
- `alembic revision -m "knowledge_tsvector"`.
- Добавить GIN-индекс + generated column.
- Обновить `knowledge.search` endpoint на `ts_rank`.

### 3.4. Backend: tests
- `backend/tests/test_recipe_calc.py` — БЖУ, себестоимость, yield, время.
- `backend/tests/test_knowledge_search.py` — скоринг, snippet, фильтры.
- `backend/tests/test_chamber_gateway.py` — singleton, fan-out, reconnect.
- `backend/tests/conftest.py` — SQLite in-memory + pytest-asyncio.

## 4. P3 (отложено)

- **Telethon парсер** — нужен `TELEGRAM_API_ID` / `TELEGRAM_API_HASH` (https://my.telegram.org/apps).
- **YouTube парсер + Whisper** — нужен OpenAI API key или локальный whisper.cpp.
- **PDF parser** — `pdfplumber` для каталога Ижица 2024 (нужно скачать PDF).
- **Web parser Ижицы** — `httpx` + `BeautifulSoup4` (блокируется без VPN/прокси? проверить).
- **Celery workers** — `parse_telegram`, `parse_pdf`, `send_report`.
- **Redis pub/sub** — для синхронизации WS между воркерами.
- **MinIO presigned URLs** — для загрузки вложений к knowledge articles.
- **CORS + HTTPS** — для production.
- **GitHub-repo** — по запросу пользователя.

## 5. Блокирующие вопросы (нужны от пользователя)

| # | Вопрос | Где нужен | Без него |
|---|---|---|---|
| 1 | Telethon `API_ID` и `API_HASH` | `backend/.env` | Не парсим TG |
| 2 | OpenAI API key (или локальный Whisper) | `backend/.env` | Не транскрибируем видео |
| 3 | Создать GitHub-репозиторий `feleti-smok/platform`? | GitHub | Локальный git only |
| 4 | Доступ к стенду FELETI-SMOK или Ижица в офисе | Офис FELETI | Не тестируем железо |
| 5 | Эскизы камер Profi H/C/U от инженеров FELETI | FELETI R&D | SPEC.md остаётся high-level |

## 6. Метрики прогресса

| Метрика | Сессия 4 | Сессия 5 | Сессия 6 (план) |
|---|---|---|---|
| Python-файлов | 53 | 61 | 65 |
| Строк кода | ~3 500 | ~7 000 | ~9 000 |
| SKILL.md | 4 | 10 | 10 |
| Endpoints (REST+WS) | 6 | 50+ | 50+ (фронт подключается) |
| Pages (frontend) | 0 | 0 | 8+ |
| Tests | 0 | 0 | 10+ |
| Alembic миграций | 0 | 0 | 2 |
| Драйверов | 4 | 4 | 7 |
| Git коммитов | 3 | 9 | 11+ |

## 7. Риски

1. **Pydantic v2 + SQLAlchemy 2.0 + FastAPI 0.115+** — свежая связка, баги возможны. Митигация: `tests/`, ручное тестирование через `docker compose up`.
2. **Modbus TCP** — разные модели камер требуют разных register maps. Митигация: `KINCO_REGISTER_MAP.md` (TODO), unit-тесты с эмулятором pymodbus.
3. **WebSocket-фанаут** — медленные подписчики могут ронять loop. Митигация: `Queue.put_nowait` с try/except, замер latency.
4. **Telethon** — баны аккаунта при агрессивном парсинге. Митигация: `FloodWaitError` handling, rate limit 1 req/sec.
5. **Frontend offline (PWA)** — Workbox конфиг кэширования. Митигация: NetworkFirst для API, CacheFirst для статики.

## 8. Сводка сессии 5

- **Коммитов**: 6 (`6d55c7e`, `4e9d41c`, `1c94839`, `4cb8852`, `f8fcb5d`, `2592f67`).
- **Файлов**: 53 → 61 (+8 net).
- **Строк кода**: +3 525 net.
- **Backend MVP**: завершён (auth + CRUD + batches + telemetry WS + knowledge search + recipe calc).
- **Драйверов**: 4 (Simulated, FELETI_SMOK, Varmen; 5 stubs TODO).
- **SKILL.md**: 4 → 10 (новые: batches-lifecycle, telemetry-websocket, knowledge-search; обновлены: smoke-platform, add-recipe, add-chamber, camera-driver, seed-data, design-system, research-competitor).
- **Документация**: CONTEXT_HANDOFF.md + RECOMMENDATIONS.md + CHANGELOG.md + TODO.md синхронизированы.
- **Поймано 6 критичных багов** в self-review (deps/Body-annotation/race-condition/Enum-missing/CASCADE-conflict/duplicate-router).
- **61 Python-файл** прошли `ast.parse` + `py_compile` (валидный синтаксис).

---

**Версия:** 0.1.0 (2026-06-02)
**Подготовил:** opencode (minimax-m3-free)
**Загружай:** перед стартом сессии 6.
