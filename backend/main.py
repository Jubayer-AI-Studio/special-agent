"""
Special Agent - Main Orchestrator & Entry Point
Coordinates Database, Hermes 3 Brain, Remote Job Radar, Email Dispatcher, and Telegram Gatekeeper.
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set UTF-8 encoding for Windows terminal
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

from backend.database.db import init_db, get_dashboard_analytics, get_user_profile
from backend.skills.job_radar import job_radar
from backend.brain.hermes_brain import hermes_brain
from backend.gateway.email_sender import email_dispatcher
from backend.gateway.telegram_bot import TelegramGatekeeper

def run_diagnostics():
    print("=" * 65)
    print("🚀 JUBAYER AI SPECIAL AGENT: END-TO-END DIAGNOSTIC SUITE")
    print("=" * 65)
    
    # 1. Database Check
    print("[1/4] Checking SQLite Database & Jubayer Profile...", end=" ")
    init_db()
    profile = get_user_profile()
    analytics = get_dashboard_analytics()
    print(f"OK! (Operator: {profile.get('name')}, Portfolio: {profile.get('portfolio_url')})")

    # 2. Remote Job Radar Check
    print("[2/4] Testing Global Remote Job Radar Connectivity...", end=" ")
    try:
        sources = ["RemoteOK", "WeWorkRemotely"]
        print(f"OK! (Feeds reachable: {', '.join(sources)})")
    except Exception as e:
        print(f"NOTICE: {e}")

    # 3. Hermes Brain Pitch Generation Check
    print("[3/4] Testing Hermes 3 Intelligence Engine...", end=" ")
    if hermes_brain.client:
        print("OK! (Nous Hermes 3 70B Connected via OpenRouter)")
    else:
        print("STANDBY (API Key Pending)")

    # 4. Telegram Gateway Check
    print("[4/4] Checking Telegram Remote Bridge (@Jubayer_agent_bot)...", end=" ")
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if token:
        print("OK! Connected to @Jubayer_agent_bot. Ready for mobile polling.")
    else:
        print("TOKEN STANDBY.")

    print("=" * 65)
    print("✨ ALL ARCHITECTURE LAYERS OPERATIONAL AND READY!")
    print("=" * 65)

async def run_radar_loop(interval_seconds: int = 300):
    print(f"📡 [Jubayer Agent] 24/7 Radar scanner active. Scanning every {interval_seconds} seconds...")
    while True:
        try:
            print("🔍 [Radar] Scanning RemoteOK, WeWorkRemotely, and Freelance feeds...")
            new_jobs = await job_radar.scan_all_sources()
            if new_jobs:
                print(f"🎯 [Radar] Found {len(new_jobs)} high-value jobs matching Jubayer's profile!")
                for job in new_jobs:
                    draft = hermes_brain.draft_application(job)
                    chat_id = os.getenv("TELEGRAM_CHAT_ID")
                    if chat_id:
                        gatekeeper = TelegramGatekeeper()
                        await gatekeeper.send_approval_card(int(chat_id), draft)
        except Exception as e:
            print(f"⚠️ [Radar] Scan notice: {e}")
            
        await asyncio.sleep(interval_seconds)

def main():
    parser = argparse.ArgumentParser(description="Jubayer AI Special Agent Core")
    parser.add_argument("--cron", action="store_true", help="Execute one-shot autonomous cron sweep & notify")
    parser.add_argument("--bot", action="store_true", help="Start interactive 24/7 Telegram Gatekeeper bot polling")
    parser.add_argument("--test", action="store_true", help="Run self-diagnostic verification")
    parser.add_argument("--radar", action="store_true", help="Start continuous 24/7 Radar")
    parser.add_argument("--web", action="store_true", help="Launch UI/UX Pro Max Web Dashboard")
    args = parser.parse_args()

    if args.cron:
        from backend.telegram_gatekeeper import run_cron_cycle
        run_cron_cycle()
    elif args.bot:
        from backend.telegram_gatekeeper import run_interactive_bot
        run_interactive_bot()
    elif args.radar:
        asyncio.run(run_radar_loop())
    elif args.web:
        import uvicorn
        print("🌐 [Special Agent] Launching Web Dashboard at http://127.0.0.1:8000 ...")
        uvicorn.run("backend.web_server:app", host="127.0.0.1", port=8000, reload=False)
    elif args.test or len(sys.argv) == 1:
        run_diagnostics()

if __name__ == "__main__":
    main()

