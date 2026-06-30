import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Локальная модель (Hermes через Ollama / LM Studio и т.п.).
# Если задан LOCAL_AI_URL — бот использует локальную модель вместо Gemini.
# Пример для Ollama:    LOCAL_AI_URL=http://localhost:11434/v1/chat/completions
# Пример для LM Studio: LOCAL_AI_URL=http://localhost:1234/v1/chat/completions
LOCAL_AI_URL = os.environ.get("LOCAL_AI_URL")
LOCAL_AI_MODEL = os.environ.get("LOCAL_AI_MODEL", "hermes3:8b")

SYSTEM_PROMPT = "Ты помощник кинезиолога Александра Бондаря. УТП: устранение боли за 1 приём или бесплатно. Отвечай на русском. Для записи направляй к @alexbond9232."


def ask_local(user_message: str) -> str:
    """Запрос к локальной модели через OpenAI-совместимый API (Ollama, LM Studio)."""
    payload = {
        "model": LOCAL_AI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "stream": False,
    }
    response = requests.post(LOCAL_AI_URL, json=payload, timeout=120)
    data = response.json()
    return data["choices"][0]["message"]["content"]


def ask_gemini(user_message: str) -> str:
    """Запрос к облачной модели Gemini."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\nВопрос: " + user_message}]}]}
    response = requests.post(url, json=payload, timeout=30)
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я помощник кинезиолога Александра Бондаря. Задайте вопрос!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        if LOCAL_AI_URL:
            reply = ask_local(user_message)
        else:
            reply = ask_gemini(user_message)
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Ошибка. Напишите: @alexbond9232")


def main():
    if LOCAL_AI_URL:
        logger.info(f"AI backend: локальная модель {LOCAL_AI_MODEL} ({LOCAL_AI_URL})")
    else:
        logger.info("AI backend: Gemini (облако)")
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
