"""
Special Agent - Remote Job Radar
Scans global remote job feeds (RemoteOK, WeWorkRemotely, Upwork RSS) for matching opportunities.
"""

import aiohttp
import asyncio
import feedparser
import re
from typing import List, Dict, Any
from backend.database.db import job_exists, insert_job, get_user_profile

class JobRadar:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

    async def fetch_remoteok_jobs(self) -> List[Dict[str, Any]]:
        """Fetches latest remote jobs from RemoteOK public API feed."""
        jobs_found = []
        url = "https://remoteok.com/api"
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # RemoteOK first element is legal notice, slice from 1
                        for item in data[1:15]:
                            apply_url = item.get("url", "")
                            if not apply_url or job_exists(apply_url):
                                continue

                            title = item.get("position", "")
                            description = item.get("description", "")
                            company = item.get("company", "Remote Company")
                            tags = [t.lower() for t in item.get("tags", [])]
                            
                            # Filter for Jubayer's skills
                            relevant_tags = {"react", "javascript", "python", "fullstack", "frontend", "backend", "web", "nextjs", "wordpress", "ai", "node"}
                            if any(t in relevant_tags for t in tags) or any(k in title.lower() for k in ["developer", "engineer", "web"]):
                                salary = f"${item.get('salary_min', 0)} - ${item.get('salary_max', 0)}" if item.get('salary_min') else "Competitive"
                                
                                # Extract potential recruiter email from description if any
                                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', description)
                                recruiter_email = email_match.group(0) if email_match else f"apply@{company.lower().replace(' ', '')}.com"

                                job_dict = {
                                    "source": "RemoteOK",
                                    "company_name": company,
                                    "title": title,
                                    "description": description[:1000],
                                    "recruiter_email": recruiter_email,
                                    "apply_url": apply_url,
                                    "salary_range": salary,
                                    "location": item.get("location", "Worldwide Remote"),
                                    "detected_language": "en",
                                    "match_score": 90,
                                    "status": "qualified"
                                }
                                job_id = insert_job(job_dict)
                                job_dict["id"] = job_id
                                jobs_found.append(job_dict)
        except Exception as e:
            print(f"[JobRadar] Notice on RemoteOK: {e}")
            
        return jobs_found

    def fetch_weworkremotely_jobs(self) -> List[Dict[str, Any]]:
        """Parses WeWorkRemotely RSS feeds for programming jobs."""
        jobs_found = []
        feed_url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                apply_url = entry.link
                if job_exists(apply_url):
                    continue

                title = entry.title
                summary = entry.summary
                company = entry.get("author", "Tech Startup")
                
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', summary)
                recruiter_email = email_match.group(0) if email_match else f"careers@{company.lower().replace(' ', '')}.com"

                job_dict = {
                    "source": "WeWorkRemotely",
                    "company_name": company,
                    "title": title,
                    "description": summary[:1000],
                    "recruiter_email": recruiter_email,
                    "apply_url": apply_url,
                    "salary_range": "Negotiable / Competitive",
                    "location": "Worldwide Remote",
                    "detected_language": "en",
                    "match_score": 88,
                    "status": "qualified"
                }
                job_id = insert_job(job_dict)
                job_dict["id"] = job_id
                jobs_found.append(job_dict)
        except Exception as e:
            print(f"[JobRadar] Notice on WeWorkRemotely: {e}")

        return jobs_found

    async def scan_all_sources(self) -> List[Dict[str, Any]]:
        """Scans all supported sources concurrently."""
        remoteok_task = self.fetch_remoteok_jobs()
        # Run WeWorkRemotely sync in thread pool
        loop = asyncio.get_event_loop()
        wwr_task = loop.run_in_executor(None, self.fetch_weworkremotely_jobs)
        
        results = await asyncio.gather(remoteok_task, wwr_task, return_exceptions=True)
        all_jobs = []
        for r in results:
            if isinstance(r, list):
                all_jobs.extend(r)
        return all_jobs

job_radar = JobRadar()
