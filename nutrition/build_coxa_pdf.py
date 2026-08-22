# -*- coding: utf-8 -*-
"""Сборка PDF: план питания при коксартрозе 4 ст."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, KeepTogether, CondPageBreak)
import plan_coxa as D

F = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DJ", os.path.join(F, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DJ-B", os.path.join(F, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ", boldItalic="DJ-B")

DARK  = HexColor("#1F3864"); HEAD = HexColor("#2E5C8A"); BAND = HexColor("#EAF0F7")
ACC   = HexColor("#FFF2CC"); GRN  = HexColor("#DDF0E0"); RED  = HexColor("#F8D7DA")
REDB  = HexColor("#C0392B"); LINE = HexColor("#B7C6D9"); GREY = HexColor("#44546A")

PW, PH = A4
LM = RM = 13 * mm; TM = 15 * mm; BM = 15 * mm
CW = PW - LM - RM

S = lambda **k: ParagraphStyle(**k)
h1   = S(name="h1", fontName="DJ-B", fontSize=15.5, leading=19, textColor=DARK, spaceAfter=2)
sub  = S(name="sub", fontName="DJ", fontSize=9, leading=12.5, textColor=GREY, spaceAfter=8)
h2   = S(name="h2", fontName="DJ-B", fontSize=12.5, leading=15.5, textColor=white)
h3   = S(name="h3", fontName="DJ-B", fontSize=10.5, leading=13, textColor=DARK,
         spaceBefore=6, spaceAfter=4)
note = S(name="note", fontName="DJ", fontSize=8, leading=11, textColor=GREY,
         spaceBefore=3, spaceAfter=5)
th   = S(name="th", fontName="DJ-B", fontSize=8, leading=10.5, textColor=white, alignment=TA_CENTER)
td   = S(name="td", fontName="DJ", fontSize=8, leading=10.6)
tdb  = S(name="tdb", fontName="DJ-B", fontSize=8, leading=10.6)
tdc  = S(name="tdc", fontName="DJ", fontSize=8, leading=10.6, alignment=TA_CENTER)
thsm = S(name="thsm", fontName="DJ-B", fontSize=6.8, leading=8.6,
         textColor=white, alignment=TA_CENTER)
tdcb = S(name="tdcb", fontName="DJ-B", fontSize=8.5, leading=11, alignment=TA_CENTER)
body = S(name="body", fontName="DJ", fontSize=9, leading=12.8, spaceAfter=4)


def P(t, s=td):
    return Paragraph(str(t).replace("\n", "<br/>"), s)


def band(title):
    t = Table([[Paragraph(title, h2)]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DARK),
                           ("LEFTPADDING", (0, 0), (-1, -1), 8),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                           ("TOPPADDING", (0, 0), (-1, -1), 5),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    return t


def callout(text, fill, border, bold_lead=None):
    txt = (f"<b>{bold_lead}</b> " if bold_lead else "") + text.replace("\n", "<br/>")
    t = Table([[Paragraph(txt, td)]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fill),
                           ("BOX", (0, 0), (-1, -1), 1.1, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 8),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    return t


def grid(header, rows, widths, bold_first=False, center=(), small_head=()):
    data = [[P(h, thsm if i in small_head else th)
             for i, h in enumerate(header)]]
    for r in rows:
        line = []
        for i, v in enumerate(r):
            st = tdc if i in center else (tdb if bold_first and i == 0 else td)
            line.append(P(v, st))
        data.append(line)
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [("BACKGROUND", (0, 0), (-1, 0), HEAD),
             ("GRID", (0, 0), (-1, -1), 0.5, LINE),
             ("VALIGN", (0, 0), (-1, -1), "TOP"),
             ("LEFTPADDING", (0, 0), (-1, -1), 4),
             ("RIGHTPADDING", (0, 0), (-1, -1), 4),
             ("TOPPADDING", (0, 0), (-1, -1), 2.8),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 2.8)]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(style))
    return t


def on_page(c, doc):
    c.saveState()
    c.setFont("DJ", 7); c.setFillColor(GREY)
    c.drawString(LM, 8 * mm, "План питания · коксартроз 4 ст. · без сахара, глютена и молочки")
    c.drawRightString(PW - RM, 8 * mm, "стр. %d" % c.getPageNumber())
    c.setStrokeColor(LINE); c.setLineWidth(0.5); c.line(LM, 11 * mm, PW - RM, 11 * mm)
    c.restoreState()


story = []; A = story.append

# ══════════════════════════ ТИТУЛ + КАРДИО-ПРЕДУПРЕЖДЕНИЕ
A(Paragraph(D.TITLE, h1))
A(Paragraph(D.SUBTITLE, sub))
A(callout(D.CARDIO_WARNING, RED, REDB))
A(Spacer(1, 8))

A(band("1. КЛИНИЧЕСКОЕ ОБОСНОВАНИЕ"))
A(Spacer(1, 5))
for i, line in enumerate(D.RATIONALE, 1):
    A(Paragraph(f"<b>{i}.</b> {line}", body))

A(Spacer(1, 6))
A(callout(D.CONFLICT_NOTE, ACC, HexColor("#D6A400")))

# ══════════════════════════ РЕЖИМЫ
A(CondPageBreak(160)); A(Spacer(1, 5))
A(band("2. ТРИ РЕЖИМА — от одного до трёх приёмов, без перекусов"))
A(Spacer(1, 5))
A(grid(D.MODES_HEAD, D.MODES,
       [CW * .16, CW * .24, CW * .27, CW * .09, CW * .24],
       bold_first=True, center=(3,)))
A(Paragraph(D.MODES_NOTE, note))

# ══════════════════════════ ЖЁСТКИЕ ОГРАНИЧЕНИЯ
A(CondPageBreak(160)); A(Spacer(1, 5))
A(band("3. ШЕСТЬ ЖЁСТКИХ ОГРАНИЧЕНИЙ — и как каждое выполнено"))
A(Spacer(1, 5))
A(grid(D.LIMITS_HEAD, D.LIMITS, [CW * .04, CW * .30, CW * .66], center=(0,)))

# ══════════════════════════ ВАРИАНТ А — МЕНЮ
A(CondPageBreak(200)); A(Spacer(1, 5))
A(band("4. ВАРИАНТ А — готовая таблица на 14 дней. Смотришь и делаешь"))
A(Spacer(1, 5))
menu_rows = []
for i, (z, o, u) in enumerate(D.MENU, 1):
    total = z[1] + o[1] + u[1]
    menu_rows.append([f"День {i}",
                      f"{z[0]}\n<b>белок {z[1]} г</b>",
                      f"{o[0]}\n<b>белок {o[1]} г</b>",
                      f"{u[0]}\n<b>белок {u[1]} г</b>",
                      f"{total} г"])
A(grid(D.MENU_HEAD, menu_rows,
       [CW * .07, CW * .29, CW * .29, CW * .28, CW * .07],
       bold_first=True, center=(4,)))
for n in D.MENU_NOTES:
    A(Paragraph("• " + n, note))

# ══════════════════════════ ВАРИАНТ Б — СВОБОДА
A(CondPageBreak(200)); A(Spacer(1, 5))
A(band("5. ВАРИАНТ Б — без таблицы. Пять правил и конструктор"))
A(Spacer(1, 5))
A(Paragraph("Правило тарелки — общий объём порции 500 г", h3))
A(grid(D.PLATE_HEAD, D.PLATE, [CW * .17, CW * .13, CW * .20, CW * .50], bold_first=True))

A(Spacer(1, 6))
A(Paragraph("Пять правил, которые заменяют всю таблицу", h3))
rules = [[str(i), t, b] for i, (t, b) in enumerate(D.RULES5, 1)]
A(grid(["№", "Правило", "Что это значит"], rules,
       [CW * .04, CW * .28, CW * .68], center=(0,)))

A(Spacer(1, 6))
A(Paragraph("Конструктор: собери тарелку сам", h3))
A(grid(D.CONSTRUCTOR_HEAD, D.CONSTRUCTOR, [CW * .22, CW * .78], bold_first=True))

# ══════════════════════════ ЗАМЕНЫ
A(CondPageBreak(170)); A(Spacer(1, 5))
A(band("6. ЗАМЕНЫ — чем закрыть сахар, глютен и молочку"))
A(Spacer(1, 5))
for gname, rows in D.SWAP_GROUPS:
    A(KeepTogether([Paragraph(gname, h3),
                    grid(D.SWAP_HEAD, rows, [CW * .27, CW * .50, CW * .23])]))
    A(Spacer(1, 4))

# ══════════════════════════ ИСКЛЮЧЕНИЯ
A(CondPageBreak(170)); A(Spacer(1, 5))
A(band("7. ИСКЛЮЧЕНИЯ — и причина по каждому пункту"))
A(Spacer(1, 5))
ex = grid(D.EXCL_HEAD, D.EXCLUSIONS, [CW * .34, CW * .66], bold_first=True)
ex.setStyle(TableStyle([("BACKGROUND", (0, i), (0, i), RED)
                        for i in range(1, len(D.EXCLUSIONS) + 1)]))
A(ex)

# ══════════════════════════ ПОКУПКИ
A(CondPageBreak(170)); A(Spacer(1, 5))
A(band("8. ПОКУПКИ — Пятёрочка · Перекрёсток · ВкусВилл · рынок"))
A(Spacer(1, 5))
sh = grid(D.SHOP_HEAD, D.SHOP,
          [CW * .14, CW * .38, CW * .12, CW * .12, CW * .12, CW * .12],
          bold_first=True, center=(2, 3, 4, 5), small_head=(2, 3, 4, 5))
extra = []
for i, r in enumerate(D.SHOP, 1):
    for col in (2, 3, 4, 5):
        v = r[col]
        fill = GRN if v in ("есть", "лучше всего") else (RED if v in ("нет", "—") else ACC)
        extra.append(("BACKGROUND", (col, i), (col, i), fill))
sh.setStyle(TableStyle(extra))
A(sh)
A(Paragraph(D.SHOP_NOTE, note))

# ══════════════════════════ НУТРИЦЕВТИКА
A(CondPageBreak(170)); A(Spacer(1, 5))
A(band("9. НУТРИЦЕВТИЧЕСКАЯ ПОДДЕРЖКА — всё только с едой, ничего натощак"))
A(Spacer(1, 5))
A(grid(D.SUPP_HEAD, D.SUPPLEMENTS,
       [CW * .16, CW * .14, CW * .12, CW * .26, CW * .32], bold_first=True))
for n in D.SUPP_NOTES:
    A(Paragraph("• " + n, note))

# ══════════════════════════ АНАЛИЗЫ
A(CondPageBreak(170)); A(Spacer(1, 5))
A(band("10. АНАЛИЗЫ К ДОСДАЧЕ — что каждый даст"))
A(Spacer(1, 5))
A(grid(D.LABS_HEAD, D.LABS, [CW * .27, CW * .73], bold_first=True))

# ══════════════════════════ КРАСНЫЕ ФЛАГИ
A(CondPageBreak(170)); A(Spacer(1, 5))
A(band("11. КРАСНЫЕ ФЛАГИ — когда немедленно к врачу"))
A(Spacer(1, 5))
rf = grid(D.RED_HEAD, D.RED_FLAGS, [CW * .55, CW * .45], bold_first=True)
rf.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), RED)
                        for i in range(1, len(D.RED_FLAGS) + 1)]))
A(rf)

A(CondPageBreak(150)); A(Spacer(1, 5))
A(band("12. С ЧЕГО НАЧАТЬ — первая неделя по шагам"))
A(Spacer(1, 5))
A(grid(D.START_HEAD, D.START, [CW * .07, CW * .70, CW * .23], center=(0,)))

A(Spacer(1, 6))
A(callout(D.DISCLAIMER, ACC, HexColor("#D6A400"), bold_lead="Важно."))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan-coxarthrosis-53m.pdf")
doc = BaseDocTemplate(out, pagesize=A4, leftMargin=LM, rightMargin=RM,
                      topMargin=TM, bottomMargin=BM,
                      title=D.TITLE, subject=D.SUBTITLE,
                      author="Нутрициология · Анатомия Здоровья")
doc.addPageTemplates([PageTemplate(id="p",
                                   frames=[Frame(LM, BM, CW, PH - TM - BM, id="m",
                                                 leftPadding=0, rightPadding=0,
                                                 topPadding=0, bottomPadding=0)],
                                   onPage=on_page)])
doc.build(story)
print("saved:", out)
