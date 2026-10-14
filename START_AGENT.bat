@echo off
title Jubayer AI Hunter - Mission Control
color 0A
echo =================================================================
echo        Jubayer AI Hunter & Career Agent - 1-Click Startup
echo =================================================================
echo.
echo [1/3] Setting up environment paths...
set PATH=%LOCALAPPDATA%\..\..\.tools\nodejs;%LOCALAPPDATA%\..\..\.tools\git\cmd;%PATH%

echo [2/3] Launching Background Engine & Telegram Gateway...
start "Jubayer Telegram Bot" /min python backend/main.py --bot

echo [3/3] Launching Mission Control Dashboard...
start "Jubayer Web Dashboard" /min python backend/main.py --web

timeout /t 2 >nul
echo.
echo Opening Dashboard in your default browser...
start http://127.0.0.1:8000

echo.
echo =================================================================
echo  STATUS: ACTIVE AND RUNNING 24/7!
echo  - Web Dashboard: http://127.0.0.1:8000
echo  - Telegram Bot:  https://t.me/Jubayer_agent_bot
echo.
echo  Keep this window open or minimized while you work.
echo =================================================================
pause
