# -*- coding: utf-8 -*-
"""PDF плана питания: навигация по ссылкам, крупный шрифт под телефон."""
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
import plan_coxa as D

F = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DJ", os.path.join(F, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DJ-B", os.path.join(F, "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ", boldItalic="DJ-B")

DARK = HexColor("#1F3864"); HEAD = HexColor("#2E5C8A"); BAND = HexColor("#EAF0F7")
ACC  = HexColor("#FFF2CC"); GRN  = HexColor("#DDF0E0"); RED  = HexColor("#F8D7DA")
REDB = HexColor("#C0392B"); LINE = HexColor("#B7C6D9"); GREY = HexColor("#44546A")
LINKC = HexColor("#1B5FA8")

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
body = S(name="body", fontName="DJ", fontSize=11, leading=15.5, spaceAfter=7)
navq = S(name="navq", fontName="DJ-B", fontSize=12, leading=16, textColor=DARK)
navl = S(name="navl", fontName="DJ-B", fontSize=12, leading=16, textColor=LINKC)

PAGES = {}          # имя якоря -> номер страницы (заполняется при первом проходе)


class Anchor(Flowable):
    """Невидимая метка: цель для внутренней ссылки и пункт в закладках PDF."""
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


def link(text, dest, style=navl):
    page = PAGES.get(dest)
    tail = f" · стр. {page}" if page else ""
    return Paragraph(
        f'<a href="#{dest}" color="#1B5FA8"><u>{text}</u>{tail}</a>', style)


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


def callout(text, fill, border, bold_lead=None, style=td):
    txt = (f"<b>{bold_lead}</b> " if bold_lead else "") + text.replace("\n", "<br/>")
    t = Table([[Paragraph(txt, style)]], colWidths=[CW])
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
          ("LEFTPADDING", (0, 0), (-1, -1), 7),
          ("RIGHTPADDING", (0, 0), (-1, -1), 7),
          ("TOPPADDING", (0, 0), (-1, -1), 6),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    for i in range(1, len(data)):
        if i % 2 == 0:
            st.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(st))
    return t


def on_page(c, doc):
    c.saveState()
    c.setFont("DJ", 8.5); c.setFillColor(GREY)
    c.drawString(LM, 8 * mm, "План питания · коксартроз 4 ст.")
    if c.getPageNumber() > 1:
        c.drawCentredString(PW / 2, 8 * mm, "к оглавлению — стр. 1")
    c.drawRightString(PW - RM, 8 * mm, "стр. %d" % c.getPageNumber())
    c.setStrokeColor(LINE); c.setLineWidth(0.6); c.line(LM, 11.5 * mm, PW - RM, 11.5 * mm)
    c.restoreState()


# ═══════════════════════════════════ НАВИГАЦИЯ
STEPS = [
    ("ШАГ 1", "Понять главное правило — почему нельзя переедать",
     [("Внутрибрюшное давление", "sec3"), ("Сколько есть", "sec5")]),
    ("ШАГ 2", "Научиться готовить по-новому",
     [("Как готовить", "sec7"), ("Тарелка", "sec6")]),
    ("ШАГ 3", "Сходить в магазин",
     [("Покупки", "sec14"), ("Чем заменить", "sec12")]),
    ("ШАГ 4", "Начать есть",
     [("Меню на 14 дней", "sec10"), ("Или собрать самому", "sec11")]),
    ("ШАГ 5", "Подключить добавки — не все сразу",
     [("Что и когда пить", "sec15"), ("Как выбрать в аптеке", "sec16")]),
    ("ШАГ 6", "Восстановить слизистые и почистить кишечник",
     [("Слизистые", "sec8"), ("Очистка", "sec9")]),
    ("ШАГ 7", "Сдать анализы и показаться кардиологу",
     [("Анализы", "sec17"), ("С чего начать", "sec19")]),
]

QUICK = [
    ("Что мне сегодня есть?", "sec10"),
    ("Не хочу по таблице — хочу собрать сам", "sec11"),
    ("Чем заменить сахар, хлеб, молоко?", "sec12"),
    ("Сколько есть, чтобы не переесть?", "sec5"),
    ("Как готовить, чтобы желудок принял?", "sec7"),
    ("Что мне нельзя и почему?", "sec13"),
    ("Что купить и где?", "sec14"),
    ("Какие добавки, когда и с чем?", "sec15"),
    ("Как выбрать добавку в аптеке?", "sec16"),
    ("Что есть для восстановления желудка?", "sec8"),
    ("Как чистить кишечник?", "sec9"),
    ("Какие анализы сдать?", "sec17"),
    ("Когда срочно к врачу?", "sec18"),
    ("Почему всё именно так?", "sec1"),
]


