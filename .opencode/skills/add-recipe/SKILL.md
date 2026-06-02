# SKILL: add-recipe

> Создание и редактирование рецепта копчения. Используй при добавлении нового рецепта в базу или редактировании существующего.
> Загружай совместно с `recipe-calc` для расчёта БЖУ/себестоимости.

## 1. Структура рецепта (реальная)

```python
Recipe:
  - id: int
  - product_id: int
  - name: str                        # "Докторская ГОСТ"
  - slug: str                        # "doktorskaya-gost", уникальный, ^[a-z0-9-]+$
  - current_version_id: int          # FK на RecipeVersion
  - status: enum[draft|pending|approved|rejected|archived]
  - description: str
  - tags: list[str]
  - created_by_id, created_at, updated_at

RecipeVersion (иммутабельный):
  - id, recipe_id, version_number, parent_version_id
  - program: list[ProgramPhase]      # фазы копчения
  - brine: dict | None               # посол
  - ingredients: list[dict]          # [{"ingredient_id": 1, "mass_kg": 5.0, "name": "Свинина"}]
  - yield_percent, losses_percent    # числа (%)
  - bju_per_100g: dict | None        # {protein, fat, carbs, kcal}
  - cost_per_kg: float | None
  - notes, gost, source
  - verified, verified_by_id, verified_at
  - status: enum[draft|pending|approved|rejected|archived]
  - created_by_id, created_at

ProgramPhase (внутри RecipeVersion.program, JSON-список):
  - index, name (Подсушка/Копчение/Варка/Охлаждение)
  - duration_min
  - t_chamber, t_product
  - humidity_percent
  - smoke: none|light|medium|heavy
  - wood_species: ольха|бук|дуб|яблоня|вишня|...
  - wood_form: щепа|опилки|стружка
  - electro_voltage_kv: float        # 0 = выкл
  - fan_speed_percent: int
  - transition: time|product_temp|delta_t

Brine (внутри RecipeVersion.brine, JSON-dict):
  - method: сухой|мокрый|шприцевание|комбинированный|смешанный
  - salt_percent, sugar_percent
  - nitrite_ppm, nitrate_ppm
  - spices: list[str]
  - duration_hours, temp_c

RecipeIngredient (внутри RecipeVersion.ingredients, JSON-список):
  - ingredient_id: int
  - mass_kg: float | None            # абсолютная масса
  - mass_g: float | None             # альтернативно
  - percent: float | None            # % от общей массы (для соли, специй)
  - name: str | None                 # денормализованное имя (для UI)
```

## 2. Алгоритм добавления рецепта

### 2.1. Сбор данных
1. **Источник:** ГОСТ, каталог производителя, технолог, книга, TG-канал.
2. **Поля для заполнения:**
   - Название продукта.
   - Категория (колбаса/мясо/птица/рыба/сыр/сало/снеки).
   - Выход (% к сырью), потери (%).
   - Ингредиенты с весами/процентами.
   - Программа копчения (фазы, t, влажность, дым, щепа, длительность).
   - Посол (если есть).
   - Условия хранения.
3. **Проверка:** указать источник и `verified: false` (до проверки технологом).

### 2.2. Создание в коде
1. **Найти `product_id`** — если продукта нет, создать в `app/scripts/seed.py` (`PRODUCTS`).
2. **Создать `Recipe`** со статусом `draft` через `POST /api/v1/recipes`.
3. **Создать `RecipeVersion v1`** через `POST /api/v1/recipes/{id}/versions` (с указанием `parent_version_id=null`).
4. **Привязать** `Recipe.current_version_id = v1.id` (делается автоматически).
5. **Запустить** `GET /api/v1/recipes/{id}/calc` для расчёта БЖУ/себестоимости.
6. **Сохранить** результат в `RecipeVersion.bju_per_100g` и `cost_per_kg` через `PATCH /versions/{vid}`.
7. **Сидировать** для повторного использования: добавить в `app/scripts/seed.py` (`RECIPES`).

