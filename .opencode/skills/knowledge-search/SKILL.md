# SKILL: knowledge-search

> CRUD статей базы знаний + полнотекстовый поиск. Загружай при работе с эндпоинтами `/knowledge/*`.
> Загружай совместно с `smoke-platform` для общей картины.

## 1. Назначение

База знаний хранит:
- Теорию копчения (типы, физика, химия дыма).
- Рецепты-нарративы (длинные тексты с иллюстрациями).
- Troubleshooting (решение типовых проблем).
- Регуляторику (ГОСТы, ТР ТС, СанПиН).
- Сравнения конкурентов.
- Обзоры (отзывы, видео, TG-посты).
- Новости отрасли.
- Гайды (step-by-step инструкции).

## 2. Структура модели (реальная)

```python
KnowledgeArticle:
  - id: int
  - title: str                      # "Холодное копчение рыбы: полный гайд"
  - slug: str                       # "holodnoe-kopchenie-ryby", ^[a-z0-9-]+$, уникальный
  - body_md: str                    # Markdown-контент
  - body_html: str | None           # Рендеренный HTML (для быстрого отображения)
  - excerpt: str | None             # Краткое описание (для превью)
  - category: ArticleCategory       # theory|recipe|troubleshooting|regulation|comparison|review|news|guide
  - tags: list[str]                 # ["холодное", "рыба", "лосось", ...]
  - manufacturer_id: int | None     # FK на Manufacturer (для сравнений/обзоров)
  - chamber_model: str | None       # "Varmen-1" (для troubleshooting по конкретной камере)
  - source_url: str | None          # URL источника
  - is_published: bool              # Только published видны в публичном API
  - version: int                    # авто-инкремент при PATCH
  - author_id: int | None           # FK на User
  - created_at, updated_at
  - published_at: datetime | None

KnowledgeAttachment:
  - id, article_id
  - file_id: str                    # ID в MinIO
  - kind: AttachmentKind            # pdf|video|image|doc|link
  - filename: str
  - size_bytes: int
  - mime_type: str | None
  - url: str | None                 # Альтернативный URL (для YouTube, etc)
```

## 3. API Endpoints (реальные)

### 3.1. CRUD
```
GET    /api/v1/knowledge                                  # список (с пагинацией, фильтрами)
GET    /api/v1/knowledge/{id}                             # детальная карточка
GET    /api/v1/knowledge/by-slug/{slug}                   # для SEO/публичных ссылок
POST   /api/v1/knowledge                                  # создать (с вложениями)
PATCH  /api/v1/knowledge/{id}                             # обновить (с авто-инкрементом version)
DELETE /api/v1/knowledge/{id}                             # удалить (с каскадом вложений)
GET    /api/v1/knowledge/search?q=...&category=...        # поиск
```

### 3.2. Фильтры для list
- `category: ArticleCategory` — фильтр по категории
- `tag: str` — JSONB contains (точное совпадение элемента массива)
- `manufacturer_id: int` — для сравнений/обзоров
- `is_published: bool` — только published

### 3.3. Параметры search
- `q: str` (2..200 символов) — поисковый запрос
- `category: ArticleCategory` (опц.) — фильтр по категории
- `limit: int` (1..100, default 20) — макс. результатов

## 4. Search Strategy v1 (текущая)

> Реализована в `api/v1/endpoints/knowledge.py` (сессия 5).

### 4.1. Алгоритм
1. **Разбивка запроса** на слова (по `[\s,.;:!?()\[\]{}\"']+`), фильтр ≥ 2 символов, max 10 слов.
2. **Построение OR-выражения**: для каждого слова — `ILIKE %word%` по `title`, `body_md`, `excerpt`.
3. **In-Python скоринг**:
   - `title` совпало: **+3**
   - `tags` совпало (== или contains): **+2**
   - `excerpt` совпало: **+2**
   - `body_md` совпало: **+1**
4. **Сортировка** по `(score desc, updated_at desc)`.
5. **Snippet**: 200 символов вокруг первого совпадения в `body_md`.

### 4.2. Ограничения
- ❌ Не учитывается морфология (стемминг, лемматизация).
- ❌ Нет рейтинга по релевантности (только частота совпадений).
- ❌ Нет фасетного поиска.
- ❌ Не используется вес полей в БД (только в Python).

### 4.3. Search Strategy v2 (TODO, нужна Alembic-миграция)

**PostgreSQL tsvector** + GIN-индекс:
```sql
ALTER TABLE knowledge_articles
ADD COLUMN search_vector tsvector
  GENERATED ALWAYS AS (
    setweight(to_tsvector('russian', coalesce(title,'')), 'A') ||
    setweight(to_tsvector('russian', coalesce(excerpt,'')), 'B') ||
    setweight(to_tsvector('russian', coalesce(array_to_string(tags, ' '),'')), 'B') ||
    setweight(to_tsvector('russian', coalesce(body_md,'')), 'C')
  ) STORED;

CREATE INDEX ix_knowledge_search ON knowledge_articles USING GIN(search_vector);
```

Запрос:
```sql
SELECT *, ts_rank(search_vector, plainto_tsquery('russian', $1)) AS rank
FROM knowledge_articles
WHERE search_vector @@ plainto_tsquery('russian', $1)
  AND category = $2
ORDER BY rank DESC
LIMIT $3;
```

