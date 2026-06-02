# CHANGELOG — FELETI-SMOK

> Все значимые изменения в проекте. Формат: [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/).

---

## [Unreleased]

### В работе
- Backend: модели chamber, product, ingredient, recipe, brine, batch, knowledge, audit
- Backend: API v1 для всех сущностей
- Frontend: init Next.js 14 + shadcn/ui + PWA
- Seed-данные: 9 производителей, 18+ камер, 50+ рецептов
- Реальный стенд FELETI-SMOK (R&D)

### Added
- `docs/FELETI_BRAND.md` — айдентика (цвета, типографика, компоненты, PWA-иконки).
- `docs/ARCHITECTURE.md` — детальная C4-архитектура.
- `docs/CONTEXT_HANDOFF.md` — протокол передачи контекста между сессиями.
- `docs/COMPETITORS.md` — детальная матрица конкурентов (Ижица, Mauting, Fessmann, Kerres, AGROS, Reich, Vemag, VSD TEC).
- `docs/RECIPES_BASE.md` — структура базы рецептов, 50+ стартовых.
- `CHANGELOG.md`, `TODO.md`, `OPEN_QUESTIONS.md` — project management.
- `.opencode/AGENTS.md` — entry point для opencode-агента.
- 7 файлов `SKILL.md` в `.opencode/skills/{smoke-platform,add-recipe,add-chamber,camera-driver,seed-data,design-system,research-competitor}/`.
- `docs/cameras/feleti-smok/SPEC.md` — спецификация камеры FELETI-SMOK.
- `backend/app/drivers/base.py` — интерфейс `ChamberDriver` (capabilities, telemetry, program).
- `backend/app/drivers/__init__.py` — реестр драйверов с декоратором `@register`.
- `backend/app/drivers/simulated.py` — мок с физической моделью (T_chamber, T_product, инерция, фазы).
- `backend/app/drivers/feleti_smok.py` — драйвер камер FELETI-SMOK (Kinco + свой модуль, Modbus TCP).
- `backend/app/drivers/varmen.py` — драйвер камер Ижица Varmen (Modbus TCP, DRAFT-карта регистров).
- `docker-compose.yml` — добавлен Mosquitto MQTT broker для облачного канала камер.
- `nginx/mosquitto.conf` — конфигурация Mosquitto с auth + ACL.

### Changed
- `docs/PROJECT_BOOT.md` — обновлён: FELETI как производитель камер + зафиксирована hardware-стратегия (Kinco + свой модуль, Profi/Industrial, свой дымогенератор, электростатика-опция).
- `docs/CAMERA_DRIVER.md` — добавлена двухуровневая архитектура камер FELETI-SMOK (Kinco + свой модуль).

### Решено
- Зафиксирована hardware-стратегия камер FELETI-SMOK: Kinco HMI/PLC + свой модуль расширения; Profi/Industrial B2B; электростатика как опция; свой дымогенератор (щепа + фрикционный + атомайзер); датчики — всегда максимальная комплектация.

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
