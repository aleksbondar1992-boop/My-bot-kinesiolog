@echo off
chcp 65001 >nul
title Экспорт Telegram-канала на диск D
cd /d "%~dp0"

echo ============================================================
echo   ЭКСПОРТ КАНАЛА: всё, кроме видео, с раскладкой по папкам
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo Python не найден.
  echo Установите его с https://python.org/downloads
  echo ВАЖНО: при установке поставьте галочку "Add python.exe to PATH".
  echo.
  pause
  exit /b 1
)

if not exist ".venv" (
  echo Первый запуск: готовлю окружение, это займёт минуту...
  python -m venv .venv || goto :fail
)

call ".venv\Scripts\activate.bat"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt || goto :fail

python export_channel.py %*
echo.
pause
exit /b 0

:fail
echo.
echo Не удалось подготовить окружение. Проверьте интернет и попробуйте снова.
pause
exit /b 1
