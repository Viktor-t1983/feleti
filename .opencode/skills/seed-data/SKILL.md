# SKILL: seed-data

> Сидирование начальных данных в БД. Используй при первоначальной настройке, добавлении каталога или миграции данных.

## 1. Структура seed-данных

```
data/seed/
├── manufacturers.json          # 9 производителей
├── chambers/                   # камеры по slug
│   ├── ijiza-varmen-1.json
│   ├── ijiza-utr-250.json
│   ├── mauting-tunnel-4.json
│   ├── fessmann-t1900.json
│   ├── kerres-kk-2800.json
│   ├── agros-universal-200.json
│   ├── reich-thermo-150.json
│   ├── vemag-cooker-300.json
│   ├── vsd-tec-z115.json
│   └── feleti-smok-profi-250.json
├── products/                   # продукты (изделия)
│   ├── doktorskaya-kolbasa.json
│   ├── molochnaya-kolbasa.json
│   ├── skumbriya-gk.json
│   └── ...
├── ingredients/                # ингредиенты + щёпа
│   ├── govyadina-1s.json
│   ├── sviniya-pzh.json
│   ├── shpiк.json
│   ├── sol-pischevaya.json
│   ├── nitritnaya-sol.json
│   ├── schepa-olha.json
│   ├── schepa-buk.json
│   ├── schepa-dub.json
│   ├── schepa-yablonya.json
│   └── ...
├── recipes/                    # рецепты (50+)
│   ├── doktorskaya-gost.json
│   ├── molochnaya-gost.json
│   ├── skumbriya-gk.json
│   ├── semga-hk.json
│   ├── skumbriya-elektro.json
│   └── ...
├── brines/                     # типовые посолы
│   ├── suhoy-dlya-okoroka.json
│   ├── mokryy-dlya-ryby.json
│   └── ...
├── knowledge/                  # статьи базы знаний
│   ├── vidy-kopcheniya.md
│   ├── drevesina-dlya-kopcheniya.md
│   ├── elektrostaticheskoe-kopchenie.md
│   ├── reshenie-problem.md
│   ├── gost-kolbasy.md
│   └── ...
└── users.json                  # demo-пользователи
```

## 2. Алгоритм сидирования

### 2.1. Через Python-скрипт
`backend/app/scripts/seed.py`:

```python
import asyncio
import json
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session_maker
from app.models.manufacturer import Manufacturer
from app.models.chamber import Chamber
# ...

SEED_DIR = Path(__file__).parent.parent.parent / "data" / "seed"

async def seed_manufacturers(session: AsyncSession):
    data = json.loads((SEED_DIR / "manufacturers.json").read_text(encoding="utf-8"))
    for item in data:
        m = Manufacturer(**item)
        session.add(m)
    await session.commit()

async def seed_chambers(session: AsyncSession):
    for file in (SEED_DIR / "chambers").glob("*.json"):
        item = json.loads(file.read_text(encoding="utf-8"))
        # Resolve manufacturer_id by name
        result = await session.execute(
            select(Manufacturer).where(Manufacturer.name == item.pop("manufacturer"))
        )
        manufacturer = result.scalar_one()
        c = Chamber(manufacturer_id=manufacturer.id, **item)
        session.add(c)
    await session.commit()

async def main():
    async with async_session_maker() as session:
        await seed_manufacturers(session)
        await seed_chambers(session)
        # await seed_products(session)
        # await seed_ingredients(session)
        # await seed_recipes(session)
        # await seed_users(session)
    print("✅ Seed complete")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2. Через Alembic (data migration)
```python
# alembic/versions/xxxx_seed_initial_data.py
def upgrade():
    op.bulk_insert(manufacturers_table, [...])
    op.bulk_insert(chambers_table, [...])
    # ...

def downgrade():
    op.execute("DELETE FROM chambers")
    op.execute("DELETE FROM manufacturers")
