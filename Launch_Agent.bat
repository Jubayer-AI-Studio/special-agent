@echo off
title Jubayer AI Special Agent - 24/7 Hunter Launcher
color 0A
chcp 65001 > nul
echo ======================================================================
echo       👑 JUBAYER AI SPECIAL AGENT - AUTONOMOUS CLIENT HUNTER 👑
echo ======================================================================
echo.
echo  [1] Run Autonomous Lead Sweep & Telegram Alerts (One-shot Cron)
echo  [2] Start Interactive 24/7 Telegram Bot (@Jubayer_agent_bot)
echo  [3] Launch Mission Control Web Dashboard (Local UI)
echo  [4] Run Diagnostics & Connection Test
echo  [5] Exit
echo.
set /p opt="Select an option [1-5]: "

if "%opt%"=="1" (
    echo.
    echo 🚀 Starting Autonomous Sweep...
    python backend/main.py --cron
    pause
    goto end
)
if "%opt%"=="2" (
    echo.
    echo 🤖 Starting Telegram Gatekeeper Bot...
    python backend/main.py --bot
    pause
    goto end
)
if "%opt%"=="3" (
    echo.
    echo 🌐 Launching Web Dashboard at http://127.0.0.1:8000 ...
    python backend/main.py --web
    pause
    goto end
)
if "%opt%"=="4" (
    echo.
    echo 🔍 Running Self-Diagnostics...
    python backend/main.py --test
    pause
    goto end
)

:end
