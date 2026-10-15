"""
Special Agent - Verified Portfolio Pitch Crafter
Uses Nous Hermes 3 70B via OpenRouter to craft:
1. Bengali Executive Summary for Jubayer (2 lines)
2. Ready-to-Send High-Converting English Pitch citing 1-2 real verified GitHub projects
"""

import os
import json
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Tuple

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = os.getenv("LLM_MODEL", "nousresearch/hermes-3-llama-3.1-70b")

# Jubayer Ahmad's Real Verified Portfolio & Flagship Projects
OPERATOR_CONTEXT = {
    "name": "Jubayer Ahmad",
    "role": "Full-Stack Software Engineer & Autonomous AI Systems Specialist",
    "location": "Dhaka, Bangladesh (UTC+6, Flexible Global Hours)",
    "github": "https://github.com/Jubayer-AI-Studio",
    "portfolio": "https://jubayer-portfolio-delta.vercel.app",
    "email": "jubayerahmadaistudio@gmail.com",
    "projects": {
        "saas_web": {
            "name": "NoorHub (Madrasa Management SaaS)",
            "url": "https://github.com/Jubayer-AI-Studio/NoorHub-Madrasa-Management-SaaS",
            "stack": "Next.js 15, React 19, TypeScript, Drizzle ORM, PostgreSQL, Leaflet GIS, 29 production routes",
            "best_for": ["web", "nextjs", "react", "saas", "database", "dashboard", "typescript", "fullstack", "full-stack"]
        },
        "python_ai_automation": {
            "name": "Desktop Jarvis & Computer Vision AI",
            "url": "https://github.com/Jubayer-AI-Studio/Jubayer-Jarvis-AI-Automation",
            "stack": "Python 3.12, OpenCV, MediaPipe, Gemini AI, System Automation",
            "best_for": ["python", "ai", "computer vision", "opencv", "automation", "desktop", "assistant"]
        },
        "bots_scraping_video": {
            "name": "Social Media & Reels AI Automator",
            "url": "https://github.com/Jubayer-AI-Studio/AI__automation",
            "stack": "Python, Selenium, Playwright, FFmpeg, 24/7 Telegram Bot, Automated Video Rendering",
            "best_for": ["bot", "telegram", "scraper", "scraping", "video", "ffmpeg", "social media", "selenium", "playwright"]
        },
        "voice_fastapi_nlp": {
            "name": "Shono AI (Bangladeshi Voice Assistant)",
            "url": "https://github.com/Jubayer-AI-Studio/Shono-AI-Bangladeshi-Jarvis",
            "stack": "FastAPI, Gemini Flash, Web Speech API, Realtime Audio Pipeline",
            "best_for": ["fastapi", "voice", "audio", "nlp", "speech", "realtime", "api"]
        },
        "gaming_3d_canvas": {
            "name": "Shafin Blade Fighter 3D",
            "url": "https://github.com/Jubayer-AI-Studio/Shafin-Blade-Fighter-Game",
            "stack": "HTML5 Canvas, Three.js, WebGL 60FPS Game Engine",
            "best_for": ["game", "3d", "canvas", "threejs", "webgl", "interactive"]
        }
    }
}

def get_api_key() -> str:
    return os.getenv("OPENROUTER_API_KEY") or os.getenv("LLM_API_KEY") or ""

def select_best_projects(text: str) -> list:
    text_lower = text.lower()
    selected = []
    for key, p in OPERATOR_CONTEXT["projects"].items():
        score = sum(1 for kw in p["best_for"] if kw in text_lower)
        if score > 0:
            selected.append((score, p))
    selected.sort(key=lambda x: -x[0])
    # Return top 1 or 2 relevant projects
    if selected:
        return [p for _, p in selected[:2]]
    # Default to web + bot automation if generic
    return [OPERATOR_CONTEXT["projects"]["saas_web"], OPERATOR_CONTEXT["projects"]["bots_scraping_video"]]