```

## 3. Производители (9 штук)

```json
[
  { "name": "Ижица", "country": "Россия", "city": "Ижевск", "website": "https://ijiza.ru", "founded": 2000, "description": "Ведущий российский производитель коптильных камер. Электростатическое копчение." },
  { "name": "FELETI-SMOK", "country": "Беларусь", "city": "Брест", "website": "https://feleti.by", "founded": 2026, "description": "Собственное производство FELETI. Profi/Industrial B2B. Kinco + свой модуль." },
  { "name": "Mauting", "country": "Чехия", "city": "Брно", "website": "https://mauting.com", "founded": 1954, "description": "Премиум-туннели для крупных производств." },
  { "name": "Fessmann", "country": "Германия", "city": "Вайнгартен", "website": "https://fessmann.com", "founded": 1922, "description": "Премиум-камеры с FES.APP mobile и Turbomat." },
  { "name": "Kerres", "country": "Германия", "city": "Бёблинген", "website": "https://kerres.de", "founded": 1965, "description": "Jet Smoke, Hybrid Airflow. Премиум-сегмент." },
  { "name": "AGROS", "country": "Словения", "city": "Любляна", "website": "https://agros.si", "founded": 1985, "description": "Средний сегмент. Хорошее соотношение цена/качество." },
  { "name": "Reich", "country": "Германия", "city": "Зинсхайм", "website": "https://reich-thermoprozesstechnik.de", "founded": 1970, "description": "Термокамеры среднего сегмента." },
  { "name": "Vemag", "country": "Германия", "city": "Баден-Баден", "website": "https://vemag.de", "founded": 1948, "description": "Наполнители + термокамеры." },
  { "name": "VSD TEC", "country": "Казахстан", "city": "Алматы", "website": "https://vsd-tec.kz", "founded": 2005, "description": "Бюджетный сегмент. Термокамеры + дымогенераторы." }
]
```

## 4. Камеры (10+ моделей)

Минимум по одной от каждого производителя. Полный список — в `data/seed/chambers/`.

## 5. Продукты (30+)

```json
[
  { "name": "Докторская (колбаса)", "category": "колбаса вареная" },
  { "name": "Молочная (колбаса)", "category": "колбаса вареная" },
  { "name": "Краковская (колбаса)", "category": "колбаса полукопченая" },
  { "name": "Сервелат", "category": "колбаса полукопченая" },
  { "name": "Суджук", "category": "колбаса сырокопченая" },
  { "name": "Салями", "category": "колбаса сырокопченая" },
  { "name": "Буженина", "category": "мясо" },
  { "name": "Карбонад", "category": "мясо" },
  { "name": "Грудинка", "category": "мясо" },
  { "name": "Балык", "category": "мясо" },
  { "name": "Курица копченая", "category": "птица" },
  { "name": "Утка копченая", "category": "птица" },
  { "name": "Индейка копченая", "category": "птица" },
  { "name": "Скумбрия г/к", "category": "рыба горячего копчения" },
  { "name": "Салака г/к", "category": "рыба горячего копчения" },
  { "name": "Килька г/к", "category": "рыба горячего копчения" },
  { "name": "Сельдь г/к", "category": "рыба горячего копчения" },
  { "name": "Треска г/к", "category": "рыба горячего копчения" },
  { "name": "Форель г/к", "category": "рыба горячего копчения" },
  { "name": "Осётр г/к", "category": "рыба горячего копчения" },
  { "name": "Сёмга х/к", "category": "рыба холодного копчения" },
  { "name": "Форель х/к", "category": "рыба холодного копчения" },
  { "name": "Палтус х/к", "category": "рыба холодного копчения" },
  { "name": "Скумбрия электро", "category": "рыба электростатического копчения" },
  { "name": "Салака электро", "category": "рыба электростатического копчения" },
  { "name": "Килька электро", "category": "рыба электростатического копчения" },
  { "name": "Масляная электро", "category": "рыба электростатического копчения" },
  { "name": "Сыр копченый", "category": "сыр" },
  { "name": "Сыр колбасный копченый", "category": "сыр" },
  { "name": "Сало копченое", "category": "прочее" },
  { "name": "Масло сливочное копченое", "category": "прочее" },
  { "name": "Орехи копченые", "category": "прочее" }
]
```

## 6. Ингредиенты (30+)

```json
[
  { "name": "Говядина 1 сорт", "type": "мясо", "protein_per_100g": 18.0, "fat_per_100g": 12.0, "carbs_per_100g": 0, "kcal_per_100g": 180, "price_per_kg": 600 },
  { "name": "Свинина полужирная", "type": "мясо", "protein_per_100g": 16.0, "fat_per_100g": 21.0, "carbs_per_100g": 0, "kcal_per_100g": 250, "price_per_kg": 350 },
  { "name": "Шпик боковой", "type": "мясо", "protein_per_100g": 2.0, "fat_per_100g": 90.0, "carbs_per_100g": 0, "kcal_per_100g": 820, "price_per_kg": 250 },
  { "name": "Соль поваренная", "type": "соль", "protein_per_100g": 0, "fat_per_100g": 0, "carbs_per_100g": 0, "kcal_per_100g": 0, "price_per_kg": 30 },
  { "name": "Нитритная соль", "type": "соль", "protein_per_100g": 0, "fat_per_100g": 0, "carbs_per_100g": 0, "kcal_per_100g": 0, "price_per_kg": 80 },
  { "name": "Сахар-песок", "type": "специя", "protein_per_100g": 0, "fat_per_100g": 0, "carbs_per_100g": 100, "kcal_per_100g": 400, "price_per_kg": 80 },
  { "name": "Молоко сухое", "type": "прочее", "protein_per_100g": 26, "fat_per_100g": 25, "carbs_per_100g": 38, "kcal_per_100g": 470, "price_per_kg": 350 },
  { "name": "Яйца куриные", "type": "прочее", "protein_per_100g": 13, "fat_per_100g": 11, "carbs_per_100g": 1, "kcal_per_100g": 160, "price_per_kg": 200 },
  { "name": "Мускатный орех", "type": "специя", "protein_per_100g": 6, "fat_per_100g": 36, "carbs_per_100g": 49, "kcal_per_100g": 530, "price_per_kg": 4500 },
  { "name": "Чеснок", "type": "специя", "protein_per_100g": 7, "fat_per_100g": 0, "carbs_per_100g": 30, "kcal_per_100g": 150, "price_per_kg": 300 },
  { "name": "Перец чёрный молотый", "type": "специя", "protein_per_100g": 10, "fat_per_100g": 3, "carbs_per_100g": 64, "kcal_per_100g": 250, "price_per_kg": 2000 },
  { "name": "Тмин", "type": "специя", "protein_per_100g": 18, "fat_per_100g": 22, "carbs_per_100g": 33, "kcal_per_100g": 380, "price_per_kg": 1800 },
  { "name": "Кориандр", "type": "специя", "protein_per_100g": 12, "fat_per_100g": 18, "carbs_per_100g": 55, "kcal_per_100g": 300, "price_per_kg": 1200 },
  { "name": "Вода/лёд", "type": "прочее", "protein_per_100g": 0, "fat_per_100g": 0, "carbs_per_100g": 0, "kcal_per_100g": 0, "price_per_kg": 0 },
  { "name": "Щёпа ольхи", "type": "щёпа", "wood_species": "ольха", "form": "щепа", "fraction_mm": "4-8", "price_per_kg": 50 },
  { "name": "Щёпа бука", "type": "щёпа", "wood_species": "бук", "form": "щепа", "fraction_mm": "4-8", "price_per_kg": 55 },
  { "name": "Щёпа дуба", "type": "щёпа", "wood_species": "дуб", "form": "щепа", "fraction_mm": "4-8", "price_per_kg": 60 },
  { "name": "Щёпа яблони", "type": "щёпа", "wood_species": "яблоня", "form": "щепа", "fraction_mm": "4-8", "price_per_kg": 70 },
  { "name": "Щёпа вишни", "type": "щёпа", "wood_species": "вишня", "form": "щепа", "fraction_mm": "4-8", "price_per_kg": 80 },
  { "name": "Опилки ольхи", "type": "щёпа", "wood_species": "ольха", "form": "опилки", "fraction_mm": "2-4", "price_per_kg": 40 },
  { "name": "Стружка ольхи", "type": "щёпа", "wood_species": "ольха", "form": "стружка", "fraction_mm": "8-15", "price_per_kg": 45 }
]
```

## 7. Рецепты (50+)

Подробный план — `docs/RECIPES_BASE.md`. Каждый рецепт — отдельный JSON.

## 8. Demo-пользователи

```json
[
  { "email": "admin@feleti.by", "full_name": "Администратор", "role": "admin", "password": "Admin123!" },
  { "email": "tech@feleti.by", "full_name": "Технолог Иванов", "role": "technologist", "password": "Tech123!" },
  { "email": "operator@feleti.by", "full_name": "Оператор Петров", "role": "operator", "password": "Op123!" },
  { "email": "manager@feleti.by", "full_name": "Менеджер Сидорова", "role": "manager", "password": "Man123!" }
]
```

## 9. Запуск сидирования

```bash
# Локально
cd backend && uv run python -m app.scripts.seed

