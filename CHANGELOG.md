# CHANGELOG — FELETI-SMOK

> Все значимые изменения в проекте. Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).

---

## [Unreleased]

### В работе
- Backend: модели chamber, product, ingredient, recipe, brine, batch, knowledge, audit
- Backend: API v1 для всех сущностей
- Frontend: init Next.js 14 + shadcn/ui + PWA
- Seed-данные: 9 производителей, 18+ камер, 80+ рецептов (после расширения холодного копчения)
- Реальный стенд FELETI-SMOK (R&D)
- Парсинг Ижицы: сайт + каталог + TG + YouTube (сессия 2+)

### Added
- **Линейка FELETI-SMOK расширена** (сессия 3, по запросу пользователя):
  - Profi H (горячее): 100/150/200/250 кг.
  - **Profi C (холодное + охлаждение, новинка):** 100/200/250 кг с холодильным агрегатом.
  - **Profi U (универсал, новинка):** 200/250 кг — горячее + холодное + электро + охлаждение в одной камере.
- `docs/cameras/feleti-smok/SPEC.md` — добавлены секции:
  - **Холодное копчение** (Profi C): программы для сёмги, форели, скумбрии, сыра, сала, балыка.
  - **Охлаждение готовой продукции** (Profi C/U): соответствие СанПиН.
  - **Заморозка полуфабриката** (Profi C-Ultra / U-Frost, опция).
  - **Полугорячее копчение** (Profi H, расширенный режим).
  - **Холодильный агрегат**: R404A/R290, T -5…+25°C, инверторный компрессор, оттайка.
  - **Таблица электрики** для H/C/U линеек.
- `docs/research/README.md` — общий план парсинга (Ижица P0, Mauting/Fessmann/Kerres P1, остальные P2-P3).
- `docs/research/ijiza/README.md` — детальный план парсинга Ижицы (сайт, каталоги, TG, YouTube, дилеры).
- `docs/research/mauting/README.md` — план по Mauting.
- `docs/research/fessmann/README.md` — план по Fessmann + FES.APP.
- `docs/research/kerres/README.md` — план по Kerres + Jet Smoke + Hybrid Airflow.
- `docs/research/dilers/README.md` — план по дилерам в РФ/СНГ.
- `docs/RECIPES_BASE.md` — расширена база рецептов: **80+** стартовых (было 50+).
  - **Холодное копчение + охлаждение (17 рецептов)**: сёмга, форель, скумбрия, палтус, сиг, осётр, балык, грудинка, корейка, сало, сыры, масло, сырокопчёные колбасы.
  - **Полугорячее копчение (5 рецептов)**: сельдь, скумбрия, треска, курица, свинина.
  - **Охлаждение (4 рецепта)**: после г/к, после п/к, подсушка, хранение.
  - **Сыры/прочее (8 рецептов)**: сыр, сало, масло, орехи, чеснок, перец, соль.
- `docs/SKILL_SMOKING.md` — расширены разделы:
  - **Холодное копчение — подробно** (Profi C-линейка): применение, параметры, технологические нюансы, оборудование, Ижица UTR-C.
  - **Охлаждение готовой продукции** (Profi C/U): СанПиН 2.3/2.4.3590-20, ТР ТС 021/2011, преимущества.
  - **Заморозка полуфабриката** (Profi C-Ultra / U-Frost): шоковая заморозка, Ижица UTR-F.

### Changed
- `docs/cameras/feleti-smok/SPEC.md` — добавлены Profi C и Profi U линейки с холодным копчением, охлаждением и заморозкой (по запросу пользователя).
- `docs/RECIPES_BASE.md` — расширена секция «Типы копчения» (добавлены C, U, F, ELE линейки FELETI-SMOK).
- `docs/SKILL_SMOKING.md` — таблица видов копчения дополнена колонкой «Камера FELETI-SMOK».

### Решено (продолжение)
- **По запросу пользователя:** FELETI-SMOK Profi C (холодное + охлаждение) и Profi U (универсал) добавлены в линейку. Источники: холодное копчение и охлаждение у Ижицы (UTR-C, UTR-F), Mauting (туннели), Fessmann (Turbomat с предварит. охлаждением).
- **Создана структура для глубокого парсинга** (`docs/research/`): Ижица — приоритет P0, остальные — P1-P3.

---

## [0.1.0] — 2026-06-02 (foundation)

### Added
- Инициализирован проект `koptilnya-platform` (Git, README, .gitignore, .env.example, docker-compose).
- Backend skeleton: `Dockerfile`, `pyproject.toml` (FastAPI 0.115, SQLAlchemy 2.0 async, asyncpg, alembic, pymodbus, asyncua, reportlab, loguru).
- `app/main.py` — FastAPI app, lifespan, CORS, healthcheck.
- `app/core/config.py` — Pydantic Settings.
- `app/core/security.py` — bcrypt + JWT.
- `app/db/base.py` — SQLAlchemy DeclarativeBase, модель-реестр для Alembic.
- `app/db/session.py` — async engine, sessionmaker.
- `app/models/user.py` — User + UserRole enum (admin/technologist/operator/manager/viewer).
- `app/models/manufacturer.py` — Manufacturer.
- Структура `.opencode/skills/` с 6 каталогами: smoke-platform, add-recipe, add-chamber, camera-driver, seed-data, design-system.
- `docs/PROJECT_BOOT.md` — главная точка входа.
- `docs/CAMERA_DRIVER.md` — универсальный драйвер (Modbus TCP + cloud).
- `docs/SKILL_DEV.md` — стек и конвенции разработки.
- `docs/SKILL_SMOKING.md` — база знаний технолога.
- `docs/ARCHITECTURE.md` — C4-архитектура.
- `docs/CONTEXT_HANDOFF.md` — протокол передачи контекста.
- `docs/COMPETITORS.md` — детальная матрица конкурентов.
- `docs/RECIPES_BASE.md` — структура базы рецептов (50+ стартовых).
- `docs/FELETI_BRAND.md` — айдентика (цвета, типографика, компоненты).
- `БАЗА_ЗНАНИЙ_КОПЧЕНИЕ.md` (в родительской папке) — общая база знаний о копчении.
- `docker-compose.yml` — 6 сервисов: postgres, redis, backend, frontend, adminer, minio.

### Changed
- (none — первый релиз)

### Fixed
- (none — первый релиз)

### Removed
- (none — первый релиз)

### Notes
- Проект находится в фазе **foundation** (документация + скелет backend).
- Hardware-стратегия FELETI-SMOK зафиксирована: Kinco + свой модуль, Profi/Industrial B2B, свой дымогенератор, электростатика как опция.
- GitHub-репозиторий — отложен (по запросу пользователя "потом").

---

## Шаблон для следующих версий

```markdown
## [X.Y.Z] — YYYY-MM-DD

### Added
- Что добавлено (фичи, файлы, API).

### Changed
- Что изменилось (рефакторинг, улучшения).

### Fixed
- Что исправлено (баги).

### Removed
- Что удалено.

### Notes
- Важные заметки для следующих сессий.
```
