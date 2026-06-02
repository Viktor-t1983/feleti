# SKILL: seed-data

> Сидирование начальных данных в БД. Используй при первоначальной настройке, добавлении/изменении каталога.
> Загружай совместно с `add-chamber` или `add-recipe` если добавляешь новые сущности.

## 1. Текущая реализация

Seed реализован **in-memory** в одном Python-файле, не через JSON.

```
backend/app/scripts/
├── __init__.py
└── seed.py                        # ← идемпотентный сидер
```

**Запуск:** `cd backend && python -m app.scripts.seed` (или через Docker).

**Идемпотентность:** все сущности вставляются по `slug`/`email`. Если уже есть — пропускается.

## 2. Структура seed.py

```python
# Константы в начале файла:
MANUFACTURERS: list[dict] = [...]  # 7 производителей
CHAMBERS: dict[str, dict] = {...}  # по slug
PRODUCTS: list[dict] = [...]       # 8 продуктов
INGREDIENTS: list[dict] = [...]    # 6 ингредиентов
USERS: list[dict] = [...]          # 3 demo-пользователя

# Анти-дубликаты (вставленные slug'и за сессию):
_inserted: set[str] = set()
```

**Шаблон сущности** (на примере производителя):
```python
{
    "name": "Ижица",
    "slug": "ijiza",
    "country": "Россия",
    "website": "https://ijiza.ru",
    "description": "...",
    "is_our_brand": False,
    "is_competitor": True,
    "sort_order": 10,
    "logo_url": None,
}
```

**Шаблон камеры** (см. SKILL `add-chamber` для полного примера):
```python
"feleti-smok-profi-h-250": {
    "manufacturer_slug": "feleti",
    "model": "Profi H 250",
    "slug": "feleti-smok-profi-h-250",
    "type": ChamberType.HOT,
    "max_load_kg": 250.0,
    "power_kw": 36.0,
    "voltage_v": 380,
    "supports_static_smoke": True,
    "supports_electro": True,    # опция
    "supports_cold_smoke": False,
    "supports_cooling": False,
    "supports_freezing": False,
    "supported_protocols": ["modbus_tcp"],
    "driver_class": "FELETI_SMOKDriver",
    "default_driver_config": {
        "kinco_host": "192.168.1.100",
        "kinco_port": 502,
        "module_host": "192.168.1.101",
        "module_port": 503,
    },
    "num_chambers": 1,
    "num_carts": 1,
    "num_probes": 3,
    "max_program_phases": 16,
    "price_rrp_rub": 4_500_000,
    "verified": True,
    "description": "Профессиональная камера горячего копчения 250 кг.",
},
```

**Шаблон продукта:**
```python
{
    "name": "Докторская (колбаса)",
    "slug": "doktorskaya-kolbasa",
    "category": "колбаса вареная",
    "description": "Классическая вареная колбаса по ГОСТ.",
}
```

**Шаблон ингредиента:**
```python
{
    "name": "Свинина п/ж",
    "slug": "svinina-pzh",
    "type": IngredientType.MEAT,
    "protein_per_100g": 14.0,
    "fat_per_100g": 33.0,
    "carbs_per_100g": 0.0,
    "kcal_per_100g": 357.0,
    "price_per_kg": 420.0,
    "unit": "кг",
    "is_allergen": False,
    "allergens": [],
    "gmo_flag": False,
}
```

**Шаблон пользователя:**
```python
{
    "username": "admin",
    "email": "admin@feleti.local",
    "full_name": "Администратор",
    "password": "feleti_admin_dev",   # будет захеширован
    "role": UserRole.ADMIN,
    "is_superuser": True,
    "is_active": True,
}
```

## 3. Алгоритм сидирования

### 3.1. Процедура
1. **Запустить миграции** (нужен Docker):
   ```bash
   docker compose exec backend alembic upgrade head
   ```
2. **Запустить seed**:
   ```bash
   docker compose exec backend python -m app.scripts.seed
   ```
   Или локально (с `DATABASE_URL` на локальную БД):
   ```bash
   cd backend && python -m app.scripts.seed
   ```
3. **Проверить**:
   ```bash
   docker compose exec db psql -U feleti -d feleti_smok -c "SELECT slug, name FROM manufacturers;"
   ```

### 3.2. Идемпотентность
- `Manufacturer`: уникальность по `slug`.
- `Chamber`: уникальность по `slug`.
- `Product`: уникальность по `slug`.
- `Ingredient`: уникальность по `slug`.
- `User`: уникальность по `email` и `username`.

Если сущность уже есть — seed логирует `SKIP: ...` и не вставляет дубль.

### 3.3. Хеширование паролей
- Используется `passlib` + `bcrypt` (см. `app/core/security.py`).
- `pwd_context.hash(plain)` вставляет хеш в `User.hashed_password`.

## 4. Целевой объём данных (TODO)

| Категория | Сейчас | Цель | Приоритет |
|---|---|---|---|
| Производители | 7 | 9 (+ Vemag, VSD TEC) | P2 |
| Камеры | 6 | 18+ (все линейки конкурентов + FELETI-SMOK H/C/U) | P0 |
| Продукты | 8 | 30+ (все категории) | P1 |
| Ингредиенты | 6 | 30+ (с щёпой по породам) | P1 |
| Brines | 0 | 10+ (типовые посолы) | P1 |
| Рецепты | 0 | 50+ (базовый набор из RECIPES_BASE.md) | P0 |
| Knowledge articles | 0 | 10+ (типы копчения, ГОСТы, troubleshooting) | P1 |
| Users | 3 | 3 (admin/tech/operator) | ✅ |

## 5. Чек-лист добавления seed-данных

- [ ] Все slug'и уникальны в рамках проекта.
- [ ] Все slug'и в формате `^[a-z0-9-]+$`.
- [ ] Производитель существует в `MANUFACTURERS` (для `manufacturer_slug`).
- [ ] `driver_class` зарегистрирован (для камер).
- [ ] `default_driver_config` — валидный dict (без `None` для обязательных полей).
- [ ] `verified: false` для новых данных.
- [ ] Источник указан (`source_url`, `source`).
- [ ] Цены реалистичны (для РФ/СНГ).
- [ ] Единицы измерения: `price_per_kg` в BYN/RUB, `max_load_kg` в кг, `volume_m3` в м³.

## 6. Альтернативные подходы (TODO)

- **JSON-файлы** в `data/seed/` — гибче, но требует парсер. Рассматривал в начале, отказались в пользу Python.
- **CSV/Excel импорт** через Celery worker — для bulk-импорта от поставщиков.
- **API-импорт** — `POST /api/v1/manufacturers` + `POST /api/v1/chambers` в цикле (для миграций).

## 7. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `add-recipe` — для добавления новых рецептов.
- `add-chamber` — для добавления новых камер.
- `camera-driver` — для регистрации драйверов перед seed камер.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при первоначальной настройке БД или добавлении/изменении каталога.