# В Docker
docker compose exec backend python -m app.scripts.seed
```

## 10. Идемпотентность

- Перед вставкой — `SELECT` по `slug` / `name`.
- Если уже есть — `UPDATE` (опц.) или `SKIP`.
- Идемпотентные миграции — можно запускать много раз.

```python
async def upsert_manufacturer(session, item):
    result = await session.execute(
        select(Manufacturer).where(Manufacturer.name == item["name"])
    )
    m = result.scalar_one_or_none()
    if m:
        return m  # skip
    m = Manufacturer(**item)
    session.add(m)
    await session.flush()
    return m
```

## 11. Чек-лист

- [ ] Все JSON валидны.
- [ ] Все slug'и уникальны в пределах таблицы.
- [ ] Все ссылки на другие сущности корректны (manufacturer_id, ingredient_id).
- [ ] `verified: false` для всех камер/рецептов (до проверки).
- [ ] Источники указаны.
- [ ] Изображения загружены в MinIO (если есть).
- [ ] Demo-пароли — сброшены при первом prod-деплое.
- [ ] Идемпотентность (можно запускать повторно).

## 12. Связь с другими скиллами

- `smoke-platform` — общие правила.
- `add-recipe` — для рецептов.
- `add-chamber` — для камер.

---

**Версия:** 0.1.0
**Загружай:** при первоначальной настройке БД, добавлении каталога или миграции.
