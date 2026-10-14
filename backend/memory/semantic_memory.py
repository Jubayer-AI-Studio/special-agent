"""
Special Agent - Semantic Memory Layer
Stores durable facts, preferences, user principles, and worldview knowledge.
"""

import sqlite3
import os
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "special_agent.db")

def init_semantic_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS semantic_facts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,           -- 'identity', 'work_style', 'values', 'skills', 'network'
        fact_key TEXT UNIQUE NOT NULL,
        fact_value TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()
    conn.close()

class SemanticMemory:
    def __init__(self):
        init_semantic_table()

    def store_fact(self, category: str, key: str, value: str, confidence: float = 1.0):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO semantic_facts (category, fact_key, fact_value, confidence, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(fact_key) DO UPDATE SET
                fact_value = excluded.fact_value,
                confidence = excluded.confidence,
                updated_at = CURRENT_TIMESTAMP
        """, (category, key, value, confidence))
        conn.commit()
        conn.close()

    def recall_fact(self, key: str) -> Optional[str]:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT fact_value FROM semantic_facts WHERE fact_key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_facts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM semantic_facts WHERE category = ? ORDER BY updated_at DESC", (category,))
        else:
            cursor.execute("SELECT * FROM semantic_facts ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

semantic_store = SemanticMemory()
