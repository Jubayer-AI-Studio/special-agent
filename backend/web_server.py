"""
Special Agent - Web Server & REST API Gateway (FastAPI)
Connects the UI/UX Pro Max Dashboard with the Database, Radar, and Email Engine.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import aiohttp
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db import (
    get_dashboard_analytics,
    get_all_applications,
    get_application_with_job,
    update_application_status,
    get_portfolio_assets,
    get_user_profile,
    save_chat_message,
    get_recent_chat_history
)
from backend.skills.job_radar import job_radar
from backend.brain.hermes_brain import hermes_brain
from backend.gateway.email_sender import email_dispatcher

app = FastAPI(title="Jubayer AI Hunter API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

@app.on_event("startup")
async def startup_event():
    # If running in persistent cloud container (Render, Railway, Docker, Local)
    if not os.getenv("VERCEL"):
        import threading
        if os.getenv("ENABLE_BG_BOT", "true").lower() == "true":
            from backend.telegram_gatekeeper import run_interactive_bot
            bot_thread = threading.Thread(target=run_interactive_bot, daemon=True)
            bot_thread.start()
            print("🤖 [Cloud Gateway] 24/7 Interactive Telegram Bot spawned concurrently in background thread.")

        if os.getenv("ENABLE_BG_RADAR", "true").lower() == "true":
            from backend.main import run_radar_loop
            interval = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))
            asyncio.create_task(run_radar_loop(interval_seconds=interval))
            print(f"🛰️ [Background Engine] 24/7 Autonomous Job Radar spawned concurrently (every {interval}s).")

@app.get("/")
async def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Jubayer AI Hunter API Online</h1><p>Frontend file loading...</p>")

@app.get("/manifest.json")
async def serve_manifest():
    manifest_file = os.path.join(FRONTEND_DIR, "manifest.json")
    if os.path.exists(manifest_file):
        return FileResponse(manifest_file, media_type="application/manifest+json")
    return {"name": "Special Agent"}

@app.get("/sw.js")
async def serve_sw():
    sw_file = os.path.join(FRONTEND_DIR, "sw.js")
    if os.path.exists(sw_file):
        return FileResponse(sw_file, media_type="application/javascript")
    raise HTTPException(status_code=404)

icons_dir = os.path.join(FRONTEND_DIR, "icons")
if os.path.exists(icons_dir):
    app.mount("/icons", StaticFiles(directory=icons_dir), name="icons")

data_dir = os.path.join(FRONTEND_DIR, "data")
if os.path.exists(data_dir):
    app.mount("/data", StaticFiles(directory=data_dir), name="data")

@app.get("/api/analytics")
async def api_analytics():
    return get_dashboard_analytics()

@app.get("/api/applications")
async def api_applications(status: Optional[str] = Query(None)):
    return get_all_applications(status=status, limit=50)

@app.get("/api/assets")
async def api_assets():
    return get_portfolio_assets()

@app.get("/api/system-status")
async def api_system_status():
    smtp_status = email_dispatcher.verify_smtp_credentials()
    profile = get_user_profile()
    return {
        "database": {"connected": True, "operator": profile.get("name")},
        "smtp": smtp_status,
        "telegram": {
            "configured": True,
            "bot_username": "Jubayer_agent_bot"
        }
    }

@app.post("/api/scan")
async def api_scan(limit: int = 2):
    jobs = await job_radar.scan_all_sources()
    drafted = []
    # Draft applications for the top new jobs within serverless execution window
    for j in jobs[:limit]:
        d = hermes_brain.draft_application(j)
        drafted.append(d)
    return {"status": "ok", "discovered_count": len(jobs), "drafted_count": len(drafted)}

@app.post("/api/approve/{app_id}")
async def api_approve(app_id: int):
    app_info = get_application_with_job(app_id)
    if not app_info:
        raise HTTPException(status_code=404, detail="Application not found")

    result = email_dispatcher.send_application_email(
        application_id=app_id,
        recipient_email=app_info.get("recruiter_email", "apply@client.com"),
        subject=app_info.get("subject", "Application for Remote Role"),
        body=app_info.get("email_body", "")
    )
    return result

@app.post("/api/reject/{app_id}")
async def api_reject(app_id: int):
    update_application_status(app_id, "rejected")
    return {"status": "rejected", "application_id": app_id}

async def send_tg(token: str, chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    # Ensure text does not exceed Telegram 4096 character limit
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)] if len(text) > 4000 else [text]
    last_res = None
    for chunk in chunks:
        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        if reply_markup and chunk == chunks[-1]:
            payload["reply_markup"] = reply_markup
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=15) as resp:
                    res = await resp.json()
                    # If Telegram fails to parse Markdown, fallback to plain text immediately
                    if not res.get("ok"):
                        payload.pop("parse_mode", None)
                        async with session.post(url, json=payload, timeout=15) as fallback_resp:
                            res = await fallback_resp.json()
                    last_res = res
        except Exception as e:
            print(f"Telegram send error: {e}")
            last_res = None
    return last_res

async def edit_tg(token: str, chat_id: int, message_id: int, text: str):
    url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=10) as resp:
                return await resp.json()
    except Exception as e:
        print(f"Telegram edit error: {e}")
        return None

@app.post("/api/telegram-webhook")
async def telegram_webhook(request: Request):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    try:
        data = await request.json()
    except Exception:
        return {"ok": False}

    if "message" in data:
        msg = data["message"]
        chat_id = msg.get("chat", {}).get("id")
        text = msg.get("text", "").strip()
        first_name = msg.get("from", {}).get("first_name", "জুবায়ের")

        if text.startswith("/start"):
            reply = (
                f"👑 **সালাম {first_name} ভাই!**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"আমি আপনার পার্সোনাল **AI Job Hunter & Career Alter-Ego**।\n"
                f"📱 মোবাইল ক্লাউড গেটওয়ে সফলভাবে কানেক্টেড!\n\n"
                f"🚀 **উপলব্ধ কমান্ডসমূহ:**\n"
                f"• `/hackathons` - লাইভ গ্লোবাল হ্যাকাথন ও টিম প্রপোজাল হান্টার\n"
                f"• `/scan` - লাইভ নতুন রিমোট জব সার্চ ও পিচ তৈরি\n"
                f"• `/status` - ড্যাশবোর্ড রিপোর্ট ও পরিসংখ্যান\n"
                f"• যেকোনো প্রশ্ন বা চ্যাট করলে আমি মুক্তভাবে হার্মেস ৩ ব্রেন দিয়ে রেসপন্স দেব।\n\n"
                f"🌐 আপনার লাইভ মিশন কন্ট্রোল ড্যাশবোর্ড:\nhttps://jubayer-ai-studio.github.io/special-agent/"
            )
            await send_tg(token, chat_id, reply)
        elif text.startswith("/status"):
            analytics = get_dashboard_analytics()
            reply = (
                f"📊 **স্পেশাল এজেন্ট ড্যাশবোর্ড রিপোর্ট**\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"📡 সিস্টেম স্টেটাস: **সক্রিয় (Active 24/7)**\n"
                f"🎯 স্ক্যানকৃত মোট জব: `{analytics['total_jobs_scanned']}`\n"
                f"⏳ সিদ্ধান্তের অপেক্ষায় (Pending): `{analytics['pending_reviews']}`\n"
                f"✅ অনুমোদিত ও প্রস্তুত: `{analytics['approved_ready']}`\n"
                f"🚀 পাঠানো অ্যাপ্লিকেশন: `{analytics['applications_sent']}`\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"নতুন কাজ সার্চ করতে চাপুন: `/scan`"
            )
            await send_tg(token, chat_id, reply)
        elif text.startswith("/scan"):
            await send_tg(token, chat_id, "🔍 গ্লোবাল রিমোট জব পোর্টালগুলোতে স্ক্যান শুরু হয়েছে... অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।")
            jobs = await job_radar.scan_all_sources()
            drafted = []
            for j in jobs[:2]:
                d = hermes_brain.draft_application(j)
                drafted.append(d)

                app_id = d.get("application_id", 0)
                card_text = (
                    f"🚨 **নতুন চাকরির সুযোগ পাওয়া গেছে!**\n"
                    f"━━━━━━━━━━━━━━━━━━━\n"
                    f"🏢 **কোম্পানি:** {d.get('company_name')}\n"
                    f"📌 **পদ:** {d.get('title')}\n"
                    f"💰 **বেতন:** {d.get('salary_range')}\n"
                    f"🌍 **লোকেশন:** {d.get('location')}\n\n"
                    f"📝 **হার্মিস ৩-এর ড্রাফট পিচ:**\n"
                    f"{d.get('email_body')[:400]}...\n\n"
                    f"আবেদনটি ক্লায়েন্টকে পাঠাতে চান?"
                )
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ অনুমোদন ও সেন্ড", "callback_data": f"send_app_{app_id}"},
                            {"text": "❌ বাতিল", "callback_data": f"reject_app_{app_id}"}
                        ]
                    ]
                }
                await send_tg(token, chat_id, card_text, reply_markup=markup)
            
            await send_tg(token, chat_id, f"✅ স্ক্যান শেষ! মোট {len(jobs)}টি নতুন জব পাওয়া গেছে। ড্যাশবোর্ডে দেখুন: https://jubayer-ai-studio.github.io/special-agent/")
        elif text.startswith("/hackathons"):
            await send_tg(token, chat_id, "🏆 Devpost ও গ্লোবাল হ্যাকাথন পোর্টালগুলোতে স্ক্যান শুরু হয়েছে... অনুগ্রহ করে কিছুক্ষণ অপেক্ষা করুন।")
            hacks = await job_radar.fetch_devpost_hackathons()
            if not hacks:
                await send_tg(token, chat_id, "ℹ️ বর্তমানে কোনো নতুন আন-রেজিস্টার্ড হ্যাকাথন পাওয়া যায়নি। পূর্বের হ্যাকাথনগুলো ড্যাশবোর্ডে সংরক্ষিত রয়েছে।")
            else:
                for h in hacks[:2]:
                    d = hermes_brain.draft_application(h)
                    app_id = d.get("application_id", 0)
                    card_text = (
                        f"🏆 **নতুন গ্লোবাল হ্যাকাথন পাওয়া গেছে!**\n"
                        f"━━━━━━━━━━━━━━━━━━━\n"
                        f"📌 **নাম:** {d.get('title')}\n"
                        f"💰 **পুরস্কার পুল:** {d.get('salary_range')}\n"
                        f"🌍 **মোড:** {d.get('location')}\n\n"
                        f"📝 **হার্মিস ৩-এর প্রপোজাল ড্রাফট:**\n"
                        f"{d.get('email_body')[:350]}...\n\n"
                        f"রেজিস্ট্রেশন লিংক ও বিস্তারিত নিচে দেখুন:"
                    )
                    markup = {
                        "inline_keyboard": [
                            [
                                {"text": "🔗 সরাসরি রেজিস্ট্রেশন পেজ", "url": d.get("apply_url")},
                                {"text": "✅ প্রপোজাল সেভ", "callback_data": f"save_hack_{app_id}"}
                            ]
                        ]
                    }
                    await send_tg(token, chat_id, card_text, reply_markup=markup)
                await send_tg(token, chat_id, f"🎉 মোট {len(hacks)}টি ওপেন হ্যাকাথন পাওয়া গেছে! ড্যাশবোর্ডে দেখুন: https://jubayer-ai-studio.github.io/special-agent/")
        else:
            # 1. Fetch recent conversation memory for contextual continuity
            history = get_recent_chat_history(chat_id, limit=6)
            
            # 2. Engage Nous Hermes 3 70B Reasoning Engine (non-blocking)
            hermes_reply = await asyncio.to_thread(hermes_brain.chat, text, first_name, history)
            
            # 3. Persist conversation turn in database
            save_chat_message(chat_id, "user", text)
            save_chat_message(chat_id, "assistant", hermes_reply)
            
            # 4. Dispatch Hermes 3's intelligent response to Telegram
            await send_tg(token, chat_id, hermes_reply)

    elif "callback_query" in data:
        cq = data["callback_query"]
        cq_data = cq.get("data", "")
        chat_id = cq.get("message", {}).get("chat", {}).get("id")
        msg_id = cq.get("message", {}).get("message_id")

        if cq_data.startswith("send_app_"):
            app_id = int(cq_data.split("_")[2])
            app_info = get_application_with_job(app_id)
            if app_info:
                res = email_dispatcher.send_application_email(
                    application_id=app_id,
                    recipient_email=app_info.get("recruiter_email", "apply@client.com"),
                    subject=app_info.get("subject", "Application for Remote Role"),
                    body=app_info.get("email_body", "")
                )
                await edit_tg(token, chat_id, msg_id, f"✅ **অনুমোদিত ও ক্লায়েন্টকে সফলভাবে ইমেইল পাঠানো হয়েছে!**\n\n{res.get('message')}")
        elif cq_data.startswith("reject_app_"):
            app_id = int(cq_data.split("_")[2])
            update_application_status(app_id, "rejected")
            await edit_tg(token, chat_id, msg_id, "❌ **আবেদনটি বাতিল করা হয়েছে (Rejected)।**")

    return {"ok": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.web_server:app", host="127.0.0.1", port=8000, reload=False)
