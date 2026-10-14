-- ====================================================================
-- Special Agent: Production Database Schema
-- Architecture: Google Developer Standards / Relational SQLite
-- ====================================================================

-- 1. Operator Profile & Master Configuration
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    title TEXT NOT NULL,
    email TEXT NOT NULL,
    portfolio_url TEXT,
    github_url TEXT,
    skills_json TEXT NOT NULL,          -- JSON Array of technical skills
    languages_json TEXT NOT NULL,       -- JSON Array of languages (Bengali, English, Arabic, Urdu, Hindi)
    target_roles_json TEXT NOT NULL,    -- JSON Array of target roles
    working_hours TEXT DEFAULT '07:00-21:00 GMT+6',
    min_budget_usd REAL DEFAULT 5.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Discovered Jobs & Client Opportunities
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,               -- 'remoteok', 'weworkremotely', 'upwork', 'facebook', 'direct'
    company_name TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    recruiter_email TEXT,               -- Contact email for direct cold outreach
    apply_url TEXT UNIQUE NOT NULL,     -- Dedup key to guarantee zero repeat spam
    salary_range TEXT DEFAULT 'Negotiable',
    location TEXT DEFAULT 'Worldwide Remote',
    detected_language TEXT DEFAULT 'en', -- 'en', 'bn', 'ar', 'ur'
    match_score INTEGER DEFAULT 0,      -- 0-100% computed by Hermes Brain
    status TEXT DEFAULT 'new',          -- 'new', 'qualified', 'disqualified', 'archived'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Pitch Drafts & Application Lifecycle
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    email_body TEXT NOT NULL,
    language TEXT DEFAULT 'en',
    status TEXT DEFAULT 'pending_review', -- 'pending_review', 'approved', 'rejected', 'sent', 'failed'
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

-- 4. Audit Trail & Outreach Execution Logs
CREATE TABLE IF NOT EXISTS outreach_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER,
    recipient_email TEXT NOT NULL,
    action TEXT NOT NULL,               -- 'email_sent', 'approval_received', 'rejected_by_operator'
    status TEXT NOT NULL,               -- 'success', 'failure'
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE SET NULL
);

-- 5. Key-Value Settings & State Store
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Dynamic Portfolio Assets Vault
CREATE TABLE IF NOT EXISTS portfolio_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,             -- 'web_dev', 'ai_video', 'freelance_platform', 'social_media'
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Optimization Indexes
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_apply_url ON jobs(apply_url);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_assets_category ON portfolio_assets(category);
