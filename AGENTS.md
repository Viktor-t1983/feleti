# AGENTS.md — FELETI-SMOK

> Инструкции для AI-агентов, работающих с проектом.

---

## 🎯 Контекст проекта

**FELETI-SMOK** — платформа управления коптильным производством (Брест, Беларусь).
- Производитель оборудования: FELETI
- Главный конкурент: Ижица / Varmen (Россия)
- Целевая аудитория: технологи, операторы камер, владельцы цехов

---

## 🏗 Стек и версии

| Компонент | Версия | Примечание |
|-----------|--------|------------|
| Python | 3.11 | FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Node.js | 24.x | Next.js 14, TypeScript strict |
| PostgreSQL | 16 | `feleti_smok` database |
| Redis | 7 | кэш, pub/sub |
| MinIO | latest | S3-совместимое хранилище |
| Mosquitto | 2.0 | MQTT брокер |

---

## 📋 Правила работы

### 1. Всегда проверяй результат
- После любых изменений: `npm run build` (frontend), `docker compose restart backend` (backend)
- Проверяй API через curl или docker exec python
- Убедись, что build проходит с 0 ошибок

### 2. Кодировка (Windows)
- Всегда используй UTF-8 для Python скриптов
- Устанавливай `PYTHONIOENCODING=utf-8` перед запуском
- PowerShell: `chcp 65001` для UTF-8 вывода

### 3. Docker команды
```powershell
# Перезапуск backend после изменений
docker compose restart backend

# Alembic миграции
docker compose exec backend alembic revision --autogenerate -m "описание"
docker compose exec backend alembic upgrade head

# Seed данных
docker compose exec backend python -m app.scripts.seed
docker compose exec backend python -m scripts.seed_recipes_batches
docker compose exec backend python -m scripts.seed_knowledge
```

### 4. Frontend conventions
- **Тема**: dark по умолчанию, `html className="dark"`
- **Цвета**: FELETI gold `#c9a96e`, graphite `#1a1a1a`
- **Шрифт**: Inter (latin + cyrillic)
- **State**: Zustand (auth), TanStack Query (server state)
- **Формы**: React Hook Form + Zod
- **Анимации**: Framer Motion
- **Графики**: Recharts

### 5. Backend conventions
- SQLAlchemy 2.0 style: `Mapped[int]`, `mapped_column()`
- Pydantic v2: `model_validate()`, `ConfigDict(from_attributes=True)`
- Endpoints: `PageParams` с default `= PageParams()`
- Seed: идемпотентен (проверяет `existing` по slug/email)

### 6. Git workflow
- Commit message format: `type(scope): описание` (Conventional Commits)
- Примеры: `feat(frontend): add dashboard charts`, `fix(backend): power_kw Float type`
- Всегда делай commit после завершения фичи
- Обновляй CHANGELOG.md перед коммитом

---

## 📁 Ключевые файлы

| Файл | Назначение |
|------|------------|
| `backend/app/models/` | SQLAlchemy модели |
| `backend/app/schemas/` | Pydantic схемы |
| `backend/app/api/v1/endpoints/` | API endpoints |
| `backend/app/scripts/seed.py` | Основной seed |
| `frontend/src/app/` | Next.js страницы |
| `frontend/src/lib/api/client.ts` | Axios + JWT |
| `frontend/src/stores/auth.ts` | Zustand auth |
| `frontend/src/components/layout/` | Sidebar, Header |
| `docker-compose.yml` | Инфраструктура |

---

## 🔑 API Endpoints (ключевые)

| Endpoint | Назначение |
|----------|------------|
| `POST /auth/login/json` | Логин (demo: admin/admin, tech/tech, operator/operator) |
| `GET /dashboard/stats` | Агрегированные данные для Dashboard |
| `GET /chambers` | Список камер |
| `GET /recipes` | Список рецептов |
| `GET /batches` | Список партий |
| `POST /batches` | Создание партии |
| `GET /competitors` | Конкуренты |
| `GET /knowledge` | Статьи базы знаний |
| `WS /chambers/{id}/telemetry/ws?token=` | WebSocket телеметрии |

---

## 📝 Проверочный чеклист (перед commit)

- [ ] Frontend build: `npm run build` — 0 ошибок
- [ ] Backend запускается: `docker compose restart backend`
- [ ] API health: `curl http://localhost:8000/api/v1/health`
- [ ] CHANGELOG.md обновлён
- [ ] README.md актуален (если менялись страницы/фичи)
- [ ] Новые скрипты в `backend/scripts/` (не в корне)
- [ ] Нет console.log / print отладки
- [ ] Кодировка UTF-8

---

## 🆘 Известные проблемы

1. **Next.js dev server timeout**: фоновая задача таймаутится через 60s, но сервер продолжает работать
2. **ijiza.ru цены скрыты**: B2B модель, цены по запросу
3. **Telegram парсинг**: требуется API_ID/API_HASH от пользователя
4. **Chamber WebSocket**: камеры используют SimulatedDriver, реальное подключение требует Modbus
