@echo off
chcp 65001 >nul
title Claude Remote Control - install
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Autostart.ps1"
echo.
pause
