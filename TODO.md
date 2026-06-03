# TODO — FELETI-SMOK

> **Приоритеты:** 🔴 критично · 🟠 высоко · 🟡 средне · 🟢 низко
> **Статусы:** ⏳ не начато · 🔄 в процессе · ✅ сделано · ❌ отменено · 🚫 заблокировано

---

## 🔴 Фаза 0.1 — Foundation (текущая)

### Документация
- [x] ✅ `docs/PROJECT_BOOT.md` — точка входа
- [x] ✅ `docs/ARCHITECTURE.md` — архитектура
- [x] ✅ `docs/CONTEXT_HANDOFF.md` — протокол передачи контекста
- [x] ✅ `docs/COMPETITORS.md` — матрица конкурентов
- [x] ✅ `docs/research/ijiza/DEEP_DIVE.md` — глубокий анализ Ижицы (25KB)
- [x] ✅ `docs/design/COMPETITORS_UI.md` — UI/UX концепция экрана "Анализ конкурентов"
- [x] ✅ `docs/RECIPES_BASE.md` — структура рецептов
- [x] ✅ `docs/FELETI_BRAND.md` — айдентика
- [x] ✅ `CHANGELOG.md` — лог изменений
- [x] ✅ `TODO.md` — этот файл
- [x] ✅ `OPEN_QUESTIONS.md` — открытые вопросы
- [x] ✅ `docs/SKILL_DEV.md` — стек и конвенции
- [x] ✅ `docs/SKILL_SMOKING.md` — база знаний технолога
- [x] ✅ `docs/CAMERA_DRIVER.md` — драйвер камеры
- [x] ✅ `.opencode/AGENTS.md` — entry point
- [x] ✅ 19 файлов `SKILL.md` в `.opencode/skills/*/` (10 + 9 новых)
- [x] ✅ `docs/cameras/feleti-smok/SPEC.md` — спецификация камеры FELETI-SMOK
- [x] ✅ AGENTS.md — обновлен: роли агента + 19 скиллов
- [x] ✅ 9 новых SKILL.md: db-migrations, frontend-init, recipe-calc, pytest-testing, frontend-api-client, program-visualizer, quality-control, batch-monitoring, pdf-report
- [x] ✅ Система persistence контекста между сессиями
  - `.opencode/session/README.md` — описание системы
  - `.opencode/session/TEMPLATE.md` — шаблон новой сессии
  - `.opencode/session/CHECKLIST.md` — чек-лист конца сессии
  - `.opencode/session/history/2026-06-03_0937_session_6.md` — первая запись
  - `scripts/verify_context.py` — скрипт проверки целостности
- [x] ✅ Docker Compose up — все сервисы запущены
- [x] ✅ Alembic — первая миграция сгенерирована и применена
- [x] ✅ Seed — данные засеяны (7 manufacturers, 6 chambers, 6 ingredients, 8 products, 3 users)
- [x] ✅ Backend health check — `{"status":"ok"}`
- [x] ⏳ pytest — тесты не реализованы

