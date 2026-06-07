import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from groq import Groq

# ─── НАСТРОЙКИ ───────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8906743609:AAF18d4NpgVFMzIezonpIIfWzK8ZKprxW2U")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "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")
CHANNEL_ID     = -1001752114983
OWNER_ID       = 8693573187  # Только Александр может управлять ботом

logging.basicConfig(level=logging.INFO)
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Ты — AI-ассистент Александра Бондаря, кинезиолога и нутрициолога из Москвы.

О хозяине:
- Александр работает с болями, стрессом, лишним весом и осанкой через тело и психику
- Принимает в ZillArt (Москва), выезжает в города (Брянск и др.)
- Форматы: Точечная коррекция 10 000 ₽, Полная Трансформация 15 000 ₽, Детский приём 8 000 ₽
- Пакеты: 3 сессии -10%, 5 сессий -15%, 8 сессий -20%
- Гарантия: если нет результата — не берёт деньги
- Контакт: @alexbond9232, +79155378233

Стиль постов Александра:
- Пишет живо, по-человечески, без официоза
- Часто использует личный опыт и кейсы клиентов
- Смешивает экспертность с простотой
- Добавляет призыв к действию в конце
- Использует эмодзи умеренно
- Длина поста: 150-300 слов

Когда пишешь посты — пиши от первого лица (от имени Александра).
Когда отвечаешь на вопросы — отвечай как ассистент Александра.
"""

draft_posts = {}

def is_owner(update: Update) -> bool:
    return update.effective_user.id == OWNER_ID

async def check_owner(update: Update) -> bool:
    if not is_owner(update):
        await update.message.reply_text("⛔️ Доступ только для Александра.")
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_owner(update): return
    await update.message.reply_text(
        "👋 Привет, Александр!\n\n"
        "Я твой AI-ассистент. Вот что умею:\n\n"
        "📝 /post [тема] — написать пост для канала\n"
        "📅 /week — план постов на неделю\n"
        "📣 /announce [город дата] — анонс выезда\n"
        "💰 /price — пост о ценах и форматах\n"
        "💬 /ask [вопрос] — любой вопрос к AI\n\n"
        "Или просто напиши мне — отвечу!"
    )

async def generate_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_owner(update): return
    if not context.args:
        await update.message.reply_text("Напиши тему. Например:\n/post осанка и боли в спине")
        return
    topic = " ".join(context.args)
    msg = await update.message.reply_text(f"✍️ Пишу пост: «{topic}»...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Напиши пост для Telegram-канала на тему: {topic}. От первого лица, в стиле Александра."}
        ],
        max_tokens=800
    )
    post_text = response.choices[0].message.content
    draft_posts[OWNER_ID] = post_text
    keyboard = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
        InlineKeyboardButton("🔄 Переписать", callback_data=f"rewrite_{topic}"),
    ]]
    await msg.edit_text(
        f"📝 Черновик:\n\n{post_text}\n\n─────\nОпубликовать или переписать?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def week_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_owner(update): return
    msg = await update.message.reply_text("📅 Составляю план на неделю...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Составь план из 7 постов на неделю. Для каждого дня: день недели, тема, краткое описание о чём пост. Темы разнообразные: боли, осанка, питание, стресс, кейс клиента, мотивация, анонс."}
        ],
        max_tokens=1200
    )
    await msg.edit_text(f"📅 План на неделю:\n\n{response.choices[0].message.content}")

async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_owner(update): return
    if not context.args:
        await update.message.reply_text("Укажи город и дату. Например:\n/announce Брянск 15-16 июня")
        return
    info = " ".join(context.args)
    msg = await update.message.reply_text(f"📣 Пишу анонс: {info}...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Напиши анонс выезда Александра в {info}. Короткий, живой, с призывом записаться через @alexbond9232"}
        ],
        max_tokens=400
    )
    post_text = response.choices[0].message.content
    draft_posts[OWNER_ID] = post_text
    keyboard = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
        InlineKeyboardButton("🔄 Переписать", callback_data=f"rewrite_анонс {info}"),
    ]]
    await msg.edit_text(
        f"📣 Анонс:\n\n{post_text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def price_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_owner(update): return
    msg = await update.message.reply_text("💰 Генерирую пост о ценах...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Напиши продающий пост о форматах и ценах приёмов. Живо, с объяснением ценности. Укажи все цены и пакеты со скидками."}
        ],
        max_tokens=600
    )
    post_text = response.choices[0].message.content
    draft_posts[OWNER_ID] = post_text
    keyboard = [[
        InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
        InlineKeyboardButton("🔄 Переписать", callback_data="rewrite_цены"),
    ]]
    await msg.edit_text(
        f"💰 Пост о ценах:\n\n{post_text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_owner(update): return
    if not context.args:
        await update.message.reply_text("Задай вопрос. Например:\n/ask как ответить клиенту который сомневается в цене")
        return
    question = " ".join(context.args)
    msg = await update.message.reply_text("🤔 Думаю...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ],
        max_tokens=800
    )
    await msg.edit_text(response.choices[0].message.content)

async def free_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update): return
    msg = await update.message.reply_text("💭...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": update.message.text}
        ],
        max_tokens=800
    )
    await msg.edit_text(response.choices[0].message.content)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != OWNER_ID:
        return

    if query.data == "publish":
        post_text = draft_posts.get(OWNER_ID)
        if not post_text:
            await query.edit_message_text("❌ Черновик не найден. Создай новый пост.")
            return
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            await query.edit_message_text(f"✅ Пост опубликован в канале!\n\n{post_text}")
            draft_posts.pop(OWNER_ID, None)
        except Exception as e:
            await query.edit_message_text(f"❌ Ошибка: {e}")

    elif query.data.startswith("rewrite_"):
        topic = query.data.replace("rewrite_", "")
        await query.edit_message_text(f"🔄 Пишу другой вариант...")
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Напиши другой вариант поста на тему: {topic}. Другой угол подачи, другой стиль."}
            ],
            max_tokens=800
        )
        post_text = response.choices[0].message.content
        draft_posts[OWNER_ID] = post_text
        keyboard = [[
            InlineKeyboardButton("✅ Опубликовать", callback_data="publish"),
            InlineKeyboardButton("🔄 Ещё раз", callback_data=f"rewrite_{topic}"),
        ]]
        await query.edit_message_text(
            f"📝 Новый вариант:\n\n{post_text}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("post", generate_post))
    app.add_handler(CommandHandler("week", week_plan))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("price", price_template))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, free_chat))
    print("🤖 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
