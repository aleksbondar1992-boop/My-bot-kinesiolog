# -*- coding: utf-8 -*-
"""PDF плана БГБКБС: навигация по ссылкам, крупный шрифт под телефон."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
                                Table, TableStyle, KeepTogether, CondPageBreak, PageBreak,
                                Flowable)
import plan_data as D

F = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DJ", os.path.join(F, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DJ-B", os.path.join(F, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ", boldItalic="DJ-B")

DARK = HexColor("#1F3864"); HEAD = HexColor("#2E5C8A"); BAND = HexColor("#EAF0F7")
ACC  = HexColor("#FFF2CC"); GRN  = HexColor("#DDF0E0"); RED  = HexColor("#F8D7DA")
LINE = HexColor("#B7C6D9"); GREY = HexColor("#44546A")

PW, PH = A4
LM = RM = 12 * mm; TM = 14 * mm; BM = 16 * mm
CW = PW - LM - RM

S = lambda **k: ParagraphStyle(**k)
h1   = S(name="h1", fontName="DJ-B", fontSize=20, leading=25, textColor=DARK, spaceAfter=3)
sub  = S(name="sub", fontName="DJ", fontSize=11, leading=15, textColor=GREY, spaceAfter=10)
h2   = S(name="h2", fontName="DJ-B", fontSize=15, leading=19, textColor=white)
h3   = S(name="h3", fontName="DJ-B", fontSize=12.5, leading=16, textColor=DARK,
         spaceBefore=8, spaceAfter=5)
note = S(name="note", fontName="DJ", fontSize=9.5, leading=13, textColor=GREY,
         spaceBefore=4, spaceAfter=6)
th   = S(name="th", fontName="DJ-B", fontSize=10, leading=13, textColor=white,
         alignment=TA_CENTER)
td   = S(name="td", fontName="DJ", fontSize=10.5, leading=14.5)
tdb  = S(name="tdb", fontName="DJ-B", fontSize=10.5, leading=14.5)
tdc  = S(name="tdc", fontName="DJ", fontSize=10.5, leading=14.5, alignment=TA_CENTER)
navq = S(name="navq", fontName="DJ-B", fontSize=12, leading=16, textColor=DARK)
navl = S(name="navl", fontName="DJ-B", fontSize=12, leading=16, textColor=HexColor("#1B5FA8"))

PAGES = {}


class Anchor(Flowable):
    """Невидимая метка: цель внутренней ссылки и пункт в закладках PDF."""
    def __init__(self, name, title=None, level=0):
        Flowable.__init__(self)
        self.name, self.title, self.level = name, title, level
        self.width = self.height = 0

    def wrap(self, aW, aH):
        return (0, 0)

    def draw(self):
        self.canv.bookmarkPage(self.name)
        PAGES[self.name] = self.canv.getPageNumber()
        if self.title:
            self.canv.addOutlineEntry(self.title, self.name, self.level, closed=0)


def P(t, s=td):
    return Paragraph(str(t).replace("\n", "<br/>"), s)


def band(title, dest=None):
    flow = []
    if dest:
        flow.append(Anchor(dest, title, 0))
    t = Table([[Paragraph(title, h2)]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), DARK),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 8),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]))
    flow.append(t)
    return flow


def callout(text, fill, border, bold_lead=None):
    txt = (f"<b>{bold_lead}</b> " if bold_lead else "") + text.replace("\n", "<br/>")
    t = Table([[Paragraph(txt, td)]], colWidths=[CW])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), fill),
                           ("BOX", (0, 0), (-1, -1), 1.3, border),
                           ("LEFTPADDING", (0, 0), (-1, -1), 11),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                           ("TOPPADDING", (0, 0), (-1, -1), 10),
                           ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    return t


def grid(header, rows, widths, bold_first=False, center=()):
    data = [[P(h, th) for h in header]]
    for r in rows:
        data.append([P(v, tdc if i in center else (tdb if bold_first and i == 0 else td))
                     for i, v in enumerate(r)])
    t = Table(data, colWidths=widths, repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), HEAD),
          ("GRID", (0, 0), (-1, -1), 0.6, LINE),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
          ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    for i in range(1, len(data)):
        if i % 2 == 0:
            st.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(st))
    return t


def on_page(c, doc):
    c.saveState()
    c.setFont("DJ", 8.5); c.setFillColor(GREY)
    c.drawString(LM, 8 * mm, "Питание БГБКБС")
    if c.getPageNumber() > 1:
        c.drawCentredString(PW / 2, 8 * mm, "к оглавлению — стр. 1")
    c.drawRightString(PW - RM, 8 * mm, "стр. %d" % c.getPageNumber())
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(LM, 11.5 * mm, PW - RM, 11.5 * mm)
    c.restoreState()


MUST = [
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

STEPS = [
    ("ШАГ 1", "Понять правило дня — что и когда есть",
     [("Правило дня", "sec1")]),
    ("ШАГ 2", "Разобраться в расписании: еда, сорбент, витамины",
     [("Схема дня по часам", "sec2")]),
    ("ШАГ 3", "Сходить в магазин",
     [("Список покупок", "sec5"), ("Чем заменить", "sec4")]),
    ("ШАГ 4", "Начать готовить",
     [("Меню на 7 дней", "sec3"), ("Как готовить овощи", "sec7")]),
    ("ШАГ 5", "Держать в голове",
     [("Нельзя и можно", "sec6"), ("Общие рекомендации", "sec8")]),
]

QUICK = [
    ("Что мне сегодня есть?", "sec3"),
    ("Чем заменить сахар, хлеб, молоко?", "sec4"),
    ("Когда пить псиллиум и витамины?", "sec2"),
    ("Что купить и где?", "sec5"),
    ("Что мне нельзя?", "sec6"),
    ("Как готовить овощи?", "sec7"),
    ("Забыла правило — напомни коротко", "sec1"),
    ("Хочу без таблиц, просто правила", "sec8"),
    ("Что ещё можно добавить из базы?", "sec9"),
]


def build_story():
    st = []; A = st.append
    A(Paragraph(D.TITLE, h1))
    A(Paragraph(D.SUBTITLE, sub))

    A(callout("Не читай документ целиком. Найди свой вопрос и нажми — ссылки кликабельные, "
              "они перебрасывают на нужную страницу. Внизу каждой страницы написано, "
              "что оглавление на стр. 1.", ACC, HexColor("#D6A400"),
              bold_lead="КАК ПОЛЬЗОВАТЬСЯ."))
    A(Spacer(1, 12))

    A(Paragraph("ПОРЯДОК ДЕЙСТВИЙ", h3))
    rows = []
    for num, what, links in STEPS:
        cell = "<br/>".join(
            f'<a href="#{d}" color="#1B5FA8"><u>{t}</u></a>'
            f'{"  · стр. " + str(PAGES[d]) if d in PAGES else ""}' for t, d in links)
        rows.append([num, what, Paragraph(cell, td)])
    t = Table([[P(x, th) for x in ["Шаг", "Что делаем", "Куда смотреть"]]] +
              [[P(r[0], tdb), P(r[1], td), r[2]] for r in rows],
              colWidths=[CW * .12, CW * .48, CW * .40], repeatRows=1)
    stl = [("BACKGROUND", (0, 0), (-1, 0), HEAD),
           ("GRID", (0, 0), (-1, -1), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
           ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)]
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            stl.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(stl))
    A(t)

    A(PageBreak())
    A(Paragraph("БЫСТРЫЙ ПОИСК — нажми на вопрос", h3))
    A(Paragraph("Открыла документ, нашла свой вопрос, нажала — попала куда нужно.",
                note))
    qrows = [[Paragraph(q, navq),
              Paragraph(f'<a href="#{d}" color="#1B5FA8"><u>смотреть</u></a>'
                        f'{"  · стр. " + str(PAGES[d]) if d in PAGES else ""}', navl)]
             for q, d in QUICK]
    qt = Table([[P("Вопрос", th), P("Ответ здесь", th)]] + qrows,
               colWidths=[CW * .64, CW * .36], repeatRows=1)
    qstl = [("BACKGROUND", (0, 0), (-1, 0), HEAD),
            ("GRID", (0, 0), (-1, -1), 0.6, LINE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]
    for i in range(1, len(qrows) + 1):
        if i % 2 == 0:
            qstl.append(("BACKGROUND", (0, i), (-1, i), BAND))
    qt.setStyle(TableStyle(qstl))
    A(qt)
    A(PageBreak())

    def sec(n, title, dest):
        st.append(CondPageBreak(170)); st.append(Spacer(1, 10))
        st.extend(band(f"{n}. {title}", dest))
        st.append(Spacer(1, 6))

    # 1
    st.extend(band("1. ГЛАВНОЕ ПРАВИЛО ДНЯ", "sec1"))
    A(Spacer(1, 6))
    A(grid(D.PRINCIPLE_HEAD, D.PRINCIPLE, [CW * .17, CW * .48, CW * .35], bold_first=True))
    A(Paragraph("Это весь протокол в трёх строчках. Всё остальное — детали.", note))
    A(Spacer(1, 8))
    A(Paragraph("Что обязательно каждый день", h3))
    A(grid(["Что", "Когда", "Как"], MUST, [CW * .27, CW * .30, CW * .43], bold_first=True))

    sec(2, "СХЕМА ДНЯ — весь день по часам", "sec2")
    A(Paragraph("Время ориентировочное: важны не часы, а порядок и промежутки в 2 часа "
                "вокруг сорбента.", note))
    tbl = grid(D.DAY_HEAD, D.DAY_SCHEDULE, [CW * .14, CW * .38, CW * .48], bold_first=True)
    extra = []
    for i, row in enumerate(D.DAY_SCHEDULE, start=1):
        if row[1].startswith(("ЗАВТРАК", "ОБЕД", "УЖИН")):
            extra.append(("BACKGROUND", (0, i), (-1, i), GRN))
        elif "ПСИЛЛИУМ" in row[1]:
            extra.append(("BACKGROUND", (0, i), (-1, i), ACC))
    tbl.setStyle(TableStyle(extra))
    A(tbl)
    A(Paragraph(D.HERBS_NOTE, note))

    sec(3, "МЕНЮ НА 7 ДНЕЙ", "sec3")
    A(Paragraph("Без сахара · без глютена · без молочки · без курицы · без пшеницы, "
                "белой муки 1 сорта и ржаной муки", note))
    A(grid(D.MENU_HEAD, D.MENU, [CW * .09, CW * .30, CW * .31, CW * .30], bold_first=True))
    A(Paragraph(D.MENU_NOTE, note))

    sec(4, "ЗАМЕНЫ — чем закрыть сахар, глютен и молочку", "sec4")
    for gname, rows in D.SWAP_GROUPS:
        A(KeepTogether([Paragraph(gname, h3),
                        grid(D.SWAP_HEAD, rows, [CW * .26, CW * .50, CW * .24])]))
        A(Spacer(1, 5))

    sec(5, "СПИСОК ПОКУПОК", "sec5")
    shop_rows = []
    for cat, what, pyat, per, vv in D.SHOP:
        parts = []
        for lbl, v in (("Пятёрочка", pyat), ("Перекрёсток", per), ("ВкусВилл", vv)):
            if v == "есть":
                parts.append(lbl)
            elif v == "не всегда":
                parts.append(f"{lbl} (не всегда)")
            elif v == "есть / аптека":
                parts.append(f"{lbl} или аптека")
        if not parts:
            parts = ["<b>только аптека</b>"]
        shop_rows.append([cat, what, " · ".join(parts)])
    A(grid(["Категория", "Что берём", "Где брать"], shop_rows,
           [CW * .17, CW * .45, CW * .38], bold_first=True))
    A(Paragraph(D.SHOP_NOTE, note))

    sec(6, "ШПАРГАЛКА: НЕЛЬЗЯ / МОЖНО", "sec6")
    yn = grid(D.YESNO_HEAD, D.YESNO, [CW * .44, CW * .56])
    yn.setStyle(TableStyle(
        [("BACKGROUND", (0, i), (0, i), RED) for i in range(1, len(D.YESNO) + 1)] +
        [("BACKGROUND", (1, i), (1, i), GRN) for i in range(1, len(D.YESNO) + 1)]))
    A(yn)

    sec(7, "КЛЕТЧАТКА — отварная или ошпаренная", "sec7")
    A(Paragraph(D.FIBER_NOTE, note))
    A(grid(D.FIBER_HEAD, D.FIBER, [CW * .28, CW * .54, CW * .18], bold_first=True))

    sec(8, "ОБЩИЕ РЕКОМЕНДАЦИИ", "sec8")
    A(Paragraph("То же самое, но словами — чтобы не заглядывать в таблицы каждый день.",
                note))
    rec = [[str(i), t, b] for i, (t, b) in enumerate(D.RECOMMENDATIONS, 1)]
    A(grid(["№", "Правило", "Что это значит"], rec,
           [CW * .06, CW * .30, CW * .64], center=(0,)))

    sec(9, "ДОПОЛНИТЕЛЬНО ИЗ БАЗЫ — по согласованию", "sec9")
    A(grid(D.EXTRA_HEAD, D.EXTRA, [CW * .33, CW * .25, CW * .42], bold_first=True))
    A(Paragraph(D.EXTRA_NOTE, note))

    A(Spacer(1, 8))
    A(callout(D.DISCLAIMER, ACC, HexColor("#D6A400"), bold_lead="Важно."))
    return st


out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pitanie-bgbkbs-menu.pdf")


def render(path):
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=LM, rightMargin=RM,
                          topMargin=TM, bottomMargin=BM,
                          title=D.TITLE, subject=D.SUBTITLE,
                          author="Анатомия Здоровья · Нутрициология")
    doc.addPageTemplates([PageTemplate(
        id="p", frames=[Frame(LM, BM, CW, PH - TM - BM, id="m", leftPadding=0,
                              rightPadding=0, topPadding=0, bottomPadding=0)],
        onPage=on_page)])
    doc.build(build_story())


tmp = out + ".pass1"
render(tmp); os.remove(tmp)      # проход 1 — узнаём страницы разделов
render(out)                      # проход 2 — печатаем номера в навигации
print("saved:", out)
print("разделы:", {k: v for k, v in sorted(PAGES.items(), key=lambda x: x[1])})
