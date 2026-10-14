"""
Special Agent - Upwork Global Radar Skill
Scans Upwork job feeds via RSS or queries to extract international client opportunities.
"""

import feedparser
from typing import List, Dict, Any
from backend.database.db import add_lead, add_proposal, lead_exists
from backend.brain.llm_engine import engine

class UpworkRadar:
    def __init__(self, search_queries: List[str] = None):
        self.queries = search_queries or ["fullstack", "python", "react", "automation"]

    def scan_rss_feed(self, rss_url: str = "https://www.upwork.com/ab/feed/jobs/rss?q=fullstack") -> List[Dict[str, Any]]:
        """
        Parses Upwork RSS feed and extracts unhandled jobs.
        """
        discovered = []
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:5]: # check latest 5 entries
                post_url = entry.link
                if lead_exists(post_url):
                    continue
                
                title = entry.title
                summary = entry.summary
                
                # Qualify with brain
                eval_result = engine.qualify_lead(summary)
                if eval_result.get("is_valid_lead", True):
                    lead_id = add_lead(
                        source="upwork",
                        title=title,
                        content=summary,
                        client_name="Upwork Client",
                        contact_info="Upwork Direct Portal",
                        budget=eval_result.get("detected_budget", "Hourly / Fixed"),
                        post_url=post_url,
                        match_score=eval_result.get("match_score", 85)
                    )
                    pitch = engine.generate_proposal(title, summary, "upwork")
                    prop_id = add_proposal(lead_id, pitch)
                    
                    discovered.append({
                        "lead_id": lead_id,
                        "proposal_id": prop_id,
                        "title": title,
                        "client_name": "Upwork Client",
                        "budget": eval_result.get("detected_budget"),
                        "pitch": pitch,
                        "url": post_url
                    })
        except Exception as e:
            print(f"[UpworkRadar] Notice: {e}")
            
        return discovered

upwork_radar = UpworkRadar()
