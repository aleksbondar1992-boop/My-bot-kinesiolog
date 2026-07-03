import os
import json
import logging
from datetime import datetime, date

import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

CONTACT = "@alexbond9232"

# --- Зодиакальные знаки: границы (месяц, день) начала каждого знака ---
ZODIAC = [
    ((1, 20), "Водолей", "♒"),
    ((2, 19), "Рыбы", "♓"),
    ((3, 21), "Овен", "♈"),
    ((4, 20), "Телец", "♉"),
    ((5, 21), "Близнецы", "♊"),
    ((6, 21), "Рак", "♋"),
    ((7, 23), "Лев", "♌"),
    ((8, 23), "Дева", "♍"),
    ((9, 23), "Весы", "♎"),
    ((10, 23), "Скорпион", "♏"),
    ((11, 22), "Стрелец", "♐"),
    ((12, 22), "Козерог", "♑"),
]

SYSTEM_PROMPT = (
    "Ты — доброжелательный персональный астролог. Говоришь тепло, образно и с "
    "заботой, на русском языке. Ты даёшь астрологические прогнозы и толкования "
    "на основе знака зодиака и даты рождения человека. Пиши живо, но без длинных "
    "вступлений — сразу по делу, 4-8 предложений. Не давай медицинских, "
    "юридических или финансовых гарантий. Заканчивай мягким ободряющим советом."
)

MENU = ReplyKeyboardMarkup(
    [["🔮 Прогноз на сегодня", "💫 Мой знак"], ["❤️ Совместимость", "✍️ Задать вопрос"]],
    resize_keyboard=True,
)


def zodiac_sign(d: date):
    """Определяет знак зодиака по дате рождения."""
    sign = ZODIAC[-1]  # Козерог по умолчанию (конец/начало года)
    for (month, day), name, symbol in ZODIAC:
        if (d.month, d.day) >= (month, day):
            sign = ((month, day), name, symbol)
    _, name, symbol = sign
    return name, symbol


def parse_birthdate(text: str):
    """Парсит дату рождения в форматах ДД.ММ.ГГГГ, ДД/ММ/ГГГГ, ДД-ММ-ГГГГ."""
    text = text.strip()
    for sep in (".", "/", "-", " "):
        parts = text.split(sep)
        if len(parts) == 3:
            try:
                day, month, year = (int(p) for p in parts)
                return date(year, month, day)
            except ValueError:
                continue
    return None


def ask_gemini(prompt: str) -> str:
    """Обращается к Gemini и возвращает текст ответа."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY не задан")
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}]
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def profile(context: ContextTypes.DEFAULT_TYPE) -> dict:
    return context.user_data.setdefault("profile", {})


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "✨ Приветствую! Я твой персональный астролог.\n\n"
        "Расскажи звёздам о себе — пришли дату рождения в формате "
        "*ДД.ММ.ГГГГ* (например, 07.03.1992), и я определю твой знак зодиака "
        "и составлю персональный прогноз.\n\n"
        "Команды: /segodnya — прогноз на сегодня, /znak — твой знак, /reset — сбросить данные."
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=MENU)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🌙 Данные сброшены. Пришли новую дату рождения (ДД.ММ.ГГГГ).",
        reply_markup=MENU,
    )


async def znak(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prof = profile(context)
    if "sign" not in prof:
        await update.message.reply_text(
            "Сначала пришли дату рождения в формате ДД.ММ.ГГГГ 🙂"
        )
        return
    await update.message.reply_text(
        f"Твой знак зодиака — {prof['symbol']} *{prof['sign']}*.",
        parse_mode="Markdown",
    )


async def segodnya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prof = profile(context)
    if "sign" not in prof:
        await update.message.reply_text(
            "Сначала пришли дату рождения в формате ДД.ММ.ГГГГ 🙂"
        )
        return
    today = datetime.now().strftime("%d.%m.%Y")
    prompt = (
        f"Составь персональный астрологический прогноз на сегодня ({today}) для "
        f"человека, знак зодиака — {prof['sign']}, дата рождения {prof['birthdate']}. "
        "Затрони любовь, работу/финансы и внутреннее состояние. Добавь счастливое "
        "число и цвет дня."
    )
    await _reply_with_gemini(update, prompt)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prof = profile(context)
    text = (update.message.text or "").strip()

    # Кнопки меню
    if text.startswith("🔮"):
        await segodnya(update, context)
        return
    if text.startswith("💫"):
        await znak(update, context)
        return
    if text.startswith("❤️"):
        context.user_data["awaiting"] = "compat"
        await update.message.reply_text(
            "С каким знаком проверить совместимость? Напиши название знака 💞"
        )
        return
    if text.startswith("✍️"):
        context.user_data["awaiting"] = "question"
        await update.message.reply_text(
            "Задай свой вопрос звёздам — я отвечу с учётом твоего знака 🌟"
        )
        return

    # Ожидаем дату рождения, если её ещё нет
    if "sign" not in prof:
        d = parse_birthdate(text)
        if d:
            name, symbol = zodiac_sign(d)
            prof.update(
                {
                    "birthdate": d.strftime("%d.%m.%Y"),
                    "sign": name,
                    "symbol": symbol,
                }
            )
            await update.message.reply_text(
                f"Готово! Твой знак — {symbol} *{name}*.\n\n"
                "Составляю первый персональный прогноз… 🔮",
                parse_mode="Markdown",
                reply_markup=MENU,
            )
            await segodnya(update, context)
            return
        await update.message.reply_text(
            "Не смог распознать дату 😔 Пришли её в формате *ДД.ММ.ГГГГ*, "
            "например 07.03.1992.",
            parse_mode="Markdown",
        )
        return

    # Совместимость
    if context.user_data.pop("awaiting", None) == "compat":
        prompt = (
            f"Разбери любовную и дружескую совместимость знака {prof['sign']} "
            f"со знаком, который человек назвал: «{text}». Дай оценку в процентах, "
            "сильные и слабые стороны пары и совет."
        )
        await _reply_with_gemini(update, prompt)
        return

    # Свободный вопрос / был запрос вопроса
    context.user_data.pop("awaiting", None)
    prompt = (
        f"Человек (знак {prof['sign']}, дата рождения {prof['birthdate']}) "
        f"спрашивает: «{text}». Ответь как персональный астролог."
    )
    await _reply_with_gemini(update, prompt)


async def _reply_with_gemini(update: Update, prompt: str):
    try:
        reply = ask_gemini(prompt)
        await update.message.reply_text(reply, reply_markup=MENU)
    except Exception as e:  # noqa: BLE001
        logger.error("Gemini error: %s", e)
        await update.message.reply_text(
            f"Звёзды сейчас молчат ⭐️ Попробуй позже или напиши {CONTACT}."
        )


def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("znak", znak))
    app.add_handler(CommandHandler("segodnya", segodnya))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Персональный астролог запущен")
    app.run_polling()


if __name__ == "__main__":
    main()
