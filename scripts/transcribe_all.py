#!/usr/bin/env python3
"""
Транскрибация всех аудио-файлов Ижицы.
Использует faster-whisper tiny на CPU (17x real-time на i5-10300H).
Оценка: 38 часов аудио = ~2.3 часа обработки.
"""

import json
import time
from pathlib import Path

from faster_whisper import WhisperModel

# Конфигурация
AUDIO_DIR = Path("docs/research/ijiza/youtube/audio")
TRANSCRIPTS_DIR = Path("docs/research/ijiza/youtube/transcripts")
SUMMARY_FILE = Path("docs/research/ijiza/youtube/summary.json")
METADATA_FILE = Path("docs/research/ijiza/youtube/videos.json")


def extract_structured_info(video_id: str, title: str, transcript: str) -> dict:
    """Извлечение структурированной информации из транскрипта."""
    info = {
        "video_id": video_id,
        "title": title,
        "products_mentioned": [],
        "technologies_mentioned": [],
        "problems_mentioned": [],
        "recipes_mentioned": [],
        "equipment_mentioned": [],
        "has_recipe_details": False,
        "has_program_details": False,
        "has_problem_details": False,
        "has_business_info": False,
    }
    
    # Продукты
    products = [
        "скумбрия", "сельдь", "форель", "палтус", "ставрида", "мойва", "окунь",
        "лосось", "семга", "горбуша", "лещ", "треска", "сом", "щука",
        "сало", "грудинка", "шейка", "окорок", "рулька", "буженина", 
        "карбонат", "балык", "пашина", "подчеревок",
        "колбаса", "сосиска", "сардельки", "ветчина", "бекон", "пастрома",
        "сервелат", "салями", "шпек", "шинка",
        "курица", "утка", "гусь", "индейка", "перепел", "цыпленок",
        "сыр", "чечил", "косичка", "копченый сыр", "адегейский",
        "оленина", "косуля", "кабан", "дичь",
        "мясные чипсы", "снеки", "джерки",
    ]
    
    # Технологии
    technologies = [
        "электростатическое копчение", "холодное копчение", "горячее копчение",
        "сушка", "варка", "запекание", "жарка", "проветривание", "прогрев",
        "влажность", "температура", "время копчения", "режим копчения",
        "дымогенератор", "щепа", "ольха", "бук", "черешня", "яблоня", 
        "фруктовые породы", "ольховая", "буковая",
        "оболочка", "натуральная оболочка", "искусственная оболочка",
        "пряжка", "коллагеновая оболочка", "фиброузная оболочка",
        "посол", "соление", "маринование", "засолка", "тузлук",
        "сушильно-вялочная", "термокамера", "электростатика",
        "инъектор", "шприц", "ручной посол", "сухой посол", "мокрый посол",
        "конденсат", "барьер", "пленка", "вакуум",
    ]
    
    # Проблемы
    problems = [
        "пересушивание", "перекопчение", "недокопчение", "сухой", "жесткий",
        "трещины", "плесень", "конденсат", "капли", "желтый", "серый", "белый налет",
        "электростатика", "статика", "изолятор", "дым", "шибер", "вентилятор",
        "поломка", "ремонт", "чистка", "зольник", "нагар", "копоть",
        "перегрев", "недогрев", "вспенивание", "вспучивание",
    ]
    
    # Оборудование
    equipment = [
        "varmen", "ижица", "z115", "z115a", "dl400", "dl450", "ф10", "ф15",
        "дымогенератор", "камера", "коптильня", "термокамера", "сушилка",
        "панель управления", "контроллер", "датчик", "тэн", "вентилятор",
        "сетка", "клеть", "тележка", "вагонетка",
    ]
    
    text_lower = transcript.lower()
    
    for p in products:
        if p in text_lower:
            info["products_mentioned"].append(p)
    
    for t in technologies:
        if t in text_lower:
            info["technologies_mentioned"].append(t)
    
    for p in problems:
        if p in text_lower:
            info["problems_mentioned"].append(p)
    
    for e in equipment:
        if e in text_lower:
            info["equipment_mentioned"].append(e)
    
    # Убираем дубликаты
    info["products_mentioned"] = list(set(info["products_mentioned"]))
    info["technologies_mentioned"] = list(set(info["technologies_mentioned"]))
    info["problems_mentioned"] = list(set(info["problems_mentioned"]))
    info["equipment_mentioned"] = list(set(info["equipment_mentioned"]))
    
    # Проверка на детали
    if any(x in text_lower for x in ["градус", "°c", "°с", "градусов", "температура"]):
        info["has_recipe_details"] = True
    if "шаг" in text_lower and any(x in text_lower for x in ["программ", "этап", "фаза"]):
        info["has_program_details"] = True
    if any(x in text_lower for x in ["проблем", "поломк", "не работает", "ошибк", "сложност"]):
        info["has_problem_details"] = True
    if any(x in text_lower for x in ["бизнес", "заработок", "прибыль", "себестоимость", "окупаемость", "цена", "стоимость"]):
        info["has_business_info"] = True
    
    return info