def build_story():
    st = []; A = st.append
    A(Paragraph(D.TITLE, h1))
    A(Paragraph(D.SUBTITLE, sub))

    A(callout("Сначала — к кардиологу с холтером. Пока нет заключения: никаких нагрузок, "
              "разгрузочных дней и голодания. Подробно — раздел 1, стр. %s."
              % PAGES.get("warn", "2"),
              RED, REDB, bold_lead="ВАЖНО."))
    A(Spacer(1, 10))

    A(callout("Не читай документ целиком. Открой нужный пункт — ссылки кликабельные, "
              "нажатие перебрасывает на нужную страницу. Внизу каждой страницы написано, "
              "что оглавление на стр. 1.", ACC, HexColor("#D6A400"),
              bold_lead="КАК ПОЛЬЗОВАТЬСЯ."))
    A(Spacer(1, 12))

    A(Paragraph("ПОРЯДОК ДЕЙСТВИЙ", h3))
    rows = []
    for num, what, links in STEPS:
        cell = "<br/>".join(
            f'<a href="#{d}" color="#1B5FA8"><u>{t}</u></a>'
            f'{"  · стр. " + str(PAGES[d]) if d in PAGES else ""}'
            for t, d in links)
        rows.append([num, what, Paragraph(cell, td)])
    t = Table([[P(x, th) for x in ["Шаг", "Что делаем", "Куда смотреть"]]] +
              [[P(r[0], tdb), P(r[1], td), r[2]] for r in rows],
              colWidths=[CW * .12, CW * .48, CW * .40], repeatRows=1)
    stl = [("BACKGROUND", (0, 0), (-1, 0), HEAD),
           ("GRID", (0, 0), (-1, -1), 0.6, LINE),
           ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]
    for i in range(1, len(rows) + 1):
        if i % 2 == 0:
            stl.append(("BACKGROUND", (0, i), (-1, i), BAND))
    t.setStyle(TableStyle(stl))
    A(t)

    A(PageBreak())
    A(Paragraph("БЫСТРЫЙ ПОИСК — нажми на вопрос", h3))
    A(Paragraph("Открыл документ, нашёл свой вопрос, нажал — попал куда нужно.", note))
    qrows = [[Paragraph(f'{q}', navq),
              Paragraph(f'<a href="#{d}" color="#1B5FA8"><u>смотреть</u></a>'
                        f'{"  · стр. " + str(PAGES[d]) if d in PAGES else ""}', navl)]
             for q, d in QUICK]
    qt = Table([[P("Вопрос", th), P("Ответ здесь", th)]] + qrows,
               colWidths=[CW * .64, CW * .36], repeatRows=1)
    qstl = [("BACKGROUND", (0, 0), (-1, 0), HEAD),
            ("GRID", (0, 0), (-1, -1), 0.6, LINE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]
    for i in range(1, len(qrows) + 1):
        if i % 2 == 0:
            qstl.append(("BACKGROUND", (0, i), (-1, i), BAND))
    qt.setStyle(TableStyle(qstl))
    A(qt)
    A(PageBreak())

    # ───────────── 1
    st += band("1. ПОЧЕМУ ПЛАН ИМЕННО ТАКОЙ", "sec1")
    A(Spacer(1, 6))
    A(Anchor("warn"))
    A(callout(D.CARDIO_WARNING, RED, REDB))
    A(Spacer(1, 8))
    for i, line in enumerate(D.RATIONALE, 1):
        A(Paragraph(f"<b>{i}.</b> {line}", body))
    A(Spacer(1, 6))
    A(callout(D.CONTROL_NOTE, ACC, HexColor("#D6A400")))

    def sec(n, title, dest):
        st.append(CondPageBreak(170)); st.append(Spacer(1, 10))
        st.extend(band(f"{n}. {title}", dest))
        st.append(Spacer(1, 6))

    sec(2, "РЕЖИМ — два приёма в день, без перекусов", "sec2")
    A(grid(D.MODES_HEAD, D.MODES, [CW * .18, CW * .37, CW * .45], bold_first=True))
    A(Paragraph(D.MODES_NOTE, note))

    sec(3, "ГЛАВНЫЙ МЕХАНИЗМ — ВНУТРИБРЮШНОЕ ДАВЛЕНИЕ", "sec3")
    A(callout(D.PRESSURE_RULE, ACC, HexColor("#D6A400")))
    A(Spacer(1, 6))
    A(Paragraph("Замкнутый круг, который мы разрываем", h3))
    A(grid(D.PRESSURE_HEAD, D.PRESSURE, [CW * .17, CW * .32, CW * .51], bold_first=True))
    A(Spacer(1, 6))
    A(Paragraph("Чем именно разрываем", h3))
    pb = grid(D.PRESSURE_BREAK_HEAD, D.PRESSURE_BREAK, [CW * .38, CW * .62], bold_first=True)
    pb.setStyle(TableStyle([("BACKGROUND", (0, i), (0, i), GRN)
                            for i in range(1, len(D.PRESSURE_BREAK) + 1)]))
    A(pb)

    sec(4, "ЧТО МЫ ХОТИМ УСВОИТЬ И ЧТО ЭТОМУ МЕШАЕТ", "sec4")
    A(grid(D.ABSORB_HEAD, D.ABSORB, [CW * .12, CW * .26, CW * .26, CW * .36],
           bold_first=True))
    A(Paragraph(D.ABSORB_NOTE, note))

    sec(5, "СКОЛЬКО ЕСТЬ — граммов нет, есть сигналы тела", "sec5")
    A(grid(D.ENOUGH_HEAD, D.ENOUGH, [CW * .33, CW * .34, CW * .33], bold_first=True))
    A(Paragraph(D.ENOUGH_NOTE, note))

    sec(6, "ТАРЕЛКА — ориентир, а не измерение", "sec6")
    A(grid(D.PLATE_HEAD, D.PLATE, [CW * .15, CW * .42, CW * .43], bold_first=True))
    A(Paragraph(D.PLATE_NOTE, note))

    sec(7, "КАК ГОТОВИТЬ — мягко, тепло, без сырого", "sec7")
    A(grid(D.COOK_HEAD, D.COOKING, [CW * .21, CW * .41, CW * .38], bold_first=True))

    sec(8, "ПРОТОКОЛ ВОССТАНОВЛЕНИЯ СЛИЗИСТЫХ", "sec8")
    A(Paragraph("Продукты, которые работают на слизистую. Постоянно, а не курсом", h3))
    A(grid(D.MUCOSA_HEAD, D.MUCOSA, [CW * .26, CW * .37, CW * .37], bold_first=True))
    A(Spacer(1, 6))
    A(Paragraph("Чего в этом протоколе нет — и почему", h3))
    mo = grid(D.MUCOSA_OUT_HEAD, D.MUCOSA_OUT, [CW * .30, CW * .70], bold_first=True)
    mo.setStyle(TableStyle([("BACKGROUND", (0, i), (0, i), RED)
                            for i in range(1, len(D.MUCOSA_OUT) + 1)]))
    A(mo)

    sec(9, "МЯГКАЯ ОЧИСТКА КИШЕЧНИКА — псиллиум по нарастающей", "sec9")
    A(grid(D.CLEAN_HEAD, D.CLEANSE, [CW * .19, CW * .22, CW * .59], bold_first=True))
    A(Paragraph(D.CLEANSE_NOTE, note))

    sec(10, "МЕНЮ НА 14 ДНЕЙ — готовая таблица", "sec10")
    menu_rows = [[f"День {i}", m[0], m[1], m[2]] for i, m in enumerate(D.MENU, 1)]
    A(grid(D.MENU_HEAD, menu_rows, [CW * .09, CW * .30, CW * .30, CW * .31],
           bold_first=True))
    for n in D.MENU_NOTES:
        A(Paragraph("• " + n, note))

    sec(11, "КОНСТРУКТОР — собери тарелку сам", "sec11")
    A(grid(D.CONSTRUCTOR_HEAD, D.CONSTRUCTOR, [CW * .24, CW * .76], bold_first=True))

    sec(12, "ЗАМЕНЫ — чем закрыть сахар, глютен и молочку", "sec12")
    for gname, rows in D.SWAP_GROUPS:
        A(KeepTogether([Paragraph(gname, h3),
                        grid(D.SWAP_HEAD, rows, [CW * .26, CW * .50, CW * .24])]))
        A(Spacer(1, 5))

    sec(13, "ИСКЛЮЧЕНИЯ — и причина по каждому пункту", "sec13")
    ex = grid(D.EXCL_HEAD, D.EXCLUSIONS, [CW * .33, CW * .67], bold_first=True)
    ex.setStyle(TableStyle([("BACKGROUND", (0, i), (0, i), RED)
                            for i in range(1, len(D.EXCLUSIONS) + 1)]))
    A(ex)

    sec(14, "ПОКУПКИ — рынок в приоритете", "sec14")
    shop_rows = []
    for cat, what, rynok, vv, per, pyat in D.SHOP:
        parts = []
        for lbl, v in (("Рынок", rynok), ("ВкусВилл", vv),
                       ("Перекрёсток", per), ("Пятёрочка", pyat)):
            if v == "лучше всего":
                parts.append(f"<b>{lbl} — лучше всего</b>")
            elif v == "есть":
                parts.append(lbl)
            elif v in ("—", "нет"):
                continue
            else:
                parts.append(f"{lbl} ({v})")
        shop_rows.append([cat, what, " · ".join(parts) or "только аптека"])
    A(grid(["Категория", "Что берём", "Где брать"], shop_rows,
           [CW * .16, CW * .42, CW * .42], bold_first=True))
    A(Paragraph(D.SHOP_NOTE, note))

    sec(15, "ДОБАВКИ — что, сколько и когда", "sec15")
    supp_rows = [[w, dose, f"{when}.<br/>{apart}", why]
                 for w, dose, when, apart, why in D.SUPPLEMENTS]
    A(grid(["Что", "Доза", "Когда и с чем разносить", "Зачем"], supp_rows,
           [CW * .17, CW * .15, CW * .32, CW * .36], bold_first=True))
    for n in D.SUPP_NOTES:
        A(Paragraph("• " + n, note))

    sec(16, "КАЧЕСТВО ДОБАВОК — как читать состав на банке", "sec16")
    q = grid(D.QUALITY_HEAD, D.QUALITY, [CW * .18, CW * .34, CW * .48], bold_first=True)
    q.setStyle(TableStyle([("BACKGROUND", (2, i), (2, i), RED)
                           for i in range(1, len(D.QUALITY) + 1)]))
    A(q)
    for n in D.QUALITY_WHY:
        A(Paragraph("• " + n, note))

    sec(17, "АНАЛИЗЫ К ДОСДАЧЕ", "sec17")
    A(grid(D.LABS_HEAD, D.LABS, [CW * .25, CW * .75], bold_first=True))

    sec(18, "КРАСНЫЕ ФЛАГИ — когда немедленно к врачу", "sec18")
    rf = grid(D.RED_HEAD, D.RED_FLAGS, [CW * .53, CW * .47], bold_first=True)
    rf.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), RED)
                            for i in range(1, len(D.RED_FLAGS) + 1)]))
    A(rf)

    sec(19, "С ЧЕГО НАЧАТЬ", "sec19")
    A(grid(D.START_HEAD, D.START, [CW * .08, CW * .68, CW * .24], center=(0,)))

    A(Spacer(1, 8))
    A(callout(D.DISCLAIMER, ACC, HexColor("#D6A400"), bold_lead="Важно."))
    return st


out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plan-coxarthrosis-53m.pdf")


def render(path):
    doc = BaseDocTemplate(path, pagesize=A4, leftMargin=LM, rightMargin=RM,
                          topMargin=TM, bottomMargin=BM,
                          title=D.TITLE, subject=D.SUBTITLE,
                          author="Нутрициология · Анатомия Здоровья")
    doc.addPageTemplates([PageTemplate(
        id="p", frames=[Frame(LM, BM, CW, PH - TM - BM, id="m", leftPadding=0,
                              rightPadding=0, topPadding=0, bottomPadding=0)],
        onPage=on_page)])
    doc.build(build_story())
    return doc


tmp = out + ".pass1"
render(tmp)                     # проход 1: узнаём, на какой странице каждый раздел
os.remove(tmp)
render(out)                     # проход 2: печатаем номера страниц в навигации
print("saved:", out)
print("якорей:", len(PAGES), "| страницы разделов:",
      {k: v for k, v in sorted(PAGES.items(), key=lambda x: x[1])})
