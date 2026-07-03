# My-bot-kinesiolog

Телеграм-боты на `python-telegram-bot` + Gemini API.

## Боты

- **`bot.py`** — помощник кинезиолога Александра Бондаря.
- **`astrolog_bot.py`** — 🔮 персональный астролог: определяет знак зодиака по дате
  рождения, даёт прогноз на день, проверяет совместимость и отвечает на вопросы.

## Переменные окружения

- `TELEGRAM_BOT_TOKEN` — токен бота из @BotFather
- `GEMINI_API_KEY` — ключ Google Gemini API

## Запуск

```bash
pip install -r requirements.txt
python astrolog_bot.py   # персональный астролог
python bot.py            # помощник кинезиолога
```

## Команды астролога

- `/start` — начать, прислать дату рождения
- `/segodnya` — прогноз на сегодня
- `/znak` — твой знак зодиака
- `/reset` — сбросить данные
