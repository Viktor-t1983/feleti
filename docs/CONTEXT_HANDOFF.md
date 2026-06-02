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

### Сессия от 2026-06-02 (продолжение foundation phase)
- **Что сделано:**
  - Создана `docs/ARCHITECTURE.md` — детальная C4-архитектура.
  - Создана `docs/CONTEXT_HANDOFF.md` — протокол передачи контекста.
  - Создана `docs/COMPETITORS.md` — детальная матрица конкурентов.
  - Создана `docs/RECIPES_BASE.md` — структура базы рецептов, 50+ стартовых.
  - Создана `docs/FELETI_BRAND.md` — айдентика.
  - Создана `docs/cameras/feleti-smok/SPEC.md` — спецификация камеры FELETI-SMOK.
  - Созданы `CHANGELOG.md`, `TODO.md`, `OPEN_QUESTIONS.md`.
  - Создана `.opencode/AGENTS.md`.
  - Созданы 7 файлов `SKILL.md`: `smoke-platform`, `add-recipe`, `add-chamber`, `camera-driver`, `seed-data`, `design-system`, `research-competitor`.
  - **Зафиксирована hardware-стратегия FELETI-SMOK** (через вопросы пользователю): Profi/Industrial B2B, Kinco HMI/PLC + свой модуль расширения, свой дымогенератор, электростатика как опция, датчики — всегда максимальная комплектация.
  - Реализованы драйверы камер: `base.py` (ChamberDriver), `simulated.py` (мок с физ-моделью), `feleti_smok.py` (Kinco + свой модуль), `varmen.py` (Modbus TCP, DRAFT-карта).
  - Реестр драйверов с декоратором `@register` в `__init__.py`.
  - `docker-compose.yml` — добавлен Mosquitto MQTT broker.
  - `nginx/mosquitto.conf` — конфигурация Mosquitto с auth + ACL.
  - Обновлены `docs/PROJECT_BOOT.md` и `docs/CAMERA_DRIVER.md` с учётом hardware-стратегии.

- **Какие файлы созданы/изменены:**
  - **Созданы документы:** `docs/{ARCHITECTURE,CONTEXT_HANDOFF,COMPETITORS,RECIPES_BASE,FELETI_BRAND}.md`, `docs/cameras/feleti-smok/SPEC.md`, `CHANGELOG.md`, `TODO.md`, `OPEN_QUESTIONS.md`, `.opencode/AGENTS.md`.
  - **Созданы скиллы:** `.opencode/skills/{smoke-platform,add-recipe,add-chamber,camera-driver,seed-data,design-system,research-competitor}/SKILL.md` (7 файлов).
  - **Созданы драйверы:** `backend/app/drivers/{base,__init__,simulated,feleti_smok,varmen}.py`.
  - **Обновлены:** `docs/PROJECT_BOOT.md`, `docs/CAMERA_DRIVER.md`, `CHANGELOG.md`, `docker-compose.yml`.
  - **Добавлено:** `nginx/mosquitto.conf`.

- **Что блокирует:**
  - 🚫 Нет Telethon API_ID/HASH от пользователя → нельзя начать парсинг TG-каналов.
  - 🚫 Не подтверждена карта Modbus-регистров Varmen-1 (нужны Wireshark или реальное устройство).
  - 🚫 Не выбран GitHub-репозиторий (отложено на потом).
  - 🚫 Не определены точные ТТХ камер FELETI-SMOK (нужны эскизы от инженеров).

- **Следующие шаги для новой сессии (по приоритету):**
  1. ⏳ Backend: модели (chamber, product, ingredient, recipe, brine, batch, knowledge, audit, telemetry).
  2. ⏳ Backend: Alembic — инициализация и первая миграция.
  3. ⏳ Backend: API v1 для auth, manufacturers, chambers, recipes, batches, telemetry (WebSocket).
  4. ⏳ Backend: services (recipe_workflow, recipe_calc, chamber_gateway, telemetry, knowledge).
  5. ⏳ Backend: workers (Celery) для parse_telegram, parse_pdf, send_report.
  6. ⏳ Backend: seed-скрипт (9 производителей, 18+ камер, 50+ рецептов).
  7. ⏳ Frontend: init Next.js 14 + TypeScript + Tailwind + shadcn/ui.
  8. ⏳ Frontend: PWA manifest + service worker (Workbox).
  9. ⏳ Frontend: Login, Dashboard, Chambers, Recipes (с конструктором и версионированием), Batches.
  10. ⏳ Hardware: детальные KINCO_REGISTER_MAP.md, EXTENSION_MODULE.md, SCHEMATIC.md, BOM.md, HMI_PROGRAM.md, TEST_PROCEDURE.md для FELETI-SMOK.
  11. ⏳ Парсинг: углубить ijiza.ru (рецепты, контроллер, цены, FES.APP-аналоги).
  12. ⏳ Парсинг: каталоги Mauting/Fessmann/Kerres.
  13. ⏳ Получить Telethon API_ID/HASH от пользователя, запустить парсер TG.

- **Открытые вопросы к пользователю:** см. `OPEN_QUESTIONS.md` (hardware FELETI-SMOK, монетизация, демо-камера, сроки).

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
