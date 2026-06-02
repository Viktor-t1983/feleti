# SKILL: add-recipe

> Создание и редактирование рецепта копчения. Используй при добавлении нового рецепта в базу или редактировании существующего.

## 1. Структура рецепта

```python
Recipe:
  - id: int
  - product_id: int
  - name: str                        # "Докторская ГОСТ"
  - slug: str                        # "doktorskaya-gost"
  - current_version_id: int
  - status: enum[draft|pending|approved|archived]
  - created_by, created_at

RecipeVersion (иммутабельный):
  - id, recipe_id, version_number, parent_version_id
  - program: list[ProgramPhase]      # фазы копчения
  - brine: BrineRecipe               # посол
  - ingredients: list[RecipeIngredient]  # с весами
  - yield_percent, losses_percent
  - notes: str
  - verified: bool                   # проверен технологом
  - verified_by, verified_at
  - created_by, created_at

ProgramPhase:
  - index, name (Подсушка/Копчение/Варка/Охлаждение)
  - duration_min
  - target_t_chamber, target_t_product
  - humidity_percent
  - smoke: none|light|medium|heavy
  - wood_species: ольха|бук|дуб|яблоня|вишня|...
  - wood_form: щепа|опилки|стружка
  - electro_voltage_kv: float        # 0 = выкл
  - electro_current_ua: float
  - fan_speed_percent: int
  - transition: time|product_temp|delta_t

BrineRecipe:
  - method: сухой|мокрый|шприцевание|комби
  - salt_percent, sugar_percent
  - nitrite_ppm, nitrate_ppm
  - spices: list[str]
  - duration_hours, temp_c
  - notes

RecipeIngredient:
  - ingredient_id, weight_g, percent, note
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
1. **Найти `product_id`** — если продукта нет, создать в `seed/products.json`.
2. **Создать `Recipe`** со статусом `draft`.
3. **Создать `RecipeVersion v1`** с полной программой.
4. **Привязать** `Recipe.current_version_id = v1.id`.
5. **Запустить** `services/recipe_calc.py` для расчёта БЖУ и себестоимости.
6. **Сохранить** в seed `data/seed/recipes/<slug>.json`.

### 2.3. Шаблон JSON (для seed)
```json
{
  "name": "Докторская ГОСТ",
  "slug": "doktorskaya-gost",
  "category": "колбаса вареная",
  "product": "Докторская (колбаса)",
  "yield_percent": 108,
  "losses_percent": -8,
  "source": "ГОСТ Р 52196-2011",
  "verified": false,
  "ingredients": [
    { "name": "Говядина 1с", "percent": 25, "note": "в фарш" },
    { "name": "Свинина п/ж", "percent": 35 },
    { "name": "Шпик", "percent": 15 },
    { "name": "Молоко сухое", "percent": 2 },
    { "name": "Яйца", "percent": 2 },
    { "name": "Соль", "percent": 2.5 },
    { "name": "Нитритная соль", "percent": 0.5 },
    { "name": "Сахар", "percent": 0.2 },
    { "name": "Мускатный орех", "percent": 0.05 },
    { "name": "Вода/лёд", "percent": 17.75 }
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

## 6. Расчёт БЖУ и себестоимости

```python
def calc_bju(ingredients: list[RecipeIngredient]) -> dict:
    """Вернёт {protein, fat, carbs, kcal} на 100г."""
    total_weight = sum(i.weight_g for i in ingredients)
    protein = sum(i.weight_g * i.ingredient.protein_per_100g for i in ingredients) / total_weight * 100
    fat     = sum(i.weight_g * i.ingredient.fat_per_100g     for i in ingredients) / total_weight * 100
    carbs   = sum(i.weight_g * i.ingredient.carbs_per_100g   for i in ingredients) / total_weight * 100
    kcal    = protein * 4 + fat * 9 + carbs * 4
    return {"protein": protein, "fat": fat, "carbs": carbs, "kcal": kcal}

def calc_cost(ingredients, yield_percent) -> Decimal:
    cost = sum(i.weight_g * i.ingredient.price_per_kg / 1000 for i in ingredients)
    return cost / (yield_percent / 100)
```

## 7. Версионирование

Создание новой версии:
1. Открыть `Recipe` (любой статус).
2. Создать `RecipeVersion` со статусом `draft`, `parent_version_id = current_version.id`, `version_number = current.version_number + 1`.
3. Отредактировать поля.
4. `submit_for_approval` → status: `pending`.
5. Апрув (admin/старший технолог) → status: `approved`, `Recipe.current_version_id = new.id`.
6. Старая версия → `archived` (опционально).

Diff:
```python
GET /api/v1/recipes/{id}/diff?v1=2&v2=3
→ {"changed_fields": ["program[0].t_chamber", "ingredients[+1]", "notes"], "old": {...}, "new": {...}}
```

## 8. Чек-лист перед сохранением

- [ ] Название корректное, slug уникален.
- [ ] Категория из справочника.
- [ ] Ингредиенты — из `data/seed/ingredients.json` (если нет — создать).
- [ ] Программа — все фазы заполнены (duration_min > 0, t_chamber разумная).
- [ ] Выход/потери указаны.
- [ ] Источник указан (`source`).
- [ ] `verified: false` (до проверки технологом).
- [ ] JSON валиден, загружается через `RecipeVersion.from_json()`.
- [ ] БЖУ и себестоимость рассчитаны и сохранены в `bju_per_100g` и `cost_per_kg`.
- [ ] `notes` содержит контрольные точки (t в центре, время посола, и т.д.).

## 9. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `seed-data` — для сидирования новых рецептов.
- `research-competitor` — для парсинга рецептов из каталогов конкурентов.

---

**Версия:** 0.1.0
**Загружай:** при создании/редактировании рецепта.
