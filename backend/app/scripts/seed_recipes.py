"""Сид рецептов: 80+ рецептов из docs/RECIPES_BASE.md.

Запуск: `docker compose exec backend python -m app.scripts.seed_recipes`
Идемпотентен — повторный запуск не дублирует (по slug).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.ingredient import Ingredient, IngredientType
from app.models.product import Product, ProductCategory
from app.models.recipe import Recipe, RecipeStatus, RecipeVersion
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


PRODUCTS_DATA: list[dict[str, Any]] = [
    # Колбасы варёные
    {"slug": "doktorskaya", "name": "Докторская колбаса", "category": ProductCategory.SAUSAGE_BOILD, "gost": "ГОСТ Р 52196-2011", "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6, "storage_humidity_min": 75, "storage_humidity_max": 80},
    {"slug": "molochnaya", "name": "Молочная колбаса", "category": ProductCategory.SAUSAGE_BOILD, "gost": "ГОСТ Р 52196-2011", "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "russkaya", "name": "Русская колбаса", "category": ProductCategory.SAUSAGE_BOILD, "gost": "ГОСТ Р 52196-2011", "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "lyubitelskaya", "name": "Любительская колбаса", "category": ProductCategory.SAUSAGE_BOILD, "gost": "ГОСТ Р 52196-2011", "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "chainaya", "name": "Чайная колбаса", "category": ProductCategory.SAUSAGE_SEMI_SMOKED, "gost": "ГОСТ 31785-2012", "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    # Колбасы полукопчёные
    {"slug": "krakovskaya", "name": "Краковская колбаса", "category": ProductCategory.SAUSAGE_SEMI_SMOKED, "gost": "ГОСТ 31785-2012", "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "odesskaya", "name": "Одесская колбаса", "category": ProductCategory.SAUSAGE_SEMI_SMOKED, "gost": "ГОСТ 31785-2012", "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "servelat", "name": "Сервелат", "category": ProductCategory.SAUSAGE_SEMI_SMOKED, "gost": "ГОСТ 31785-2012", "shelf_life_days": 15, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "tallinskaya", "name": "Таллиннская колбаса", "category": ProductCategory.SAUSAGE_SEMI_SMOKED, "gost": "ГОСТ 31785-2012", "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "polskaya", "name": "Польская колбаса", "category": ProductCategory.SAUSAGE_SEMI_SMOKED, "gost": "ГОСТ 31785-2012", "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    # Колбасы сырокопчёные
    {"slug": "sudzhuk", "name": "Суджук домашний", "category": ProductCategory.SAUSAGE_RAW_SMOKED, "gost": "ГОСТ 16131-86", "shelf_life_days": 30, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "salyami-moskovskaya", "name": "Салями Московская", "category": ProductCategory.SAUSAGE_RAW_SMOKED, "gost": "ГОСТ 16131-86", "shelf_life_days": 45, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "braunshveigskaya", "name": "Брауншвейгская колбаса", "category": ProductCategory.SAUSAGE_RAW_SMOKED, "gost": "ГОСТ 16131-86", "shelf_life_days": 30, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "servelat-elitny", "name": "Сервелат Элитный", "category": ProductCategory.SAUSAGE_RAW_SMOKED, "gost": "ГОСТ 16131-86", "shelf_life_days": 45, "storage_temp_min": 2, "storage_temp_max": 6},
    # Мясо
    {"slug": "buzhenina", "name": "Буженина копчёная", "category": ProductCategory.MEAT, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "karbonad", "name": "Карбонад копчёный", "category": ProductCategory.MEAT, "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "grudinka", "name": "Грудинка копчёная", "category": ProductCategory.MEAT, "shelf_life_days": 14, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "balyk-svinoy", "name": "Балык свиной", "category": ProductCategory.MEAT, "shelf_life_days": 20, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "rostbif", "name": "Ростбиф копчёный", "category": ProductCategory.MEAT, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "yazik-govyazhiy", "name": "Язык говяжий копчёный", "category": ProductCategory.MEAT, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "koreyka", "name": "Корейка копчёная", "category": ProductCategory.MEAT, "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    # Птица
    {"slug": "kuritsa-tselaya", "name": "Курица копчёная целиком", "category": ProductCategory.POULTRY, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "utka", "name": "Утка копчёная", "category": ProductCategory.POULTRY, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "indeyka", "name": "Грудинка индейки копчёная", "category": ProductCategory.POULTRY, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "krylushki", "name": "Крылышки куриные копчёные", "category": ProductCategory.POULTRY, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "perepelka", "name": "Перепёлка копчёная", "category": ProductCategory.POULTRY, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    # Рыба горячего копчения
    {"slug": "skumbria-gk", "name": "Скумбрия горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "salaka-gk", "name": "Салака горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "kilka-gk", "name": "Килька горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "seld-gk", "name": "Сельдь горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "treska-gk", "name": "Треска горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "forel-gk", "name": "Форель горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "osetr-gk", "name": "Осётр горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "leshch-gk", "name": "Лещ горячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
    # Рыба холодного копчения
    {"slug": "semga-hk", "name": "Сёмга холодного копчения", "category": ProductCategory.FISH_COLD, "shelf_life_days": 10, "storage_temp_min": 0, "storage_temp_max": 4},
    {"slug": "forel-hk", "name": "Форель холодного копчения", "category": ProductCategory.FISH_COLD, "shelf_life_days": 10, "storage_temp_min": 0, "storage_temp_max": 4},
    {"slug": "skumbria-hk", "name": "Скумбрия холодного копчения", "category": ProductCategory.FISH_COLD, "shelf_life_days": 10, "storage_temp_min": 0, "storage_temp_max": 4},
    {"slug": "paltus-hk", "name": "Палтус холодного копчения", "category": ProductCategory.FISH_COLD, "shelf_life_days": 10, "storage_temp_min": 0, "storage_temp_max": 4},
    {"slug": "seld-hk", "name": "Сельдь холодного копчения", "category": ProductCategory.FISH_COLD, "shelf_life_days": 10, "storage_temp_min": 0, "storage_temp_max": 4},
    # Электростатическое
    {"slug": "skumbria-elektro", "name": "Скумбрия электростатического копчения", "category": ProductCategory.FISH_ELECTRO, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "salaka-elektro", "name": "Салака электростатического копчения", "category": ProductCategory.FISH_ELECTRO, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "kilka-elektro", "name": "Килька электростатического копчения", "category": ProductCategory.FISH_ELECTRO, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "maslyanaya-elektro", "name": "Масляная рыба электростатического копчения", "category": ProductCategory.FISH_ELECTRO, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "stavrida-elektro", "name": "Ставрида электростатического копчения", "category": ProductCategory.FISH_ELECTRO, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "kuritsa-file-elektro", "name": "Куриное филе электростатического копчения", "category": ProductCategory.POULTRY, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    # Сыры и прочее
    {"slug": "syr-kopcheniy", "name": "Сыр копчёный полутвёрдый", "category": ProductCategory.CHEESE, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "syr-kolbasniy", "name": "Сыр колбасный копчёный", "category": ProductCategory.CHEESE, "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "salo-gk", "name": "Сало копчёное г/к", "category": ProductCategory.BACON, "shelf_life_days": 14, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "maslo-slivochnoe", "name": "Сливочное масло копчёное", "category": ProductCategory.BUTTER, "shelf_life_days": 10, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "orekhi", "name": "Орехи копчёные", "category": ProductCategory.SNACKS, "shelf_life_days": 30, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "chesnok", "name": "Чеснок копчёный", "category": ProductCategory.OTHER, "shelf_life_days": 30, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "perets", "name": "Перец копчёный", "category": ProductCategory.OTHER, "shelf_life_days": 60, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "sol-kopchenaya", "name": "Соль копчёная", "category": ProductCategory.OTHER, "shelf_life_days": 365, "storage_temp_min": 2, "storage_temp_max": 25},
    # Полугорячее
    {"slug": "seld-pg", "name": "Сельдь полугорячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "skumbria-pg", "name": "Скумбрия полугорячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "treska-pg", "name": "Треска полугорячего копчения", "category": ProductCategory.FISH_HOT, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "kuritsa-file-pg", "name": "Куриное филе полугорячего копчения", "category": ProductCategory.POULTRY, "shelf_life_days": 5, "storage_temp_min": 2, "storage_temp_max": 6},
    {"slug": "svinina-koreyka-pg", "name": "Свиная корейка полугорячего копчения", "category": ProductCategory.MEAT, "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
]

INGREDIENTS_DATA: list[dict[str, Any]] = [
    # Мясо
    {"slug": "govyadina-1s", "name": "Говядина 1 сорта", "type": IngredientType.MEAT, "protein_per_100g": 19.0, "fat_per_100g": 12.0, "kcal_per_100g": 187, "price_per_kg": 850},
    {"slug": "govyadina-vs", "name": "Говядина высшего сорта", "type": IngredientType.MEAT, "protein_per_100g": 20.0, "fat_per_100g": 10.0, "kcal_per_100g": 170, "price_per_kg": 950},
    {"slug": "svinina-poluzhirn", "name": "Свинина полужирная", "type": IngredientType.MEAT, "protein_per_100g": 16.0, "fat_per_100g": 27.0, "kcal_per_100g": 305, "price_per_kg": 650},
    {"slug": "svinina-nezhirn", "name": "Свинина нежирная", "type": IngredientType.MEAT, "protein_per_100g": 19.0, "fat_per_100g": 14.0, "kcal_per_100g": 210, "price_per_kg": 700},
    {"slug": "shpik-bokovoy", "name": "Шпик боковой", "type": IngredientType.MEAT, "protein_per_100g": 2.0, "fat_per_100g": 85.0, "kcal_per_100g": 770, "price_per_kg": 400},
    {"slug": "shpik-hrebtoviy", "name": "Шпик хребтовый", "type": IngredientType.MEAT, "protein_per_100g": 2.0, "fat_per_100g": 90.0, "kcal_per_100g": 810, "price_per_kg": 380},
    {"slug": "svinaya-sheya", "name": "Свиная шея", "type": IngredientType.MEAT, "protein_per_100g": 17.0, "fat_per_100g": 22.0, "kcal_per_100g": 270, "price_per_kg": 750},
    {"slug": "svinoy-karbonad", "name": "Свиной карбонад", "type": IngredientType.MEAT, "protein_per_100g": 18.0, "fat_per_100g": 15.0, "kcal_per_100g": 210, "price_per_kg": 800},
    {"slug": "govyazhiy-yazik", "name": "Говяжий язык", "type": IngredientType.MEAT, "protein_per_100g": 16.0, "fat_per_100g": 16.0, "kcal_per_100g": 210, "price_per_kg": 1200},
    {"slug": "govyadina-dlya-rostbifa", "name": "Говядина для ростбифа (толстый край)", "type": IngredientType.MEAT, "protein_per_100g": 20.0, "fat_per_100g": 8.0, "kcal_per_100g": 155, "price_per_kg": 1100},
    {"slug": "grudinka-svinaya", "name": "Грудинка свиная", "type": IngredientType.MEAT, "protein_per_100g": 10.0, "fat_per_100g": 50.0, "kcal_per_100g": 500, "price_per_kg": 550},
    # Птица
    {"slug": "kuritsa-tselaya-1", "name": "Курица целая (1.5-2 кг)", "type": IngredientType.MEAT, "protein_per_100g": 18.0, "fat_per_100g": 14.0, "kcal_per_100g": 200, "price_per_kg": 350},
    {"slug": "kurinoe-file", "name": "Куриное филе", "type": IngredientType.MEAT, "protein_per_100g": 23.0, "fat_per_100g": 2.0, "kcal_per_100g": 110, "price_per_kg": 450},
    {"slug": "krylo-kurinoe", "name": "Куриное крыло", "type": IngredientType.MEAT, "protein_per_100g": 18.0, "fat_per_100g": 15.0, "kcal_per_100g": 210, "price_per_kg": 280},
    {"slug": "utka-tselaya", "name": "Утка целая (2-2.5 кг)", "type": IngredientType.MEAT, "protein_per_100g": 16.0, "fat_per_100g": 28.0, "kcal_per_100g": 320, "price_per_kg": 500},
    {"slug": "indeyka-file", "name": "Индейка филе грудки", "type": IngredientType.MEAT, "protein_per_100g": 24.0, "fat_per_100g": 1.0, "kcal_per_100g": 110, "price_per_kg": 600},
    {"slug": "perepelka", "name": "Перепёлка (150-200 г)", "type": IngredientType.MEAT, "protein_per_100g": 19.0, "fat_per_100g": 12.0, "kcal_per_100g": 185, "price_per_kg": 700},
    # Рыба
    {"slug": "skumbriya", "name": "Скумбрия", "type": IngredientType.MEAT, "protein_per_100g": 18.0, "fat_per_100g": 12.0, "kcal_per_100g": 190, "price_per_kg": 400},
    {"slug": "salaka", "name": "Салака", "type": IngredientType.MEAT, "protein_per_100g": 16.0, "fat_per_100g": 5.0, "kcal_per_100g": 110, "price_per_kg": 250},
    {"slug": "kilka", "name": "Килька", "type": IngredientType.MEAT, "protein_per_100g": 17.0, "fat_per_100g": 8.0, "kcal_per_100g": 140, "price_per_kg": 200},
    {"slug": "seld", "name": "Сельдь", "type": IngredientType.MEAT, "protein_per_100g": 17.0, "fat_per_100g": 12.0, "kcal_per_100g": 180, "price_per_kg": 300},
    {"slug": "treska", "name": "Треска", "type": IngredientType.MEAT, "protein_per_100g": 18.0, "fat_per_100g": 1.0, "kcal_per_100g": 80, "price_per_kg": 550},
    {"slug": "forel", "name": "Форель", "type": IngredientType.MEAT, "protein_per_100g": 19.0, "fat_per_100g": 12.0, "kcal_per_100g": 190, "price_per_kg": 900},
    {"slug": "osetr", "name": "Осётр", "type": IngredientType.MEAT, "protein_per_100g": 17.0, "fat_per_100g": 10.0, "kcal_per_100g": 160, "price_per_kg": 1500},
    {"slug": "leshch", "name": "Лещ", "type": IngredientType.MEAT, "protein_per_100g": 17.0, "fat_per_100g": 4.0, "kcal_per_100g": 105, "price_per_kg": 280},
    {"slug": "maslyanaya", "name": "Масляная рыба", "type": IngredientType.MEAT, "protein_per_100g": 18.0, "fat_per_100g": 8.0, "kcal_per_100g": 150, "price_per_kg": 650},
    {"slug": "stavrida", "name": "Ставрида", "type": IngredientType.MEAT, "protein_per_100g": 19.0, "fat_per_100g": 6.0, "kcal_per_100g": 130, "price_per_kg": 350},
    {"slug": "paltus", "name": "Палтус", "type": IngredientType.MEAT, "protein_per_100g": 18.0, "fat_per_100g": 15.0, "kcal_per_100g": 210, "price_per_kg": 850},
    {"slug": "semga", "name": "Сёмга", "type": IngredientType.MEAT, "protein_per_100g": 20.0, "fat_per_100g": 13.0, "kcal_per_100g": 200, "price_per_kg": 1200},
    # Соль/специи
    {"slug": "sol-povarennaya", "name": "Соль поваренная", "type": IngredientType.SALT, "price_per_kg": 25},
    {"slug": "nitritnaya-sol", "name": "Нитритная соль", "type": IngredientType.ADDITIVE, "price_per_kg": 350},
    {"slug": "sahar", "name": "Сахар", "type": IngredientType.SALT, "price_per_kg": 50},
    {"slug": "perec-cherniy-molotiy", "name": "Перец чёрный молотый", "type": IngredientType.SPICE, "price_per_kg": 600},
    {"slug": "perec-dushistiy", "name": "Перец душистый", "type": IngredientType.SPICE, "price_per_kg": 800},
    {"slug": "chesnok-svegiy", "name": "Чеснок свежий", "type": IngredientType.SPICE, "price_per_kg": 200},
    {"slug": "muskatniy-oreh", "name": "Мускатный орех", "type": IngredientType.SPICE, "price_per_kg": 3000},
    {"slug": "kardamon", "name": "Кардамон", "type": IngredientType.SPICE, "price_per_kg": 4000},
    {"slug": "koriandr", "name": "Кориандр", "type": IngredientType.SPICE, "price_per_kg": 500},
    {"slug": "tmin", "name": "Тмин", "type": IngredientType.SPICE, "price_per_kg": 400},
    {"slug": "paprika", "name": "Паприка", "type": IngredientType.SPICE, "price_per_kg": 450},
    {"slug": "imbir", "name": "Имбирь", "type": IngredientType.SPICE, "price_per_kg": 700},
    {"slug": "gvozdika", "name": "Гвоздика", "type": IngredientType.SPICE, "price_per_kg": 2500},
    # Молочные и яйца
    {"slug": "moloko-suhoe", "name": "Молоко сухое", "type": IngredientType.OTHER, "protein_per_100g": 26.0, "fat_per_100g": 26.0, "kcal_per_100g": 370, "price_per_kg": 400},
    {"slug": "yaytsa", "name": "Яйца куриные", "type": IngredientType.OTHER, "protein_per_100g": 13.0, "fat_per_100g": 11.0, "kcal_per_100g": 155, "price_per_kg": 150, "unit": "шт"},
    {"slug": "syr-polutverdy", "name": "Сыр полутвёрдый (Российский)", "type": IngredientType.OTHER, "protein_per_100g": 24.0, "fat_per_100g": 30.0, "kcal_per_100g": 360, "price_per_kg": 700},
    {"slug": "syr-kolbasniy-plavleniy", "name": "Сыр колбасный плавленый", "type": IngredientType.OTHER, "protein_per_100g": 21.0, "fat_per_100g": 25.0, "kcal_per_100g": 320, "price_per_kg": 500},
    {"slug": "maslo-slivochnoe-1", "name": "Масло сливочное", "type": IngredientType.OTHER, "protein_per_100g": 1.0, "fat_per_100g": 82.0, "kcal_per_100g": 740, "price_per_kg": 900},
    {"slug": "salo-svine", "name": "Сало свиное", "type": IngredientType.MEAT, "protein_per_100g": 2.0, "fat_per_100g": 90.0, "kcal_per_100g": 810, "price_per_kg": 300},
    # Орехи и прочее
    {"slug": "mindal", "name": "Миндаль", "type": IngredientType.OTHER, "protein_per_100g": 21.0, "fat_per_100g": 50.0, "kcal_per_100g": 580, "price_per_kg": 1200},
    {"slug": "keshyu", "name": "Кешью", "type": IngredientType.OTHER, "protein_per_100g": 18.0, "fat_per_100g": 44.0, "kcal_per_100g": 550, "price_per_kg": 1400},
    {"slug": "chesnok-golovki", "name": "Чеснок (головки)", "type": IngredientType.OTHER, "price_per_kg": 250},
    {"slug": "perets-svegiy-struchkovy", "name": "Перец свежий стручковый", "type": IngredientType.OTHER, "price_per_kg": 300},
    # Щепа
    {"slug": "sheel-olkha", "name": "Щепа ольхи", "type": IngredientType.WOOD, "wood_species": "ольха", "wood_form": "щепа", "fraction_mm": "4-8", "price_per_kg": 180, "unit": "кг"},
    {"slug": "sheel-buk", "name": "Щепа бука", "type": IngredientType.WOOD, "wood_species": "бук", "wood_form": "щепа", "fraction_mm": "4-8", "price_per_kg": 200, "unit": "кг"},
    {"slug": "sheel-dub", "name": "Щепа дуба", "type": IngredientType.WOOD, "wood_species": "дуб", "wood_form": "щепа", "fraction_mm": "4-8", "price_per_kg": 220, "unit": "кг"},
    {"slug": "sheel-yablonya", "name": "Щепа яблони", "type": IngredientType.WOOD, "wood_species": "яблоня", "wood_form": "щепа", "fraction_mm": "4-8", "price_per_kg": 300, "unit": "кг"},
    {"slug": "sheel-vishnya", "name": "Щепа вишни", "type": IngredientType.WOOD, "wood_species": "вишня", "wood_form": "щепа", "fraction_mm": "4-8", "price_per_kg": 320, "unit": "кг"},
    {"slug": "voda-led", "name": "Вода/лёд", "type": IngredientType.OTHER, "price_per_kg": 0.1, "unit": "л"},
]

RECIPES_DATA: list[dict[str, Any]] = [
    # === КОЛБАСЫ ВАРЁНЫЕ ===
    {
        "slug": "doktorskaya-gost", "product_slug": "doktorskaya", "name": "Докторская ГОСТ",
        "description": "Классическая варёная колбаса по ГОСТ Р 52196-2011",
        "tags": ["колбаса", "вареная", "гос", "классика"],
        "yield_percent": 108, "losses_percent": -8,
        "gost": "ГОСТ Р 52196-2011", "source": "ГОСТ Р 52196-2011",
        "program": [
            {"name": "Подсушка", "duration_min": 30, "t_chamber": 50, "humidity": 30, "smoke": "none", "fan_speed_percent": 60},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 75, "humidity": 50, "smoke": "medium", "wood_species": "ольха", "fan_speed_percent": 70},
            {"name": "Варка", "duration_min": 60, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72, "fan_speed_percent": 50},
            {"name": "Охлаждение душем", "duration_min": 15, "t_chamber": 18, "humidity": 100, "smoke": "none", "fan_speed_percent": 80},
            {"name": "Подсушка", "duration_min": 30, "t_chamber": 22, "humidity": 60, "smoke": "none", "fan_speed_percent": 60},
        ],
        "ingredients": [
            {"name": "Говядина 1с", "percent": 25, "note": "в фарш"},
            {"name": "Свинина п/ж", "percent": 35, "note": "в фарш"},
            {"name": "Шпик боковой", "percent": 15, "note": "в фарш"},
            {"name": "Молоко сухое", "percent": 2},
            {"name": "Яйца", "percent": 2},
            {"name": "Соль", "percent": 2.5},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Сахар", "percent": 0.2},
            {"name": "Мускатный орех", "percent": 0.05},
            {"name": "Вода/лёд", "percent": 17.75},
        ],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 0},
        "notes": "Контроль: t в центре батона ≥ +72°C. Цвет: светло-розовый.",
    },
    {
        "slug": "molochnaya-gost", "product_slug": "molochnaya", "name": "Молочная ГОСТ",
        "description": "Варёная колбаса с молочным вкусом",
        "tags": ["колбаса", "вареная", "гос", "молочная"],
        "yield_percent": 108, "losses_percent": -8,
        "gost": "ГОСТ Р 52196-2011",
        "program": [
            {"name": "Подсушка", "duration_min": 30, "t_chamber": 50, "humidity": 30, "smoke": "none"},
            {"name": "Копчение", "duration_min": 45, "t_chamber": 75, "humidity": 50, "smoke": "light", "wood_species": "ольха"},
            {"name": "Варка", "duration_min": 60, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72},
            {"name": "Охлаждение", "duration_min": 30, "t_chamber": 18, "humidity": 80, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Говядина в/с", "percent": 30, "note": "в фарш"},
            {"name": "Свинина п/ж", "percent": 30, "note": "в фарш"},
            {"name": "Молоко сухое", "percent": 5},
            {"name": "Яйца", "percent": 2},
            {"name": "Соль", "percent": 2.5},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Сахар", "percent": 0.2},
            {"name": "Вода/лёд", "percent": 29.8},
        ],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 0},
        "notes": "Нежный молочный вкус. Контроль: t ≥ +72°C.",
    },
    {
        "slug": "russkaya-gost", "product_slug": "russkaya", "name": "Русская ГОСТ",
        "description": "Варёная колбаса с чесноком и дымком",
        "tags": ["колбаса", "вареная", "гос", "чеснок"],
        "yield_percent": 107, "losses_percent": -7,
        "gost": "ГОСТ Р 52196-2011",
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 55, "humidity": 30, "smoke": "none"},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 75, "humidity": 50, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Варка", "duration_min": 55, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72},
            {"name": "Охлаждение", "duration_min": 30, "t_chamber": 18, "humidity": 80, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Говядина 1с", "percent": 40, "note": "в фарш"},
            {"name": "Свинина п/ж", "percent": 25, "note": "в фарш"},
            {"name": "Шпик боковой", "percent": 10, "note": "кубики 6 мм"},
            {"name": "Чеснок свежий", "percent": 0.5},
            {"name": "Соль", "percent": 2.5},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Перец чёрный", "percent": 0.1},
            {"name": "Вода/лёд", "percent": 21.4},
        ],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 0},
    },
    {
        "slug": "lyubitelskaya-gost", "product_slug": "lyubitelskaya", "name": "Любительская ГОСТ",
        "description": "Нежная варёная колбаса высшего сорта",
        "tags": ["колбаса", "вареная", "гос", "нежная"],
        "yield_percent": 108, "losses_percent": -8,
        "gost": "ГОСТ Р 52196-2011",
        "program": [
            {"name": "Подсушка", "duration_min": 25, "t_chamber": 50, "humidity": 30, "smoke": "none"},
            {"name": "Копчение", "duration_min": 50, "t_chamber": 75, "humidity": 50, "smoke": "light", "wood_species": "ольха"},
            {"name": "Варка", "duration_min": 65, "t_chamber": 77, "humidity": 90, "smoke": "none", "t_product_target": 72},
            {"name": "Охлаждение", "duration_min": 30, "t_chamber": 18, "humidity": 80, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Говядина в/с", "percent": 35, "note": "в фарш"},
            {"name": "Свинина н/ж", "percent": 30, "note": "в фарш"},
            {"name": "Молоко сухое", "percent": 3},
            {"name": "Яйца", "percent": 2},
            {"name": "Соль", "percent": 2.5},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Мускатный орех", "percent": 0.05},
            {"name": "Вода/лёд", "percent": 26.95},
        ],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 0},
    },
    {
        "slug": "chainaya-polukopchenaya", "product_slug": "chainaya", "name": "Чайная п/к",
        "description": "Полукопчёная колбаса с характерным чайным оттенком",
        "tags": ["колбаса", "полукопченая", "классика"],
        "yield_percent": 85, "losses_percent": 15,
        "gost": "ГОСТ 31785-2012",
        "program": [
            {"name": "Подсушка", "duration_min": 30, "t_chamber": 55, "humidity": 25, "smoke": "none"},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 75, "humidity": 45, "smoke": "medium", "wood_species": "бук"},
            {"name": "Варка", "duration_min": 40, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72},
            {"name": "Охлаждение", "duration_min": 20, "t_chamber": 18, "humidity": 80, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Говядина 1с", "percent": 30},
            {"name": "Свинина п/ж", "percent": 30},
            {"name": "Шпик боковой", "percent": 15},
            {"name": "Соль", "percent": 3},
            {"name": "Чеснок свежий", "percent": 0.3},
            {"name": "Перец чёрный", "percent": 0.1},
            {"name": "Вода/лёд", "percent": 21.6},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.0, "duration_hours": 0},
    },
    # === КОЛБАСЫ ПОЛУКОПЧЁНЫЕ ===
    {
        "slug": "krakovskaya-polukopchenaya", "product_slug": "krakovskaya", "name": "Краковская п/к",
        "description": "Полукопчёная колбаса по ГОСТ 31785-2012",
        "tags": ["колбаса", "полукопченая", "гос"],
        "yield_percent": 80, "losses_percent": 20,
        "gost": "ГОСТ 31785-2012",
        "program": [
            {"name": "Подсушка", "duration_min": 30, "t_chamber": 60, "humidity": 25, "smoke": "none"},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "бук"},
            {"name": "Варка", "duration_min": 40, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72},
            {"name": "Охлаждение", "duration_min": 30, "t_chamber": 18, "humidity": 60, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Говядина 1с", "percent": 40},
            {"name": "Свинина п/ж", "percent": 20},
            {"name": "Шпик боковой", "percent": 15},
            {"name": "Чеснок свежий", "percent": 0.3},
            {"name": "Соль", "percent": 3},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Перец чёрный", "percent": 0.1},
            {"name": "Вода/лёд", "percent": 21.1},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.0},
    },
    {
        "slug": "odesskaya-polukopchenaya", "product_slug": "odesskaya", "name": "Одесская п/к",
        "description": "Пикантная полукопчёная колбаса",
        "tags": ["колбаса", "полукопченая", "пикантная"],
        "yield_percent": 82, "losses_percent": 18,
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 60, "humidity": 25, "smoke": "none"},
            {"name": "Копчение", "duration_min": 50, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "бук"},
            {"name": "Варка", "duration_min": 45, "t_chamber": 78, "humidity": 85, "smoke": "none", "t_product_target": 72},
            {"name": "Сушка", "duration_min": 60, "t_chamber": 30, "humidity": 35, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Свинина п/ж", "percent": 50},
            {"name": "Говядина 1с", "percent": 20},
            {"name": "Шпик боковой", "percent": 10},
            {"name": "Чеснок свежий", "percent": 0.5},
            {"name": "Перец чёрный", "percent": 0.2},
            {"name": "Кориандр", "percent": 0.3},
            {"name": "Соль", "percent": 3},
            {"name": "Вода/лёд", "percent": 16.0},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.0},
    },
    {
        "slug": "servelat-polukopcheniy", "product_slug": "servelat", "name": "Сервелат п/к",
        "description": "Полукопчёный сервелат крупного помола",
        "tags": ["колбаса", "полукопченая", "сервелат", "крупный помол"],
        "yield_percent": 78, "losses_percent": 22,
        "program": [
            {"name": "Подсушка", "duration_min": 30, "t_chamber": 55, "humidity": 25, "smoke": "none"},
            {"name": "Копчение", "duration_min": 90, "t_chamber": 75, "humidity": 40, "smoke": "medium", "wood_species": "бук"},
            {"name": "Варка", "duration_min": 40, "t_chamber": 76, "humidity": 90, "smoke": "none", "t_product_target": 70},
            {"name": "Сушка", "duration_min": 120, "t_chamber": 25, "humidity": 40, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Свинина н/ж", "percent": 45},
            {"name": "Говядина 1с", "percent": 20},
            {"name": "Шпик хребтовый", "percent": 15},
            {"name": "Соль", "percent": 3},
            {"name": "Перец чёрный", "percent": 0.2},
            {"name": "Мускатный орех", "percent": 0.1},
            {"name": "Вода/лёд", "percent": 16.7},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.0},
    },
    {
        "slug": "tallinskaya-polukopchenaya", "product_slug": "tallinskaya", "name": "Таллиннская п/к",
        "description": "Полукопчёная колбаса с пряным вкусом",
        "tags": ["колбаса", "полукопченая", "пряная"],
        "yield_percent": 80, "losses_percent": 20,
        "program": [
            {"name": "Подсушка", "duration_min": 25, "t_chamber": 55, "humidity": 25, "smoke": "none"},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 75, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Варка", "duration_min": 45, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72},
            {"name": "Сушка", "duration_min": 60, "t_chamber": 28, "humidity": 40, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Говядина 1с", "percent": 35},
            {"name": "Свинина п/ж", "percent": 25},
            {"name": "Шпик боковой", "percent": 15},
            {"name": "Чеснок свежий", "percent": 0.3},
            {"name": "Тмин", "percent": 0.2},
            {"name": "Соль", "percent": 3},
            {"name": "Перец чёрный", "percent": 0.1},
            {"name": "Вода/лёд", "percent": 21.4},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.0},
    },
    {
        "slug": "polskaya-polukopchenaya", "product_slug": "polskaya", "name": "Польская п/к",
        "description": "Польская полукопчёная колбаса с чесноком",
        "tags": ["колбаса", "полукопченая", "польская"],
        "yield_percent": 80, "losses_percent": 20,
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 60, "humidity": 25},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "бук"},
            {"name": "Варка", "duration_min": 40, "t_chamber": 78, "humidity": 90, "smoke": "none", "t_product_target": 72},
            {"name": "Сушка", "duration_min": 60, "t_chamber": 30, "humidity": 35},
        ],
        "ingredients": [
            {"name": "Свинина п/ж", "percent": 55},
            {"name": "Говядина 1с", "percent": 15},
            {"name": "Чеснок свежий", "percent": 0.5},
            {"name": "Перец чёрный", "percent": 0.2},
            {"name": "Соль", "percent": 2.5},
            {"name": "Вода/лёд", "percent": 26.8},
        ],
        "brine": {"method": "сухой", "salt_percent": 2.5},
    },
    # === КОЛБАСЫ СЫРОКОПЧЁНЫЕ ===
    {
        "slug": "sudzhuk-domashniy", "product_slug": "sudzhuk", "name": "Суджук домашний",
        "description": "Домашний суджук — сырокопчёная колбаса с тмином и чесноком",
        "tags": ["колбаса", "сырокопченая", "суджук", "домашний"],
        "yield_percent": 65, "losses_percent": 35,
        "gost": "ГОСТ 16131-86",
        "program": [
            {"name": "Ферментация", "duration_min": 1440, "t_chamber": 22, "humidity": 75, "smoke": "none", "fan_speed_percent": 20},
            {"name": "Подсушка", "duration_min": 120, "t_chamber": 25, "humidity": 50, "smoke": "none"},
            {"name": "Копчение", "duration_min": 720, "t_chamber": 22, "humidity": 55, "smoke": "light", "wood_species": "дуб", "fan_speed_percent": 40},
            {"name": "Сушка", "duration_min": 2880, "t_chamber": 18, "humidity": 45, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Говядина 1с", "percent": 50},
            {"name": "Свинина п/ж", "percent": 30},
            {"name": "Шпик боковой", "percent": 10},
            {"name": "Чеснок свежий", "percent": 0.8},
            {"name": "Тмин", "percent": 0.2},
            {"name": "Соль", "percent": 3},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Перец чёрный", "percent": 0.3},
            {"name": "Вода", "percent": 5.2},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.5, "duration_hours": 24},
        "notes": "Ферментация 24 ч при +22°C. Созревание 3-5 сут.",
    },
    {
        "slug": "salyami-moskovskaya", "product_slug": "salyami-moskovskaya", "name": "Салями Московская",
        "description": "Сырокопчёная салями с характерным рисунком фарша",
        "tags": ["колбаса", "сырокопченая", "салями"],
        "yield_percent": 60, "losses_percent": 40,
        "gost": "ГОСТ 16131-86",
        "program": [
            {"name": "Ферментация", "duration_min": 2880, "t_chamber": 20, "humidity": 78, "smoke": "none"},
            {"name": "Подсушка", "duration_min": 180, "t_chamber": 22, "humidity": 55, "smoke": "none"},
            {"name": "Копчение", "duration_min": 1440, "t_chamber": 20, "humidity": 55, "smoke": "medium", "wood_species": "бук"},
            {"name": "Сушка", "duration_min": 4320, "t_chamber": 15, "humidity": 40, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Свинина п/ж", "percent": 50},
            {"name": "Говядина 1с", "percent": 20},
            {"name": "Шпик хребтовый", "percent": 15},
            {"name": "Соль", "percent": 3},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Перец чёрный", "percent": 0.2},
            {"name": "Коньяк", "percent": 0.5},
            {"name": "Вода", "percent": 10.8},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.5, "duration_hours": 48},
        "notes": "Созревание 45 сут. Дым: бук или дуб.",
    },
    {
        "slug": "braunshveigskaya-syrokopchenaya", "product_slug": "braunshveigskaya", "name": "Брауншвейгская с/к",
        "description": "Сырокопчёная колбаса с острым вкусом",
        "tags": ["колбаса", "сырокопченая", "брауншвейгская"],
        "yield_percent": 62, "losses_percent": 38,
        "gost": "ГОСТ 16131-86",
        "program": [
            {"name": "Ферментация", "duration_min": 1440, "t_chamber": 22, "humidity": 75},
            {"name": "Копчение", "duration_min": 2880, "t_chamber": 20, "humidity": 55, "smoke": "medium", "wood_species": "дуб"},
            {"name": "Сушка", "duration_min": 4320, "t_chamber": 14, "humidity": 40},
        ],
        "ingredients": [
            {"name": "Говядина 1с", "percent": 40},
            {"name": "Свинина п/ж", "percent": 25},
            {"name": "Шпик боковой", "percent": 15},
            {"name": "Соль", "percent": 3},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Перец чёрный", "percent": 0.3},
            {"name": "Мускатный орех", "percent": 0.1},
            {"name": "Вода", "percent": 16.1},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.5},
    },
    {
        "slug": "servelat-elitniy-syrokopcheniy", "product_slug": "servelat-elitny", "name": "Сервелат Элитный с/к",
        "description": "Сырокопчёный сервелат длительного созревания",
        "tags": ["колбаса", "сырокопченая", "сервелат", "элитный"],
        "yield_percent": 58, "losses_percent": 42,
        "program": [
            {"name": "Ферментация", "duration_min": 2880, "t_chamber": 20, "humidity": 78, "smoke": "none"},
            {"name": "Подсушка", "duration_min": 240, "t_chamber": 20, "humidity": 55, "smoke": "none"},
            {"name": "Копчение", "duration_min": 2880, "t_chamber": 18, "humidity": 50, "smoke": "medium", "wood_species": "дуб"},
            {"name": "Сушка", "duration_min": 5760, "t_chamber": 12, "humidity": 35, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Свинина н/ж", "percent": 45},
            {"name": "Говядина в/с", "percent": 20},
            {"name": "Шпик хребтовый", "percent": 15},
            {"name": "Соль", "percent": 3},
            {"name": "Нитритная соль", "percent": 0.5},
            {"name": "Коньяк", "percent": 0.3},
            {"name": "Мускатный орех", "percent": 0.1},
            {"name": "Вода", "percent": 16.1},
        ],
        "brine": {"method": "сухой", "salt_percent": 3.5, "duration_hours": 48},
        "notes": "Длительное созревание до 60 сут. Дым: дуб.",
    },
    # === РЫБА ГОРЯЧЕГО КОПЧЕНИЯ ===
    {
        "slug": "skumbriya-gk", "product_slug": "skumbria-gk", "name": "Скумбрия г/к",
        "description": "Классическая скумбрия горячего копчения",
        "tags": ["рыба", "горячее копчение", "скумбрия", "классика"],
        "yield_percent": 92, "losses_percent": 8,
        "gost": "ГОСТ 7447-2015",
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 50, "humidity": 35, "smoke": "none"},
            {"name": "Копчение", "duration_min": 80, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "ольха", "t_product_target": 65},
            {"name": "Охлаждение", "duration_min": 20, "t_chamber": 18, "humidity": 70, "smoke": "none"},
        ],
        "ingredients": [
            {"name": "Скумбрия", "percent": 100},
            {"name": "Соль", "percent": 3},
        ],
        "brine": {"method": "тузлучный", "salt_percent": 15, "duration_hours": 4, "temp_c": 5, "notes": "Плотность тузлука 1.17"},
        "notes": "Оптимальная загрузка: 70 кг. Цель: золотистый цвет.",
    },
    {
        "slug": "salaka-gk", "product_slug": "salaka-gk", "name": "Салака г/к",
        "description": "Мелкая рыба горячего копчения",
        "tags": ["рыба", "горячее копчение", "салака"],
        "yield_percent": 90, "losses_percent": 10,
        "program": [
            {"name": "Подсушка", "duration_min": 15, "t_chamber": 50, "humidity": 35},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 15, "t_chamber": 18, "humidity": 70},
        ],
        "ingredients": [{"name": "Салака", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "тузлучный", "salt_percent": 12, "duration_hours": 2, "temp_c": 5},
    },
    {
        "slug": "kilka-gk", "product_slug": "kilka-gk", "name": "Килька г/к",
        "description": "Килька горячего копчения",
        "tags": ["рыба", "горячее копчение", "килька"],
        "yield_percent": 88, "losses_percent": 12,
        "program": [
            {"name": "Подсушка", "duration_min": 10, "t_chamber": 50, "humidity": 35},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 10, "t_chamber": 18, "humidity": 70},
        ],
        "ingredients": [{"name": "Килька", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "сухой", "salt_percent": 3, "duration_hours": 2},
    },
    {
        "slug": "seld-gk", "product_slug": "seld-gk", "name": "Сельдь г/к",
        "description": "Сельдь горячего копчения",
        "tags": ["рыба", "горячее копчение", "сельдь"],
        "yield_percent": 90, "losses_percent": 10,
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 50, "humidity": 35},
            {"name": "Копчение", "duration_min": 75, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 20, "t_chamber": 18, "humidity": 70},
        ],
        "ingredients": [{"name": "Сельдь", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "тузлучный", "salt_percent": 15, "duration_hours": 4},
    },
    {
        "slug": "treska-gk", "product_slug": "treska-gk", "name": "Треска г/к",
        "description": "Треска горячего копчения",
        "tags": ["рыба", "горячее копчение", "треска"],
        "yield_percent": 93, "losses_percent": 7,
        "program": [
            {"name": "Подсушка", "duration_min": 15, "t_chamber": 55, "humidity": 35},
            {"name": "Копчение", "duration_min": 50, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 20, "t_chamber": 18},
        ],
        "ingredients": [{"name": "Треска", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "тузлучный", "salt_percent": 12, "duration_hours": 3},
    },
    {
        "slug": "forel-gk", "product_slug": "forel-gk", "name": "Форель г/к",
        "description": "Деликатесная форель горячего копчения",
        "tags": ["рыба", "горячее копчение", "форель", "деликатес"],
        "yield_percent": 95, "losses_percent": 5,
        "program": [
            {"name": "Подсушка", "duration_min": 15, "t_chamber": 50, "humidity": 35},
            {"name": "Копчение", "duration_min": 40, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "ольха+яблоня"},
            {"name": "Охлаждение", "duration_min": 20, "t_chamber": 18},
        ],
        "ingredients": [{"name": "Форель", "percent": 100}, {"name": "Соль", "percent": 2.5}],
        "brine": {"method": "тузлучный", "salt_percent": 10, "duration_hours": 3},
        "notes": "Щепа ольха+яблоня 50/50 для нежного аромата.",
    },
    {
        "slug": "osetr-gk", "product_slug": "osetr-gk", "name": "Осётр г/к",
        "description": "Царская рыба горячего копчения",
        "tags": ["рыба", "горячее копчение", "осётр", "деликатес"],
        "yield_percent": 93, "losses_percent": 7,
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 50, "humidity": 35},
            {"name": "Копчение", "duration_min": 75, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "бук"},
            {"name": "Охлаждение", "duration_min": 30, "t_chamber": 18},
        ],
        "ingredients": [{"name": "Осётр", "percent": 100}, {"name": "Соль", "percent": 2.5}],
        "brine": {"method": "тузлучный", "salt_percent": 10, "duration_hours": 4},
    },
    {
        "slug": "leshch-gk", "product_slug": "leshch-gk", "name": "Лещ г/к",
        "description": "Лещ горячего копчения",
        "tags": ["рыба", "горячее копчение", "лещ"],
        "yield_percent": 90, "losses_percent": 10,
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 50, "humidity": 35},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 50, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 20, "t_chamber": 18},
        ],
        "ingredients": [{"name": "Лещ", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "тузлучный", "salt_percent": 15, "duration_hours": 4},
    },
    # === РЫБА ХОЛОДНОГО КОПЧЕНИЯ ===
    {
        "slug": "semga-hk", "product_slug": "semga-hk", "name": "Сёмга х/к",
        "description": "Сёмга холодного копчения, классический рецепт",
        "tags": ["рыба", "холодное копчение", "сёмга"],
        "yield_percent": 88, "losses_percent": 12,
        "gost": "ГОСТ 2623-2014",
        "program": [
            {"name": "Подсушка", "duration_min": 120, "t_chamber": 22, "humidity": 50, "smoke": "none"},
            {"name": "Копчение", "duration_min": 1440, "t_chamber": 22, "humidity": 55, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 60, "t_chamber": 4, "humidity": 80},
        ],
        "ingredients": [{"name": "Сёмга", "percent": 100}, {"name": "Соль", "percent": 4}],
        "brine": {"method": "смешанный", "salt_percent": 15, "duration_hours": 12, "temp_c": 5},
        "notes": "Посол 12 ч в тузлуке 1.17, затем подсушка 2 ч.",
    },
    {
        "slug": "forel-hk", "product_slug": "forel-hk", "name": "Форель х/к",
        "description": "Радужная форель холодного копчения",
        "tags": ["рыба", "холодное копчение", "форель"],
        "yield_percent": 90, "losses_percent": 10,
        "program": [
            {"name": "Подсушка", "duration_min": 90, "t_chamber": 22, "humidity": 50},
            {"name": "Копчение", "duration_min": 720, "t_chamber": 20, "humidity": 55, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 60, "t_chamber": 4},
        ],
        "ingredients": [{"name": "Форель", "percent": 100}, {"name": "Соль", "percent": 3.5}],
        "brine": {"method": "смешанный", "salt_percent": 12, "duration_hours": 8},
    },
    {
        "slug": "skumbria-hk", "product_slug": "skumbria-hk", "name": "Скумбрия х/к",
        "description": "Скумбрия холодного копчения",
        "tags": ["рыба", "холодное копчение", "скумбрия"],
        "yield_percent": 85, "losses_percent": 15,
        "program": [
            {"name": "Подсушка", "duration_min": 60, "t_chamber": 22, "humidity": 50},
            {"name": "Копчение", "duration_min": 1080, "t_chamber": 20, "humidity": 55, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 60, "t_chamber": 4},
        ],
        "ingredients": [{"name": "Скумбрия", "percent": 100}, {"name": "Соль", "percent": 4}],
        "brine": {"method": "смешанный", "salt_percent": 15, "duration_hours": 10},
    },
    {
        "slug": "paltus-hk", "product_slug": "paltus-hk", "name": "Палтус х/к",
        "description": "Палтус холодного копчения",
        "tags": ["рыба", "холодное копчение", "палтус"],
        "yield_percent": 88, "losses_percent": 12,
        "program": [
            {"name": "Подсушка", "duration_min": 90, "t_chamber": 22, "humidity": 50},
            {"name": "Копчение", "duration_min": 960, "t_chamber": 20, "humidity": 55, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 60, "t_chamber": 4},
        ],
        "ingredients": [{"name": "Палтус", "percent": 100}, {"name": "Соль", "percent": 3.5}],
        "brine": {"method": "смешанный", "salt_percent": 12, "duration_hours": 10},
    },
    {
        "slug": "seld-hk", "product_slug": "seld-hk", "name": "Сельдь х/к",
        "description": "Сельдь холодного копчения",
        "tags": ["рыба", "холодное копчение", "сельдь"],
        "yield_percent": 85, "losses_percent": 15,
        "program": [
            {"name": "Подсушка", "duration_min": 60, "t_chamber": 22, "humidity": 50},
            {"name": "Копчение", "duration_min": 720, "t_chamber": 20, "humidity": 55, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Охлаждение", "duration_min": 60, "t_chamber": 4},
        ],
        "ingredients": [{"name": "Сельдь", "percent": 100}, {"name": "Соль", "percent": 4}],
        "brine": {"method": "смешанный", "salt_percent": 15, "duration_hours": 8},
    },
    # === ЭЛЕКТРОСТАТИЧЕСКОЕ ===
    {
        "slug": "skumbriya-elektro", "product_slug": "skumbria-elektro", "name": "Скумбрия электро",
        "description": "Скумбрия электростатического копчения (Ижица-стиль)",
        "tags": ["рыба", "электро", "скумбрия", "быстро"],
        "yield_percent": 98, "losses_percent": 2,
        "program": [
            {"name": "Копчение электро", "duration_min": 90, "t_chamber": 25, "humidity": 50, "smoke": "medium", "wood_species": "ольха", "electro_voltage_kv": 20},
        ],
        "ingredients": [{"name": "Скумбрия", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "тузлучный", "salt_percent": 15, "duration_hours": 4},
        "notes": "Электростатика 20 кВ. Загрузка 80 кг. Время 90 мин.",
    },
    {
        "slug": "salaka-elektro", "product_slug": "salaka-elektro", "name": "Салака электро",
        "description": "Салака электростатического копчения",
        "tags": ["рыба", "электро", "салака"],
        "yield_percent": 98, "losses_percent": 2,
        "program": [
            {"name": "Копчение электро", "duration_min": 90, "t_chamber": 25, "humidity": 50, "smoke": "medium", "wood_species": "ольха", "electro_voltage_kv": 20},
        ],
        "ingredients": [{"name": "Салака", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "тузлучный", "salt_percent": 12, "duration_hours": 2},
    },
    {
        "slug": "kilka-elektro", "product_slug": "kilka-elektro", "name": "Килька электро",
        "description": "Килька электростатического копчения",
        "tags": ["рыба", "электро", "килька"],
        "yield_percent": 98, "losses_percent": 2,
        "program": [
            {"name": "Копчение электро", "duration_min": 120, "t_chamber": 25, "humidity": 50, "smoke": "medium", "wood_species": "ольха", "electro_voltage_kv": 20},
        ],
        "ingredients": [{"name": "Килька", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "сухой", "salt_percent": 3, "duration_hours": 2},
    },
    {
        "slug": "maslyanaya-elektro", "product_slug": "maslyanaya-elektro", "name": "Масляная электро",
        "description": "Масляная рыба электростатического копчения",
        "tags": ["рыба", "электро", "масляная"],
        "yield_percent": 98, "losses_percent": 2,
        "program": [
            {"name": "Копчение электро", "duration_min": 40, "t_chamber": 25, "humidity": 50, "smoke": "medium", "wood_species": "ольха", "electro_voltage_kv": 20},
        ],
        "ingredients": [{"name": "Масляная рыба", "percent": 100}, {"name": "Соль", "percent": 2.5}],
        "brine": {"method": "тузлучный", "salt_percent": 10, "duration_hours": 4},
    },
    {
        "slug": "stavrida-elektro", "product_slug": "stavrida-elektro", "name": "Ставрида электро",
        "description": "Ставрида электростатического копчения",
        "tags": ["рыба", "электро", "ставрида"],
        "yield_percent": 98, "losses_percent": 2,
        "program": [
            {"name": "Копчение электро", "duration_min": 60, "t_chamber": 25, "humidity": 50, "smoke": "medium", "wood_species": "ольха", "electro_voltage_kv": 20},
        ],
        "ingredients": [{"name": "Ставрида", "percent": 100}, {"name": "Соль", "percent": 3}],
        "brine": {"method": "тузлучный", "salt_percent": 12, "duration_hours": 3},
    },
    {
        "slug": "kuritsa-file-elektro", "product_slug": "kuritsa-file-elektro", "name": "Куриное филе электро",
        "description": "Куриное филе электростатического копчения",
        "tags": ["птица", "электро", "курица", "филе"],
        "yield_percent": 96, "losses_percent": 4,
        "program": [
            {"name": "Копчение электро", "duration_min": 30, "t_chamber": 55, "humidity": 45, "smoke": "medium", "wood_species": "ольха+яблоня", "electro_voltage_kv": 20},
        ],
        "ingredients": [{"name": "Куриное филе", "percent": 100}, {"name": "Соль", "percent": 2}, {"name": "Перец чёрный", "percent": 0.2}],
        "brine": {"method": "сухой", "salt_percent": 2, "duration_hours": 2},
    },
    # === МЯСО ===
    {
        "slug": "buzhenina-kopchenaya", "product_slug": "buzhenina", "name": "Буженина копчёная",
        "description": "Свиная шея, запечённо-копчёная",
        "tags": ["мясо", "свинина", "буженина"],
        "yield_percent": 85, "losses_percent": 15,
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 90, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "ольха+яблоня"},
            {"name": "Запекание", "duration_min": 90, "t_chamber": 100, "humidity": 60, "smoke": "none", "t_product_target": 72},
        ],
        "ingredients": [{"name": "Свиная шея", "percent": 100}, {"name": "Соль", "percent": 2.5}, {"name": "Чеснок свежий", "percent": 0.5}, {"name": "Перец чёрный", "percent": 0.3}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 6},
    },
    {
        "slug": "karbonad-kopcheniy", "product_slug": "karbonad", "name": "Карбонад копчёный",
        "description": "Свиной карбонад горячего копчения",
        "tags": ["мясо", "свинина", "карбонад"],
        "yield_percent": 85, "losses_percent": 15,
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Запекание", "duration_min": 60, "t_chamber": 95, "humidity": 60, "smoke": "none", "t_product_target": 70},
        ],
        "ingredients": [{"name": "Свиной карбонад", "percent": 100}, {"name": "Соль", "percent": 2.5}, {"name": "Перец чёрный", "percent": 0.2}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 6},
    },
    {
        "slug": "grudinka-kopchenaya", "product_slug": "grudinka", "name": "Грудинка копчёная",
        "description": "Свиная грудинка горячего копчения",
        "tags": ["мясо", "свинина", "грудинка"],
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 90, "t_chamber": 75, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Запекание", "duration_min": 90, "t_chamber": 90, "humidity": 60, "smoke": "none", "t_product_target": 68},
        ],
        "ingredients": [{"name": "Грудинка свиная", "percent": 100}, {"name": "Соль", "percent": 3}, {"name": "Чеснок свежий", "percent": 0.8}, {"name": "Перец чёрный", "percent": 0.3}],
        "brine": {"method": "сухой", "salt_percent": 3, "duration_hours": 12},
        "yield_percent": 80, "losses_percent": 20,
    },
    {
        "slug": "balyk-svinoy-hk", "product_slug": "balyk-svinoy", "name": "Балык свиной х/к",
        "description": "Свиной балык холодного копчения",
        "tags": ["мясо", "свинина", "балык", "холодное копчение"],
        "program": [
            {"name": "Подсушка", "duration_min": 120, "t_chamber": 22, "humidity": 50},
            {"name": "Копчение", "duration_min": 1440, "t_chamber": 20, "humidity": 55, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Сушка", "duration_min": 720, "t_chamber": 18, "humidity": 45},
        ],
        "ingredients": [{"name": "Свиной карбонад", "percent": 100}, {"name": "Соль", "percent": 3.5}],
        "brine": {"method": "смешанный", "salt_percent": 15, "duration_hours": 12},
        "yield_percent": 75, "losses_percent": 25,
    },
    {
        "slug": "rostbif-kopcheniy", "product_slug": "rostbif", "name": "Ростбиф копчёный",
        "description": "Говяжий ростбиф горячего копчения",
        "tags": ["мясо", "говядина", "ростбиф"],
        "program": [
            {"name": "Подсушка", "duration_min": 15, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 45, "t_chamber": 75, "humidity": 45, "smoke": "medium", "wood_species": "дуб"},
            {"name": "Запекание", "duration_min": 45, "t_chamber": 90, "humidity": 60, "smoke": "none", "t_product_target": 55},
        ],
        "ingredients": [{"name": "Говядина для ростбифа", "percent": 100}, {"name": "Соль", "percent": 2.5}, {"name": "Перец чёрный", "percent": 0.3}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 4},
        "yield_percent": 80, "losses_percent": 20,
        "notes": "Стейк Medium Rare: t в центре +55°C. Отдых 10 мин.",
    },
    {
        "slug": "yazik-govyazhiy-kopcheniy", "product_slug": "yazik-govyazhiy", "name": "Язык говяжий копчёный",
        "description": "Говяжий язык горячего копчения",
        "tags": ["мясо", "говядина", "язык", "деликатес"],
        "program": [
            {"name": "Варка", "duration_min": 120, "t_chamber": 90, "humidity": 90, "smoke": "none", "t_product_target": 80},
            {"name": "Очистка", "duration_min": 10, "t_chamber": 20, "humidity": 50, "smoke": "none", "note": "очистка от кожицы"},
            {"name": "Подсушка", "duration_min": 15, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 40, "t_chamber": 75, "humidity": 50, "smoke": "medium", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Говяжий язык", "percent": 100}, {"name": "Соль", "percent": 2.5}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 4},
        "yield_percent": 60, "losses_percent": 40,
        "notes": "Язык предварительно отварить, очистить, затем коптить 40 мин.",
    },
    {
        "slug": "koreyka-kopchenaya", "product_slug": "koreyka", "name": "Корейка копчёная",
        "description": "Свиная корейка горячего копчения",
        "tags": ["мясо", "свинина", "корейка"],
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Запекание", "duration_min": 60, "t_chamber": 95, "humidity": 60, "smoke": "none", "t_product_target": 70},
        ],
        "ingredients": [{"name": "Свиной карбонад", "percent": 100}, {"name": "Соль", "percent": 2.5}, {"name": "Чеснок свежий", "percent": 0.5}, {"name": "Перец чёрный", "percent": 0.2}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 6},
        "yield_percent": 85, "losses_percent": 15,
    },
    # === ПТИЦА ===
    {
        "slug": "kuritsa-gk", "product_slug": "kuritsa-tselaya", "name": "Курица г/к целиком",
        "description": "Курица горячего копчения целиком",
        "tags": ["птица", "курица", "горячее копчение"],
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 60, "humidity": 30},
            {"name": "Копчение", "duration_min": 120, "t_chamber": 85, "humidity": 45, "smoke": "medium", "wood_species": "ольха+яблоня"},
            {"name": "Запекание", "duration_min": 60, "t_chamber": 95, "humidity": 60, "smoke": "none", "t_product_target": 75},
        ],
        "ingredients": [{"name": "Курица целая", "percent": 100}, {"name": "Соль", "percent": 2.5}, {"name": "Перец чёрный", "percent": 0.3}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 6},
        "yield_percent": 85, "losses_percent": 15,
    },
    {
        "slug": "utka-kopchenaya", "product_slug": "utka", "name": "Утка копчёная",
        "description": "Утка горячего копчения",
        "tags": ["птица", "утка", "горячее копчение"],
        "program": [
            {"name": "Подсушка", "duration_min": 30, "t_chamber": 60, "humidity": 30},
            {"name": "Копчение", "duration_min": 180, "t_chamber": 85, "humidity": 45, "smoke": "medium", "wood_species": "ольха+дуб"},
            {"name": "Запекание", "duration_min": 60, "t_chamber": 90, "humidity": 60, "smoke": "none", "t_product_target": 75},
        ],
        "ingredients": [{"name": "Утка целая", "percent": 100}, {"name": "Соль", "percent": 2.5}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 8},
        "yield_percent": 75, "losses_percent": 25,
        "notes": "Утка жирная — проколы кожи для выхода жира.",
    },
    {
        "slug": "indeyka-gk", "product_slug": "indeyka", "name": "Грудинка индейки г/к",
        "description": "Филе грудки индейки горячего копчения",
        "tags": ["птица", "индейка", "грудинка"],
        "program": [
            {"name": "Подсушка", "duration_min": 15, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},
            {"name": "Запекание", "duration_min": 30, "t_chamber": 85, "humidity": 60, "smoke": "none", "t_product_target": 72},
        ],
        "ingredients": [{"name": "Индейка филе грудки", "percent": 100}, {"name": "Соль", "percent": 2}],
        "brine": {"method": "сухой", "salt_percent": 2, "duration_hours": 4},
        "yield_percent": 85, "losses_percent": 15,
    },
    {
        "slug": "krylushki-kurinye-gk", "product_slug": "krylushki", "name": "Крылышки г/к",
        "description": "Куриные крылья горячего копчения",
        "tags": ["птица", "курица", "крылья"],
        "program": [
            {"name": "Подсушка", "duration_min": 10, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 60, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Куриное крыло", "percent": 100}, {"name": "Соль", "percent": 2.5}, {"name": "Перец чёрный", "percent": 0.2}, {"name": "Паприка", "percent": 0.5}],
        "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 2},
        "yield_percent": 85, "losses_percent": 15,
    },
    {
        "slug": "perepelka-gk", "product_slug": "perepelka", "name": "Перепёлка г/к",
        "description": "Перепёлка горячего копчения",
        "tags": ["птица", "перепёлка", "деликатес"],
        "program": [
            {"name": "Подсушка", "duration_min": 10, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 45, "t_chamber": 80, "humidity": 45, "smoke": "medium", "wood_species": "ольха+яблоня"},
            {"name": "Запекание", "duration_min": 30, "t_chamber": 85, "humidity": 60, "smoke": "none", "t_product_target": 72},
        ],
        "ingredients": [{"name": "Перепёлка", "percent": 100}, {"name": "Соль", "percent": 2}],
        "brine": {"method": "сухой", "salt_percent": 2, "duration_hours": 2},
        "yield_percent": 80, "losses_percent": 20,
    },
    # === СЫРЫ И ПРОЧЕЕ ===
    {
        "slug": "syr-kopcheniy-gk", "product_slug": "syr-kopcheniy", "name": "Сыр копчёный г/к",
        "description": "Полутвёрдый сыр горячего копчения",
        "tags": ["сыр", "горячее копчение"],
        "program": [
            {"name": "Копчение", "duration_min": 45, "t_chamber": 50, "humidity": 45, "smoke": "medium", "wood_species": "ольха+яблоня"},
        ],
        "ingredients": [{"name": "Сыр полутвёрдый", "percent": 100}],
        "yield_percent": 95, "losses_percent": 5,
        "notes": "Сыр предварительно охладить до +4°C. Коптить при +50°C, не выше.",
    },
    {
        "slug": "syr-kolbasniy-kopcheniy", "product_slug": "syr-kolbasniy", "name": "Сыр колбасный копчёный",
        "description": "Плавленый колбасный сыр копчёный",
        "tags": ["сыр", "колбасный", "плавленый"],
        "program": [
            {"name": "Копчение", "duration_min": 25, "t_chamber": 60, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Сыр колбасный плавленый", "percent": 100}],
        "yield_percent": 97, "losses_percent": 3,
    },
    {
        "slug": "salo-kopchenoe-gk", "product_slug": "salo-gk", "name": "Сало копчёное г/к",
        "description": "Сало горячего копчения с чесноком",
        "tags": ["сало", "горячее копчение", "чеснок"],
        "program": [
            {"name": "Подсушка", "duration_min": 20, "t_chamber": 55, "humidity": 30},
            {"name": "Копчение", "duration_min": 180, "t_chamber": 75, "humidity": 45, "smoke": "heavy", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Сало свиное", "percent": 100}, {"name": "Чеснок свежий", "percent": 1}, {"name": "Соль", "percent": 3}, {"name": "Перец чёрный", "percent": 0.3}],
        "brine": {"method": "сухой", "salt_percent": 3, "duration_hours": 12},
        "yield_percent": 80, "losses_percent": 20,
    },
    {
        "slug": "maslo-slivochnoe-kopchenoe", "product_slug": "maslo-slivochnoe", "name": "Масло сливочное копчёное",
        "description": "Сливочное масло холодного копчения",
        "tags": ["масло", "холодное копчение"],
        "program": [
            {"name": "Копчение", "duration_min": 30, "t_chamber": 18, "humidity": 50, "smoke": "light", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Масло сливочное", "percent": 100}],
        "yield_percent": 98, "losses_percent": 2,
        "notes": "Масло охладить до +4°C. Коптить 30 мин при +18°C.",
    },
    {
        "slug": "orekhi-kopchenie", "product_slug": "orekhi", "name": "Орехи копчёные",
        "description": "Миндаль и кешью горячего копчения",
        "tags": ["снеки", "орехи", "горячее копчение"],
        "program": [
            {"name": "Копчение", "duration_min": 30, "t_chamber": 60, "humidity": 30, "smoke": "light", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Миндаль", "percent": 50}, {"name": "Кешью", "percent": 50}],
        "yield_percent": 98, "losses_percent": 2,
    },
    {
        "slug": "chesnok-kopcheniy", "product_slug": "chesnok", "name": "Чеснок копчёный",
        "description": "Головки чеснока горячего копчения",
        "tags": ["чеснок", "горячее копчение", "ингредиент"],
        "program": [
            {"name": "Копчение", "duration_min": 60, "t_chamber": 60, "humidity": 40, "smoke": "medium", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Чеснок (головки)", "percent": 100}],
        "yield_percent": 90, "losses_percent": 10,
    },
    {
        "slug": "perets-kopcheniy", "product_slug": "perets", "name": "Перец копчёный",
        "description": "Стручковый перец горячего копчения",
        "tags": ["перец", "горячее копчение", "ингредиент"],
        "program": [
            {"name": "Копчение", "duration_min": 90, "t_chamber": 70, "humidity": 40, "smoke": "medium", "wood_species": "дуб"},
        ],
        "ingredients": [{"name": "Перец свежий стручковый", "percent": 100}],
        "yield_percent": 85, "losses_percent": 15,
    },
    {
        "slug": "sol-kopchenaya", "product_slug": "sol-kopchenaya", "name": "Соль копчёная",
        "description": "Соль холодного копчения (финский стиль)",
        "tags": ["соль", "холодное копчение", "финский стиль"],
        "program": [
            {"name": "Копчение", "duration_min": 300, "t_chamber": 40, "humidity": 30, "smoke": "heavy", "wood_species": "ольха"},
        ],
        "ingredients": [{"name": "Соль поваренная", "percent": 100}],
        "yield_percent": 100, "losses_percent": 0,
    },
]

# === ПОЛУГОРЯЧЕЕ === (добавим кратко)
POLUGORYACHEE: list[dict[str, Any]] = [
    {"slug": "seld-polugoryachee", "product_slug": "seld-pg", "name": "Сельдь п/г",
     "program": [{"name": "Подсушка", "duration_min": 10, "t_chamber": 50, "humidity": 35},{"name": "Копчение", "duration_min": 60, "t_chamber": 50, "humidity": 50, "smoke": "medium", "wood_species": "ольха"}],
     "ingredients": [{"name": "Сельдь", "percent": 100}, {"name": "Соль", "percent": 3}],
     "brine": {"method": "тузлучный", "salt_percent": 12, "duration_hours": 3},
     "yield_percent": 90, "losses_percent": 10},
    {"slug": "skumbriya-polugoryachee", "product_slug": "skumbria-pg", "name": "Скумбрия п/г",
     "program": [{"name": "Подсушка", "duration_min": 10, "t_chamber": 50, "humidity": 35},{"name": "Копчение", "duration_min": 60, "t_chamber": 55, "humidity": 50, "smoke": "medium", "wood_species": "ольха"}],
     "ingredients": [{"name": "Скумбрия", "percent": 100}, {"name": "Соль", "percent": 3}],
     "brine": {"method": "тузлучный", "salt_percent": 12, "duration_hours": 4},
     "yield_percent": 90, "losses_percent": 10},
    {"slug": "treska-polugoryachee", "product_slug": "treska-pg", "name": "Треска п/г",
     "program": [{"name": "Подсушка", "duration_min": 10, "t_chamber": 50, "humidity": 35},{"name": "Копчение", "duration_min": 45, "t_chamber": 50, "humidity": 50, "smoke": "medium", "wood_species": "ольха"}],
     "ingredients": [{"name": "Треска", "percent": 100}, {"name": "Соль", "percent": 3}],
     "brine": {"method": "тузлучный", "salt_percent": 10, "duration_hours": 3},
     "yield_percent": 92, "losses_percent": 8},
    {"slug": "kuritsa-file-polugoryachee", "product_slug": "kuritsa-file-pg", "name": "Куриное филе п/г",
     "program": [{"name": "Подсушка", "duration_min": 10, "t_chamber": 50, "humidity": 30},{"name": "Копчение", "duration_min": 90, "t_chamber": 60, "humidity": 45, "smoke": "medium", "wood_species": "ольха"}],
     "ingredients": [{"name": "Куриное филе", "percent": 100}, {"name": "Соль", "percent": 2}],
     "brine": {"method": "сухой", "salt_percent": 2, "duration_hours": 2},
     "yield_percent": 88, "losses_percent": 12},
    {"slug": "svinina-koreyka-polugoryachee", "product_slug": "svinina-koreyka-pg", "name": "Свиная корейка п/г",
     "program": [{"name": "Подсушка", "duration_min": 15, "t_chamber": 55, "humidity": 30},{"name": "Копчение", "duration_min": 120, "t_chamber": 65, "humidity": 45, "smoke": "medium", "wood_species": "ольха"},{"name": "Запекание", "duration_min": 60, "t_chamber": 85, "humidity": 60, "smoke": "none", "t_product_target": 65}],
     "ingredients": [{"name": "Свиной карбонад", "percent": 100}, {"name": "Соль", "percent": 2.5}],
     "brine": {"method": "сухой", "salt_percent": 2.5, "duration_hours": 6},
     "yield_percent": 85, "losses_percent": 15},
]

# === ОХЛАЖДЕНИЕ (простые режимы) ===
COOLING: list[dict[str, Any]] = [
    {"slug": "cooling-fish-gk", "product_slug": "skumbria-gk", "name": "Охлаждение рыбы г/к",
     "program": [{"name": "Охлаждение", "duration_min": 60, "t_chamber": 4, "humidity": 80, "smoke": "none"}],
     "ingredients": [{"name": "Скумбрия", "percent": 100}],
     "yield_percent": 100, "losses_percent": 0,
     "notes": "Режим охлаждения готовой продукции после г/к."},
    {"slug": "cooling-sausage-pk", "product_slug": "krakovskaya", "name": "Охлаждение колбас п/к",
     "program": [{"name": "Охлаждение", "duration_min": 90, "t_chamber": 4, "humidity": 80, "smoke": "none"}],
     "ingredients": [{"name": "Свинина п/ж", "percent": 100}],
     "yield_percent": 100, "losses_percent": 0,
     "notes": "Режим охлаждения после варки/копчения колбас."},
    {"slug": "drying-after-cooling", "product_slug": "krakovskaya", "name": "Подсушка предпродажная",
     "program": [{"name": "Подсушка", "duration_min": 30, "t_chamber": 18, "humidity": 60, "smoke": "none"}],
     "ingredients": [{"name": "Свинина п/ж", "percent": 100}],
     "yield_percent": 98, "losses_percent": 2,
     "notes": "Предпродажная подсушка для удаления конденсата."},
    {"slug": "storage-ready-products", "product_slug": "krakovskaya", "name": "Хранение готовой продукции",
     "program": [{"name": "Хранение", "duration_min": 720, "t_chamber": 3, "humidity": 80, "smoke": "none"}],
     "ingredients": [{"name": "Свинина п/ж", "percent": 100}],
     "yield_percent": 100, "losses_percent": 0,
     "notes": "До 12 ч хранения при +2...+4°C."},
]


async def get_or_create_products(session) -> dict[str, Product]:
    by_slug = {}
    for item in PRODUCTS_DATA:
        slug = item["slug"]
        existing = await session.scalar(select(Product).where(Product.slug == slug))
        if existing:
            by_slug[slug] = existing
            continue
        obj = Product(**item)
        session.add(obj)
        by_slug[slug] = obj
    await session.flush()
    return by_slug


async def get_or_create_ingredients(session) -> dict[str, Ingredient]:
    by_slug = {}
    for item in INGREDIENTS_DATA:
        slug = item["slug"]
        existing = await session.scalar(select(Ingredient).where(Ingredient.slug == slug))
        if existing:
            by_slug[slug] = existing
            continue
        obj = Ingredient(**item)
        session.add(obj)
        by_slug[slug] = obj
    await session.flush()
    return by_slug


async def get_or_create_recipe(
    session, data: dict, products: dict, user: User | None
) -> dict:
    slug = data["slug"]
    existing = await session.scalar(select(Recipe).where(Recipe.slug == slug))
    if existing:
        return {"recipe": existing, "created": False}

    product_slug = data.pop("product_slug")
    product = products.get(product_slug)
    if not product:
        logger.warning("Product %s not found for recipe %s", product_slug, slug)
        return {"recipe": None, "created": False}

    program = data.pop("program", [])
    ingredients = data.pop("ingredients", [])
    brine = data.pop("brine", None)
    yield_percent = data.pop("yield_percent", None)
    losses_percent = data.pop("losses_percent", None)
    notes = data.pop("notes", None)
    gost = data.pop("gost", None)
    source = data.pop("source", None)
    bju_per_100g = data.pop("bju_per_100g", None)
    cost_per_kg = data.pop("cost_per_kg", None)

    recipe = Recipe(
        product_id=product.id,
        created_by_id=user.id if user else None,
        status=RecipeStatus.APPROVED,
        **data,
    )
    session.add(recipe)
    await session.flush()

    version = RecipeVersion(
        recipe_id=recipe.id,
        version_number=1,
        program=program,
        ingredients=ingredients,
        brine=brine,
        yield_percent=yield_percent,
        losses_percent=losses_percent,
        notes=notes,
        gost=gost,
        source=source,
        bju_per_100g=bju_per_100g,
        cost_per_kg=cost_per_kg,
        created_by_id=user.id if user else None,
        status=RecipeStatus.APPROVED,
    )
    session.add(version)
    await session.flush()

    recipe.current_version_id = version.id
    await session.flush()

    return {"recipe": recipe, "created": True}


async def run_seed() -> None:
    logger.info("=== SEED RECIPES: start ===")
    async with AsyncSessionLocal() as session:
        try:
            products = await get_or_create_products(session)
            logger.info("Products: %d", len(products))

            ingredients = await get_or_create_ingredients(session)
            logger.info("Ingredients: %d", len(ingredients))

            admin = await session.scalar(
                select(User).where(User.username == "admin")
            )
            logger.info("Admin user: %s", admin)

            created = 0
            skipped = 0

            for data in RECIPES_DATA:
                result = await get_or_create_recipe(session, dict(data), products, admin)
                if result["recipe"]:
                    if result["created"]:
                        created += 1
                    else:
                        skipped += 1

            for data in POLUGORYACHEE:
                result = await get_or_create_recipe(session, dict(data), products, admin)
                if result["recipe"]:
                    if result["created"]:
                        created += 1
                    else:
                        skipped += 1

            for data in COOLING:
                result = await get_or_create_recipe(session, dict(data), products, admin)
                if result["recipe"]:
                    if result["created"]:
                        created += 1
                    else:
                        skipped += 1

            await session.commit()
            logger.info("=== Recipes seeded: %d created, %d skipped ===", created, skipped)
        except Exception:
            await session.rollback()
            logger.exception("Seed recipes failed, rolled back")
            raise
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_seed())
