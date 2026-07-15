# My-bot-kinesiolog

## AI Content Manager (v1)

Модуль `content_manager.py`: из **одного длинного видео** автоматически делает
**10 готовых сценариев Reels** — с сильными хуками, тайм-кодами и заголовками.

Каждый сценарий содержит:
- 🎣 **сильный хук** (первые 1–3 секунды, останавливают скролл);
- ⏱ **тайм-коды** фрагмента в исходном видео (что нарезать);
- 📝 **заголовок**, текст сценария по секундам, готовую подпись, хэштеги и CTA.

### Как работает
Модуль использует Google Gemini. Вход может быть:
1. **Видео-файл** (`.mp4`, `.mov`, …) — загружается в Gemini File API, тайм-коды
   берутся из нативного анализа видео (точные).
2. **Транскрипт** — текстовый файл (`.txt`/`.srt`/`.vtt`) или строка с текстом.

### Установка
```bash
pip install -r requirements.txt
export GEMINI_API_KEY="ваш_ключ"
```

### Запуск из терминала
```bash
# из видео → 10 сценариев в консоль (markdown)
python content_manager.py lecture.mp4

# из субтитров → сохранить как JSON
python content_manager.py transcript.srt --num 10 --output reels.json
```

### Использование из кода
```python
from content_manager import generate_reels_scripts, reels_to_markdown

reels = generate_reels_scripts("lecture.mp4")   # список из 10 ReelScript
print(reels_to_markdown(reels))
```
