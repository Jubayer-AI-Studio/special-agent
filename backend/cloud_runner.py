"""
Special Agent - Cloud Autonomous Runner
Performs headless job discovery sweeps and Hermes 3 pitch drafting in the cloud.
Sends interactive review cards to Jubayer's Telegram and records applications in the database.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from backend.database.db import init_db
from backend.skills.job_radar import job_radar
from backend.brain.hermes_brain import hermes_brain
from backend.gateway.telegram_bot import TelegramGatekeeper

async def run_cloud_sweep():
    print("=" * 65)
    print("🛰️ [Cloud Radar] Initiating 24/7 Autonomous Job Sweep...")
    print("=" * 65)
    init_db()
    
    jobs = await job_radar.scan_all_sources()
    print(f"🛰️ [Cloud Radar] Scanned global feeds. Found {len(jobs)} high-matching opportunities.")
    
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    drafted = []
    for job in jobs:
        print(f"🧠 [Hermes 3] Crafting tailored application for: {job.get('title')} @ {job.get('company_name')}...")
        draft = hermes_brain.draft_application(job)
        drafted.append(draft)
        
        if token and chat_id:
            try:
                gatekeeper = TelegramGatekeeper(token)
                await gatekeeper.send_approval_card(int(chat_id), draft)
                print(f"📱 [Telegram] Approval card sent to Operator Chat ID: {chat_id}")
            except Exception as e:
                print(f"⚠️ [Telegram Notice]: {e}")
                
    print("=" * 65)
    print(f"✅ [Cloud Radar] Sweep Complete: {len(jobs)} jobs evaluated, {len(drafted)} applications drafted.")
    print("=" * 65)
    return {"jobs": len(jobs), "drafts": len(drafted)}

if __name__ == "__main__":
    asyncio.run(run_cloud_sweep())