### 2.3. Шаблон JSON (для seed)
```json
{
  "name": "Докторская ГОСТ",
  "slug": "doktorskaya-gost",
  "category": "колбаса вареная",
  "product_slug": "doktorskaya-kolbasa",
  "yield_percent": 108,
  "losses_percent": -8,
  "source": "ГОСТ Р 52196-2011",
  "verified": false,
  "ingredients": [
    { "ingredient_slug": "govyadina-1s", "percent": 25 },
    { "ingredient_slug": "svinina-pzh", "percent": 35 },
    { "ingredient_slug": "shpik", "percent": 15 },
    { "ingredient_slug": "moloko-sukhoe", "percent": 2 },
    { "ingredient_slug": "yaitsa", "percent": 2 },
    { "ingredient_slug": "sol-pischevaya", "percent": 2.5 },
    { "ingredient_slug": "nitritnaya-sol", "percent": 0.5 },
    { "ingredient_slug": "sahar", "percent": 0.2 },
    { "ingredient_slug": "muskatny-oreh", "percent": 0.05 },
    { "ingredient_slug": "voda-led", "percent": 17.75 }
  ],
  "brine": null,
  "program": [
    { "phase": "Подсушка", "duration_min": 30, "t_chamber": 50, "humidity": 30, "smoke": "none" },
    { "phase": "Копчение", "duration_min": 60, "t_chamber": 75, "humidity": 50, "smoke": "medium", "wood": "ольха" },
    { "phase": "Варка", "duration_min": 60, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72 },
    { "phase": "Охлаждение душем", "duration_min": 15, "t_chamber": 18, "humidity": 100, "smoke": "none" },
    { "phase": "Подсушка после душа", "duration_min": 30, "t_chamber": 22, "humidity": 60, "smoke": "none" }
  ],
  "storage": { "temp_c": [2, 8], "humidity": [78, 80], "shelf_life_days": 5 },
  "gost": "ГОСТ Р 52196-2011",
  "notes": "Классический рецепт. Контроль: t в центре батона ≥ +72°C."
}
```

## 3. Типы копчения (reference)

| Тип | Т камеры | Т продукта | Время | Дым | Электро |
|---|---|---|---|---|---|
| **Холодное** | 18–25 | 18–25 | 12 ч – 14 сут | лёгкий/средний, длительно | иногда |
| **Горячее** | 40–110 | 40–95 | 30 мин – 6 ч | средний/сильный | часто |
| **Полугорячее** | 30–60 | 30–55 | 1–4 ч | средний | часто |
| **Электростатическое** | 18–60 | 18–55 | 30–120 мин | лёгкий, 10–30 кВ | обязательно |
| **Универсальное** | 18–110 | 18–95 | 30 мин – 14 сут | любой | опц. |

## 4. Древесина для копчения (reference)

| Порода | Вкус/аромат | Лучше для | Цвет |
|---|---|---|---|
| **Ольха** | Мягкий, нейтральный | Рыба, курица, свинина, сало | Золотистый |
| **Бук** | Нейтральный, сладковатый | Колбасы, сыры, говядина | Жёлто-коричневый |
| **Дуб** | Терпкий, насыщенный | Говядина, баранина, дичь, выдержанные колбасы | Тёмно-коричневый |
| **Яблоня** | Сладковатый, фруктовый | Свинина, птица, сыры | Золотистый |
| **Вишня** | Сладковатый, лёгкий | Птица, свинина, сыры | Красно-коричневый |
| **Груша** | Мягкий, сладковатый | Рыба, птица | Золотистый |

**Нельзя:** хвойные с большим содержанием смолы (сосна, ель) — горечь и вредные вещества.

## 5. Стартовый список рецептов (50+)

См. `docs/RECIPES_BASE.md`, секция 4. Целевой набор:
- **Колбасы варёные (5):** Докторская, Молочная, Русская, Любительская, Чайная.
- **Колбасы полукопчёные (5):** Краковская, Одесская, Сервелат, Таллиннская, Польская.
- **Колбасы сырокопчёные (4):** Суджук, Салями Московская, Брауншвейгская, Сервелат Элитный.
- **Мясо (7):** Буженина, Карбонад, Грудинка, Балык, Ростбиф, Язык, Корейка.
- **Птица (5):** Курица, Утка, Грудинка индейки, Крылышки, Перепёлка.
- **Рыба горячего копчения (8):** Скумбрия, Салака, Килька, Сельдь, Треска, Форель, Осётр, Лещ.
- **Рыба холодного копчения (5):** Сёмга, Форель, Скумбрия, Палтус, Сельдь.
- **Электростатическое (6):** Скумбрия, Салака, Килька, Масляная, Ставрида, Курица.
- **Сыры/прочее (5):** Сыр копчёный, Сыр колбасный, Сало, Масло, Орехи.

