# SKILL: pdf-report

> Генерация PDF отчётов: ТТК, акты КК, журналы партий, калькуляции себестоимости. Используй при создании экспорта документов.

## 1. Типы отчётов

| Отчёт | Содержание | Когда генерировать |
|---|---|---|
| **ТТК** (технико-технологическая карта) | Рецепт, фазы, ингредиенты, БЖУ, хранение | По кнопке из карточки рецепта |
| **Акт КК** | Органолептика, лаборатория, дефекты, решение | После проверки партии |
| **Журнал партии** | Телеметрия, фазы, события, фото | После завершения партии |
| **Калькуляция себестоимости** | Сырьё, ингредиенты, yield, итог за кг | По кнопке из рецепта |
| **Отчёт за смену** | Список партий, выход, дефекты, OEE | По окончании смены |
| **Сравнение партий** | 2+ партий, графики, различия | Аналитика |

## 2. Библиотека

Используем **ReportLab** (уже в `pyproject.toml`):
```python
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрация шрифта с кириллицей
pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
```

## 3. Пример: ТТК

```python
# backend/app/services/report.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

async def generate_ttk(recipe: Recipe, version: RecipeVersion) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []
    
    # Заголовок
    story.append(Paragraph(f"ТТК: {recipe.name}", styles['Heading1']))
    story.append(Paragraph(f"Версия: {version.version_number} | ГОСТ: {version.gost or '—'}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    # Ингредиенты
    story.append(Paragraph("Ингредиенты:", styles['Heading2']))
    ing_data = [["Ингредиент", "Масса, кг", "%"]]
    for ing in version.ingredients:
        ing_data.append([ing['name'], str(ing.get('mass_kg', '-')),
                        f"{ing.get('percent', 0)}%"])
    ing_table = Table(ing_data, colWidths=[8*cm, 3*cm, 3*cm])
    ing_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    story.append(ing_table)
    story.append(Spacer(1, 0.5*cm))
    
    # Программа копчения
    story.append(Paragraph("Программа копчения:", styles['Heading2']))
    prog_data = [["Фаза", "t°C", "Влажность", "Дым", "Время"]]
    for phase in version.program:
        prog_data.append([
            phase.get('name', '—'),
            str(phase.get('t_chamber', '—')),
            f"{phase.get('humidity', '—')}%",
            phase.get('smoke', 'none'),
            f"{phase.get('duration_min', '—')} мин",
        ])
    prog_table = Table(prog_data, colWidths=[4*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
    prog_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))
    story.append(prog_table)
    
    # БЖУ
    if version.bju_per_100g:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("БЖУ (на 100 г):", styles['Heading2']))
        bju = version.bju_per_100g
        story.append(Paragraph(
            f"Белки: {bju['protein']} г | Жиры: {bju['fat']} г | "
            f"Углеводы: {bju['carbs']} г | Ккал: {bju['kcal']}",
            styles['Normal']
        ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer.read()
```

## 4. Endpoint

```python
# backend/app/api/v1/endpoints/reports.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/recipes/{recipe_id}/ttk.pdf")
async def download_ttk(
    recipe_id: int,
    db: DBSession,
    user: CurrentUser,
):
    recipe = await get_recipe(db, recipe_id)
    version = recipe.current_version
    pdf_bytes = await generate_ttk(recipe, version)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=ttk_{recipe.slug}.pdf"}
    )
```

## 5. Frontend: кнопка скачивания

```tsx
// components/reports/download-button.tsx
export function DownloadTTKButton({ recipeId }: { recipeId: number }) {
  const handleDownload = async () => {
    const response = await api.get(`/reports/recipes/${recipeId}/ttk.pdf`, {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `ttk_${recipeId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <Button variant="outline" onClick={handleDownload}>
      <FileDown className="mr-2 h-4 w-4" />
      Скачать ТТК (PDF)
    </Button>
  );
}
```

## 6. Чек-лист

- [ ] PDF содержит логотип FELETI
- [ ] Шрифт с кириллицей (DejaVu или аналог)
- [ ] Таблицы с границами и заголовками
- [ ] Номера страниц
- [ ] Дата генерации
- [ ] Footer с "FELETI-SMOK © 2026"
- [ ] Файл именован понятно (`ttk_doktorskaya_v3_20260603.pdf`)

## 7. Связь с другими скиллами

- `add-recipe` — данные рецепта
- `recipe-calc` — БЖУ, себестоимость
- `quality-control` — акт КК
- `batch-monitoring` — журнал партии
- `smoke-platform` — общие правила

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при создании PDF-экспорта.
