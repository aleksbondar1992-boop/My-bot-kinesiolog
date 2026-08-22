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
body_st = S(name="body", fontName="DJ", fontSize=9, leading=12.8, spaceAfter=4)


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

A(Paragraph(D.TITLE, h1))
A(Paragraph(D.SUBTITLE, sub))
A(callout(D.CARDIO_WARNING, RED, REDB))
A(Spacer(1, 7))

A(band("1. КЛИНИЧЕСКОЕ ОБОСНОВАНИЕ"))
A(Spacer(1, 5))
for i, line in enumerate(D.RATIONALE, 1):
    A(Paragraph(f"<b>{i}.</b> {line}", body_st))
A(Spacer(1, 5))
A(callout(D.CONTROL_NOTE, ACC, HexColor("#D6A400")))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("2. РЕЖИМ — два приёма в день, без перекусов"))
A(Spacer(1, 5))
A(grid(D.MODES_HEAD, D.MODES, [CW * .17, CW * .38, CW * .45], bold_first=True))
A(Paragraph(D.MODES_NOTE, note))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("3. ГЛАВНЫЙ МЕХАНИЗМ — ВНУТРИБРЮШНОЕ ДАВЛЕНИЕ"))
A(Spacer(1, 5))
A(callout(D.PRESSURE_RULE, ACC, HexColor("#D6A400")))
A(Spacer(1, 5))
A(Paragraph("Замкнутый круг, который мы разрываем", h3))
A(grid(D.PRESSURE_HEAD, D.PRESSURE, [CW * .16, CW * .32, CW * .52], bold_first=True))
A(Spacer(1, 5))
A(Paragraph("Чем именно разрываем", h3))
pb = grid(D.PRESSURE_BREAK_HEAD, D.PRESSURE_BREAK, [CW * .38, CW * .62], bold_first=True)
pb.setStyle(TableStyle([("BACKGROUND", (0, i), (0, i), GRN)
                        for i in range(1, len(D.PRESSURE_BREAK) + 1)]))
A(pb)

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("4. ЧТО МЫ ХОТИМ УСВОИТЬ И ЧТО ЭТОМУ МЕШАЕТ"))
A(Spacer(1, 5))
A(grid(D.ABSORB_HEAD, D.ABSORB,
       [CW * .11, CW * .26, CW * .27, CW * .36], bold_first=True))
A(Paragraph(D.ABSORB_NOTE, note))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("5. СКОЛЬКО ЕСТЬ — граммов нет, есть сигналы тела"))
A(Spacer(1, 5))
A(grid(D.ENOUGH_HEAD, D.ENOUGH, [CW * .33, CW * .34, CW * .33], bold_first=True))
A(Paragraph(D.ENOUGH_NOTE, note))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("6. ТАРЕЛКА — ориентир, а не измерение"))
A(Spacer(1, 5))
A(grid(D.PLATE_HEAD, D.PLATE, [CW * .14, CW * .43, CW * .43], bold_first=True))
A(Paragraph(D.PLATE_NOTE, note))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("7. КАК ГОТОВИТЬ — мягко, тепло, без сырого"))
A(Spacer(1, 5))
A(grid(D.COOK_HEAD, D.COOKING, [CW * .20, CW * .42, CW * .38], bold_first=True))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("8. ПРОТОКОЛ ВОССТАНОВЛЕНИЯ СЛИЗИСТЫХ"))
A(Spacer(1, 5))
A(Paragraph("Продукты, которые работают на слизистую. Должны быть в рационе постоянно, "
            "а не курсом", h3))
A(grid(D.MUCOSA_HEAD, D.MUCOSA, [CW * .26, CW * .38, CW * .36], bold_first=True))
A(Spacer(1, 5))
A(Paragraph("Чего в этом протоколе нет — и почему именно у этого клиента", h3))
mo = grid(D.MUCOSA_OUT_HEAD, D.MUCOSA_OUT, [CW * .30, CW * .70], bold_first=True)
mo.setStyle(TableStyle([("BACKGROUND", (0, i), (0, i), RED)
                        for i in range(1, len(D.MUCOSA_OUT) + 1)]))
