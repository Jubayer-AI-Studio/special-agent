"""
Special Agent - Web Server & REST API Gateway (FastAPI)
Connects the UI/UX Pro Max Dashboard with the Database, Radar, and Email Engine.
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.db import (
    get_dashboard_analytics,
    get_all_applications,
    get_application_with_job,
    update_application_status,
    get_portfolio_assets,
    get_user_profile
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

@app.get("/")
async def serve_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Frontend not found"}

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
async def api_scan():
    jobs = await job_radar.scan_all_sources()
    drafted = []
    for j in jobs:
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.web_server:app", host="127.0.0.1", port=8000, reload=False)
