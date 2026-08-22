@echo off
chcp 65001 >nul
title Пересортировка скачанного
cd /d "%~dp0"

echo ============================================================
echo   ПЕРЕСОРТИРОВКА: раскладывает уже скачанное заново
echo   (после того, как вы поправили слова в categories.json)
echo   Ничего не качается заново.
echo ============================================================
echo.

if not exist ".venv" (
  echo Сначала запустите 1_СКАЧАТЬ_КАНАЛ.bat
  pause
  exit /b 1
)

call ".venv\Scripts\activate.bat"
python export_channel.py --resort %*
echo.
pause
