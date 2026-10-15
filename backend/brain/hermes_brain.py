"""
Special Agent - Hermes 3 Pitch & Application Crafter
Synthesizes Jubayer's skills, portfolio, and multi-lingual capabilities into high-converting job applications.
Integrates dynamically with the Smart Asset Vault (Web, Video/AI, Social Proof).
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from backend.database.db import get_user_profile, get_portfolio_assets, insert_application

load_dotenv()

class HermesBrain:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("LLM_MODEL", "nousresearch/hermes-3-llama-3.1-70b")
        self.client = None
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def select_relevant_assets(self, title: str, description: str) -> List[Dict[str, Any]]:
        """
        Intelligently selects the most convincing portfolio assets matching the job domain.
        """
        all_assets = get_portfolio_assets()
        text = f"{title} {description}".lower()

        selected = []
        is_video_job = any(k in text for k in ["video", "youtube", "movie", "ai content", "media", "editor", "animat", "tiktok", "instagram"])
        is_web_job = any(k in text for k in ["web", "developer", "engineer", "react", "next", "python", "fullstack", "frontend", "backend", "shopify", "wordpress"])
        is_freelance = any(k in text for k in ["upwork", "freelance", "gig", "contract", "hourly"])

        for asset in all_assets:
            cat = asset.get("category")
            if is_video_job and cat == "ai_video":
                selected.append(asset)
            elif is_web_job and cat == "web_dev":
                selected.append(asset)
            elif is_freelance and cat == "freelance_platform":
                selected.append(asset)

        # Fallback: If nothing specifically matched, provide primary web & upwork assets
        if not selected:
            selected = [a for a in all_assets if a.get("category") in ["web_dev", "freelance_platform"]]

        return selected

    def draft_application(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Drafts a personalized, high-converting application for a specific job."""
        profile = get_user_profile()
        company = job.get("company_name", "the team")
        title = job.get("title", "Developer")
        desc = job.get("description", "")
        lang = job.get("detected_language", "en")

        name = profile.get("name", "Jubayer")
        role_title = profile.get("title", "AI Specialist & Full Stack Developer")
        email = profile.get("email", "jubayerahmadaistudio@gmail.com")

        # Select domain-relevant assets from Asset Vault
        relevant_assets = self.select_relevant_assets(title, desc)
        asset_lines = "\n".join([f"• {a['title']}: {a['url']}" for a in relevant_assets])

        is_hackathon = "hackathon" in job.get("source", "").lower() or "hackathon" in title.lower()

        if is_hackathon:
            subject = f"🏆 Hackathon Project Proposal: {title} - {name}"
        else:
            subject = f"Application for {title} - {name} ({role_title})"

        if not self.client:
            if is_hackathon:
                body = (
                    f"Hi {company} & Hackathon Review Committee,\n\n"
                    f"I am submitting our project concept and registration for {title}.\n\n"
                    f"Developer & AI Engineer: {name} ({role_title})\n"
                    f"Core Stack: React, Next.js, Python FastAPI, Autonomous AI Agents\n\n"
                    f"Relevant Technical Proof & Live Projects:\n"
                    f"{asset_lines}\n\n"
                    f"Project Execution Plan:\n"
                    f"Building an ultra-responsive, scalable solution targeting the competition's core challenge with rapid prototyping and production-grade stability.\n\n"
                    f"Best regards,\n"
                    f"{name}\n"
                    f"Team Lead / Full Stack Developer\n"
                    f"Email: {email}"
                )
            # Dynamic template tuned to the exact matching category
            elif any(a.get("category") == "ai_video" for a in relevant_assets):
                body = (
                    f"Hi {company} Hiring Team,\n\n"
                    f"I noticed your opening for the {title} role and wanted to reach out. "
                    f"As an {role_title}, I specialize in AI-driven media production, cinematic video creation, and high-impact digital content.\n\n"
                    f"Relevant Work & Creative Portfolios:\n"
                    f"{asset_lines}\n\n"
                    f"I can deliver production-ready, captivating visual assets with rapid turnaround. "
                    f"Available for flexible remote hours (07:00 - 21:00 GMT+6).\n\n"
                    f"Best regards,\n"
                    f"{name}\n"
                    f"{role_title}\n"
                    f"Email: {email}"
                )
            else:
                body = (
                    f"Hi {company} Hiring Team,\n\n"
                    f"I came across your opening for the {title} position and wanted to reach out directly. "
                    f"As an {role_title} with hands-on experience in modern Full-Stack engineering (React, Next.js, Python), "
                    f"I build scalable, responsive web solutions and automated systems.\n\n"
                    f"Relevant Code & Live Projects:\n"
                    f"{asset_lines}\n\n"
                    f"I work flexible remote hours (07:00 - 21:00 GMT+6) and can integrate into your workflow immediately.\n\n"
                    f"Best regards,\n"
                    f"{name}\n"
                    f"{role_title}\n"
                    f"Email: {email}"
                )
        else:
            try:
                system_prompt = (
                    f"You are Nous Hermes 3 acting on behalf of {name}, an {role_title}.\n"
                    f"Write a concise, high-converting cold outreach email for the given position.\n"
                    f"You MUST reference these exact verified proof links:\n{asset_lines}\n"
                    f"Tone: Direct, confident, no generic buzzwords, focused on execution and value."
                )
                user_prompt = f"Company: {company}\nRole: {title}\nJob Scope:\n{desc[:800]}"
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.6,
                    max_tokens=450
                )
                body = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[HermesBrain] Notice: {e}")
                body = f"Hi {company} Team,\n\nI am applying for the {title} position. Please review my work:\n{asset_lines}\n\nBest,\n{name}"

        # Insert application into database
        app_id = insert_application(
            job_id=job["id"],
            subject=subject,
            email_body=body,
            language=lang
        )

        return {
            "application_id": app_id,
            "job_id": job["id"],
            "company_name": company,
            "title": title,
            "recruiter_email": job.get("recruiter_email"),
            "apply_url": job.get("apply_url"),
            "salary_range": job.get("salary_range"),
            "location": job.get("location"),
            "subject": subject,
            "email_body": body,
            "assets_used": [a['title'] for a in relevant_assets]
        }

    def chat(self, user_message: str, user_name: str = "Jubayer", history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Conversational reasoning engine. Allows Jubayer to talk directly with Hermes 3 on Telegram.
        Hermes acts as Jubayer's 10x Chief of Staff, career strategist, and Alter Ego.
        """
        profile = get_user_profile()
        name = profile.get("name", user_name)
        role_title = profile.get("title", "AI Specialist & Full Stack Developer")
        assets = get_portfolio_assets()
        asset_summary = "\n".join([f"• {a['title']} ({a['category']}): {a['url']}" for a in assets])

        system_prompt = (
            f"You are Nous Hermes 3, the autonomous AI Chief of Staff and strategic partner of {name}.\n"
            f"Operator Identity: {name} ({role_title}).\n"
            f"Verified Portfolio & Proof Assets:\n{asset_summary}\n\n"
            f"Your Role & Personality:\n"
            f"1. You are Jubayer's real AI alter ego. You are sharp, proactive, professional, and knowledgeable about fullstack web development (React, Next.js, FastAPI, Python) and AI agent engineering.\n"
            f"2. You communicate primarily in fluent, natural, professional Bengali (unless Jubayer speaks in English, Arabic, Urdu, or Hindi).\n"
            f"3. You know everything about this Special Agent platform: 24/7 cloud job radar (RemoteOK, WeWorkRemotely, Freelance), Hermes 3 pitch crafter, Gmail SMTP dispatcher, and Telegram gateway.\n"
            f"4. If Jubayer asks who you are, what you can do, or gives you advice/training on how to write pitches, respond with high intelligence, clarity, and adaptability.\n"
            f"5. Always finish your thoughts, sentences, and explanations completely. NEVER cut off mid-sentence or leave answers incomplete.\n"
            f"6. Keep responses clear, articulate, and beautifully formatted for Telegram mobile reading."
        )

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        if not self.client:
            if self.api_key:
                self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            else:
                return f"সালাম {name} ভাই! আমি হার্মিস ৩। বর্তমানে এপিআই সংযোগ অফলাইনে আছে, অনুগ্রহ করে LLM_API_KEY চেক করুন।"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[HermesBrain Chat Error]: {e}")
            return f"জুবায়ের ভাই, হার্মিস ব্রেইনে সংযোগের সময় একটি নোটিশ এসেছে: {str(e)[:120]}।"

hermes_brain = HermesBrain()