def generate_pitch(lead: Dict[str, Any]) -> Tuple[str, str]:
    """
    Generates:
    1. bengali_summary: 2-line summary in Bengali for Jubayer.
    2. ai_pitch: 120-word ready-to-send personalized English pitch with verified links.
    """
    title = lead.get("title", "")
    source = lead.get("source", "")
    desc = lead.get("description", "")
    budget = lead.get("budget_or_prize", "Negotiable")
    lead_type = lead.get("type", "client_gig")
    
    best_projs = select_best_projects(f"{title} {desc}")
    proof_lines = "\n".join([f"• {p['name']}: {p['url']} ({p['stack']})" for p in best_projs])

    api_key = get_api_key()
    
    # 1. Fallback Template if API key not available or offline
    def fallback_result() -> Tuple[str, str]:
        if lead_type == "hackathon":
            b_summary = f"🏆 হ্যাকাথন: {title} ({budget})। এআই ও ফুলস্ট্যাক টেক-স্ট্যাক দিয়ে অংশগ্রহণের জন্য প্রস্তুত।"
            p_pitch = (
                f"Hi Hackathon Review Team,\n\n"
                f"I am excited to submit our project proposal for {title}. As a Full-Stack AI Engineer, "
                f"I specialize in building production-grade autonomous agent pipelines and reactive web interfaces.\n\n"
                f"Relevant Repositories & Live Proof:\n{proof_lines}\n\n"
                f"We are ready to build a high-impact, functional solution within the hackathon timeline.\n\n"
                f"Best regards,\nJubayer Ahmad | {OPERATOR_CONTEXT['github']}"
            )
        else:
            b_summary = f"📌 ক্লায়েন্ট রিকোয়ারমেন্ট: {title[:75]}... বাজেট: {budget}। জুবায়েরের পূর্বের প্রোজেক্টের সাথে চমৎকার ম্যাচ করেছে।"
            p_pitch = (
                f"Hi there,\n\n"
                f"I read your post regarding '{title}' and can deliver this reliably. "
                f"As a Full-Stack Software & AI Automation Engineer, I build fast, clean, and robust solutions.\n\n"
                f"Here is verified code from my GitHub directly relevant to your scope:\n{proof_lines}\n\n"
                f"I am available to start immediately and maintain clear communication throughout. Let's discuss your timeline!\n\n"
                f"Best regards,\nJubayer Ahmad | GitHub: {OPERATOR_CONTEXT['github']}"
            )
        return b_summary, p_pitch

    if not api_key:
        return fallback_result()

    system_prompt = (
        f"You are the AI Pitch Strategist for {OPERATOR_CONTEXT['name']}, a {OPERATOR_CONTEXT['role']} based in {OPERATOR_CONTEXT['location']}.\n"
        f"Verified GitHub Profile: {OPERATOR_CONTEXT['github']}\n\n"
        f"VERIFIED PROJECTS YOU CAN CITE:\n{proof_lines}\n\n"
        f"TASK:\n"
        f"Output EXACTLY TWO sections separated by '---':\n"
        f"SECTION 1 (Bengali Summary - strictly 2 lines in Bengali):\n"
        f"Line 1: ক্লায়েন্ট কী চাচ্ছে এবং বাজেট কত ({budget})।\n"
        f"Line 2: কেন জুবায়েরের জন্য উপযুক্ত এবং কোন প্রজেক্ট দিয়ে পিচ করা হয়েছে।\n"
        f"---\n"
        f"SECTION 2 (Ready-to-Send Client Pitch in English):\n"
        f"A direct, professional, 100-120 word pitch to the client. Reference 1 or 2 of the verified project URLs above. "
        f"No robotic buzzwords ('delve', 'testament'). Focus on fast execution, clean architecture, and invite a quick chat. Sign off as 'Jubayer Ahmad'."
    )

    user_prompt = f"Opportunity Source: {source}\nTitle: {title}\nBudget/Prize: {budget}\nScope Details:\n{desc[:800]}"

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/Jubayer-AI-Studio/special-agent",
            "X-Title": "SpecialAgent Client Hunter",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEFAULT_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.65,
            "max_tokens": 500
        }
        res = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=18)
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"].strip()
            if "---" in content:
                parts = content.split("---", 1)
                bengali_summary = parts[0].strip()
                ai_pitch = parts[1].strip()
                return bengali_summary, ai_pitch
            return "📌 ক্লায়েন্ট রিকোয়ারমেন্ট শনাক্ত হয়েছে।", content
        else:
            print(f"[PitchEngine] OpenRouter returned status {res.status_code}")
            return fallback_result()
    except Exception as e:
        print(f"[PitchEngine] Notice: {e}")
        return fallback_result()
