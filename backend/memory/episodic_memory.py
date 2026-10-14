"""
Special Agent - Episodic Memory Layer
Maintains an autobiographical timeline of interactions, decisions, and lived experiences.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "special_agent.db")

def init_episodic_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS episodic_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,          -- 'conversation', 'decision', 'reflection', 'milestone'
        summary TEXT NOT NULL,
        raw_content TEXT,
        user_insight TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

class EpisodicMemory:
    def __init__(self):
        init_episodic_table()

    def log_episode(self, event_type: str, summary: str, 
                    raw_content: Optional[str] = None, user_insight: Optional[str] = None) -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO episodic_events (event_type, summary, raw_content, user_insight)
            VALUES (?, ?, ?, ?)
        """, (event_type, summary, raw_content, user_insight))
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return event_id

    def get_recent_episodes(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM episodic_events ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

episodic_store = EpisodicMemory()
