import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # Твой Telegram chat_id

SYSTEM_PROMPT = (
    "Ты помощник кинезиолога Александра Бондаря. "
    "УТП: устранение боли за 1 приём или бесплатно. "
    "Отвечай на русском. Для записи направляй к @alexbond9232."
)

# Состояния анкеты
NAME, CITY, PHONE, PROBLEM = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📝 Заполнить анкету", callback_data="open_form")]]
    await update.message.reply_text(
        "Привет! Я помощник кинезиолога Александра Бондаря.\n\n"
        "✅ <b>Устранение боли за 1 приём — или бесплатно!</b>\n\n"
        "Задайте вопрос прямо здесь или заполните анкету для записи:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def open_form_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопки «Заполнить анкету» из /start."""
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Как вас зовут? (Имя и фамилия)")
    return NAME


async def anketa_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /anketa — запуск анкеты."""
    await update.message.reply_text("Как вас зовут? (Имя и фамилия)")
    return NAME


async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    city_keyboard = [["🏙 Москва", "🌆 Брянск"]]
    await update.message.reply_text(
        "В каком городе вы находитесь?",
        reply_markup=ReplyKeyboardMarkup(city_keyboard, one_time_keyboard=True, resize_keyboard=True),
    )
    return CITY


async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text(
        "Укажите ваш номер телефона:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return PHONE


async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text("Опишите вашу проблему / что болит:")
    return PROBLEM


async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["problem"] = update.message.text.strip()
    user = update.message.from_user

    # Ссылка для перехода в чат с клиентом
    if user.username:
        chat_url = f"https://t.me/{user.username}"
    else:
        chat_url = f"tg://user?id={user.id}"

    username_display = f"@{user.username}" if user.username else f"ID: {user.id}"

    admin_text = (
        f"🔔 <b>Новая анкета!</b>\n\n"
        f"👤 <b>Имя:</b> {context.user_data['name']}\n"
        f"📱 <b>Telegram:</b> {username_display}\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"🌆 <b>Город:</b> {context.user_data['city']}\n"
        f"📞 <b>Телефон:</b> {context.user_data['phone']}\n"
        f"💬 <b>Проблема:</b> {context.user_data['problem']}"
    )

    admin_keyboard = [[InlineKeyboardButton("💬 Написать клиенту", url=chat_url)]]

    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=admin_text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(admin_keyboard),
            )
        except Exception as e:
            logger.error(f"Не удалось уведомить администратора: {e}")
    else:
        logger.warning("ADMIN_CHAT_ID не задан — уведомление не отправлено.")

    await update.message.reply_text(
        "✅ Спасибо! Анкета отправлена.\n\n"
        "Александр свяжется с вами в ближайшее время.\n"
        "Также можете написать напрямую: @alexbond9232"
    )
    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Анкета отменена. Если нужна помощь — просто напишите!",
        reply_markup=ReplyKeyboardRemove(),
    )
    return ConversationHandler.END


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        )
        payload = {
            "contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\nВопрос: " + user_message}]}]
        }
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Ошибка. Напишите: @alexbond9232")


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("anketa", anketa_start),
            CallbackQueryHandler(open_form_callback, pattern="^open_form$"),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
