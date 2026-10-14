"""
Special Agent - Feedback Learner (Continuous Self-Improvement)
Captures explicit user instructions, rules, and critiques to evolve the agent's behavior.
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "special_agent.db")

def init_feedback_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_text TEXT NOT NULL,
        category TEXT DEFAULT 'behavior',  -- 'behavior', 'pitching', 'communication', 'preference'
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

class FeedbackLearner:
    def __init__(self):
        init_feedback_table()

    def learn_rule(self, rule_text: str, category: str = "behavior") -> int:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback_rules (rule_text, category)
            VALUES (?, ?)
        """, (rule_text.strip(), category))
        rule_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return rule_id

    def get_active_rules(self) -> List[str]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT rule_text FROM feedback_rules WHERE is_active = 1 ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows]

learner = FeedbackLearner()