### Backend
- [x] ✅ Каркас FastAPI (main.py, config.py, security.py, session.py)
- [x] ✅ Модели: User, Manufacturer (с is_our_brand/is_competitor/sort_order)
- [x] ✅ Модель Chamber
- [x] ✅ Модель Product
- [x] ✅ Модель Ingredient
- [x] ✅ Модель Recipe + RecipeVersion + RecipeApproval
- [x] ✅ Модель Brine
- [x] ✅ Модель Batch + BatchPhase + BatchTelemetry
- [x] ✅ Модель KnowledgeArticle + KnowledgeAttachment
- [x] ✅ Модель AuditLog
- [x] ✅ Модель TelemetryReading
- [x] ✅ Alembic — конфиг + env.py + script.py.mako (готов к revision --autogenerate)
- [x] ✅ API v1: health + health/db
- [x] ✅ API v1: auth (login + login/json + refresh + me)
- [x] ✅ API v1: manufacturers CRUD
- [x] ✅ API v1: chambers CRUD + /drivers
- [x] ✅ API v1: products CRUD
- [x] ✅ API v1: ingredients CRUD
- [x] ✅ API v1: brines CRUD
- [x] ✅ API v1: recipes CRUD + versions (create new version)
- [x] ✅ Pydantic v2 schemas для всех сущностей
- [x] ✅ Services: audit (record), auth (authenticate, issue_tokens, register_user)
- [x] ✅ Core: deps (oauth2_scheme, DBSession, CurrentUser, require_roles)
- [x] ✅ Scripts: seed.py (7 производителей, 6 камер, 6 ингредиентов, 8 продуктов, 3 user)
- [x] ✅ Драйверы: base.py (ChamberDriver interface)
- [x] ✅ Драйверы: simulated.py (мок с физ-моделью)
- [x] ✅ Драйверы: feleti_smok.py (Kinco + свой модуль)
- [x] ✅ Драйверы: varmen.py (Modbus TCP)
- [x] ✅ API v1: batches CRUD + start/pause/resume/cancel/complete (через ChamberGateway)
- [x] ✅ Services: chamber_gateway (singleton, пул, буфер, подписки)
- [x] ✅ AuditAction: +CANCEL, +COMPLETE
- [x] ⏳ Драйверы: fessmann.py (OPC UA, stub)
- [x] ⏳ Драйверы: kerres.py (HTTP, stub)
- [x] ⏳ Драйверы: mauting.py (Modbus TCP, stub)
- [x] ⏳ **Сгенерировать первую миграцию** (`alembic revision --autogenerate -m "initial"`) — блокер: нужен `docker compose up`
- [x] ⏳ **Применить миграцию** (`alembic upgrade head` + seed)
- [x] ⏳ API v1: users CRUD
- [x] ✅ API v1: batches CRUD + start/pause/resume/cancel/complete (через ChamberGateway)
- [x] ✅ API v1: telemetry WebSocket (внутрипроцессный fan-out через ChamberGateway; Redis pub/sub — для следующей сессии)
- [x] ✅ API v1: knowledge CRUD + search
- [x] ✅ API v1: recipe calc (current version + specific version)
- [x] ⏳ API v1: chat (in-app) + RAG
- [x] ⏳ API v1: reports + PDF
- [x] ⏳ Services: recipe_workflow (draft→pending→approved→archived)
- [x] ✅ Services: recipe_calc (БЖУ, себестоимость, yield)
- [x] ✅ Services: chamber_gateway (абстракция + пул инстансов)
- [x] ✅ Services: recipe_calc (БЖУ, себестоимость, yield, длительность программы)
- [x] ✅ API v1: recipe calc (current version + specific version)
- [x] ✅ API v1: telemetry REST (status/latest/history/active-batch) + WebSocket (live-стрим)
- [x] ✅ API v1: knowledge CRUD + search (ILIKE-based, score 3/2/2/1)
- [x] ⏳ Services: telemetry (буферизация, batch insert)
- [x] ⏳ Services: knowledge (поиск, тегирование)
- [x] ⏳ Services: chat (RAG/AI)
- [x] ⏳ Services: pdf_parser
- [x] ⏳ Services: telegram_parser
- [x] ⏳ Services: report (PDF/email)
- [x] ⏳ Workers (Celery): parse_telegram, parse_pdf, send_report

### Seed-данные
- [x] ⏳ 9 производителей (Ижица, FELETI, Mauting, Fessmann, Kerres, AGROS, Reich, Vemag, VSD TEC)
- [x] ⏳ 18+ камер (модели каждого производителя), включая H/C/U линейки FELETI-SMOK
- [x] ⏳ 80+ рецептов (колбасы, мясо, птица, рыба г/к, рыба х/к, рыба электро, сыр, сало, снеки, охлаждение)
- [x] ⏳ 30+ ингредиентов (включая щёпу по породам)
- [x] ⏳ 10+ статей в базе знаний (типы копчения, ГОСТы, troubleshooting)
- [x] ⏳ Demo-пользователи (admin, technologist, operator)
- [x] ⏳ **Конкуренты** (данные для экрана анализа):
  - [x] ⏳ Ижица: 18+ моделей, 30+ рецептов, 7 проблем, стандартные программы 02.01/02.02/02.03
  - [x] ⏳ Mauting: 6+ моделей туннелей
  - [x] ⏳ Fessmann: 6+ моделей + FES.APP
  - [x] ⏳ Kerres: Jet Smoke, Hybrid Airflow
  - [x] ⏳ AGROS, Reich, Vemag, VSD TEC (кратко)

