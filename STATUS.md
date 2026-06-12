# FELETI-SMOK — Статус проекта

## Легенда
- [x] — сделано / проверено
- [~] — в работе
- [ ] — не начато

---

## 1. Инфраструктура

- [x] Docker Compose: postgres + redis + minio + mosquitto + adminer + backend
- [x] FastAPI 0.115.6 на localhost:8000
- [x] Next.js 14.2.35 на localhost:3001
- [x] JWT-авторизация (middleware: cookie `access_token`, Edge runtime)
- [x] RBAC (role=admin, is_superuser)
- [x] 104 теста — все проходят
- [x] Frontend build — успешно

---

## 2. Модели данных

- [x] `users` — пользователи (JWT, роли)
- [x] `products` — продукты/сырьё
- [x] `brines` — рассолы
- [x] `ingredients` — ингредиенты
- [x] `chambers` — коптильные камеры
- [x] `manufacturers` — производители (83 шт.)
- [x] `recipes` — рецепты (+ RecipeVersion, RecipeApproval)
- [x] `competitors` — конкуренты (20 шт.)
- [x] `competitor_models` — модели конкурентов
- [x] `competitor_problems` — проблемы конкурентов
- [x] `knowledge_articles` — статьи базы знаний (~50 шт.)
- [x] `article_analyses` — AI-анализ статей
- [x] `article_topics` — связь статья ↔ тема (M2M)
- [x] `knowledge_topics` — семантическое дерево (49 узлов)
- [x] `batches` + `batch_phases` + `batch_telemetry` — партии (не трогать)
- [x] `telemetry_readings` — телеметрия камер
- [x] `ai_settings` — настройки AI
- [x] `audit_logs` — аудит действий
- [x] `chat_sessions` + `chat_messages` — история диалогов
- [ ] `entity_links` — Knowledge Graph (связи между сущностями)
- [ ] `source_reputation` — репутация источников
- [ ] `collection_jobs` — задания на сбор знаний

---

## 3. UI-страницы

### CRUD-формы
- [x] Продукты: список, создание, редактирование
- [x] Ингредиенты: список, создание, редактирование
- [x] Рассолы: список, создание, редактирование
- [x] Камеры: список, создание, редактирование
- [x] Производители: список (сетка/список), группировка по странам
- [x] Конкуренты: список, 3 таба (инфо/модели/проблемы)

### AI & Знания
- [x] `/ai` — полностраничный AI-ассистент (stream, источники)
- [x] `/knowledge` — база знаний (список статей)
- [x] `/settings` — настройки AI
- [x] ChatOverlay — плавающий чат на всех страницах (stream, контекст страницы, история диалогов)
- [x] `PATCH /chat/sessions/{id}` — обновление заголовка/контекста диалога
- [x] `/knowledge/tree` — визуальный браузер семантического дерева (49 узлов, expand/collapse, иконки, счётчики, CRUD из UI для admin)
- [x] CRUD тем (добавление/редактирование узлов из UI)
- [x] Привязка статей к темам из UI — ✓ (селектор тем на странице статьи, GET/POST /knowledge/{id}/topics)

### Партии
- [ ] Модуль партий (последняя задача — не трогать)

---

## 4. API-эндпоинты

### Auth
- [x] `POST /auth/login` — вход
- [x] `POST /auth/register` — регистрация
- [x] `GET /auth/me` — текущий пользователь

### Products / Ingredients / Brines / Chambers
- [x] CRUD + list + search + pagination (для каждой сущности)

### Manufacturers
- [x] CRUD + list (группировка по странам)

### Competitors
- [x] CRUD + модели + проблемы

### Knowledge
- [x] CRUD статей
- [x] `GET /knowledge/search` — FTS-поиск
- [x] `GET /knowledge/tree` — дерево из topic_path (legacy)
- [x] `POST /knowledge/{id}/analyze` — AI-анализ
- [x] `POST /knowledge/analyze/batch` — пакетный анализ
- [x] `POST /knowledge/ask` — RAG без LLM (rule-based)
- [x] `GET /knowledge/topics/tree` — дерево KnowledgeTopic
- [x] `POST /knowledge/{id}/topics` — привязка статей к темам
- [x] CRUD `/knowledge/topics/*`
- [x] `topic_id` фильтр в `GET /knowledge`
- [x] CRUD тем из UI (модалка, админ-кнопки на дереве)

