"""Сид-данные: производители, камеры, рецепты, ингредиенты.

Запуск: `python -m app.scripts.seed`
Идемпотентен — повторный запуск не дублирует (по slug).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base  # noqa: F401 — регистрация моделей в metadata
from app.db.session import AsyncSessionLocal, engine
from app.models.chamber import Chamber, ChamberType
from app.models.competitor import Competitor, CompetitorModel, CompetitorProblem
from app.models.ingredient import Ingredient, IngredientType
from app.models.manufacturer import Manufacturer
from app.models.product import Product, ProductCategory
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


async def seed_manufacturers(session) -> list[Manufacturer]:
    data = [
        # === Наш бренд ===
        {"slug": "feleti", "name": "FELETI", "country": "Беларусь", "city": "Брест",
         "website": "https://feleti.by", "founded_year": 2008,
         "description": "FELETI (Брест) — производитель коптильного оборудования. Собственная линейка FELETI-SMOK.",
         "is_our_brand": True, "is_competitor": False, "sort_order": 0},
        # === Германия ===
        {"slug": "fessmann", "name": "Fessmann", "country": "Германия", "city": "Winnenden",
         "website": "https://fessmann.com", "founded_year": 1924,
         "description": "Fessmann — премиум-сегмент коптильного оборудования. Turbomat, FOOD.CON 2, FES.APP.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 10},
        {"slug": "kerres", "name": "Kerres Anlagensysteme", "country": "Германия", "city": "Backnang",
         "website": "https://kerres-group.de", "founded_year": 1966,
         "description": "Kerres — модульные коптильные системы. Технологии Jet Smoke, Hybrid Airflow. Дилеры в 50+ странах.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 20},
        {"slug": "bastra", "name": "Bastra", "country": "Германия", "city": "Arnsberg",
         "website": "https://bastra.com", "founded_year": None,
         "description": "Bastra — немецкий производитель коптильных камер премиум-сегмента. Дилеры в 30+ странах мира.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 30},
        {"slug": "reich", "name": "REICH Thermoprozesstechnik", "country": "Германия", "city": "Schechingen",
         "website": "https://reich-foodsystems.com", "founded_year": 1893,
         "description": "REICH — термо-процесс техника: копчение, обжарка, варка. Серия MULTIMAT, INJECTA.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 40},
        {"slug": "maurer", "name": "Maurer", "country": "Германия",
         "website": None, "founded_year": None,
         "description": "Maurer — немецкий производитель коптильного оборудования (б/у через REICH).",
         "is_our_brand": False, "is_competitor": True, "sort_order": 50},
        {"slug": "schroter", "name": "Schröter", "country": "Германия",
         "website": None, "founded_year": None,
         "description": "Schröter — немецкий производитель коптильных камер (б/у через REICH).",
         "is_our_brand": False, "is_competitor": True, "sort_order": 60},
        {"slug": "vemag", "name": "Vemag", "country": "Германия", "city": "Verden",
         "website": "https://vemag.com", "founded_year": None,
         "description": "Vemag — немецкий производитель промышленного пищевого оборудования, включая коптильные камеры.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 70},
        {"slug": "autotherm", "name": "Autotherm", "country": "Германия",
         "website": "https://autotherm.de", "founded_year": None,
         "description": "Autotherm — немецкий производитель термокамер премиум-сегмента.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 80},
        {"slug": "sumann", "name": "SüMann Korz + Co.", "country": "Германия", "city": "Walzbachtal",
         "website": "https://suemann.de", "founded_year": 1910,
         "description": "SüMann — немецкий производитель коптильных и термокамер с 1910 года.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 90},
        {"slug": "germos-ness", "name": "GERMOS NESS GmbH & Co. KG", "country": "Германия",
         "website": "https://germos-ness.de", "founded_year": None,
         "description": "GERMOS NESS — немецкий производитель коптильного оборудования премиум-сегмента.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 100},
        {"slug": "agk-kronawitter", "name": "AGK Kronawitter", "country": "Германия",
         "website": None, "founded_year": None,
         "description": "AGK Kronawitter — немецкий производитель бюджетных коптильных камер.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 110},
        {"slug": "peetz", "name": "Peetz Metallverarbeitung", "country": "Германия", "city": "Meschede",
         "website": None, "founded_year": None,
         "description": "Peetz — немецкий производитель домашних коптилен.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 120},
        # === Австрия ===
        {"slug": "sorgo", "name": "Sorgo Anlagenbau", "country": "Австрия", "city": "Klagenfurt",
         "website": "https://sorgo-anlagenbau.de", "founded_year": 1986,
         "description": "Sorgo — австрийский производитель коптильных камер премиум-сегмента.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 130},
        {"slug": "inject-star", "name": "Inject Star (Doleschal)", "country": "Австрия",
         "website": "https://inject-star.at", "founded_year": None,
         "description": "Inject Star — австрийский производитель промышленного коптильного оборудования.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 140},
        {"slug": "strasser", "name": "Strasser GmbH", "country": "Австрия", "city": "Nußdorf",
         "website": "https://strasser.co.at", "founded_year": None,
         "description": "Strasser — австрийский производитель премиум-камер, дилер Bastra в Австрии.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 150},
        # === Чехия ===
        {"slug": "mauting", "name": "Mauting", "country": "Чехия", "city": "Valtice",
         "website": "https://mauting.com", "founded_year": 1992,
         "description": "Mauting — чешский производитель туннельных и камерных коптилен, лидер сегмента Industrial.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 160},
        # === Италия ===
        {"slug": "emerson-technik", "name": "Emerson Technik SRL", "country": "Италия",
         "website": "https://emerson-technik.eu", "founded_year": None,
         "description": "Emerson Technik — итальянский производитель коптильных камер среднего сегмента.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 170},
        {"slug": "comat", "name": "Comat", "country": "Италия",
         "website": None, "founded_year": None,
         "description": "Comat — итальянский производитель коптильного оборудования среднего сегмента (DirectIndustry).",
         "is_our_brand": False, "is_competitor": True, "sort_order": 180},
        {"slug": "wielander", "name": "Ernst Wielander GmbH", "country": "Италия", "city": "Merano",
         "website": None, "founded_year": None,
         "description": "Wielander — итальянский производитель премиум-камер, дилер Bastra в Италии.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 190},
        # === Нидерланды ===
        {"slug": "visser-goes", "name": "Visser Goes Food Equipment", "country": "Нидерланды", "city": "Goes",
         "website": "https://vissergoes.nl", "founded_year": None,
         "description": "Visser Goes — голландский производитель, дилер Bastra в Нидерландах.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 200},
        {"slug": "van-uhm", "name": "Handelmij Van Uhm B.V.", "country": "Нидерланды", "city": "Borne",
         "website": None, "founded_year": None,
         "description": "Van Uhm — голландский производитель, дилер Kerres в Нидерландах.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 210},
        # === Франция ===
        {"slug": "hoegger-alpina", "name": "Hoegger Alpina France", "country": "Франция",
         "website": "https://alpinafrance.com", "founded_year": None,
         "description": "Hoegger Alpina — французский производитель, дилер Kerres для Франции и Африки (20+ стран).",
         "is_our_brand": False, "is_competitor": True, "sort_order": 220},
        # === Испания ===
        {"slug": "celestino-gil", "name": "Comercial Celestino Gil", "country": "Испания", "city": "Barcelona",
         "website": None, "founded_year": None,
         "description": "Celestino Gil — испанский производитель, дилер Bastra в Испании.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 230},
        # === Швейцария ===
        {"slug": "josef-koch", "name": "Josef Koch AG", "country": "Швейцария", "city": "Malters",
         "website": "https://josefkoch.ch", "founded_year": None,
         "description": "Josef Koch — швейцарский производитель премиум-камер, дилер Bastra в Швейцарии.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 240},
        # === Великобритания ===
        {"slug": "vanguard-processing", "name": "Vanguard Processing Equipment", "country": "Великобритания",
         "website": None, "founded_year": None,
         "description": "Vanguard — британский производитель, дилер Bastra в Великобритании.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 250},
        # === США ===
        {"slug": "kerres-usa", "name": "Kerres USA", "country": "США",
         "website": "https://kerresusa.com", "founded_year": None,
         "description": "Kerres USA — дочерняя компания Kerres для рынка США и Канады.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 260},
        {"slug": "jr-manufacturing", "name": "J&R Manufacturing", "country": "США", "city": "Mesquite, TX",
         "website": "https://jrmanufacturing.com", "founded_year": 1974,
         "description": "J&R Manufacturing — американский производитель коптилен Oyler Pit, Smoke-Master.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 270},
        {"slug": "pro-smoker", "name": "Pro Smoker", "country": "США",
         "website": "https://pro-smoker.com", "founded_year": None,
         "description": "Pro Smoker — американский производитель коптилен среднего/премиум-сегмента. NSF, MET сертификация.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 280},
        {"slug": "cookshack", "name": "Cookshack", "country": "США", "city": "Ponca City, OK",
         "website": "https://cookshack.com", "founded_year": None,
         "description": "Cookshack — американский производитель. Fast Eddy Pellet Smokers.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 290},
        {"slug": "marlen", "name": "Marlen", "country": "США",
         "website": "https://marlen.com", "founded_year": None,
         "description": "Marlen — американский производитель промышленных коптильных камер и пищевого оборудования.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 300},
        {"slug": "alkar", "name": "Alkar", "country": "США",
         "website": None, "founded_year": None,
         "description": "Alkar — американский производитель промышленных коптильных решений.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 310},
        {"slug": "fusiontech", "name": "FusionTech Inc (FTI)", "country": "США",
         "website": "https://ftiinc.org", "founded_year": None,
         "description": "FusionTech — американский производитель промышленных коптилен и дегидраторов.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 320},
        {"slug": "mpbs-industries", "name": "MPBS Industries", "country": "США", "city": "Los Angeles, CA",
         "website": "https://mpbs.com", "founded_year": None,
         "description": "MPBS Industries — американский производитель. Value-Plus, Flavor-Cook.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 330},
        # === Канада ===
        {"slug": "klever-equipped", "name": "Klever Equipped", "country": "Канада", "city": "Vaughan, ON",
         "website": "https://goklever.com", "founded_year": None,
         "description": "Klever Equipped — канадский дилер и производитель, дилер Fessmann в Канаде.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 340},
        # === Россия ===
        {"slug": "ijiza", "name": "Ижица / Varmen", "country": "Россия", "city": "Санкт-Петербург",
         "website": "https://ijiza.ru", "founded_year": 1992,
         "description": "Ижица — главный конкурент. Производитель с 1992 года, 4000+ клиентов. Линейка 20–1200 кг, контроллер Varmen-1.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 350},
        {"slug": "agros", "name": "AGROS", "country": "Россия",
         "website": "https://agros.si", "founded_year": None,
         "description": "AGROS — бюджетный сегмент (Словения — Россия). Интегратор коптильного оборудования.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 360},
        {"slug": "tekhtronik", "name": "Техтроник", "country": "Россия",
         "website": None, "founded_year": None,
         "description": "Техтроник — российский производитель коптильных камер среднего сегмента.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 370},
        {"slug": "vortice", "name": "Vortice", "country": "Россия",
         "website": None, "founded_year": None,
         "description": "Vortice — российский производитель бюджетных коптильных камер.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 380},
        {"slug": "master-kopt", "name": "ООО Мастер-Копт", "country": "Россия",
         "website": None, "founded_year": None,
         "description": "Мастер-Копт — производитель настольных коптилен (домашний сегмент).",
         "is_our_brand": False, "is_competitor": True, "sort_order": 390},
        {"slug": "smoke-m", "name": "Smoke-M", "country": "Россия",
         "website": None, "founded_year": None,
         "description": "Smoke-M — российский производитель бюджетных коптилен.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 400},
        {"slug": "baranov", "name": "Баранов", "country": "Россия",
         "website": None, "founded_year": None,
         "description": "Баранов — российский производитель бюджетных коптилен.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 410},
        {"slug": "dzheri-tehno", "name": "Джери-Техно", "country": "Россия",
         "website": None, "founded_year": None,
         "description": "Джери-Техно — российский производитель бюджетных коптильных камер.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 420},
        {"slug": "zpo", "name": "ЗПО (Завод пищевого оборудования)", "country": "Россия",
         "website": "https://russia-zpo.ru", "founded_year": None,
         "description": "ЗПО — российский завод промышленных коптильных камер среднего сегмента.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 430},
        {"slug": "voltek", "name": "Волтэк Групп", "country": "Россия",
         "website": "https://voltekgroup.com", "founded_year": None,
         "description": "Волтэк Групп — российский поставщик коптильных камер.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 440},
        # === Словения ===
        {"slug": "agros-slovenia", "name": "AGROS (Словения)", "country": "Словения",
         "website": "https://agros.si", "founded_year": None,
         "description": "AGROS — словенский производитель бюджетных коптильных камер.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 450},
        # === Китай ===
        {"slug": "helper-food", "name": "Shijiazhuang Helper Food Machinery", "country": "Китай",
         "website": "https://ihelper.en.made-in-china.com", "founded_year": None,
         "description": "Helper — китайский производитель бюджетных коптильных линий.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 460},
        {"slug": "taizy-food", "name": "Taizy Food Machine", "country": "Китай",
         "website": "https://taizyfoodmachine.com", "founded_year": None,
         "description": "Taizy — китайский производитель бюджетного коптильного оборудования.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 470},
        {"slug": "freund-mado", "name": "Freund MADO", "country": "Китай", "city": "Beijing",
         "website": None, "founded_year": None,
         "description": "Freund MADO — китайский дилер Kerres, производство копий.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 480},
        # === Турция ===
        {"slug": "feyzi", "name": "Feyzi", "country": "Турция",
         "website": None, "founded_year": None,
         "description": "Feyzi — турецкий дилер и производитель коптильных камер (дилер Kerres).",
         "is_our_brand": False, "is_competitor": True, "sort_order": 490},
        # === Польша ===
        {"slug": "panepol", "name": "Panepol", "country": "Польша", "city": "Przeźmierowo",
         "website": "https://panepol.pl", "founded_year": None,
         "description": "Panepol — польский производитель, дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 500},
        # === Швеция ===
        {"slug": "lr-maskin", "name": "LR Maskin AB", "country": "Швеция", "city": "Malmö",
         "website": "https://lrmaskin.se", "founded_year": None,
         "description": "LR Maskin — шведский производитель, дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 510},
        # === Норвегия ===
        {"slug": "bokken", "name": "Bokken AG", "country": "Норвегия", "city": "Oslo",
         "website": "https://bokken.no", "founded_year": None,
         "description": "Bokken — норвежский производитель, дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 520},
        # === Финляндия ===
        {"slug": "solotop", "name": "Solotop Oy", "country": "Финляндия", "city": "Helsinki",
         "website": None, "founded_year": None,
         "description": "Solotop — финский производитель, дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 530},
        # === Дания ===
        {"slug": "multivac-dk", "name": "Multivac A/S", "country": "Дания",
         "website": "https://multivac.dk", "founded_year": None,
         "description": "Multivac — датский производитель, дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 540},
        # === Другие страны (дилеры Kerres) ===
        {"slug": "claes-machines", "name": "Claes Machines nv", "country": "Бельгия",
         "website": None, "founded_year": None,
         "description": "Claes Machines — бельгийский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 550},
        {"slug": "swe-flex", "name": "SWE-Flex", "country": "Болгария",
         "website": None, "founded_year": None,
         "description": "SWE-Flex — болгарский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 560},
        {"slug": "kerres-kft", "name": "Kerres Kft", "country": "Венгрия",
         "website": None, "founded_year": None,
         "description": "Kerres Kft — венгерское представительство Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 570},
        {"slug": "makelis", "name": "Makelis N.A.", "country": "Греция",
         "website": None, "founded_year": None,
         "description": "Makelis — греческий дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 580},
        {"slug": "multivac-iceland", "name": "Multivac Iceland", "country": "Исландия",
         "website": None, "founded_year": None,
         "description": "Multivac Iceland — исландский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 590},
        {"slug": "alltex", "name": "ALLTEX", "country": "Латвия",
         "website": None, "founded_year": None,
         "description": "ALLTEX — латвийский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 600},
        {"slug": "rovabo", "name": "Rovabo / ALLTEX", "country": "Литва",
         "website": None, "founded_year": None,
         "description": "Rovabo — литовский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 610},
        {"slug": "i-solutions", "name": "I-Solutions", "country": "Португалия",
         "website": None, "founded_year": None,
         "description": "I-Solutions — португальский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 620},
        {"slug": "dico-total", "name": "DI-CO TOTAL", "country": "Румыния",
         "website": None, "founded_year": None,
         "description": "DI-CO TOTAL — румынский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 630},
        {"slug": "ksm-machine", "name": "KSM Machine / YU Petrovic", "country": "Сербия",
         "website": None, "founded_year": None,
         "description": "KSM Machine — сербский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 640},
        {"slug": "eurostandart", "name": "Eurostandart / Kotlin Ukraine", "country": "Украина",
         "website": None, "founded_year": None,
         "description": "Eurostandart — украинский дилер Kerres.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 650},
        # === Дилеры Bastra по миру ===
        {"slug": "mbr-plus", "name": "MBR Plus", "country": "Беларусь",
         "website": None, "founded_year": None,
         "description": "MBR Plus — белорусский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 660},
        {"slug": "all-food-machines", "name": "All Food Machines", "country": "Бельгия",
         "website": None, "founded_year": None,
         "description": "All Food Machines — бельгийский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 670},
        {"slug": "bonner-ltd", "name": "Bonner Ltd", "country": "Болгария",
         "website": None, "founded_year": None,
         "description": "Bonner Ltd — болгарский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 680},
        {"slug": "maso-profit", "name": "MASO-PROFIT", "country": "Чехия",
         "website": None, "founded_year": None,
         "description": "MASO-PROFIT — чешский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 690},
        {"slug": "secoser", "name": "SECOSER KFT", "country": "Венгрия",
         "website": None, "founded_year": None,
         "description": "SECOSER — венгерский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 700},
        {"slug": "geiri-ehf", "name": "Geiri ehf.", "country": "Исландия",
         "website": None, "founded_year": None,
         "description": "Geiri ehf. — исландский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 710},
        {"slug": "tomlon", "name": "A. TomLon Ltd", "country": "Израиль",
         "website": None, "founded_year": None,
         "description": "A. TomLon — израильский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 720},
        {"slug": "calion", "name": "CALION Co. Ltd", "country": "Япония",
         "website": None, "founded_year": None,
         "description": "CALION — японский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 730},
        {"slug": "andonov", "name": "TD Andonov", "country": "Македония",
         "website": None, "founded_year": None,
         "description": "TD Andonov — македонский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 740},
        {"slug": "debitron-termo", "name": "DEBITRON termo", "country": "Румыния",
         "website": None, "founded_year": None,
         "description": "DEBITRON termo — румынский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 750},
        {"slug": "yu-petrovic", "name": "YU PETROVIC", "country": "Сербия",
         "website": None, "founded_year": None,
         "description": "YU PETROVIC — сербский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 760},
        {"slug": "lifa-pte", "name": "LIFA PTE LTD", "country": "Сингапур",
         "website": None, "founded_year": None,
         "description": "LIFA — сингапурский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 770},
        {"slug": "kumkwang", "name": "KumKwang Corp.", "country": "Южная Корея",
         "website": None, "founded_year": None,
         "description": "KumKwang — южнокорейский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 780},
        {"slug": "u-life-food", "name": "U-Life Food Machine", "country": "Тайвань",
         "website": None, "founded_year": None,
         "description": "U-Life — тайваньский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 790},
        {"slug": "siam-foods", "name": "Siam Foodsconsultant", "country": "Таиланд",
         "website": None, "founded_year": None,
         "description": "Siam Foodsconsultant — тайский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 800},
        {"slug": "bmp-e-food", "name": "B M P E Food Processing", "country": "ЮАР",
         "website": None, "founded_year": None,
         "description": "B M P E — южноафриканский дилер Bastra.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 810},
        {"slug": "qindao-tla", "name": "Qingdao TLA Food Tech", "country": "Китай", "city": "Qingdao",
         "website": None, "founded_year": None,
         "description": "Qingdao TLA — китайский дилер Kerres, производство копий.",
         "is_our_brand": False, "is_competitor": True, "sort_order": 820},
    ]

    result: list[Manufacturer] = []
    for item in data:
        existing = await session.scalar(
            select(Manufacturer).where(Manufacturer.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        obj = Manufacturer(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_chambers(session, manufacturers: list[Manufacturer]) -> list[Chamber]:
    by_slug = {m.slug: m for m in manufacturers}
    data: list[dict[str, Any]] = [
        # FELETI-SMOK собственная линейка
        {"manufacturer": "feleti", "model": "Profi H-100", "slug": "feleti-profih-100",
         "type": ChamberType.HOT, "max_load_kg": 100, "volume_m3": 1.2, "power_kw": 12,
         "voltage_v": 380, "supports_electro": False, "supports_cold_smoke": False,
         "driver_class": "FELETI_SMOKDriver", "description": "FELETI-SMOK Profi H-100 — горячее копчение, 100 кг загрузки."},
        {"manufacturer": "feleti", "model": "Profi H-200", "slug": "feleti-profih-200",
         "type": ChamberType.HOT, "max_load_kg": 200, "volume_m3": 2.4, "power_kw": 18,
         "voltage_v": 380, "supports_electro": False, "supports_cold_smoke": False,
         "driver_class": "FELETI_SMOKDriver", "description": "FELETI-SMOK Profi H-200 — горячее копчение, 200 кг."},
        {"manufacturer": "feleti", "model": "Profi C-200", "slug": "feleti-profic-200",
         "type": ChamberType.COLD, "max_load_kg": 200, "volume_m3": 2.4, "power_kw": 6,
         "voltage_v": 380, "supports_electro": False, "supports_cold_smoke": True,
         "supports_cooling": True, "driver_class": "FELETI_SMOKDriver",
         "description": "FELETI-SMOK Profi C-200 — холодное копчение + охлаждение, 200 кг."},
        {"manufacturer": "feleti", "model": "Profi U-250", "slug": "feleti-profiu-250",
         "type": ChamberType.UNIVERSAL, "max_load_kg": 250, "volume_m3": 3.0, "power_kw": 24,
         "voltage_v": 380, "supports_electro": True, "supports_cold_smoke": True,
         "supports_cooling": True, "supports_joint": True,
         "driver_class": "FELETI_SMOKDriver",
         "description": "FELETI-SMOK Profi U-250 — универсал: горячее + холодное + электро + охлаждение."},
        # Ижица
        {"manufacturer": "ijiza", "model": "Ижица 1200М4", "slug": "ijiza-1200m4",
         "type": ChamberType.ELECTRO, "max_load_kg": 120, "volume_m3": 1.4, "power_kw": 14,
         "voltage_v": 380, "supports_electro": True,
         "driver_class": "VarmenDriver",
         "description": "Ижица 1200М4 — электростатическое копчение, контроллер Varmen-1."},
        {"manufacturer": "ijiza", "model": "Ижица UTR-C 250", "slug": "ijiza-utr-c-250",
         "type": ChamberType.COLD, "max_load_kg": 250, "volume_m3": 3.0, "power_kw": 7,
         "voltage_v": 380, "supports_cold_smoke": True, "supports_cooling": True,
         "driver_class": "VarmenDriver",
         "description": "Ижица UTR-C 250 — холодное копчение + охлаждение готовой продукции."},
    ]
    result: list[Chamber] = []
    for item in data:
        existing = await session.scalar(
            select(Chamber).where(Chamber.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        manuf_slug = item.pop("manufacturer")
        manuf = by_slug.get(manuf_slug)
        if not manuf:
            continue
        obj = Chamber(manufacturer_id=manuf.id, **item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_ingredients(session) -> list[Ingredient]:
    data = [
        {"slug": "govyadina-zhel", "name": "Говядина жилованная", "type": IngredientType.MEAT,
         "protein_per_100g": 19.0, "fat_per_100g": 12.0, "kcal_per_100g": 187, "price_per_kg": 850},
        {"slug": "svinina-poluzhirn", "name": "Свинина полужирная", "type": IngredientType.MEAT,
         "protein_per_100g": 16.0, "fat_per_100g": 27.0, "kcal_per_100g": 305, "price_per_kg": 650},
        {"slug": "sheel-olkha", "name": "Щепа ольхи", "type": IngredientType.WOOD,
         "wood_species": "ольха", "wood_form": "щепа", "fraction_mm": "4-8",
         "price_per_kg": 180, "unit": "кг"},
        {"slug": "sheel-dub", "name": "Щепа дуба", "type": IngredientType.WOOD,
         "wood_species": "дуб", "wood_form": "щепа", "fraction_mm": "4-8",
         "price_per_kg": 220, "unit": "кг"},
        {"slug": "sol-povarennaya", "name": "Соль поваренная", "type": IngredientType.SALT,
         "price_per_kg": 25},
        {"slug": "nitritnaya-sol", "name": "Нитритная соль", "type": IngredientType.ADDITIVE,
         "price_per_kg": 350},
    ]
    result: list[Ingredient] = []
    for item in data:
        existing = await session.scalar(
            select(Ingredient).where(Ingredient.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        obj = Ingredient(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_products(session) -> list[Product]:
    data = [
        {"slug": "doktorskaya", "name": "Докторская колбаса", "category": ProductCategory.SAUSAGE_BOILD,
         "gost": "ГОСТ Р 52196-2011", "shelf_life_days": 5,
         "storage_temp_min": 2, "storage_temp_max": 6, "storage_humidity_min": 75, "storage_humidity_max": 80},
        {"slug": "polukopchenaya-moskovskaya", "name": "Московская полукопчёная", "category": ProductCategory.SAUSAGE_SEMI_SMOKED,
         "gost": "ГОСТ 31785-2012", "shelf_life_days": 10,
         "storage_temp_min": 2, "storage_temp_max": 6, "storage_humidity_min": 75, "storage_humidity_max": 80},
        {"slug": "syrokopchenaya-braunschweig", "name": "Брауншвейгская сырокопчёная", "category": ProductCategory.SAUSAGE_RAW_SMOKED,
         "gost": "ГОСТ 31785-2012", "shelf_life_days": 30,
         "storage_temp_min": 2, "storage_temp_max": 6, "storage_humidity_min": 75, "storage_humidity_max": 80},
        {"slug": "skumbria-gk", "name": "Скумбрия горячего копчения", "category": ProductCategory.FISH_HOT,
         "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
        {"slug": "semga-hk", "name": "Сёмга холодного копчения", "category": ProductCategory.FISH_COLD,
         "shelf_life_days": 10, "storage_temp_min": 0, "storage_temp_max": 4},
        {"slug": "kuritsa-gk", "name": "Курица горячего копчения", "category": ProductCategory.POULTRY,
         "shelf_life_days": 3, "storage_temp_min": 2, "storage_temp_max": 6},
        {"slug": "syr-kopcheniy-gouda", "name": "Сыр копчёный Гауда", "category": ProductCategory.CHEESE,
         "shelf_life_days": 7, "storage_temp_min": 2, "storage_temp_max": 6},
        {"slug": "salo-kopchenoe", "name": "Сало копчёное", "category": ProductCategory.BACON,
         "shelf_life_days": 14, "storage_temp_min": 2, "storage_temp_max": 6},
    ]
    result: list[Product] = []
    for item in data:
        existing = await session.scalar(
            select(Product).where(Product.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        obj = Product(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_competitors(session) -> list[Competitor]:
    data = [
        # === Приоритетные конкуренты (P0) ===
        {
            "slug": "ijiza",
            "name": "Ижица / Varmen",
            "country": "Россия",
            "founded_year": 1992,
            "segment": "Horeca / Profi / Industrial",
            "is_main_competitor": True,
            "client_count": 4000,
            "recipe_count": 200,
            "warranty_years": 1,
            "has_cloud": True,
            "has_mobile_app": True,
            "has_remote_monitoring": True,
            "has_video_camera": False,
            "base_url": "https://ijiza.ru",
            "description": "Ижица / Varmen (Санкт-Петербург, Россия, 1992) — ведущий российский производитель.\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильно-варочные камеры (20-1200 кг): Z115, Z200, 1200М4, UNI, UTM, UTR, Atomic, СВ.\nДРУГОЕ ОБОРУДОВАНИЕ: дымогенераторы, варочные котлы, системы холодного копчения.\nСегменты: Horeca, Profi, Industrial. Контроллер Varmen-1, облачная платформа, мобильное приложение, удалённый мониторинг. 4000+ клиентов в 50+ странах.",
            "strengths": ["25+ лет на рынке", "200+ готовых рецептов", "Собственное производство", "Широкая линейка (20-1200 кг)", "Фрикционный дымогенератор", "Электростатическое копчение", "Облако / мобильное / удаленный мониторинг"],
            "weaknesses": ["Плохие инструкции", "Проблемы с электростатикой", "Заводской дефект вентилятора", "Нагар и перегрев", "Плесень при неправильной эксплуатации", "Капли конденсата", "Проблемы с цветом продукта", "Шибер/зольник"],
            "models": [
                {"name": "Varmen Mini", "max_load_kg": 20, "power_kw": 3.5, "voltage_v": 220, "weight_kg": 70, "dimensions": "0.65 x 0.65 x 1.1 м", "modes": ["горячее копчение", "проварка паром", "запекание", "сушка", "обжарка"], "automation_level": "полуавтомат"},
                {"name": "Ижица-Z115.2 (полуавтомат)", "max_load_kg": 100, "power_kw": 10, "voltage_v": 380, "weight_kg": 300, "dimensions": "1.51 x 1.1 x 1.9 м", "modes": ["горячее копчение", "проварка паром", "сушка", "запекание", "обжарка"], "automation_level": "полуавтомат"},
                {"name": "Ижица-Z115.2-A (автомат)", "max_load_kg": 250, "power_kw": 14, "voltage_v": 380, "weight_kg": 650, "dimensions": "1.6 x 1.3 x 2.25 м", "modes": ["горячее копчение", "проварка паром", "запекание", "холодное копчение"], "automation_level": "автомат"},
                {"name": "Ижица-Z115.2АС", "max_load_kg": 250, "power_kw": 12, "voltage_v": 380, "weight_kg": 650, "dimensions": "1.75 x 1.55 x 2.25 м", "modes": ["прогрев", "сушка", "сушка по влажности", "копчение", "варка", "обжарка"], "automation_level": "автомат"},
                {"name": "Ижица-Z200", "max_load_kg": 500, "power_kw": 30, "voltage_v": 380, "weight_kg": 600, "dimensions": "2.0 x 1.4 x 2.7 м", "modes": ["горячее копчение", "проварка паром", "запекание"], "automation_level": "полуавтомат"},
                {"name": "Ижица-UNI-100", "max_load_kg": 100, "power_kw": 11, "voltage_v": 380, "weight_kg": 340, "dimensions": "1.51 x 1.1 x 1.9 м", "modes": ["горячее копчение", "холодное копчение", "запекание", "проварка паром", "сушка", "обжарка"], "automation_level": "полуавтомат"},
                {"name": "Ижица-miniGK", "max_load_kg": 20, "power_kw": 3.5, "voltage_v": 220, "weight_kg": 70, "dimensions": "0.63 x 0.65 x 1.1 м", "modes": ["сушка", "копчение", "жарка", "варка паром", "проветривание"], "automation_level": "полуавтомат"},
                {"name": "Ижица-1200М4", "max_load_kg": 1200, "power_kw": 3.2, "voltage_v": 380, "weight_kg": 250, "dimensions": "1.3 x 0.95 x 2.0 м", "modes": ["холодное копчение"], "automation_level": "полуавтомат"},
                {"name": "Ижица-1200М4-А (электростатика)", "max_load_kg": 1200, "power_kw": 5, "voltage_v": 380, "weight_kg": 400, "dimensions": "1.4 x 1.2 x 2.25 м", "modes": ["холодное копчение"], "automation_level": "автомат"},
                {"name": "VARMEN UTM.250", "max_load_kg": 250, "power_kw": 31, "voltage_v": 380, "dimensions": "2.04 x 1.5 x 3.1 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "VARMEN UTM.500", "max_load_kg": 500, "power_kw": 62, "voltage_v": 380, "dimensions": "2.04 x 2.5 x 3.5 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "VARMEN UTR.250", "max_load_kg": 250, "power_kw": 31, "voltage_v": 380, "dimensions": "2.04 x 1.5 x 3.1 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "холодное копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "VARMEN UTR.500", "max_load_kg": 500, "power_kw": 62, "voltage_v": 380, "dimensions": "2.04 x 2.5 x 3.5 м", "modes": ["сушка", "интервальная сушка", "сушка по влажности", "прогрев", "горячее копчение", "холодное копчение", "варка", "мойка автоматическая", "эвакуация"], "automation_level": "полностью автоматизированная"},
                {"name": "Varmen Atomic 250", "max_load_kg": 250, "power_kw": 30, "voltage_v": 380, "dimensions": "1.97 x 1.5 x 3.05 м", "modes": ["сушка", "интервальная сушка", "копчение", "варка"], "automation_level": "полностью автоматизированная"},
                {"name": "BBQ Smoker Red Dolly", "max_load_kg": 100, "power_kw": 9, "voltage_v": 380, "dimensions": "1.4 x 1.0 x 1.85 м", "modes": ["горячее копчение", "проварка паром"], "automation_level": "сенсорная панель с удаленным доступом"},
                {"name": "Ижица-СВ-Н", "max_load_kg": 80, "power_kw": 0.7, "voltage_v": 220, "weight_kg": 80, "dimensions": "0.9 x 0.9 x 1.9 м", "modes": ["сушка", "вяление"], "automation_level": "полуавтомат"},
                {"name": "Ижица-СВ-Z", "max_load_kg": 100, "power_kw": 1.2, "voltage_v": 220, "dimensions": "0.95 x 1.2 x 1.6 м", "modes": ["сушка", "вяление"], "automation_level": "полуавтомат"},
                {"name": "Ижица-СВ2500", "max_load_kg": 250, "power_kw": 1.5, "voltage_v": 220, "dimensions": "1.48 x 1.6 x 2.25 м", "modes": ["сушка", "вяление"], "automation_level": "полуавтомат"},
            ],
            "problems": [
                {"title": "Вентилятор установлен вверх ногами", "description": "В сушильно-вялочной камере вентилятор стоит с лопастями для подачи воздуха вверх, а крутится вниз. Обдув идет по стенкам, в центре противоток.", "severity": "medium", "frequency": "Часто", "source": "me23.ru (фев 2018)"},
                {"title": "Электростатика не работает", "description": "Увеличилось время копчения. Статика на ноль ушла через 2 года. Искра на генераторе при полной загрузке — пара миллиметров.", "severity": "high", "frequency": "Часто", "source": "ijiza.userecho.ru (2024)"},
                {"title": "Плохие инструкции", "description": "Инструкция у производителя никакая, приходится звонить и спрашивать на завод. Не понятно как чистить коптильню.", "severity": "medium", "frequency": "Всегда", "source": "me23.ru (2018-2019)"},
                {"title": "Много дыма, толку мало", "description": "У двух одинаковых печей Ижица-М4 одна работает без претензий, во второй много дыма, толку мало. Напряжение везде одинаковое.", "severity": "high", "frequency": "Иногда", "source": "me23.ru (янв 2023)"},
                {"title": "Нагар и перегрев", "description": "При длительной работе нагревательных элементов образуется нагар, снижающий эффективность. Перегрев приводит к подгоранию продукта.", "severity": "high", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Плесень на продукции", "description": "При холодном копчении и нарушении режима влажности на поверхности продукта появляется плесень.", "severity": "high", "frequency": "Иногда", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Капли конденсата", "description": "Во время охлаждения и при резком перепаде температур внутри камеры образуются капли конденсата.", "severity": "medium", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Неправильный цвет продукта", "description": "Продукт получается желтым или серым вместо золотисто-коричневого.", "severity": "medium", "frequency": "Часто", "source": "YouTube-анализ 118 видео (2026-06-03)"},
                {"title": "Проблемы с шибером и зольником", "description": "Шибер заклинивает, зольник забивается золой.", "severity": "medium", "frequency": "Всегда", "source": "YouTube-анализ 118 видео (2026-06-03)"},
            ],
            "dealers": None,
        },
        {
            "slug": "mauting",
            "name": "Mauting",
            "country": "Чехия",
            "founded_year": 1992,
            "segment": "Industrial",
            "is_main_competitor": True,
            "recipe_count": 1000,
            "warranty_years": 2,
            "has_cloud": False,
            "has_mobile_app": False,
            "has_remote_monitoring": False,
            "has_video_camera": False,
            "base_url": "https://www.mauting.com",
            "description": "Mauting s.r.o. (Валтице, Чехия, 1992) — чешский лидер. 33 года опыта.\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильные камеры UKM (Classic, Central, Versatile, Compact, Junior), дымогенераторы.\nДРУГОЕ ОБОРУДОВАНИЕ: варочно-пекарные камеры PKM, транспортные системы, климатические камеры созревания, системы очистки дыма, варочные котлы, камеры интенсивного охлаждения.\n80% экспорт в 80+ стран.",
            "strengths": ["33 года опыта", "80 стран экспорта", "Широкая линейка UKM", "Собственное КБ и производство", "Транспортные системы"],
            "weaknesses": ["Высокая цена", "Нет mobile/cloud", "Сложности с сервисом в РФ"],
            "models": [
                {"name": "UKM Junior", "max_load_kg": 150, "modes": ["копчение", "варка", "сушка", "запекание"]},
                {"name": "UKM Compact", "max_load_kg": 300, "modes": ["копчение", "варка", "сушка", "запекание"]},
                {"name": "UKM Classic", "max_load_kg": 600, "modes": ["копчение", "варка", "сушка", "запекание", "охлаждение"]},
                {"name": "UKM Central", "max_load_kg": 1200, "modes": ["копчение", "варка", "сушка", "запекание", "охлаждение"]},
                {"name": "UKM Versatile", "max_load_kg": 2000, "modes": ["копчение", "варка", "сушка", "запекание", "охлаждение"]},
            ],
            "problems": [],
            "dealers": [
                {"country": "Австрия", "company": "Josef Schwarhofer / SLT", "contact": "+43 664 860 01 89", "website": "https://slt-schwarhofer.at"},
                {"country": "Беларусь", "company": "ООО ВАРА", "contact": "+375 17 219 05 93"},
                {"country": "Бельгия", "company": "BERIMEX", "contact": "+49 6556 93056", "website": "https://berimex.de"},
                {"country": "Болгария", "company": "INOVATEC Ltd.", "contact": "+359 56 874 033", "website": "https://inovatec.bg"},
                {"country": "Великобритания", "company": "Unitech Engineering Ltd", "contact": "+44 01543 675800"},
                {"country": "Венгрия", "company": "STEVIA Kft.", "contact": "+36 1 468 3562"},
                {"country": "Германия", "company": "ALIMEX Lebensmitteltechnik", "contact": "+49 8341 938912", "website": "https://alimex-gmbh.com"},
                {"country": "Греция", "company": "SIVVAS S.A.", "contact": "+30 2310 948 851", "website": "https://sivvas.com.gr"},
                {"country": "Дания", "company": "INGVALD CHRISTENSEN A/S", "contact": "+45 6611 8211", "website": "https://ingvald.dk"},
                {"country": "Испания", "company": "DORDAL, S.A.", "contact": "+34 93 5443800", "website": "https://dordal.com"},
                {"country": "Италия", "company": "FRIGO IMPIANTI S.R.L.", "contact": "+39 075 8010489", "website": "https://frigoimpianti.it"},
                {"country": "Казахстан", "company": "NHL-Agro Kazakhstan", "contact": "+7 727 341 09 81"},
                {"country": "Литва", "company": "UAB MPTI", "contact": "+370 523 873 56", "website": "https://mpti.lt"},
                {"country": "Нидерланды", "company": "LEX FOOD EQUIPMENT B.V.", "contact": "+31 30 268 79 99", "website": "https://lexfoodequipment.nl"},
                {"country": "Норвегия", "company": "Nordic Supply System AS", "contact": "+47 70244500", "website": "https://nordicsupply.no"},
                {"country": "Польша", "company": "FMTech Robert Wanat", "contact": "+48 662 30 55 88"},
                {"country": "Россия", "company": "ООО АНТЕС", "contact": "+7 495 500-4-500", "website": "https://antes.ru"},
                {"country": "Россия", "company": "ООО ОКАНТПРОМ", "contact": "+7 495 739-76-72", "website": "https://okant.ru"},
                {"country": "Россия", "company": "ООО Дельта Машинен", "contact": "+7 812 337 55 85", "website": "https://deltamaschinen.ru"},
                {"country": "Сербия", "company": "FIBA d.o.o.", "contact": "+381 65 3422 001"},
                {"country": "Словакия", "company": "G.P.R., spol. s r.o.", "contact": "+421 49 491919", "website": "https://gpr.sk"},
                {"country": "Турция", "company": "Maes ODIN Makine", "contact": "+90 212 856 26 20", "website": "https://odinmakine.com.tr"},
                {"country": "Украина", "company": "ООО АГРО-3", "contact": "+38 44 202 746", "website": "https://agro3.com.ua"},
                {"country": "Франция", "company": "STALE PROCESSING", "contact": "+33 3 83 26 38 26", "website": "https://stale.fr"},
                {"country": "Чехия", "company": "Mauting s.r.o. (головной офис)", "contact": "+420 519 352 761", "website": "https://mauting.com"},
                {"country": "Швейцария", "company": "SUHNER AG", "contact": "+41 56 648 4242", "website": "https://suhner-ag.ch"},
                {"country": "Южная Корея", "company": "Dootumann Eng.", "contact": "+82 31 797 7366", "website": "https://dootumann.co.kr"},
            ],
        },
        {
            "slug": "fessmann",
            "name": "Fessmann",
            "country": "Германия",
            "founded_year": 1924,
            "segment": "Industrial",
            "is_main_competitor": True,
            "recipe_count": 1000,
            "warranty_years": 3,
            "has_cloud": True,
            "has_mobile_app": True,
            "has_remote_monitoring": True,
            "has_video_camera": False,
            "base_url": "https://www.fessmann.com",
            "description": "Fessmann GmbH (Винненден, Германия, 1924) — премиум-производитель, семейное предприятие в 4-м поколении.\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильные камеры Turbomat, промышленные системы, полунепрерывные и непрерывные линии.\nДРУГОЕ ОБОРУДОВАНИЕ: варочные системы, хлебопекарные камеры, системы охлаждения, дымогенераторы, климатические камеры созревания, варочные котлы.\nСистема управления FOOD.CON 2, мобильное приложение FES.APP. Технологии: ECO.LiNE (энергоэффективность). Применение: мясо, колбасы, рыба, птица, сыр, растительные продукты, корма.",
            "strengths": ["FES.APP — лучшее mobile в отрасли", "OPC UA MES интеграция", "100+ лет опыта (с 1924)", "4 поколения семьи", "ECO.LiNE энергоэффективность"],
            "weaknesses": ["Цены от 8M ₽", "Нет производства в РФ", "Таможенные риски"],
            "models": [
                {"name": "Turbomat 1", "max_load_kg": 500, "modes": ["копчение", "варка", "сушка", "запекание", "охлаждение"]},
                {"name": "Turbomat 2", "max_load_kg": 1000, "modes": ["копчение", "варка", "сушка", "запекание", "охлаждение"]},
                {"name": "Turbomat 3", "max_load_kg": 2000, "modes": ["копчение", "варка", "сушка", "запекание", "охлаждение"]},
            ],
            "problems": [],
            "dealers": [{"country": "Германия", "company": "Fessmann GmbH (головной офис)", "contact": "+49 7195 701-0", "website": "https://fessmann.com"}],
        },
        {
            "slug": "kerres",
            "name": "Kerres",
            "country": "Германия",
            "founded_year": 1966,
            "segment": "Profi / Industrial",
            "is_main_competitor": True,
            "recipe_count": 500,
            "warranty_years": 2,
            "has_cloud": True,
            "has_mobile_app": True,
            "has_remote_monitoring": True,
            "has_video_camera": False,
            "base_url": "https://www.kerres-group.de",
            "description": "Kerres Anlagensysteme GmbH (Бакнанг, Германия, 1966) — производитель модульных систем термообработки и моечного оборудования.\nОСНОВНОЕ ОБОРУДОВАНИЕ: универсальные коптильно-варочные системы (промышленные и ремесленные), дымогенераторы, варочные системы, хлебопекарные камеры, системы интенсивного охлаждения, климатические камеры созревания, варочные котлы.\nДРУГОЕ ОБОРУДОВАНИЕ: моечные системы Cleanline KLT для пищевой и непищевой промышленности.\nТехнологии: Hybrid Air Technology, Jet Smoke. Дилеры в 50+ странах, Kerres USA, Китай (Freund MADO).",
            "strengths": ["Jet Smoke технология", "Hybrid Airflow", "Hybrid Air Technology", "Облачная синхронизация", "50+ стран дилеров", "Kerres USA"],
            "weaknesses": ["Высокие цены", "Нет производства в РФ"],
            "models": [
                {"name": "Universal KS 500", "max_load_kg": 500, "modes": ["копчение", "варка", "сушка", "запекание"]},
                {"name": "Universal KS 1000", "max_load_kg": 1000, "modes": ["копчение", "варка", "сушка", "запекание"]},
                {"name": "Universal KS 2000", "max_load_kg": 2000, "modes": ["копчение", "варка", "сушка", "запекание"]},
            ],
            "problems": [],
            "dealers": [
                {"country": "Германия", "company": "Kerres Anlagensysteme GmbH (головной офис)", "contact": "+49 7191 9129-0", "website": "https://kerres-group.de"},
                {"country": "США", "company": "Kerres USA", "website": "https://kerresusa.com"},
                {"country": "Китай", "company": "Freund MADO / Qingdao TLA"},
                {"country": "Международные", "company": "Дилеры в 50+ странах", "website": "https://kerres-group.de"},
            ],
        },
        # P1 — премиум
        {
            "slug": "bastra",
            "name": "Bastra",
            "country": "Германия",
            "founded_year": 1946,
            "segment": "Premium",
            "is_main_competitor": True,
            "base_url": "https://bastra.de",
            "description": "BASTRA GmbH (Арнсберг, Германия, 1946) — семейный производитель, 3-е поколение. Основатели: Gustav Bayha и Theodor Strackbein.\nОСНОВНОЕ ОБОРУДОВАНИЕ: установки BASTRAMAT Classic Line, Industrial Line, BastraSmart 500.\nДРУГОЕ ОБОРУДОВАНИЕ: варочные котлы, дымогенераторы.\nТехнологии: горячее копчение, обжарка, подсушка, варка паром, холодное копчение. Лидер в технологии жидкого дыма. 65 000+ установок в 80+ странах, 100+ патентов. Сайт: bastra.de. Дилеры в 30+ странах.",
            "strengths": ["65 000+ установок в 80+ странах", "100+ патентов", "Лидер liquid smoke", "3 поколения семейный бизнес", "30+ стран дилеров"],
            "weaknesses": ["Высокие цены", "Нет производства в РФ"],
            "models": [],
            "problems": [],
            "dealers": [
                {"country": "Германия", "company": "BASTRA GmbH (головной офис)", "contact": "+49 2932 481-0", "website": "https://bastra.de"},
                {"country": "Международные", "company": "BASTRA International — 30+ стран", "website": "https://bastra.de"},
            ],
        },
        {
            "slug": "sorgo",
            "name": "Sorgo Anlagenbau",
            "country": "Австрия",
            "founded_year": 1986,
            "segment": "Premium",
            "is_main_competitor": True,
            "base_url": "https://www.sorgo.at",
            "description": "Sorgo Anlagenbau GmbH (Клагенфурт, Австрия) — семейное предприятие, 3 поколения опыта. 7 000 м² производство.\nОСНОВНОЕ ОБОРУДОВАНИЕ: универсальные коптильно-варочные камеры, камеры холодного копчения, камеры созревания.\nДРУГОЕ ОБОРУДОВАНИЕ: системы интенсивного охлаждения, компактные системы, непрерывные линии, дымогенераторы (фрикционные).\nДистрибьюторы: Новая Зеландия, Австралия, Чехия, Словакия, Польша, Румыния, Турция, Бельгия, Франция, Италия, Украина, Россия.",
            "strengths": ["3 поколения опыта", "7 000 м² производство", "Премиум качество", "13 стран дистрибуции"],
            "weaknesses": ["Высокие цены", "Нет производства в РФ"],
            "models": [],
            "problems": [],
            "dealers": [
                {"country": "Австрия", "company": "Sorgo Anlagenbau GmbH (головной офис)", "website": "https://sorgo.at"},
                {"country": "Австралия", "company": "Sorgo Australia", "website": "https://sorgo.at"},
                {"country": "Италия", "company": "Sorgo Italia", "website": "https://sorgo.at"},
                {"country": "Новая Зеландия", "company": "Sorgo New Zealand", "website": "https://sorgo.at"},
                {"country": "Польша", "company": "Sorgo Polska", "website": "https://sorgo.at"},
                {"country": "Турция", "company": "Sorgo Turkey", "website": "https://sorgo.at"},
                {"country": "Франция", "company": "Sorgo France", "website": "https://sorgo.at"},
                {"country": "Чехия", "company": "Sorgo Czech", "website": "https://sorgo.at"},
            ],
        },
        # Германия
        {
            "slug": "reich",
            "name": "REICH Thermoprozesstechnik",
            "country": "Германия",
            "founded_year": 1893,
            "segment": "Premium",
            "is_main_competitor": True,
            "base_url": "https://reich-germany.de",
            "description": "REICH Thermoprozesstechnik GmbH (Шехинген, Германия, 1893) — старейший немецкий производитель.\nОСНОВНОЕ ОБОРУДОВАНИЕ: AIRMASTER UKQ AIRJET (флагман), AIRMASTER UK, дымогенераторы.\nДРУГОЕ ОБОРУДОВАНИЕ: BKQ AIRJET (хлебопекарные), IKK/IC INTERCOOLER (интенсивное охлаждение), KK (варочные), KBK (хлебопекарные), KRAI/KKRI/KNRI CLIMASTAR (камеры созревания), ATA ClimaStar (дефростеры), пастеризаторы.\nСистемы: UNICONTROL, BlueConnect (облачный мониторинг). Применение: мясо, колбасы, рыба, птица, сыр, веган, полуфабрикаты, снеки, корма.",
            "strengths": ["Старейший производитель (с 1893)", "AIRMASTER UKQ AIRJET — мировой стандарт", "BlueConnect облачный мониторинг", "Made in Germany", "Полный спектр: от копчения до пастеризации"],
            "weaknesses": ["Очень высокие цены", "Premium сегмент", "Нет производства в РФ"],
            "models": [],
            "problems": [],
            "dealers": [
                {"country": "Германия", "company": "REICH Thermoprozesstechnik GmbH", "contact": "+49 7175 99 790 0", "website": "https://reich-germany.de"},
                {"country": "Германия", "company": "REICH Food Systems (used equipment)", "website": "https://reich-foodsystems.com"},
            ],
        },
        {
            "slug": "sumann",
            "name": "SuMann Korz + Co.",
            "country": "Германия",
            "founded_year": 1910,
            "segment": "Premium",
            "is_main_competitor": False,
            "base_url": "https://suemann.de",
            "description": "SuMann Korz + Co. e.K. (Вальцбахталь, Германия) — немецкий производитель с 114+ лет опыта (основан ~1910).\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильные камеры (Rauchanlagen), варочные системы (Kochanlagen), хлебопекарные камеры (KB 2000, KKB 12, LBK).\nДРУГОЕ ОБОРУДОВАНИЕ: жаровни для целых поросят, тепловые шкафы, дымогенераторы, запчасти.\nТехнологии: низкая потеря веса, низкое энергопотребление, Made in Germany.",
            "strengths": ["114+ лет опыта", "Made in Germany", "Низкое энергопотребление", "Семейное предприятие"],
            "weaknesses": ["Малый размер", "Только Германия"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "vemag",
            "name": "Vemag",
            "country": "Германия",
            "segment": "Industrial",
            "is_main_competitor": False,
            "base_url": "https://vemag.com",
            "description": "Vemag Maschinenbau (Ферден, Германия) — ведущий производитель вакуумных шприцев и формовочного оборудования.\nОСНОВНОЕ ОБОРУДОВАНИЕ (НЕ КОПТИЛЬНИ): вакуумные шприцы, порционирующие устройства, перекрутчики, клипсаторы, линии колбас, формовочные машины.\nВАЖНО: подразделение коптильных камер выделено в 2000 как VEMAG Anlagenbau GmbH, в 2001 продано семье Kruger — сейчас VETEC Anlagenbau GmbH. Vemag НЕ производит коптильные камеры с 2001 года.",
            "strengths": ["Мировой лидер вакуумных шприцев", "Немецкое качество"],
            "weaknesses": ["Не производит коптильни с 2001"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "autotherm",
            "name": "Autotherm",
            "country": "Германия",
            "segment": "Premium",
            "is_main_competitor": False,
            "base_url": "https://autotherm.de",
            "description": "Autotherm GmbH (Ваксвайлер, Германия) — производитель промышленного термообрабатывающего оборудования.\nОСНОВНОЕ ОБОРУДОВАНИЕ: Dampfrauchanlagen (парокоптильные), универсальные коптильные камеры, камеры холодного копчения, системы для копчения рыбы, дымогенераторы.\nДРУГОЕ ОБОРУДОВАНИЕ: варочные системы, хлебопекарные камеры, камеры созревания/климатизации, системы разморозки, системы охлаждения.",
            "strengths": ["Специализация на парокоптильных установках", "Германское качество", "Широкий спектр: от копчения до разморозки"],
            "weaknesses": ["Малый размер", "Ограниченная дилерская сеть"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "germos-ness",
            "name": "GERMOS NESS GmbH & Co. KG",
            "country": "Германия",
            "segment": "Premium",
            "is_main_competitor": False,
            "base_url": "https://germos-ness.de",
            "description": "GERMOS NESS GmbH & Co. KG (Вельцхайм, Германия) — семейное предприятие, более 50 лет на рынке.\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильные камеры (горячее/холодное копчение, 1-14 тележек), дымогенераторы (паровые, фрикционные, тлеющие, жидкого дыма), варочные системы (1-14 тележек), варочные котлы (200-1200л), хлебопекарные камеры, системы интенсивного охлаждения, Compact Climate Unit CCU.\nДРУГОЕ ОБОРУДОВАНИЕ: камеры созревания/сушки (4-100м2), система энергоменеджмента ISO 50001, системы управления GN 22.1/GN 22.2, системы уничтожения дыма.\nУслуги: проектирование, ретрофит, обучение, сервис по всему миру.",
            "strengths": ["50+ лет опыта", "Полный спектр: от 1 до 14 тележек", "CCU — компактная климатическая установка", "Сервис по всему миру", "Ретрофит существующих установок"],
            "weaknesses": ["Нет производства в РФ", "Ограниченная известность на русском рынке"],
            "models": [],
            "problems": [],
            "dealers": [{"country": "Германия", "company": "GERMOS NESS GmbH", "contact": "+49 7182 53195 20", "website": "https://germos-ness.de"}],
        },
        # Австрия
        {
            "slug": "inject-star",
            "name": "Inject Star (Doleschal)",
            "country": "Австрия",
            "segment": "Industrial",
            "is_main_competitor": False,
            "base_url": "https://inject-star.at",
            "description": "Inject Star Maschinenbau GmbH (Хагенбрунн, Австрия) — ведущий производитель оборудования для мясопереработки. Бренды: Inject Star (инъекционные машины) и Doleschal (термические системы).\nОСНОВНОЕ ОБОРУДОВАНИЕ (Inject Star): инъекторы IS-290/300/400/590/600/800, массажеры Magnum-II/EcoGusto, установки извлечения остаточного мяса.\nТЕРМИЧЕСКОЕ ОБОРУДОВАНИЕ (Doleschal): коптильные камеры (Heisrauchanlagen), варочные системы, жарочные/хлебопекарные камеры, интенсивное охлаждение, климатические камеры созревания FMR/FML.\nДРУГОЕ: линии соусов для влажного корма животных. Дистрибьюторы по всему миру.",
            "strengths": ["Два бренда: Inject Star + Doleschal", "Мировой лидер инъекторов", "Полный спектр: от инъекции до термообработки"],
            "weaknesses": ["Основной фокус на инъекторах", "Термокамеры — вторичный продукт"],
            "models": [],
            "problems": [],
            "dealers": [{"country": "Австрия", "company": "Inject Star Maschinenbau GmbH", "contact": "+43 2246 3118", "website": "https://inject-star.at"}],
        },
        # США
        {
            "slug": "jr-manufacturing",
            "name": "J&R Manufacturing",
            "country": "США",
            "founded_year": 1974,
            "segment": "Middle",
            "is_main_competitor": True,
            "base_url": "https://jrmanufacturing.com",
            "description": "J&R Manufacturing (Мекуит, Техас, США, 1974) — американский производитель коммерческих коптилен.\nОСНОВНОЕ ОБОРУДОВАНИЕ: дровяные коптильни Oyler Pit (1300, 700, Electric 1300E, 700E), Smoke-Master, Little Red Smokehouse.\nДРУГОЕ ОБОРУДОВАНИЕ: грили, ротиссери, Offset Smokers для BBQ-соревнований.\nРаботают без присмотра, термостатический контроль. Топливо: дрова/электричество. Made in USA.",
            "strengths": ["Oyler Pit — легендарный бренд", "Made in USA", "Работа без присмотра", "50+ лет опыта (с 1974)"],
            "weaknesses": ["Только BBQ/мясо, нет рыбы/сыра", "Не автоматизированы", "США — основной рынок"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "pro-smoker",
            "name": "Pro Smoker",
            "country": "США",
            "founded_year": 1977,
            "segment": "Middle / Premium",
            "is_main_competitor": False,
            "base_url": "https://pro-smoker.com",
            "description": "Pro Smoker (Woodland Manufacturing Inc.) (Хартфорд, Висконсин, США, 1977) — американский производитель. Семейное предприятие, 3 поколения.\nОСНОВНОЕ ОБОРУДОВАНИЕ: Truckload (загрузка тележками), Handload (ручная загрузка), BBQ Pellet Smokers.\nДРУГОЕ ОБОРУДОВАНИЕ: камеры сухого созревания Reserve 100/300 (dry aging), дымогенераторы, пеллеты/опилки.\nСделано в США. Цифровое управление с WiFi/Bluetooth. Серии: Pro Classic, Pro Max.",
            "strengths": ["Made in USA", "3 поколения семейный бизнес", "Truckload промышленные объемы", "Reserve — камеры сухого созревания"],
            "weaknesses": ["В основном BBQ сегмент", "США — основной рынок"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "cookshack",
            "name": "Cookshack",
            "country": "США",
            "segment": "Middle",
            "is_main_competitor": False,
            "base_url": "https://cookshack.com",
            "description": "Cookshack, Inc. (Понка-Сити, Оклахома, США) — производитель BBQ-оборудования.\nОСНОВНОЕ ОБОРУДОВАНИЕ: электрические и пеллетные коптильни (Smokette Elite, Super Smoker Elite).\nДРУГОЕ ОБОРУДОВАНИЕ: пеллетные грили, чарбройлеры, печи для пиццы на пеллетах, соусы/специи, древесная щепа.",
            "strengths": ["Широкий ассортимент", "BBQ-культура США", "Собственные соусы и специи"],
            "weaknesses": ["Не промышленные объемы", "Только BBQ"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "marlen",
            "name": "Marlen",
            "country": "США",
            "segment": "Industrial",
            "is_main_competitor": False,
            "base_url": "https://marlen.com",
            "description": "Marlen International (Риверсайд, Миссури, США) — глобальный производитель промышленного пищевого оборудования. Часть группы Duravant.\nОСНОВНОЕ ОБОРУДОВАНИЕ: вакуумные шприцы и насосы (Opti 70), порционирующие системы, куттеры/измельчители (DuraKut 6000).\nТЕРМИЧЕСКОЕ ОБОРУДОВАНИЕ: Batch Ovens, Smokehouses, Chillers, Dehydrators, Spiral Ovens, системы обжарки/гриль-маркировки.\nДРУГОЕ: sous-vide линии, пастеризаторы, тумблеры/инъекторы, слайсеры/дайсеры.",
            "strengths": ["Глобальный производитель", "Duravant group", "Полный спектр: от шприцев до термообработки"],
            "weaknesses": ["Основной фокус не на коптильнях", "Очень дорого", "США/Европа — основной рынок"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "mpbs-industries",
            "name": "MPBS Industries",
            "country": "США",
            "segment": "Middle",
            "is_main_competitor": False,
            "base_url": "https://mpbs.com",
            "description": "MPBS Industries (Лос-Анджелес, Калифорния, США) — поставщик оборудования для мясопереработки.\nОСНОВНОЕ: дистрибуция коптильных камер (Smokehouses), вакуумных упаковщиков, клипсаторов, слайсеров, мясорубок, куттеров.\nДРУГОЕ: профессиональные ножи (Victorinox, Dexter Russell), вакуумные пакеты, запчасти, средства гигиены.\nВАЖНО: MPBS — дистрибьютор/ритейлер, а не производитель.",
            "strengths": ["Широкий ассортимент", "Известные бренды в ассортименте", "Онлайн-магазин"],
            "weaknesses": ["Не производитель", "Только дистрибуция", "США — единственный рынок"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        # Россия
        {
            "slug": "agros",
            "name": "AGROS",
            "country": "Россия",
            "segment": "Budget",
            "is_main_competitor": False,
            "base_url": "https://agros.si",
            "description": "Agros (Словения) — производитель коптильного оборудования бюджетного сегмента для малых и средних предприятий.\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильные камеры, варочные котлы.\nДРУГОЕ ОБОРУДОВАНИЕ: дымогенераторы.",
            "strengths": ["Бюджетные цены"],
            "weaknesses": ["Низкое качество", "Минимум сервиса"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        # Китай
        {
            "slug": "helper-food",
            "name": "Shijiazhuang Helper Food Machinery",
            "country": "Китай",
            "segment": "Budget",
            "is_main_competitor": False,
            "base_url": "https://ihelper.en.made-in-china.com",
            "description": "Shijiazhuang Helper Food Machinery (Китай) — производитель бюджетного оборудования для мясопереработки.\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильные камеры.\nДРУГОЕ ОБОРУДОВАНИЕ: мясорубки, куттеры, шприцы, клипсаторы, морозильные камеры, упаковочное оборудование, линии колбас.",
            "strengths": ["Бюджетные цены", "Широкий ассортимент"],
            "weaknesses": ["Низкое качество", "Китай"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
        {
            "slug": "taizy-food",
            "name": "Taizy Food Machine",
            "country": "Китай",
            "segment": "Budget",
            "is_main_competitor": False,
            "base_url": "https://taizyfoodmachine.com",
            "description": "Taizy Food Machine (Китай) — производитель пищевого оборудования бюджетного сегмента.\nОСНОВНОЕ ОБОРУДОВАНИЕ: коптильные камеры, варочные котлы.\nДРУГОЕ ОБОРУДОВАНИЕ: линии колбасного производства, мясорубки, куттеры, шприцы, вакуумные упаковщики, морозильное оборудование.",
            "strengths": ["Бюджетные цены"],
            "weaknesses": ["Низкое качество", "Китай"],
            "models": [],
            "problems": [],
            "dealers": None,
        },
    ]

    result: list[Competitor] = []
    for item in data:
        existing = await session.scalar(
            select(Competitor).where(Competitor.slug == item["slug"])
        )
        if existing:
            result.append(existing)
            continue
        models = item.pop("models", [])
        problems = item.pop("problems", [])
        obj = Competitor(**item)
        for m in models:
            obj.models.append(CompetitorModel(**m))
        for p in problems:
            obj.problems.append(CompetitorProblem(**p))
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def seed_demo_users(session) -> list[User]:
    data = [
        {"email": "admin@feleti.by", "username": "admin", "full_name": "Администратор",
         "hashed_password": hash_password("admin"), "role": UserRole.ADMIN,
         "is_superuser": True},
        {"email": "tech@feleti.by", "username": "technologist", "full_name": "Технолог",
         "hashed_password": hash_password("tech"), "role": UserRole.TECHNOLOGIST},
        {"email": "operator@feleti.by", "username": "operator", "full_name": "Оператор",
         "hashed_password": hash_password("operator"), "role": UserRole.OPERATOR},
    ]
    result: list[User] = []
    for item in data:
        existing = await session.scalar(
            select(User).where(User.email == item["email"])
        )
        if existing:
            result.append(existing)
            continue
        obj = User(**item)
        session.add(obj)
        result.append(obj)
    await session.flush()
    return result


async def run_seed() -> None:
    logger.info("=== FELETI-SMOK: seed start ===")
    async with AsyncSessionLocal() as session:
        try:
            manufacturers = await seed_manufacturers(session)
            logger.info("Manufacturers: %s", len(manufacturers))

            chambers = await seed_chambers(session, manufacturers)
            logger.info("Chambers: %s", len(chambers))

            ingredients = await seed_ingredients(session)
            logger.info("Ingredients: %s", len(ingredients))

            products = await seed_products(session)
            logger.info("Products: %s", len(products))

            users = await seed_demo_users(session)
            logger.info("Users: %s", len(users))

            competitors = await seed_competitors(session)
            logger.info("Competitors: %s", len(competitors))

            await session.commit()
            logger.info("=== seed committed ===")
        except Exception:
            await session.rollback()
            logger.exception("Seed failed, rolled back")
            raise
    await engine.dispose()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run_seed())