def main():
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    
    if not METADATA_FILE.exists():
        print("ERROR: No videos.json found.")
        return
    
    videos = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    
    # Формируем список файлов
    tasks = []
    for v in videos:
        video_id = v["id"]
        audio_path = AUDIO_DIR / f"{video_id}.webm"
        if not audio_path.exists():
            audio_path = AUDIO_DIR / f"{video_id}.m4a"
        if not audio_path.exists():
            audio_path = AUDIO_DIR / f"{video_id}.mp3"
        if not audio_path.exists():
            continue
        tasks.append((video_id, audio_path, v["title"]))
    
    print(f"Total files: {len(tasks)}")
    print(f"Model: faster-whisper tiny (CPU, int8)")
    print("=" * 60)
    
    # Загружаем модель
    print("Loading model...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("Model loaded. Starting transcription...")
    print("=" * 60)
    
    results = []
    done = 0
    skipped = 0
    errors = 0
    start_time = time.time()
    
    for video_id, audio_path, title in tasks:
        transcript_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
        
        if transcript_path.exists():
            skipped += 1
            done += 1
            results.append({
                "video_id": video_id,
                "title": title,
                "status": "skipped",
                "chars": len(transcript_path.read_text(encoding="utf-8")),
            })
            continue
        
        try:
            segments, info = model.transcribe(str(audio_path), language="ru", beam_size=1)
            
            # Формат с таймкодами
            lines = []
            for seg in segments:
                start = time.strftime("%H:%M:%S", time.gmtime(seg.start))
                end = time.strftime("%H:%M:%S", time.gmtime(seg.end))
                lines.append(f"[{start} --> {end}] {seg.text}")
            
            transcript = "\n".join(lines)
            transcript_path.write_text(transcript, encoding="utf-8")
            
            results.append({
                "video_id": video_id,
                "title": title,
                "status": "done",
                "chars": len(transcript),
                "duration": info.duration,
            })
            done += 1
            
        except Exception as e:
            errors += 1
            done += 1
            results.append({
                "video_id": video_id,
                "title": title,
                "status": "error",
                "error": str(e),
            })
        
        # Прогресс каждые 5 файлов
        if done % 5 == 0:
            elapsed = time.time() - start_time
            rate = done / (elapsed / 60) if elapsed > 0 else 0
            eta_min = (len(tasks) - done) / rate if rate > 0 else 0
            print(f"Progress: {done}/{len(tasks)} | {rate:.1f} files/min | ETA: {eta_min:.0f} min | Errors: {errors}")
    
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"DONE: {done}/{len(tasks)} in {elapsed/60:.1f} min")
    print(f"Skipped: {skipped}, Errors: {errors}")
    
    # Извлекаем структурированную информацию
    print("\nExtracting structured info...")
    structured_results = []
    
    for result in results:
        if result["status"] not in ("done", "skipped"):
            continue
        
        video_id = result["video_id"]
        transcript_path = TRANSCRIPTS_DIR / f"{video_id}.txt"
        
        if transcript_path.exists():
            transcript = transcript_path.read_text(encoding="utf-8")
            info = extract_structured_info(video_id, result["title"], transcript)
            structured_results.append(info)
    
    # Сохраняем сводку
    SUMMARY_FILE.write_text(
        json.dumps(structured_results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Summary saved: {SUMMARY_FILE}")
    
    # Статистика
    all_products = set()
    all_technologies = set()
    all_problems = set()
    all_equipment = set()
    
    for r in structured_results:
        all_products.update(r["products_mentioned"])
        all_technologies.update(r["technologies_mentioned"])
        all_problems.update(r["problems_mentioned"])
        all_equipment.update(r["equipment_mentioned"])
    
    print("\n" + "=" * 60)
    print("STATISTICS:")
    print(f"  Products: {len(all_products)}")
    print(f"  Technologies: {len(all_technologies)}")
    print(f"  Problems: {len(all_problems)}")
    print(f"  Equipment: {len(all_equipment)}")
    print(f"  Total transcript chars: {sum(r.get('chars', 0) for r in results):,}")
    
    # Сохраняем отчет в markdown
    report_path = Path("docs/research/ijiza/youtube/REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# YouTube-анализ Ижицы — Отчет\n\n")
        f.write(f"**Дата:** {time.strftime('%Y-%m-%d')}\n")
        f.write(f"**Всего видео:** {len(structured_results)}\n")
        f.write(f"**Время обработки:** {elapsed/60:.0f} мин\n\n")
        
        f.write("## Найденные продукты\n\n")
        for p in sorted(all_products):
            f.write(f"- {p}\n")
        
        f.write("\n## Найденные технологии\n\n")
        for t in sorted(all_technologies):
            f.write(f"- {t}\n")
        
        f.write("\n## Найденные проблемы\n\n")
        for p in sorted(all_problems):
            f.write(f"- {p}\n")
        
        f.write("\n## Упомянутое оборудование\n\n")
        for e in sorted(all_equipment):
            f.write(f"- {e}\n")
        
        f.write("\n## Видео с деталями\n\n")
        for r in structured_results:
            if r["has_recipe_details"] or r["has_program_details"] or r["has_problem_details"]:
                flags = []
                if r["has_recipe_details"]: flags.append("рецепт")
                if r["has_program_details"]: flags.append("программа")
                if r["has_problem_details"]: flags.append("проблемы")
                if r["has_business_info"]: flags.append("бизнес")
                f.write(f"- [{r['video_id']}] {r['title']} — {', '.join(flags)}\n")
    
    print(f"\nReport saved: {report_path}")


if __name__ == "__main__":
    main()
