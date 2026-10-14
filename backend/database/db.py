"""
Special Agent - Enterprise Database Repository Layer
Adheres to Google Engineering Standards with transactional integrity and parameterized queries.
"""

import sqlite3
import os
import json
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "special_agent.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

@contextmanager
def get_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initializes tables from schema.sql and seeds default operator profile."""
    with get_db() as conn:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    seed_jubayer_profile()
    seed_portfolio_assets()

def seed_jubayer_profile():
    """Seeds or updates Jubayer's master operator profile."""
    from backend.database.models import UserProfileModel
    profile = UserProfileModel()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM user_profile LIMIT 1")
        row = cursor.fetchone()
        if not row:
            cursor.execute("""
                INSERT INTO user_profile (
                    name, title, email, portfolio_url, github_url,
                    skills_json, languages_json, target_roles_json,
                    working_hours, min_budget_usd
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                profile.name,
                profile.title,
                profile.email,
                profile.portfolio_url,
                profile.github_url,
                json.dumps(profile.skills),
                json.dumps(profile.languages),
                json.dumps(profile.target_roles),
                profile.working_hours,
                profile.min_budget_usd
            ))

def seed_portfolio_assets():
    """Seeds Jubayer's verified portfolio and social proof links."""
    assets = [
        ("web_dev", "Vercel Live Portfolio", "https://jubayer-portfolio-delta.vercel.app", "Production full-stack web portfolio"),
        ("web_dev", "GitHub Code Studio", "https://github.com/Jubayer-AI-Studio", "Public software repositories, Next.js, and Python code"),
        ("ai_video", "YouTube AI Specialist", "https://youtube.com/@jubayeraispecialist?si=xPntRnZnSnzAaS3D", "AI generated movies, content creation and editing channel"),
        ("freelance_platform", "Upwork Freelancer Profile", "https://www.upwork.com/freelancers/~0185d56d4075d701a6", "Verified Upwork agency/freelancer profile"),
        ("social_media", "Facebook Profile 1", "https://www.facebook.com/share/1CopAWZnyX/", "Primary Facebook profile for social proof"),
        ("social_media", "Facebook Profile 2", "https://www.facebook.com/share/1C8RmiURup/", "Secondary Facebook page / profile"),
        ("social_media", "Instagram Profile", "https://instagram.com/jubayer_ahmad_2002?utm_source=qr&exln=MWlhb2c2aTA2ZG1tcg==", "Official Instagram creative presence"),
        ("social_media", "TikTok Profile", "https://tiktok.com/@jubayer.ahmad092", "TikTok video content creations")
    ]
    with get_db() as conn:
        cursor = conn.cursor()
        for cat, title, url, desc in assets:
            cursor.execute("""
                INSERT INTO portfolio_assets (category, title, url, description)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description
            """, (cat, title, url, desc))

def get_portfolio_assets(category: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM portfolio_assets WHERE category = ? AND is_active = 1", (category,))
        else:
            cursor.execute("SELECT * FROM portfolio_assets WHERE is_active = 1")
        return [dict(r) for r in cursor.fetchall()]

def get_user_profile() -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user_profile ORDER BY id ASC LIMIT 1")
        row = cursor.fetchone()
        if row:
            data = dict(row)
            data["skills"] = json.loads(data["skills_json"])
            data["languages"] = json.loads(data["languages_json"])
            data["target_roles"] = json.loads(data["target_roles_json"])
            return data
        return {}

def job_exists(apply_url: str) -> bool:
    if not apply_url:
        return False
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM jobs WHERE apply_url = ?", (apply_url.strip(),))
        return cursor.fetchone() is not None

def insert_job(job: Dict[str, Any]) -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (
                source, company_name, title, description,
                recruiter_email, apply_url, salary_range, location,
                detected_language, match_score, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("source", "remote_web"),
            job.get("company_name", "Tech Client"),
            job.get("title", "Remote Developer"),
            job.get("description", ""),
            job.get("recruiter_email"),
            job.get("apply_url"),
            job.get("salary_range", "Negotiable"),
            job.get("location", "Worldwide Remote"),
            job.get("detected_language", "en"),
            job.get("match_score", 85),
            job.get("status", "new")
        ))
        return cursor.lastrowid

def insert_application(job_id: int, subject: str, email_body: str, language: str = "en") -> int:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (job_id, subject, email_body, language, status)
            VALUES (?, ?, ?, ?, 'pending_review')
        """, (job_id, subject, email_body, language))
        return cursor.lastrowid

def update_application_status(app_id: int, status: str):
    with get_db() as conn:
        cursor = conn.cursor()
        if status == 'sent':
            cursor.execute("""
                UPDATE applications
                SET status = ?, sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, app_id))
        else:
            cursor.execute("""
                UPDATE applications
                SET status = ?
                WHERE id = ?
            """, (status, app_id))

def get_application_with_job(app_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id as application_id, a.subject, a.email_body, a.status as app_status,
                   j.id as job_id, j.title, j.company_name, j.recruiter_email, j.apply_url,
                   j.salary_range, j.location, j.source
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.id = ?
        """, (app_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_pending_applications(limit: int = 20) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.id as application_id, a.subject, a.email_body, a.status,
                   j.id as job_id, j.title, j.company_name, j.recruiter_email, j.apply_url,
                   j.salary_range, j.location, j.source
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.status = 'pending_review'
            ORDER BY a.id DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

def get_all_applications(status: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    with get_db() as conn:
        cursor = conn.cursor()
        if status and status != 'all':
            cursor.execute("""
                SELECT a.id as application_id, a.subject, a.email_body, a.status, a.created_at, a.sent_at,
                       j.id as job_id, j.title, j.company_name, j.recruiter_email, j.apply_url,
                       j.salary_range, j.location, j.source
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                WHERE a.status = ?
                ORDER BY a.id DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT a.id as application_id, a.subject, a.email_body, a.status, a.created_at, a.sent_at,
                       j.id as job_id, j.title, j.company_name, j.recruiter_email, j.apply_url,
                       j.salary_range, j.location, j.source
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                ORDER BY a.id DESC
                LIMIT ?
            """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

def log_outreach(application_id: Optional[int], recipient: str, action: str, status: str, details: str = ""):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO outreach_logs (application_id, recipient_email, action, status, details)
            VALUES (?, ?, ?, ?, ?)
        """, (application_id, recipient, action, status, details))

def get_dashboard_analytics() -> Dict[str, Any]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total_jobs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'pending_review'")
        pending_reviews = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'approved'")
        approved_ready = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applications WHERE status = 'sent'")
        sent_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT a.id, j.title, j.company_name, a.status, a.created_at
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            ORDER BY a.id DESC LIMIT 5
        """)
        recent_activity = [dict(r) for r in cursor.fetchall()]

        profile = get_user_profile()

        return {
            "total_jobs_scanned": total_jobs,
            "pending_reviews": pending_reviews,
            "approved_ready": approved_ready,
            "applications_sent": sent_count,
            "active_operator": profile.get("name", "Jubayer"),
            "recent_activity": recent_activity
        }

# Initialize on module load
init_db()
