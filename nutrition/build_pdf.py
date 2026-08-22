# -*- coding: utf-8 -*-
"""Сборка PDF протокола питания БГБКБС."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, KeepTogether,
                                CondPageBreak)
import plan_data as D

FDIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DJ", os.path.join(FDIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DJ-B", os.path.join(FDIR, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B",
                              italic="DJ", boldItalic="DJ-B")

DARK   = HexColor("#1F3864")
HEAD   = HexColor("#2E5C8A")
BAND   = HexColor("#EAF0F7")
ACCENT = HexColor("#FFF2CC")
GREEN  = HexColor("#DDF0E0")
RED    = HexColor("#F8D7DA")
LINE   = HexColor("#B7C6D9")
GREY   = HexColor("#44546A")

PW, PH = A4
LM = RM = 15 * mm
TM = 16 * mm
BM = 16 * mm
CW = PW - LM - RM          # рабочая ширина ≈ 180 мм

S = lambda **kw: ParagraphStyle(**kw)
st_h1    = S(name="h1", fontName="DJ-B", fontSize=17, leading=21, textColor=DARK,
             spaceAfter=2)
st_sub   = S(name="sub", fontName="DJ", fontSize=10, leading=14, textColor=GREY,
             spaceAfter=8)
st_h2    = S(name="h2", fontName="DJ-B", fontSize=13, leading=16, textColor=white,
             spaceBefore=0, spaceAfter=0)
st_h3    = S(name="h3", fontName="DJ-B", fontSize=11, leading=14, textColor=DARK,
             spaceBefore=6, spaceAfter=4)
st_body  = S(name="body", fontName="DJ", fontSize=9.5, leading=13.5, alignment=TA_LEFT,
             spaceAfter=5)
st_note  = S(name="note", fontName="DJ", fontSize=8.5, leading=11.5, textColor=GREY,
             spaceBefore=3, spaceAfter=6)
st_th    = S(name="th", fontName="DJ-B", fontSize=8.5, leading=11, textColor=white,
             alignment=TA_CENTER)
st_td    = S(name="td", fontName="DJ", fontSize=8.5, leading=11.2)
st_tdb   = S(name="tdb", fontName="DJ-B", fontSize=8.5, leading=11.2)
st_tdc   = S(name="tdc", fontName="DJ", fontSize=8.5, leading=11.2, alignment=TA_CENTER)
st_th_sm = S(name="thsm", fontName="DJ-B", fontSize=7.5, leading=9.5, textColor=white,
             alignment=TA_CENTER)
st_td_sm = S(name="tdsm", fontName="DJ", fontSize=8, leading=10.4)
st_tdc_sm= S(name="tdcsm", fontName="DJ", fontSize=8, leading=10.4, alignment=TA_CENTER)


def P(t, s=st_td):
    return Paragraph(str(t).replace("\n", "<br/>"), s)


def band(title):
    """Тёмная плашка-заголовок раздела на всю ширину."""
    t = Table([[Paragraph(title, st_h2)]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def grid(header, rows, widths, bold_first=False, center_cols=(), repeat=True,
         small_head_cols=(), compact=False):
    td = st_td_sm if compact else st_td
    tdc = st_tdc_sm if compact else st_tdc
    pad = 3 if compact else 3.5
    data = [[P(h, st_th_sm if i in small_head_cols else st_th)
             for i, h in enumerate(header)]]
    for r in rows:
        line = []
        for i, v in enumerate(r):
            if i in center_cols:
                line.append(P(v, tdc))
            elif bold_first and i == 0:
                line.append(P(v, st_tdb))
            else:
                line.append(P(v, td))
        data.append(line)
    t = Table(data, colWidths=widths, repeatRows=1 if repeat else 0)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), HEAD),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(style))
    return t


def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("DJ", 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(LM, 9 * mm, "Питание БГБКБС · без сахара, без глютена, без молочки")
    canvas.drawRightString(PW - RM, 9 * mm, "стр. %d" % canvas.getPageNumber())
    canvas.setStrokeColor(LINE)
    canvas.setLineWidth(0.5)
    canvas.line(LM, 12 * mm, PW - RM, 12 * mm)
    canvas.restoreState()


story = []
A = story.append

# ═══════════════════════════════════ ТИТУЛ
A(Paragraph(D.TITLE, st_h1))
A(Paragraph(D.SUBTITLE + ". " + D.SOURCE, st_sub))

A(band("ГЛАВНОЕ ПРАВИЛО ДНЯ"))
A(Spacer(1, 4))
A(grid(D.PRINCIPLE_HEAD, D.PRINCIPLE, [CW * .17, CW * .48, CW * .35], bold_first=True))
A(Paragraph("Это весь протокол в трёх строчках. Всё остальное — детали.", st_note))

A(Spacer(1, 6))
A(band("ЧТО ОБЯЗАТЕЛЬНО КАЖДЫЙ ДЕНЬ"))
A(Spacer(1, 4))
must = [
    ["КЛЕТЧАТКА", "В каждый приём пищи",
     "Овощи отварные или ошпаренные. Сырыми — только огурец и зелень"],
    ["СОРБЕНТ — псиллиум", "Между приёмами: за 2 ч до еды или через 2 ч после",
     "1 ст. л. на стакан воды, сверху запить ещё стаканом. Отдельно от еды и БАДов"],
    ["ТРАВКИ", "После каждого приёма пищи",
     "Укроп и семя укропа, фенхель, анис, тмин, имбирь, куркума, кинза, солодка, шиповник"],
    ["Масло пшеничных зародышей — витамин Е", "Сразу после завтрака",
     "1 ч. л. Только с едой, не натощак"],
    ["Витамин А", "С завтраком, из еды",
     "Желток, печень индейки, морковь, тыква, шпинат — обязательно вместе с жиром"],
    ["Омега-3 — 1600 мг", "Завтрак и обед", "С едой, 2 раза в день"],
    ["Цинк — 25 мг", "Утром сразу после завтрака", "Или на обед — выбрать один приём"],
    ["Витамин С — 1000 мг", "Между приёмами пищи", "С биофлавоноидами"],
    ["ВОДА", "В течение дня", "30 мл на кг веса. Например: 60 кг → 1,8 л"],
]
A(grid(["Что", "Когда", "Как"], must, [CW * .28, CW * .30, CW * .42], bold_first=True))

# ═══════════════════════════════════ СХЕМА ДНЯ
A(CondPageBreak(150))
A(Spacer(1, 10))
A(band("СХЕМА ДНЯ — весь день по часам"))
A(Spacer(1, 4))
A(Paragraph("Время ориентировочное: важны не часы, а порядок и промежутки в 2 часа "
            "вокруг сорбента.", st_note))
tbl = grid(D.DAY_HEAD, D.DAY_SCHEDULE, [CW * .13, CW * .40, CW * .47], bold_first=True)
extra = []
for i, row_data in enumerate(D.DAY_SCHEDULE, start=1):
    txt = row_data[1]
    if txt.startswith(("ЗАВТРАК", "ОБЕД", "УЖИН")):
        extra.append(("BACKGROUND", (0, i), (-1, i), GREEN))
    elif "ПСИЛЛИУМ" in txt:
        extra.append(("BACKGROUND", (0, i), (-1, i), ACCENT))
tbl.setStyle(TableStyle(extra))
A(tbl)
A(Paragraph(D.HERBS_NOTE, st_note))

A(Spacer(1, 6))
A(Paragraph("Дополнительно из базы — по согласованию, в основную схему не входит", st_h3))
A(grid(D.EXTRA_HEAD, D.EXTRA, [CW * .35, CW * .25, CW * .40], bold_first=True))
A(Paragraph(D.EXTRA_NOTE, st_note))

# ═══════════════════════════════════ МЕНЮ
A(CondPageBreak(150))
A(Spacer(1, 10))
A(band("МЕНЮ НА 7 ДНЕЙ"))
A(Spacer(1, 4))
A(Paragraph("Без сахара · без глютена · без молочки · без курицы · "
            "без пшеницы, белой муки 1 сорта и ржаной муки", st_note))
A(grid(D.MENU_HEAD, D.MENU, [CW * .09, CW * .30, CW * .31, CW * .30], bold_first=True))
A(Paragraph(D.MENU_NOTE, st_note))
A(Paragraph("Из базы: мясо примерно дважды в неделю, красное мясо — реже; при вздутии "
            "всё отварное или паровое и порции меньше.", st_note))

# ═══════════════════════════════════ ЗАМЕНЫ
A(CondPageBreak(150))
A(Spacer(1, 10))
A(band("ЧЕМ ЗАМЕНИТЬ САХАР, ГЛЮТЕН И МОЛОЧКУ"))
A(Spacer(1, 4))
for gname, rows in D.SWAP_GROUPS:
    A(KeepTogether([
        Paragraph(gname, st_h3),
        grid(D.SWAP_HEAD, rows, [CW * .27, CW * .48, CW * .25]),
    ]))
    A(Spacer(1, 4))
A(Paragraph("Гхи — единственное исключение из «без молочки»: по базе сливочное масло "
            "и гхи разрешены, в гхи нет казеина и лактозы.", st_note))

# ═══════════════════════════════════ ПОКУПКИ
A(CondPageBreak(150))
A(Spacer(1, 10))
A(band("СПИСОК ПОКУПОК — Пятёрочка · Перекрёсток · ВкусВилл"))
A(Spacer(1, 4))
shop_tbl = grid(D.SHOP_HEAD, D.SHOP,
                [CW * .15, CW * .43, CW * .14, CW * .14, CW * .14],
                bold_first=True, center_cols=(2, 3, 4), small_head_cols=(2, 3, 4))
extra = []
for i, row_data in enumerate(D.SHOP, start=1):
    for col in (2, 3, 4):
        v = row_data[col]
        color = GREEN if v == "есть" else (RED if v == "нет" else ACCENT)
        extra.append(("BACKGROUND", (col, i), (col, i), color))
shop_tbl.setStyle(TableStyle(extra))
A(shop_tbl)
A(Paragraph(D.SHOP_NOTE, st_note))

# ═══════════════════════════════════ МОЖНО / НЕЛЬЗЯ
A(CondPageBreak(150))
A(Spacer(1, 10))
A(band("ШПАРГАЛКА: НЕЛЬЗЯ / МОЖНО"))
A(Spacer(1, 4))
yn = grid(D.YESNO_HEAD, D.YESNO, [CW * .45, CW * .55])
extra = []
for i in range(1, len(D.YESNO) + 1):
    extra.append(("BACKGROUND", (0, i), (0, i), RED))
    extra.append(("BACKGROUND", (1, i), (1, i), GREEN))
yn.setStyle(TableStyle(extra))
A(yn)

# ═══════════════════════════════════ КЛЕТЧАТКА
A(CondPageBreak(150))
A(Spacer(1, 10))
A(band("КЛЕТЧАТКА — отварная или ошпаренная"))
A(Spacer(1, 4))
A(grid(D.FIBER_HEAD, D.FIBER, [CW * .28, CW * .55, CW * .17], bold_first=True))
A(Paragraph(D.FIBER_NOTE, st_note))

# ═══════════════════════════════════ РЕКОМЕНДАЦИИ
A(CondPageBreak(150))
A(Spacer(1, 10))
A(band("ОБЩИЕ РЕКОМЕНДАЦИИ"))
A(Spacer(1, 4))
A(Paragraph("Здесь то же самое, но словами — чтобы не заглядывать в таблицы каждый день.",
            st_note))
rec_rows = [[str(i), t, b] for i, (t, b) in enumerate(D.RECOMMENDATIONS, start=1)]
A(grid(["№", "Правило", "Что это значит"], rec_rows,
       [CW * .05, CW * .30, CW * .65], bold_first=False, center_cols=(0,),
       compact=True))

A(Spacer(1, 8))
disc = Table([[Paragraph("<b>Важно.</b> " + D.DISCLAIMER, st_td)]], colWidths=[CW])
disc.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
    ("BOX", (0, 0), (-1, -1), 0.7, LINE),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
]))
A(disc)

out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "pitanie-bgbkbs-menu.pdf")
doc = BaseDocTemplate(out, pagesize=A4,
                      leftMargin=LM, rightMargin=RM, topMargin=TM, bottomMargin=BM,
                      title=D.TITLE, author="Анатомия Здоровья · Нутрициология",
                      subject=D.SUBTITLE)
frame = Frame(LM, BM, CW, PH - TM - BM, id="main",
              leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
doc.addPageTemplates([PageTemplate(id="p", frames=[frame], onPage=on_page)])
doc.build(story)
print("saved:", out)
