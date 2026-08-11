@echo off
chcp 65001 >nul
title Claude Remote Control - stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Stop-RemoteControl.ps1"
echo.
pause
