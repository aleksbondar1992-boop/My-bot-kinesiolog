import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = """Ты — AI-помощник кинезиолога Александра Бондаря.
Помогаешь клиентам узнать о кинезиологии и записаться на приём.
УТП: устранение боли за 1 приём или бесплатно.
Отвечай тепло, на русском. Для записи направляй к @alexbond9232."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋 Я помощник кинезиолога Александра Бондаря.\n\n"
        "Помогу узнать о методах работы с болью или записаться на приём.\n\n"
        "Задайте любой вопрос! 💪"
    )

async def handle_message(update:
