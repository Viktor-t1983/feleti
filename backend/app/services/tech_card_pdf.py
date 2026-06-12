"""PDF-генератор технологической карты (tech card)."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

# --- Register fonts ---
for fname, alias in [
    ("DejaVuSans.ttf", "DejaVu"),
    ("DejaVuSans-Bold.ttf", "DejaVu-Bold"),
    ("DejaVuSans-Oblique.ttf", "DejaVu-Italic"),
    ("DejaVuSans-BoldOblique.ttf", "DejaVu-BoldItalic"),
]:
    path = os.path.join(_FONTS_DIR, fname)
    if os.path.exists(path):
        pdfmetrics.registerFont(TTFont(alias, path))

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 2 * cm

# --- Styles ---
styles = getSampleStyleSheet()

COLOR_PRIMARY = colors.HexColor("#1a1a2e")
COLOR_ACCENT = colors.HexColor("#b8860b")  # feleti-gold
COLOR_MUTED = colors.HexColor("#666666")
COLOR_BG = colors.HexColor("#f8f8f8")
COLOR_BORDER = colors.HexColor("#cccccc")


def _s(name: str, **kw) -> ParagraphStyle:
    defaults = {"fontName": "DejaVu", "fontSize": 9, "leading": 13, "spaceAfter": 4}
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)


style_title = _s("Title", fontName="DejaVu-Bold", fontSize=18, leading=24, alignment=TA_CENTER, spaceAfter=2, textColor=COLOR_PRIMARY)
style_subtitle = _s("Subtitle", fontSize=11, leading=15, alignment=TA_CENTER, spaceAfter=12, textColor=COLOR_MUTED)
style_section = _s("Section", fontName="DejaVu-Bold", fontSize=12, leading=16, spaceBefore=12, spaceAfter=6, textColor=COLOR_ACCENT, borderWidth=0, borderColor=COLOR_ACCENT, borderPadding=4)
style_label = _s("Label", fontName="DejaVu-Bold", fontSize=8, leading=11, textColor=COLOR_MUTED)
style_value = _s("Value", fontSize=9, leading=13)
style_small = _s("Small", fontSize=7, leading=10, textColor=COLOR_MUTED)
style_footer = _s("Footer", fontSize=7, leading=10, alignment=TA_CENTER, textColor=COLOR_MUTED)
style_cell = _s("Cell", fontSize=8, leading=11)
style_cell_bold = _s("CellBold", fontName="DejaVu-Bold", fontSize=8, leading=11)
style_header_cell = _s("HeaderCell", fontName="DejaVu-Bold", fontSize=8, leading=11, textColor=colors.white)


class TechCardPDF:
    """Генератор технологической карты."""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    def _header(self) -> list:
        elements = []
        elements.append(Spacer(1, 0.5 * cm))
        elements.append(Paragraph("ТЕХНОЛОГИЧЕСКАЯ КАРТА", style_title))
        elements.append(Paragraph(f"на производство: {self.data.get('product_name', '')}", style_subtitle))
        elements.append(Spacer(1, 0.3 * cm))
        return elements

    def _meta_block(self) -> list:
        meta = self.data.get("meta", {})
        rows = []
        labels = [
            ("Наименование продукции", meta.get("product_name", "")),
            ("Код ОКП", meta.get("okp", "")),
            ("Номер рецептуры", meta.get("recipe_number", "")),
            ("ГОСТ / ТУ", meta.get("gost", "")),
            ("Предприятие-разработчик", meta.get("developer", "")),
            ("Дата разработки", meta.get("date", "")),
        ]
        for label, value in labels:
            rows.append([
                Paragraph(label, style_label),
                Paragraph(str(value), style_value),
            ])

        col_w = [5 * cm, 10 * cm]
        t = Table(rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        return [t, Spacer(1, 0.3 * cm)]

    def _ingredients_table(self) -> list:
        ings = self.data.get("ingredients", [])
        if not ings:
            return [Spacer(1, 0.1 * cm)]

        header = ["№", "Наименование сырья", "Масса, кг", "Белки, г", "Жиры, г", "Углеводы, г", "Ккал", "Цена, руб"]
        col_w = [0.6 * cm, 6 * cm, 1.8 * cm, 1.5 * cm, 1.3 * cm, 1.5 * cm, 1.3 * cm, 1.5 * cm]
        col_w = [c * 0.9 for c in col_w]

        hdr = [Paragraph(h, style_header_cell) for h in header]
        body = [hdr]

        for i, ing in enumerate(ings, 1):
            row = [
                Paragraph(str(i), style_cell),
                Paragraph(ing.get("name", ""), style_cell),
                Paragraph(f"{ing.get('mass_kg', 0):.3f}", style_cell),
                Paragraph(f"{ing.get('protein', 0):.1f}", style_cell),
                Paragraph(f"{ing.get('fat', 0):.1f}", style_cell),
                Paragraph(f"{ing.get('carbs', 0):.1f}", style_cell),
                Paragraph(f"{ing.get('kcal', 0):.1f}", style_cell),
                Paragraph(f"{ing.get('cost', 0):.2f}", style_cell),
            ]
            body.append(row)

        t = Table(body, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [Paragraph("Сырьё и ингредиенты", style_section), t, Spacer(1, 0.2 * cm)]

    def _program_table(self) -> list:
        program = self.data.get("program", [])
        if not program:
            return [Spacer(1, 0.1 * cm)]

        header = ["Фаза", "Наименование этапа", "T камеры, °C", "T продукта, °C", "Длит., мин", "Дым", "Электро, кВ"]
        col_w = [0.8 * cm, 5.5 * cm, 2.2 * cm, 2.2 * cm, 1.8 * cm, 1.3 * cm, 1.5 * cm]
        col_w = [c * 0.85 for c in col_w]

        hdr = [Paragraph(h, style_header_cell) for h in header]
        body = [hdr]

        for phase in program:
            row = [
                Paragraph(str(phase.get("index", "")), style_cell),
                Paragraph(phase.get("name", ""), style_cell),
                Paragraph(str(phase.get("t_chamber", "") or ""), style_cell),
                Paragraph(str(phase.get("t_product", "") or ""), style_cell),
                Paragraph(str(phase.get("duration_min", "") or ""), style_cell),
                Paragraph(phase.get("smoke", ""), style_cell),
                Paragraph(str(phase.get("electro_voltage_kv", "") or ""), style_cell),
            ]
            body.append(row)

        t = Table(body, colWidths=col_w, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [Paragraph("Программа копчения", style_section), t, Spacer(1, 0.2 * cm)]

    def _calc_table(self) -> list:
        calc = self.data.get("calculation", {})
        if not calc:
            return [Spacer(1, 0.1 * cm)]

        rows = [
            [Paragraph("Показатель", style_label), Paragraph("Значение", style_label)],
        ]
        labels_map = [
            ("total_mass_kg", "Масса сырья, кг"),
            ("finished_mass_kg", "Масса готового продукта, кг"),
            ("losses_percent", "Потери, %"),
            ("cost_per_kg_raw", "Себестоимость сырья, руб/кг"),
            ("cost_per_kg_finished", "Себестоимость готового, руб/кг"),
            ("total_cost", "Общая стоимость, руб"),
        ]
        for key, label in labels_map:
            v = calc.get(key)
            if v is not None:
                rows.append([
                    Paragraph(label, style_cell),
                    Paragraph(f"{v:.2f}" if isinstance(v, float) else str(v), style_cell_bold),
                ])

        bju = calc.get("bju_per_100g", {})
        if bju:
            rows.append([Paragraph("Белки (на 100 г), г", style_cell), Paragraph(str(bju.get("protein", "")), style_cell_bold)])
            rows.append([Paragraph("Жиры (на 100 г), г", style_cell), Paragraph(str(bju.get("fat", "")), style_cell_bold)])
            rows.append([Paragraph("Углеводы (на 100 г), г", style_cell), Paragraph(str(bju.get("carbs", "")), style_cell_bold)])
            rows.append([Paragraph("Калорийность (на 100 г), ккал", style_cell), Paragraph(str(bju.get("kcal", "")), style_cell_bold)])

        col_w = [7 * cm, 3 * cm]
        t = Table(rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ]))
        return [Paragraph("Расчётные характеристики", style_section), t, Spacer(1, 0.2 * cm)]

    def _storage_block(self) -> list:
        storage = self.data.get("storage", {})
        if not storage:
            return [Spacer(1, 0.1 * cm)]

        rows = [
            [Paragraph("Условия хранения", style_label), Paragraph("", style_value)],
        ]
        labels_map = [
            ("shelf_life_days", "Срок годности, сут"),
            ("storage_temp", "Температура хранения, °C"),
            ("storage_humidity", "Относительная влажность, %"),
        ]
        for key, label in labels_map:
            v = storage.get(key)
            if v is not None:
                rows.append([Paragraph(label, style_cell), Paragraph(str(v), style_cell)])

        if len(rows) <= 1:
            return [Spacer(1, 0.1 * cm)]

        col_w = [7 * cm, 3 * cm]
        t = Table(rows, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ]))
        return [Paragraph("Условия хранения", style_section), t, Spacer(1, 0.2 * cm)]

    def _notes_block(self) -> list:
        notes = self.data.get("notes", "")
        if not notes:
            return [Spacer(1, 0.1 * cm)]

        return [Paragraph("Примечания", style_section), Paragraph(notes, style_value), Spacer(1, 0.2 * cm)]

    def _footer(self) -> list:
        return [
            Spacer(1, 1 * cm),
            Table(
                [
                    [
                        Paragraph("Технолог: ___________________", style_small),
                        Paragraph(f"Дата: {datetime.now().strftime('%d.%m.%Y')}", style_small),
                    ]
                ],
                colWidths=[8 * cm, 5 * cm],
            ),
            Spacer(1, 0.3 * cm),
            Paragraph(
                "ФЕЛЕТИ-СМОК — Система управления знаниями коптильного производства",
                style_small,
            ),
        ]

    def _draw_page_border(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(COLOR_ACCENT)
        canvas.setLineWidth(0.5)
        canvas.rect(MARGIN, MARGIN, PAGE_WIDTH - 2 * MARGIN, PAGE_HEIGHT - 2 * MARGIN)
        canvas.setFillColor(COLOR_PRIMARY)
        canvas.setFont("DejaVu", 6)
        canvas.drawCentredString(PAGE_WIDTH / 2, MARGIN / 2, f"Страница {doc.page}")
        canvas.setFillColor(COLOR_ACCENT)
        canvas.setFont("DejaVu-Bold", 7)
        canvas.drawString(MARGIN, PAGE_HEIGHT - MARGIN + 0.3 * cm, "FELETI-SMOK")
        canvas.drawRightString(PAGE_WIDTH - MARGIN, PAGE_HEIGHT - MARGIN + 0.3 * cm, "Технологическая карта")
        canvas.restoreState()

    def build(self, output_path: str | None = None) -> bytes:
        buf = output_path is None
        doc = SimpleDocTemplate(
            output_path if output_path else "buf.pdf",
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN + 0.5 * cm,
            bottomMargin=MARGIN + 0.5 * cm,
            title="Технологическая карта",
            author="FELETI-SMOK",
        )

        elements: list = []
        elements.extend(self._header())
        elements.append(Spacer(1, 0.3 * cm))
        elements.extend(self._meta_block())
        elements.extend(self._ingredients_table())
        elements.extend(self._program_table())
        elements.extend(self._calc_table())
        elements.extend(self._storage_block())
        elements.extend(self._notes_block())
        elements.extend(self._footer())

        if buf:
            import io
            buf = io.BytesIO()
            doc = SimpleDocTemplate(
                buf,
                pagesize=A4,
                leftMargin=MARGIN,
                rightMargin=MARGIN,
                topMargin=MARGIN + 0.5 * cm,
                bottomMargin=MARGIN + 0.5 * cm,
                title="Технологическая карта",
                author="FELETI-SMOK",
            )
            doc.build(elements, onFirstPage=self._draw_page_border, onLaterPages=self._draw_page_border)
            return buf.getvalue()
        else:
            doc.build(elements, onFirstPage=self._draw_page_border, onLaterPages=self._draw_page_border)
            return b""


def build_tech_card(data: dict) -> bytes:
    return TechCardPDF(data).build()