Преимущества:
- Стемминг и лемматизация для русского.
- Учёт веса полей (A/B/C).
- GIN-индекс = O(log N) на больших объёмах.
- Сортировка по rank в БД.

## 5. Создание статьи

### 5.1. Через REST API
```python
POST /api/v1/knowledge
{
  "title": "Холодное копчение лосося: полный гайд",
  "slug": "holodnoe-kopchenie-lososya",
  "body_md": "## Введение\n\nХолодное копчение — это...",
  "body_html": "<h2>Введение</h2><p>Холодное копчение — это...</p>",  // опц.
  "excerpt": "Пошаговый гайд по холодному копчению лосося...",
  "category": "guide",
  "tags": ["холодное", "рыба", "лосось", "гайд"],
  "manufacturer_id": null,
  "chamber_model": null,
  "source_url": "https://feleti.by/articles/...",
  "is_published": true,
  "attachments": [
    {
      "file_id": "minio-uuid-1",
      "kind": "image",
      "filename": "losos-1.jpg",
      "size_bytes": 245678,
      "mime_type": "image/jpeg",
      "url": "https://cdn.feleti.by/losos-1.jpg"
    }
  ]
}
```

Backend:
1. Создаёт `KnowledgeArticle` + `KnowledgeAttachment` (каскадно).
2. Проверяет уникальность `slug` → иначе 409.
3. Audit (CREATE).
4. Возвращает полную карточку с вложениями.

### 5.2. Через seed (для dev)
Добавить в `app/scripts/seed.py`:
```python
KNOWLEDGE_ARTICLES: list[dict] = [
    {
        "title": "Холодное копчение лосося: полный гайд",
        "slug": "holodnoe-kopchenie-lososya",
        "body_md": "...",
        "category": ArticleCategory.GUIDE,
        "tags": ["холодное", "рыба", "лосось"],
        "is_published": True,
        "version": 1,
    },
    ...
]
```

## 6. Обновление статьи

```python
PATCH /api/v1/knowledge/{id}
{
  "body_md": "## Введение (обновлено)\n\n...",
  "tags": ["холодное", "рыба", "лосось", "форель", "обновлено"],
  "is_published": true
}
```

Backend:
1. Загружает статью + вложения.
2. Применяет изменения (только переданные поля).
3. **Авто-инкремент `version`**: 1 → 2 → 3 → ...
4. Audit (UPDATE, before/after).

**Вложения НЕ обновляются через PATCH** — для этого отдельный endpoint (TODO):
- `POST /knowledge/{id}/attachments` — добавить
- `DELETE /knowledge/{id}/attachments/{aid}` — удалить

## 7. Удаление

```python
DELETE /api/v1/knowledge/{id}
```

- Каскадно удаляются `KnowledgeAttachment` (`cascade="all, delete-orphan"`).
- Audit (DELETE, before).

## 8. Формат Markdown (body_md)

Поддерживаем:
- **Заголовки**: `# H1`, `## H2`, `### H3`.
- **Текст**: `**жирный**`, `*курсив*`, `~~зачёркнутый~~`, `` `код` ``.
- **Списки**: `-`, `1.`, `- [ ]` (todo).
- **Ссылки**: `[текст](url)`.
- **Изображения**: `![alt](url)`.
- **Таблицы**: GFM.
- **Блоки кода**: ` ``` ` (с языком).
- **Цитаты**: `>`.
- **HTML inline**: разрешён, но body_html предпочтительнее для UI.

**Конвертация в HTML** — на frontend (react-markdown) или backend (TODO: `markdown` пакет).

## 9. Чек-лист при работе с базой знаний

- [ ] `slug` уникален, формат `^[a-z0-9-]+$`.
- [ ] `category` из справочника (8 вариантов).
- [ ] `body_md` не пустой.
- [ ] `excerpt` ≤ 1000 символов (если задан).
- [ ] `tags` — массив строк (не объекты).
- [ ] `is_published: true` для публичных статей.
- [ ] `manufacturer_id` существует (если задан).
- [ ] При PATCH `version` инкрементируется автоматически.
- [ ] Audit логируется при CREATE/UPDATE/DELETE.
- [ ] Вложения привязаны к MinIO (file_id валиден).

## 10. TODO для будущих сессий

- [ ] **tsvector fulltext search** (нужна Alembic-миграция с GIN).
- [ ] **Markdown → HTML конвертация** на backend (для SEO/email).
- [ ] **CRUD для вложений** (`POST/DELETE /knowledge/{id}/attachments`).
- [ ] **MinIO интеграция** для загрузки файлов (presigned URLs).
- [ ] **Публичный endpoint** для опубликованных статей (без auth, rate-limited).
- [ ] **RAG endpoint**: `/knowledge/rag?q=...` — возвращает top-K с контекстом для AI-чата.
- [ ] **Импорт** из Markdown-файлов (batch из `docs/research/`).
- [ ] **Версионирование статей** (хранить историю PATCH в `knowledge_article_versions`).

## 11. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `seed-data` — для сидирования начальных статей.
- `research-competitor` — для парсинга статей конкурентов.
- (TODO) `knowledge-rag` — для AI-копилота на основе базы знаний.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при работе с эндпоинтами `/knowledge/*` или создании UI базы знаний.
