# AGENTS.md — точка входа для opencode-агента

> **Этот файл читается opencode-агентом в начале сессии.**
> Содержит инструкции, как работать с проектом FELETI-SMOK.

## 0. Контекст

**FELETI-SMOK** — fullstack-платформа (hardware + software) для управления коптильным производством. Бренд FELETI (Беларусь, Брест) входит на рынок коптильного оборудования с собственной линейкой камер + софтверной платформой, конкурент Ижицы/Varmen.

**Стек:** Next.js 14 + FastAPI + PostgreSQL + Docker Compose. Подробности — `docs/ARCHITECTURE.md`.

## 1. Первое действие в каждой сессии

Прочитай **по порядку**:

1. `docs/PROJECT_BOOT.md` — общая сводка проекта.
2. `docs/CONTEXT_HANDOFF.md` — что было в прошлой сессии, что делать дальше.
3. `CHANGELOG.md` — что реально сделано.
4. `TODO.md` — что в работе / что blocked.
5. `OPEN_QUESTIONS.md` — вопросы к пользователю.
6. `docs/ARCHITECTURE.md` — как устроена система.
7. `docs/SKILL_DEV.md` — конвенции разработки.
8. `docs/SKILL_SMOKING.md` — база знаний технолога.
9. `docs/CAMERA_DRIVER.md` — архитектура драйверов камер.
10. `docs/COMPETITORS.md` — конкуренты.
11. `docs/RECIPES_BASE.md` — структура рецептов.
12. `docs/FELETI_BRAND.md` — айдентика.

**После прочтения** проверь `git status` и `git log --oneline -10`.

## 2. Правила работы

### 2.1. Стиль общения
- **На русском** (пользователь явно попросил).
- Короткие, ёмкие ответы (< 4 строк, если не просят деталей).
- Без эмодзи (если пользователь не просил).
- Без преамбул и заключений ("Хорошо!", "Сделано!", "Готово!" — излишни).

### 2.2. Стиль кода
- **Python:** type hints везде, async где I/O, SQLAlchemy 2.0 style, Pydantic v2.
- **TypeScript:** strict mode, no `any` (только осознанно с комментарием), RHF + Zod для форм.
- **Без комментариев в коде** (если пользователь не просил).
- **Snake_case** в Python, **camelCase** в TS/JS.
- **Идемпотентные миграции** (Alembic).

### 2.3. Git
- Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `perf:`.
- Scope: `backend`, `frontend`, `docs`, `infra`, `seed`, `db`, `driver`, `knowledge`.
- `main` — стабильная. `feature/*` — фичи.
- **Не коммитить без явной просьбы.**

### 2.4. Документация
- Все значимые изменения — в `CHANGELOG.md`.
- Все планы — в `TODO.md`.
- Все открытые вопросы — в `OPEN_QUESTIONS.md`.
- Все новые доменные знания — в `docs/`.
- Все скиллы — в `.opencode/skills/<name>/SKILL.md`.

## 3. Загрузка скиллов

Скиллы подключаются через `skill` tool. Доступные:

| Скилл | Когда использовать |
|---|---|
| `smoke-platform` | Любая задача по FELETI-SMOK — общие правила, конвенции, контекст |
| `add-recipe` | Создание/редактирование рецепта (код + данные) + /calc |
| `add-chamber` | Добавление новой камеры в каталог (модель, ТТХ, драйвер) |
| `camera-driver` | Работа с драйверами камер (Kinco, Varmen, Fessmann, ...) + ChamberGateway |
| `batches-lifecycle` | Создание/запуск партий, интеграция с ChamberGateway |
| `telemetry-websocket` | Live-стрим телеметрии через WebSocket + REST |
| `knowledge-search` | CRUD статей базы знаний + полнотекстовый поиск |
| `seed-data` | Сидирование начальных данных (производители, камеры, рецепты) |
| `design-system` | Брендирование UI (цвета, шрифты, компоненты) |
| `research-competitor` | Парсинг сайта/каталога конкурента (Ижица, Fessmann, ...) |

**Правило:** если задача подходит под скилл — загрузи его ПЕРЕД началом работы.

## 4. Типичные задачи

### 4.1. Создать новую модель
```
1. backend/app/models/<name>.py — SQLAlchemy 2.0 модель
2. Зарегистрировать в backend/app/models/__init__.py (импорт для Alembic)
3. backend/app/schemas/<name>.py — Pydantic v2 DTO
4. (если нужен endpoint) backend/app/api/v1/endpoints/<name>.py — роутер
5. Зарегистрировать роутер в backend/app/api/v1/__init__.py
6. (если нужна логика) backend/app/services/<name>.py
7. alembic revision --autogenerate -m "add <name>" (нужен Docker)
8. alembic upgrade head
9. (если нужно) backend/tests/test_<name>.py
10. (если нужно) добавить seed-данные в app/scripts/seed.py
11. CHANGELOG.md, TODO.md
```

