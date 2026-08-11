@echo off
chcp 65001 >nul
title Claude Remote Control - start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-RemoteControl.ps1"
echo.
pause
