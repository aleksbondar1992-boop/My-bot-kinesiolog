import os
import logging
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = "Ты помощник кинезиолога Александра Бондаря. УТП: устранение боли за 1 приём или бесплатно. Отвечай на русском. Для записи направляй к @alexbond9232."

def start(update, context):
    update.message.reply_text("Привет! Я помощник кинезиолога Александра Бондаря. Задайте вопрос!")

def handle_message(update, context):
    user_message = update.message.text
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": SYSTEM_PROMPT + "\n\nВопрос: " + user_message}]}]}
        response = requests.post(url, json=payload, timeout=30)
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        update.message.reply_text(reply)
    except Exception as e:
        logger.error(f"Error: {e}")
        update.message.reply_text("Ошибка. Напишите: @alexbond9232")

def main():
    updater = Updater(TELEGRAM_TOKEN)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