### 4.2. Создать новый драйвер камеры
```
1. docs/cameras/<manufacturer>/SPEC.md — спецификация
2. backend/app/drivers/<name>.py — реализация ChamberDriver (см. SKILL camera-driver)
3. Зарегистрировать в backend/app/drivers/__init__.py через @register("Name")
4. Добавить manufacturer + chamber в app/scripts/seed.py
5. (если нужно) тесты с моком
6. CHANGELOG.md, TODO.md
```

### 4.3. Добавить endpoint
```
1. backend/app/api/v1/endpoints/<resource>.py — роутер
2. Зарегистрировать в backend/app/api/v1/__init__.py (api_router.include_router)
3. (если нужна логика) backend/app/services/<resource>.py
4. (если нужна схема) backend/app/schemas/<resource>.py
5. Тесты
6. Документация (auto-generated OpenAPI доступен по /api/v1/docs)
7. CHANGELOG.md
```

### 4.4. Добавить UI-страницу
```
1. frontend/app/(dashboard)/<page>/page.tsx
2. Компоненты в frontend/components/<domain>/
3. API-клиент в frontend/lib/api/<resource>.ts
4. Типы в frontend/lib/api/<resource>.types.ts (или из OpenAPI)
5. (если нужна форма) RHF + Zod
6. (если нужны графики) Recharts
7. (если нужен WS) WebSocketManager
8. Брендирование (FELETI Red, dark/light)
9. A11y (контраст, фокус, ARIA)
10. PWA (если offline)
11. CHANGELOG.md
```

### 4.5. Запустить парсинг конкурента
```
1. backend/app/services/web_parser.py — извлечь данные
2. (опц.) PDF-парсинг через pdfplumber/PyMuPDF
3. Сохранить в docs/cameras/<manufacturer>/ или docs/research/
4. Структурировать по шаблону (см. .opencode/skills/research-competitor/SKILL.md)
5. Засеять в БД через seed
6. CHANGELOG.md, TODO.md
```

## 5. Чего НЕ делать

- ❌ Не коммитить без явной просьбы.
- ❌ Не выдумывать URL, цены, ТТХ — только то, что в БАЗЕ_ЗНАНИЙ или открытых источниках.
- ❌ Не удалять чужие файлы без подтверждения.
- ❌ Не менять `БАЗА_ЗНАНИЙ_КОПЧЕНИЕ.md` без явной просьбы.
- ❌ Не выдумывать рецепты с точными цифрами — помечать `verified: false`.
- ❌ Не игнорировать ошибки — фиксировать в CHANGELOG/TODO.
- ❌ Не использовать эмодзи в коде/документации (если пользователь не просил).
- ❌ Не добавлять комментарии в код (если пользователь не просил).
- ❌ Не отвечать длинными блоками текста, если можно коротко.

## 6. Что делать, если неясно

1. **Спросить пользователя** через `question` tool с вариантами.
2. **Записать в OPEN_QUESTIONS.md**, если пользователь не отвечает.
3. **Предложить разумный дефолт** (с пометкой `[assumed]`) и двигаться дальше.

## 7. Что делать, если что-то сломалось

1. **Проверить `git status` и `git diff`** — что изменилось.
2. **`git log --oneline -10`** — последние коммиты.
3. **`docker compose ps`** — все ли контейнеры healthy.
4. **`docker compose logs <service>`** — что в логах.
5. **Прочитать `OPEN_QUESTIONS.md`** — нет ли зарегистрированной проблемы.
6. **Спросить пользователя**, если не получается восстановить.

## 8. Финальные действия сессии

Перед завершением работы ОБЯЗАТЕЛЬНО:

1. Обновить `CHANGELOG.md` (что сделано).
2. Обновить `TODO.md` (что осталось).
3. Обновить `OPEN_QUESTIONS.md` (новые вопросы).
4. Обновить `docs/CONTEXT_HANDOFF.md` (сводка последней сессии).
5. Если менялась архитектура — `docs/ARCHITECTURE.md`.
6. Если появлялись новые скиллы — `.opencode/skills/<name>/SKILL.md`.
7. `git add . && git commit -m "..."` (только если пользователь попросил).

---

**Связанные файлы:**
- `docs/PROJECT_BOOT.md` — общая сводка
- `docs/CONTEXT_HANDOFF.md` — сводка последней сессии
- `docs/ARCHITECTURE.md` — архитектура
- `docs/SKILL_DEV.md` — конвенции разработки
- `docs/SKILL_SMOKING.md` — база знаний технолога
- `.opencode/skills/*/SKILL.md` — специализированные скиллы