### AI
- [x] `POST /ai/ask` — вопрос с RAG-контекстом
- [x] `POST /ai/ask/stream` — потоковый ответ (SSE)
- [x] `POST /ai/analyze` — анализ текста
- [x] `GET /ai/settings` — настройки
- [x] `PUT /ai/settings` — обновить настройки
- [x] `POST /ai/test` — тест подключения
- [x] CRUD `/chat/sessions` — диалоги (+ PATCH title)
- [x] CRUD `/chat/sessions/{id}/messages` — сообщения диалогов
- [x] `POST /ai/collect` — запуск сбора знаний (агент)
- [x] `GET /ai/collect/{id}` — статус задачи
- [x] `GET /ai/collect/{id}/progress` — SSE прогресс сбора

---

## 5. Сервисы сбора знаний

- [x] `web_crawler.py` — краулер сайтов
- [x] `youtube_transcriber.py` — YouTube → субтитры
- [x] `telegram_parser.py` — Telegram-каналы
- [x] `knowledge_pipeline.py` — оркестратор CrawlResult → ExtractedData
- [x] `competitor_onboarder.py` — разведка конкурентов
- [x] `article_analyzer.py` — AI-анализ статей
- [x] `llm_extractor.py` — извлечение структуры
- [x] `ai_service.py` — AI-сервис (Ollama/OpenAI)
- [x] `knowledge_collector.py` — агент-коллектор (единый оркестратор)
- [ ] Scheduled сбор (APScheduler / Celery beat)

---

## 6. Семантическое дерево (knowledge_topics)

### Корневые узлы (6)
- [x] `/technologies` — Технологии (засол, термообработка, охлаждение, упаковка)
- [x] `/syrio` — Сырьё (рыба, мясо, морепродукты, оболочки)
- [x] `/oborudovanie` — Оборудование (камеры, дымогенераторы, компрессоры)
- [x] `/recepty` — Рецепты (рыбные, мясные, морепродукты)
- [x] `/problemy-i-resheniya` — Проблемы и решения
- [x] `/konkurenty` — Конкуренты (отечественные, импортные)

### Всего узлов: 49

---

## 7. Очерёдность задач

### Фаза 1 — Чат + Дерево ✓
- [x] Модель KnowledgeTopic
- [x] Миграция + seed
- [x] Tree-aware RAG
- [x] Чат-оверлей (история диалогов, PATCH title)
- [x] AGENTS.md + директивы агента

### Фаза 2 — Визуальный браузер дерева ✓
- [x] Кликабельное дерево на `/knowledge/tree`
- [x] CRUD тем из UI (модалка создания/редактирования, подтверждение удаления, кнопки для admin)
- [x] `topic_id` фильтр в `GET /knowledge`
- [x] Привязка статей к темам из UI (селектор на странице статьи)

### Фаза 3 — Коллектор знаний (текущая)
- [x] `knowledge_collector.py` — агент-оркестратор
- [x] `POST /ai/collect` — запуск сбора
- [x] `GET /ai/collect/{id}/progress` — SSE прогресс сбора
- [x] `GET /ai/collect/{id}` — статус задачи
- [ ] De-duplication (SimHash)
- [ ] Quality gate
- [ ] Определение источников по запросу (LLM)
- [ ] Менеджер источников (UI)

### Фаза 3 — Коллектор знаний
- [ ] `knowledge_collector.py` — агент-оркестратор
- [ ] `POST /ai/collect` — запуск сбора
- [ ] SSE progress
- [ ] De-duplication (SimHash)
- [ ] Quality gate
- [ ] Определение источников по запросу (LLM)
- [ ] Менеджер источников (UI)

### Фаза 4 — Платформа знаний
- [ ] Knowledge Graph (entity_links)
- [ ] Scheduled сбор
- [ ] Экспорт техкарт (PDF)

### Фаза 5 — Интеллект
- [ ] Предиктивная аналитика
- [ ] Технологический калькулятор
- [ ] Photo-диагностика
- [ ] Интеграция с HMI
- [ ] Матрица совместимости

---

## 8. Документы

- [x] `AGENTS.md` — архитектура агента, источники, план реализации
- [x] `STATUS.md` — этот файл
