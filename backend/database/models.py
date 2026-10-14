"""
Special Agent - Type-Safe Data Models (Pydantic V2)
Strict schemas ensuring data integrity across Database, Backend, and Frontend.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class UserProfileModel(BaseModel):
    id: Optional[int] = None
    name: str = "Jubayer"
    title: str = "AI Specialist & Full Stack Developer"
    email: str = "jubayerahmadaistudio@gmail.com"
    portfolio_url: str = "https://jubayer-portfolio-delta.vercel.app"
    github_url: str = "https://github.com/Jubayer-AI-Studio"
    skills: List[str] = Field(default_factory=lambda: [
        "Full-Stack Web Development", "React", "Next.js", "Python Backend",
        "WordPress", "Shopify", "Mobile Apps & PWA", "AI Content Creation",
        "Web Scraping & Bots", "Game Development", "Translation"
    ])
    languages: List[str] = Field(default_factory=lambda: [
        "Bengali", "English", "Arabic", "Urdu", "Hindi"
    ])
    target_roles: List[str] = Field(default_factory=lambda: [
        "Full Stack Developer", "Frontend Developer", "Python Developer",
        "WordPress / Shopify Developer", "Software Engineer", "AI Assistant"
    ])
    working_hours: str = "07:00-21:00 GMT+6"
    min_budget_usd: float = 5.0

class JobModel(BaseModel):
    id: Optional[int] = None
    source: str
    company_name: str
    title: str
    description: str
    recruiter_email: Optional[str] = None
    apply_url: str
    salary_range: str = "Negotiable"
    location: str = "Worldwide Remote"
    detected_language: str = "en"
    match_score: int = 0
    status: str = "new"
    created_at: Optional[datetime] = None

class ApplicationModel(BaseModel):
    id: Optional[int] = None
    job_id: int
    subject: str
    email_body: str
    language: str = "en"
    status: str = "pending_review"
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class OutreachLogModel(BaseModel):
    id: Optional[int] = None
    application_id: Optional[int] = None
    recipient_email: str
    action: str
    status: str
    details: Optional[str] = None
    timestamp: Optional[datetime] = None

class DashboardStatsModel(BaseModel):
    total_jobs_scanned: int
    qualified_leads: int
    pending_approvals: int
    approved_ready: int
    applications_sent: int
    active_operator: str

class PortfolioAssetModel(BaseModel):
    id: Optional[int] = None
    category: str  # 'web_dev', 'ai_video', 'freelance_platform', 'social_media'
    title: str
    url: str
    description: Optional[str] = None
    is_active: int = 1

