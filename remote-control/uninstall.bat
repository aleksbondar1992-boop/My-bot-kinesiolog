@echo off
chcp 65001 >nul
title Claude Remote Control - uninstall
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall-Autostart.ps1"
echo.
pause
