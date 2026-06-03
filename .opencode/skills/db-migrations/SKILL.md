# SKILL: db-migrations

> Работа с Alembic: генерация, применение, откат миграций PostgreSQL. Используй при изменении моделей SQLAlchemy.

## 1. Контекст

Проект использует **Alembic** с async-режимом (SQLAlchemy 2.0 + asyncpg). Миграции хранятся в `backend/alembic/versions/`.

**Ключевые файлы:**
- `backend/alembic.ini` — конфигурация Alembic
- `backend/alembic/env.py` — async-окружение, импорт всех моделей
- `backend/app/db/base.py` — DeclarativeBase + реестр моделей
- `backend/app/models/__init__.py` — импорт всех моделей для autogenerate

## 2. Генерация миграции

### 2.1. Предусловия
1. Все модели импортированы в `app/db/base.py` или `app/models/__init__.py`
2. Docker Compose запущен (`docker compose up -d db`)
3. База данных `feleti_smok` существует

### 2.2. Команда
```bash
cd D:/Коптильные камеры/koptilnya-platform/backend
docker compose exec backend alembic revision --autogenerate -m "initial"
```

Или локально (с правильным DATABASE_URL):
```bash
cd backend
alembic revision --autogenerate -m "add recipe approval workflow"
```

### 2.3. Проверка сгенерированной миграции
```bash
# Посмотреть последнюю миграцию
ls -la alembic/versions/
cat alembic/versions/xxxx_initial.py
```

**Что проверить:**
- [ ] Все таблицы созданы (не пропущены)
- [ ] Foreign keys корректны
- [ ] Типы данных соответствуют моделям
- [ ] Нет `drop_table` без явной необходимости
- [ ] Enum созданы через `sa.Enum` (не `VARCHAR`)

## 3. Применение миграций

```bash
# В Docker
docker compose exec backend alembic upgrade head

# Локально
cd backend && alembic upgrade head
```

**Проверка:**
```bash
docker compose exec db psql -U feleti -d feleti_smok -c "\dt"
```

## 4. Откат миграций

```bash
# Откат на 1 миграцию назад
docker compose exec backend alembic downgrade -1

# Откат до начала
docker compose exec backend alembic downgrade base

# Конкретная ревизия
docker compose exec backend alembic downgrade abc123
```

## 5. Исправление ошибок миграций

### 5.1. Миграция упала на prod
1. Не редактировать уже примененную миграцию!
2. Создать **новую** миграцию с `op.alter_column` / `op.add_column`
3. Проверить на staging

### 5.2. autogenerate пропустил что-то
- Alembic не видит: CHECK constraints, триггеры, индексы GIN, partial indexes
- Добавить руками в миграцию:
```python
op.create_index('ix_knowledge_search', 'knowledge_articles', ['search_vector'], postgresql_using='gin')
```

## 6. Seed после миграций

```bash
docker compose exec backend python -m app.scripts.seed
```

## 7. Чек-лист

- [ ] Модели импортированы в `models/__init__.py`
- [ ] `alembic.ini` настроен на правильную БД
- [ ] Миграция проверена глазами перед `upgrade head`
- [ ] Seed запущен после миграций
- [ ] API проверен (`curl /api/v1/health/db`)

## 8. Связь с другими скиллами

- `smoke-platform` — общие правила
- `seed-data` — для наполнения после миграций
- `pytest-testing` — для проверки миграций

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при изменении моделей SQLAlchemy.