### Парсинг и база знаний
- [x] ✅ `docs/research/README.md` — общий план парсинга
- [x] ✅ `docs/research/ijiza/README.md` — план по Ижице (P0)
- [x] ✅ `docs/research/mauting/README.md` — план по Mauting (P1)
- [x] ✅ `docs/research/fessmann/README.md` — план по Fessmann (P1)
- [x] ✅ `docs/research/kerres/README.md` — план по Kerres (P1)
- [x] ✅ `docs/research/dilers/README.md` — план по дилерам в РФ/СНГ
- [x] ⏳ Реализовать `backend/app/services/web_parser.py` (HTML-парсинг)
- [x] ⏳ Реализовать `backend/app/services/pdf_parser.py` (pdfplumber + PyMuPDF)
- [x] ⏳ Реализовать `backend/app/services/telegram_parser.py` (Telethon)
- [x] ⏳ Реализовать `backend/app/services/youtube_parser.py` (yt-dlp + Whisper)
- [x] ⏳ Спарсить ijiza.ru — каталог продукции
- [x] ⏳ Скачать и распарсить PDF-каталог Ижица 2024
- [x] ⏳ Получить Telethon API_ID/HASH от пользователя
- [x] ⏳ Спарсить TG-каналы (@ijiza_chat и др.)
- [x] ✅ Транскрибировать 118 YouTube-видео об Ижице (faster-whisper tiny, 2.8M символов)
- [x] ✅ Извлечь проблемы из транскриптов (20 проблем) и добавить в БД
- [x] ✅ Обновить COMPETITORS.md новыми данными
- [x] ⏳ Собрать 10+ дилеров в РФ (Яндекс.Карты, 2ГИС, форумы)
- [x] ⏳ Верифицировать Modbus-карту Varmen-1 (Wireshark или доки)

