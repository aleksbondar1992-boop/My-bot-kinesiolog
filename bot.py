import os
import logging

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
CONTACT = os.environ.get("CONTACT_USERNAME", "@alexbond9232")
# Куда присылать заявки. Свой ID можно узнать у @userinfobot.
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = f"""Ты помощник кинезиолога Александра Бондаря.

УТП: устранение боли за 1 приём или бесплатно.

Как отвечать:
- Только на русском языке.
- Коротко: 3-5 предложений, без воды и без списков на десять пунктов.
- Спрашивай, что именно и как давно болит — это помогает человеку раскрыться.
- Не ставь диагнозов и не назначай лечение. Ты не врач.
- Если человек описывает боль, объясни, с чем это может быть связано с точки
  зрения кинезиологии, и предложи записаться на приём.
- Для записи говори про команду /zapis, а не про личные сообщения.

Красные флаги. Если человек упоминает что-то из этого, сразу и прямо скажи
обратиться к врачу очно, без попыток разбирать случай: травма с сильным отёком,
онемение обеих ног, потеря контроля над мочеиспусканием, резкая потеря веса,
температура вместе с болью в спине, боль в груди.

Контакт для срочных вопросов: {CONTACT}"""

GREETING = (
    "Привет! Я помощник кинезиолога Александра Бондаря.\n\n"
    "Расскажите, что беспокоит — что болит и как давно. "
    "Разберём, с чем это может быть связано.\n\n"
    "Готовы записаться на приём — отправьте /zapis"
)

LEAD_PROMPT = (
    "Записываю. Отправьте одним сообщением:\n\n"
    "1. Имя\n"
    "2. Телефон или @username\n"
    "3. Что болит и как давно\n\n"
    "Например: «Игорь, +79001234567, поясница, третью неделю»"
)

FALLBACK = f"Что-то пошло не так. Напишите напрямую: {CONTACT}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("awaiting_lead", None)
    await update.message.reply_text(GREETING)


async def zapis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["awaiting_lead"] = True
    await update.message.reply_text(LEAD_PROMPT)


async def save_lead(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пересылает заявку администратору. Заявка не теряется, даже если пересылка упала."""
    user = update.effective_user
    username = f"@{user.username}" if user.username else "без username"
    lead = (
        "🔥 НОВАЯ ЗАЯВКА\n\n"
        f"{update.message.text}\n\n"
        f"От: {user.full_name} ({username})\n"
        f"ID: {user.id}"
    )

    logger.info("LEAD | %s (%s) | %s", user.full_name, user.id, update.message.text)

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=lead)
        except Exception:
            logger.exception("Не удалось отправить заявку админу")
    else:
        logger.warning("ADMIN_CHAT_ID не задан — заявка осталась только в логах")

    context.user_data.pop("awaiting_lead", None)
    await update.message.reply_text(
        "Записал, спасибо! Александр свяжется с вами в ближайшее время.\n\n"
        f"Если срочно — пишите сразу: {CONTACT}"
    )


async def ask_gemini(user_message: str) -> str:
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_message}]}],
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            GEMINI_URL, json=payload, params={"key": GEMINI_API_KEY}
        )
        response.raise_for_status()
        data = response.json()

    candidates = data.get("candidates")
    if not candidates:
        # Обычно это срабатывание фильтра безопасности Gemini.
        logger.warning("Gemini вернул пустой ответ: %s", data.get("promptFeedback"))
        raise ValueError("no candidates")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise ValueError("empty text")
    return text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get("awaiting_lead"):
        await save_lead(update, context)
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        reply = await ask_gemini(update.message.text)
    except httpx.HTTPStatusError as e:
        logger.error("Gemini HTTP %s: %s", e.response.status_code, e.response.text[:500])
        await update.message.reply_text(FALLBACK)
    except Exception:
        logger.exception("Ошибка при обращении к Gemini")
        await update.message.reply_text(FALLBACK)
    else:
        await update.message.reply_text(reply)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Необработанная ошибка", exc_info=context.error)


def main() -> None:
    missing = [
        name
        for name, value in (
            ("TELEGRAM_BOT_TOKEN", TELEGRAM_TOKEN),
            ("GEMINI_API_KEY", GEMINI_API_KEY),
        )
        if not value
    ]
    if missing:
        raise SystemExit(
            "Не заданы переменные окружения: "
            + ", ".join(missing)
            + ". Пропишите их в настройках хостинга и перезапустите."
        )

    if not ADMIN_CHAT_ID:
        logger.warning(
            "ADMIN_CHAT_ID не задан — заявки будут только в логах. "
            "Свой ID можно узнать у @userinfobot."
        )

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("zapis", zapis))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(on_error)

    logger.info("Бот запущен, модель %s", GEMINI_MODEL)
    app.run_polling()


if __name__ == "__main__":
    main()
