import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8906743609:AAF18d4NpgVFMzIezonpIIfWzK8ZKprxW2U")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "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")
CHANNEL_ID     = -1001752114983
OWNER_ID       = 8693573187

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — AI-ассистент Александра Бондаря, кинезиолога и нутрициолога из Москвы.
Александр работает с болями, стрессом, лишним весом и осанкой через тело и психику.
Принимает в ZillArt (Москва). Контакт: @alexbond9232, +79155378233.
Форматы: Точечная коррекция 10 000 ₽, Полная Трансформация 15 000 ₽, Детский 8 000 ₽.
Пакеты: 3 сессии -10%, 5 сессий -15%, 8 сессий -20%. Гарантия результата.
Пиши посты живо, от первого лица, с эмодзи, 150-300 слов."""

draft_posts = {}

def ask_groq(prompt, system=SYSTEM_PROMPT):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 800
    }
    r = requests.post(url, headers=headers, json=data, timeout=30)
    return r.json()["choices"][0]["message"]["content"]

def is_owner(update):
    return update.effective_user.id == OWNER_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    await update.message.reply_text(
        "👋 Привет, Александр!\n\n"
        "Команды:\n"
        "📝 /post [тема] — написать пост\n"
        "📅 /week — план на неделю\n"
        "📣 /announce [город дата] — анонс выезда\n"
        "💰 /price — пост о ценах\n"
        "💬 /ask [вопрос] — любой вопрос\n\n"
        "Или просто напиши мне!"
    )

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not context.args:
        await update.message.reply_text("Напиши тему. Пример: /post осанка")
        return
    topic = " ".join(context.args)
    msg = await update.message.reply_text(f"✍️ Пишу пост: «{topic}»...")
    text = ask_groq(f"Напиши пост для Telegram-канала на тему: {topic}. От первого лица.")
    draft_posts[OWNER_ID] = text
    kb = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
        InlineKeyboardButton("🔄 Переписать", callback_data=f"rewrite_{topic}"),
    ]]
    await msg.edit_text(f"📝 Черновик:\n\n{text}", reply_markup=InlineKeyboardMarkup(kb))

async def week_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    msg = await update.message.reply_text("📅 Составляю план...")
    text = ask_groq("Составь план 7 постов на неделю. День недели + тема + краткое описание.")
    await msg.edit_text(f"📅 План на неделю:\n\n{text}")

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not context.args:
        await update.message.reply_text("Пример: /announce Брянск 15-16 июня")
        return
    info = " ".join(context.args)
    msg = await update.message.reply_text(f"📣 Пишу анонс: {info}...")
    text = ask_groq(f"Напиши анонс выезда в {info}. Коротко, с призывом записаться через @alexbond9232")
    draft_posts[OWNER_ID] = text
    kb = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
        InlineKeyboardButton("🔄 Переписать", callback_data=f"rewrite_анонс {info}"),
    ]]
    await msg.edit_text(f"📣 Анонс:\n\n{text}", reply_markup=InlineKeyboardMarkup(kb))

async def price_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    msg = await update.message.reply_text("💰 Генерирую пост о ценах...")
    text = ask_groq("Напиши продающий пост о форматах и ценах приёмов. Укажи все цены и пакеты.")
    draft_posts[OWNER_ID] = text
    kb = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
        InlineKeyboardButton("🔄 Переписать", callback_data="rewrite_цены"),
    ]]
    await msg.edit_text(f"💰 Пост о ценах:\n\n{text}", reply_markup=InlineKeyboardMarkup(kb))

async def ask_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    if not context.args:
        await update.message.reply_text("Пример: /ask как ответить на возражение по цене")
        return
    question = " ".join(context.args)
    msg = await update.message.reply_text("🤔 Думаю...")
    text = ask_groq(question)
    await msg.edit_text(text)

async def free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    msg = await update.message.reply_text("💭...")
    text = ask_groq(update.message.text)
    await msg.edit_text(text)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != OWNER_ID: return

    if query.data == "publish":
        text = draft_posts.get(OWNER_ID)
        if not text:
            await query.edit_message_text("❌ Черновик не найден.")
            return
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
            await query.edit_message_text(f"✅ Опубликовано!\n\n{text}")
            draft_posts.pop(OWNER_ID, None)
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {e}")

    elif query.data.startswith("rewrite_"):
        topic = query.data.replace("rewrite_", "")
        await query.edit_message_text("🔄 Пишу другой вариант...")
        text = ask_groq(f"Напиши другой вариант поста на тему: {topic}. Другой угол подачи.")
        draft_posts[OWNER_ID] = text
        kb = [[
            InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
            InlineKeyboardButton("🔄 Ещё раз", callback_data=f"rewrite_{topic}"),
        ]]
        await query.edit_message_text(f"📝 Новый вариант:\n\n{text}", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", generate_post))
    app.add_handler(CommandHandler("week", week_plan))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("price", price_post))
    app.add_handler(CommandHandler("ask", ask_ai))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_chat))
    logger.info("Бот запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