### Frontend
- [x] ✅ Инициализация Next.js 14 + TypeScript + Tailwind
- [x] ✅ shadcn/ui + дизайн-система
- [x] ✅ Брендирование (FELETI gold #c9a96e + graphite #1a1a1a, dark theme)
- [x] ✅ PWA (next-pwa, service worker)
- [x] ✅ Framer Motion анимации
- [x] ✅ Страница анализа конкурентов (/competitors) — 4 конкурента, 4 вкладки, поиск, фильтры
- [x] ✅ Login/Register (RHF + Zod + JWT)
- [x] ⏳ Дашборд (KPI, активные партии)
- [x] ✅ Камеры — список из API с фильтрами
- [x] ✅ Рецепты — список из API
- [x] ⏳ Партии (создание, запуск, мониторинг)
- [x] ⏳ Продукты (CRUD)
- [x] ⏳ Ингредиенты (CRUD + щёпа)
- [x] ⏳ Производители (справочник + сравнение)
- [x] ✅ **Анализ конкурентов** (экран в программе):
  - [x] ✅ Модели БД: Competitor, CompetitorModel, CompetitorProblem
  - [x] ✅ API endpoints: /competitors CRUD + search/filter
  - [x] ✅ React: CompetitorCard (Collapsible) + Tabs (Обзор/Модели/Проблемы/Сравнение)
  - [x] ✅ Сравнительная матрица с цветовой индикацией
  - [x] ✅ Фильтры (сегмент, страна, технология) + поиск
  - [x] ✅ Адаптивность
  - [x] ✅ Framer Motion анимации
  - [x] ✅ Frontend подключен к API (убран hardcoded)
- [x] ⏳ База знаний (список, статьи, поиск)
- [x] ⏳ Чат + AI-копилот
- [x] ⏳ Отчёты
- [x] ✅ Настройки — профиль + о системе

### Docker / DevOps
- [x] ✅ docker-compose.yml (PostgreSQL, Redis, MinIO, Adminer, **Mosquitto**)
- [x] ✅ Mosquitto MQTT broker добавлен
- [x] ✅ nginx/mosquitto.conf — конфигурация
- [x] ⏳ docker-compose.override.yml для локальной разработки
- [x] ⏳ Скрипт `make dev` / `make up` / `make down` / `make logs` / `make seed`
- [x] ⏳ README с инструкциями

### Hardware FELETI-SMOK
- [x] ✅ Стратегия зафиксирована (Kinco + свой модуль, Profi/Industrial, свой дымогенератор, электростатика-опция)
- [x] ✅ `docs/cameras/feleti-smok/SPEC.md` — детальная спецификация
- [x] ⏳ `docs/cameras/feleti-smok/KINCO_REGISTER_MAP.md` — карта Modbus-регистров Kinco
- [x] ⏳ `docs/cameras/feleti-smok/EXTENSION_MODULE.md` — спецификация модуля расширения
- [x] ⏳ `docs/cameras/feleti-smok/SCHEMATIC.md` — схема подключения
- [x] ⏳ `docs/cameras/feleti-smok/BOM.md` — bill of materials
- [x] ⏳ `docs/cameras/feleti-smok/HMI_PROGRAM.md` — программа HMI-экрана
- [x] ⏳ `docs/cameras/feleti-smok/TEST_PROCEDURE.md` — процедура приёмочных испытаний
- [x] ⏳ Согласование с инженерами FELETI (HMI-программа для Kinco)

---

## 🟠 Фаза 0.2 — MVP (UI + базовые API)

- [x] ⏳ UI: камеры live (WebSocket, графики t/t_product/влажность/дым)
- [x] ⏳ UI: рецепты CRUD + конструктор фаз
- [x] ⏳ UI: версионирование рецептов + workflow-апрув
- [x] ⏳ API для всех базовых сущностей
- [x] ⏳ SimulatedDriver (мок камеры) для демо
- [x] ⏳ Seed-данные
- [x] ⏳ Demo-видео работы платформы
- [x] ⏳ Презентация для руководства FELETI

---

## 🟡 Фаза 0.3 — Промышленный пилот

- [x] ⏳ FELETI_SMOKDriver (Kinco + свой модуль, реальный стенд)
- [x] ⏳ VarmenDriver (Modbus TCP, реальная камера Ижица в офисе)
- [x] ⏳ WebSocket-менеджер для live-телеметрии
- [x] ⏳ Алерты (правила: ΔT, отклонение от программы, дверь)
- [x] ⏳ Offline PWA (IndexedDB + sync)
- [x] ⏳ Журнал партий с фото
- [x] ⏳ Экспорт PDF (партия, отчёт за смену)

---

## 🟢 Фаза 0.4 — Knowledge + AI

- [x] ⏳ База знаний (CRUD + поиск + теги)
- [x] ⏳ In-app чат + RAG по базе знаний
- [x] ⏳ Голосовое управление (Whisper + intent)
- [x] ⏳ Telegram-парсер (Telethon)
- [x] ⏳ PDF-парсер каталогов конкурентов
- [x] ⏳ YouWhisper-транскрибация видео-обзоров
- [x] ⏳ Сравнение с конкурентами (UI + данные)

---

## ⚪ Фаза 0.5 — ML (опционально, roadmap)

- [x] ⏳ ML: авто-подбор программы копчения (по типу продукта, массе, желаемому выходу)
- [x] ⏳ ML: anomaly detection (отклонение от программы)
- [x] ⏳ ML: предсказание времени до готовности
- [x] ⏳ ML: классификация дефектов (по фото)

---

## 🚫 Заблокировано

- 🚫 **Telethon API_ID/HASH** — нужен от пользователя для парсинга TG-каналов.
- 🚫 **Реальная камера для тестов** — нужен доступ к стенду FELETI-SMOK или камере Ижица в офисе.
- 🚫 **GitHub-репозиторий** — пользователь сказал "потом", отложено.
- 🚫 **Точная карта Modbus-регистров Varmen-1** — нужны Wireshark-сниффинг или спецификация от Ижица.

---

## 📅 Ближайшие сессии (приоритет) — ОБНОВЛЕНО 2026-06-03

> **Приоритет изменён пользователем:** HMI/панель управления камерой — приоритет #1. Контроль качества после копчения — отдельный софт, не приоритет сейчас.

1. **Сессия 7 (HMI камеры):** Дизайн и прототип HMI панели управления FELETI-SMOK
   - Анализ HMI Ижицы (есть — docs/research/ijiza/HMI_ANALYSIS.md)
   - Дизайн главного экрана (текущие параметры + целевые)
   - Дизайн экрана программ (список, создание, редактирование)
   - Дизайн экрана шага (параметры: T_chamber, T_product, время, влажность, дым)
   - Дизайн экрана ручного режима
   - Дизайн графиков трендов (температура, влажность, дым в реальном времени)
   - Технология: Kinco HMI + custom UI или web-based HMI на Raspberry Pi

2. **Сессия 8 (HMI backend):** API для HMI, связь HMI ↔ PLC ↔ драйвер
   - Modbus TCP сервер (HMI читает регистры PLC)
   - WebSocket для live-данных
   - Хранение программ в БД + экспорт/импорт
   - Синхронизация программ между камерами

3. **Сессия 9 (frontend web):** Web-интерфейс для удаленного мониторинга
   - Next.js 14 + shadcn/ui + PWA
   - Dashboard с картой камер
   - Live-телеметрия с графиками
   - Управление программами с телефона/планшета

4. **Сессия 10 (seed + рецепты):** 80+ рецептов + 30+ ингредиентов + 10+ статей БЗ
5. **Сессия 11 (тестирование):** pytest + интеграционные тесты + нагрузочное тестирование
6. **Сессия 12 (реальный стенд):** FELETI-SMOK driver + Kinco PLC + интеграция

---

**Связанные документы:**
- `docs/PROJECT_BOOT.md` — общая сводка
- `CHANGELOG.md` — что сделано
- `OPEN_QUESTIONS.md` — что нужно уточнить