## 6. Расчёт БЖУ и себестоимости (через /calc endpoint)

### 6.1. Endpoint
```
GET /api/v1/recipes/{recipe_id}/calc                    # для current version
GET /api/v1/recipes/{recipe_id}/versions/{version_id}/calc  # для конкретной версии
```

### 6.2. Логика (services/recipe_calc.py)
- **compute_bju(ingredients)**: суммирует БЖУ ингредиентов и нормирует на 100 г.
- **compute_cost(ingredients)**: суммирует `price_per_kg * mass_kg`.
- **compute_yield(ingredients, program, brine_method)**: учитывает потери копчения + посола.

### 6.3. Дефолтные потери по типу копчения
| Тип | Потери, % |
|---|---|
| Горячее | 32 |
| Полугорячее | 25 |
| Холодное | 12 |
| Электро | 8 |
| Универсальное | 25 |

### 6.4. Доп. потери при посоле
| Метод | Потери, % |
|---|---|
| Сухой | 4 |
| Мокрый | 2 |
| Шприцевание | 1 |
| Комбинированный | 3 |
| Смешанный | 3 |

### 6.5. Пример вычисления
- Свинина 5 кг + Говядина 3 кг + Соль 0.15 кг = 8.15 кг сырья.
- Горячее копчение + сухой посол = 32% + 4% = 36% потерь.
- Готовый продукт: 8.15 × (1 − 0.36) = 5.216 кг.
- Себестоимость сырья: (5×420 + 3×560 + 0.15×15) / 8.15 = 464.08 BYN/кг.
- Себестоимость готового: 464.08 / (1 − 0.36) = 725.12 BYN/кг.

**Smoke-test пройден** (см. сессию 5, коммит `4cb8852`).

## 7. Версионирование

### 7.1. Создание новой версии
```
POST /api/v1/recipes/{recipe_id}/versions
{
  "parent_version_id": 1,         // ID предыдущей версии
  "program": [...],               // новая программа
  "brine": {...},
  "ingredients": [...],
  "yield_percent": 110,
  "losses_percent": -10,
  "notes": "Уменьшил t варки на 3°C",
  "gost": "ГОСТ Р 52196-2011"
}
```
- `version_number` авто-инкремент (1, 2, 3, ...).
- Новая версия создаётся в статусе `draft`.

### 7.2. Апрув (TODO — не реализован)
```
POST /api/v1/recipes/{id}/versions/{vid}/approve   # TODO
{ "comment": "OK, проверил в цехе" }
```
- Меняет `RecipeVersion.status` на `approved`.
- Устанавливает `Recipe.current_version_id = vid`.
- Старая current → `archived` (TODO автоматический переход).

### 7.3. Diff (TODO)
```
GET /api/v1/recipes/{id}/diff?v1=2&v2=3   # TODO
→ {"changed_fields": ["program[0].t_chamber", "ingredients[+1]", "notes"],
   "old": {...}, "new": {...}}
```

## 8. Чек-лист перед сохранением

- [ ] Название корректное, slug уникален и `^[a-z0-9-]+$`.
- [ ] Категория из справочника.
- [ ] Ингредиенты — из `seed/ingredients` (если нет — создать).
- [ ] Программа — все фазы заполнены (duration_min > 0, t_chamber разумная).
- [ ] Выход/потери указаны.
- [ ] Источник указан (`source`).
- [ ] `verified: false` (до проверки технологом).
- [ ] JSON валиден, загружается через seed.
- [ ] БЖУ и себестоимость рассчитаны и сохранены в `bju_per_100g` и `cost_per_kg`.
- [ ] `notes` содержит контрольные точки (t в центре, время посола, и т.д.).

## 9. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `recipe-calc` — для расчёта БЖУ/себестоимости (services/recipe_calc.py).
- `seed-data` — для сидирования новых рецептов.
- `research-competitor` — для парсинга рецептов из каталогов конкурентов.
- `batches-lifecycle` — для запуска партии по рецепту.

---

**Версия:** 0.2.0 (2026-06-02)
**Загружай:** при создании/редактировании рецепта.