A(mo)

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("9. МЯГКАЯ ОЧИСТКА КИШЕЧНИКА — псиллиум по нарастающей"))
A(Spacer(1, 5))
A(grid(D.CLEAN_HEAD, D.CLEANSE, [CW * .18, CW * .22, CW * .60], bold_first=True))
A(Paragraph(D.CLEANSE_NOTE, note))

A(CondPageBreak(200)); A(Spacer(1, 6))
A(band("10. ВАРИАНТ А — готовая таблица на 14 дней"))
A(Spacer(1, 5))
menu_rows = [[f"День {i}", m[0], m[1], m[2]] for i, m in enumerate(D.MENU, 1)]
A(grid(D.MENU_HEAD, menu_rows, [CW * .07, CW * .31, CW * .31, CW * .31], bold_first=True))
for n in D.MENU_NOTES:
    A(Paragraph("• " + n, note))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("11. ВАРИАНТ Б — без таблицы. Собери тарелку сам"))
A(Spacer(1, 5))
A(grid(D.CONSTRUCTOR_HEAD, D.CONSTRUCTOR, [CW * .22, CW * .78], bold_first=True))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("12. ЗАМЕНЫ — чем закрыть сахар, глютен и молочку"))
A(Spacer(1, 5))
for gname, rows in D.SWAP_GROUPS:
    A(KeepTogether([Paragraph(gname, h3),
                    grid(D.SWAP_HEAD, rows, [CW * .26, CW * .51, CW * .23])]))
    A(Spacer(1, 4))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("13. ИСКЛЮЧЕНИЯ — и причина по каждому пункту"))
A(Spacer(1, 5))
ex = grid(D.EXCL_HEAD, D.EXCLUSIONS, [CW * .33, CW * .67], bold_first=True)
ex.setStyle(TableStyle([("BACKGROUND", (0, i), (0, i), RED)
                        for i in range(1, len(D.EXCLUSIONS) + 1)]))
A(ex)

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("14. ПОКУПКИ — рынок в приоритете"))
A(Spacer(1, 5))
sh = grid(D.SHOP_HEAD, D.SHOP,
          [CW * .13, CW * .39, CW * .12, CW * .12, CW * .12, CW * .12],
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

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("15. НУТРИЦЕВТИКА — всё только с едой, ничего натощак"))
A(Spacer(1, 5))
A(grid(D.SUPP_HEAD, D.SUPPLEMENTS,
       [CW * .15, CW * .15, CW * .13, CW * .25, CW * .32], bold_first=True))
for n in D.SUPP_NOTES:
    A(Paragraph("• " + n, note))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("16. КАЧЕСТВО САМИХ ДОБАВОК — как читать состав на банке"))
A(Spacer(1, 5))
q = grid(D.QUALITY_HEAD, D.QUALITY, [CW * .18, CW * .34, CW * .48], bold_first=True)
q.setStyle(TableStyle([("BACKGROUND", (2, i), (2, i), RED)
                       for i in range(1, len(D.QUALITY) + 1)]))
A(q)
for n in D.QUALITY_WHY:
    A(Paragraph("• " + n, note))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("17. АНАЛИЗЫ К ДОСДАЧЕ"))
A(Spacer(1, 5))
A(grid(D.LABS_HEAD, D.LABS, [CW * .24, CW * .76], bold_first=True))

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("18. КРАСНЫЕ ФЛАГИ — когда немедленно к врачу"))
A(Spacer(1, 5))
rf = grid(D.RED_HEAD, D.RED_FLAGS, [CW * .55, CW * .45], bold_first=True)
rf.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), RED)
                        for i in range(1, len(D.RED_FLAGS) + 1)]))
A(rf)

A(CondPageBreak(150)); A(Spacer(1, 6))
A(band("19. С ЧЕГО НАЧАТЬ"))
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
