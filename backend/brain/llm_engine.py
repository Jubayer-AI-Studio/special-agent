"""
Special Agent - Intelligence & Alter-Ego Engine
Powers cognitive decision-making, MBTI alignment, persistent memory recall, and proposal crafting.
"""

import os
import json
import re
from typing import Dict, Any, Optional, List
from openai import OpenAI
from backend.brain.prompt_templates import (
    QUALIFICATION_SYSTEM_PROMPT,
    PROPOSAL_SYSTEM_PROMPT,
    DEFAULT_USER_PROFILE
)
from backend.brain.alter_ego.mbti_matrix import generate_cognitive_system_prompt, get_mbti_details
from backend.brain.alter_ego.tone_alignment import tone_mirror, load_persona_profile
from backend.memory.feedback_learner import learner
from backend.memory.semantic_memory import semantic_store
from backend.memory.episodic_memory import episodic_store

class LLMEngine:
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv("LLM_MODEL", "nousresearch/hermes-3-llama-3.1-8b")
        self.persona = load_persona_profile()
        self.mbti_type = self.persona.get("mbti", {}).get("type", "INTJ")
        
        self.client = None
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

    def _build_alter_ego_system_prompt(self) -> str:
        """
        Dynamically constructs system prompt from MBTI, active user feedback rules, and memory facts.
        """
        base_prompt = generate_cognitive_system_prompt(self.mbti_type)
        
        # Inject learned rules from user feedback
        active_rules = learner.get_active_rules()
        rules_text = ""
        if active_rules:
            rules_text = "\n\nCRITICAL USER RULES (NEVER VIOLATE):\n" + "\n".join(f"- {r}" for r in active_rules)
            
        # Inject known facts from semantic memory
        facts = semantic_store.get_all_facts()
        facts_text = ""
        if facts:
            facts_text = "\n\nKNOWN USER FACTS & CONTEXT:\n" + "\n".join(f"- {f['fact_key']}: {f['fact_value']}" for f in facts[:15])

        user_name = self.persona.get("user_name", "Operator")
        return (
            f"{base_prompt}\n"
            f"User Identity: {user_name} ({self.mbti_type} Archetype)\n"
            f"Language & Tone: {self.persona.get('communication_dna', {}).get('preferred_language', 'Bengali & English blend')}. "
            f"Tone: {self.persona.get('communication_dna', {}).get('tone', 'Direct, strategic, zero fluff')}."
            f"{rules_text}"
            f"{facts_text}"
        )

    def consult_alter_ego(self, user_query: str, context: Optional[str] = None) -> str:
        """
        Allows the user to speak directly with their Alter-Ego for advice, decisions, brainstorming, or technical design.
        """
        system_prompt = self._build_alter_ego_system_prompt()
        prompt_with_context = f"{user_query}\n\nContext:\n{context}" if context else user_query

        if not self.client:
            # High-fidelity simulated Alter-Ego response
            is_bangla = any(ord(char) >= 0x0980 and ord(char) <= 0x09FF for char in user_query)
            if is_bangla:
                reply = (
                    f"আমি ঠিক তোমার চিন্তার সাথে একমত। আমাদের {self.mbti_type} স্ট্র্যাটেজিক নীতি অনুযায়ী:\n\n"
                    f"১. কোনো অস্পষ্ট পদক্ষেপ নেওয়ার চেয়ে আগে আর্কিটেকচার ঠিক করা সবচেয়ে ভালো সিদ্ধান্ত।\n"
                    f"২. হাই-লেভারেজ কাজ এবং ডলার আয়ের লক্ষ্য অর্জনে আমাদের প্রতিটি স্টেপ হিসাব করে এগোতে হবে।\n\n"
                    f"তোমার প্রশ্নের বিষয়ে আমার স্পষ্ট পরামর্শ: প্রথমে মূল ভিত্তি শেষ করো, তারপর ধাপে ধাপে এক্সিকিউট করো।"
                )
            else:
                reply = (
                    f"Thinking through our {self.mbti_type} strategic lens:\n\n"
                    f"1. First-principles analysis: focus strictly on high-ROI leverage and zero unnecessary overhead.\n"
                    f"2. Keep human-in-the-loop control while automating the low-level grind.\n\n"
                    f"Recommendation: Proceed with structured execution and verify each milestone."
                )
            
            # Log this episode in memory
            episodic_store.log_episode(
                event_type="alter_ego_consultation",
                summary=f"Q: {user_query[:50]}...",
                raw_content=f"User: {user_query}\nAlterEgo: {reply}"
            )
            return reply

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt_with_context}
                ],
                temperature=0.7,
                max_tokens=600
            )
            raw_reply = response.choices[0].message.content.strip()
            sanitized = tone_mirror.clean_robotic_fillers(raw_reply)
            
            episodic_store.log_episode(
                event_type="alter_ego_consultation",
                summary=f"Q: {user_query[:50]}...",
                raw_content=f"User: {user_query}\nAlterEgo: {sanitized}"
            )
            return sanitized
        except Exception as e:
            return f"Error from Alter-Ego engine: {str(e)}"

    def qualify_lead(self, content: str) -> Dict[str, Any]:
        """
        Analyzes a post to verify if it's a hiring lead and extracts contact info.
        """
        phone_match = re.search(r'(?:\+?880|0)1[3-9]\d{8}', content)
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', content)
        extracted_contact = []
        if phone_match:
            extracted_contact.append(phone_match.group(0))
        if email_match:
            extracted_contact.append(email_match.group(0))
        contact_str = ", ".join(extracted_contact) if extracted_contact else "Not Found"

        if not self.client:
            hiring_keywords = [
                "looking for", "need developer", "need designer", "hiring", "developer দরকার", 
                "ডেভেলপার দরকার", "ওয়েবসাইট বানাতে হবে", "কাজ করাতে চাই", "বাজেট", "freelancer",
                "urgently required", "project"
            ]
            matches = [k for k in hiring_keywords if k in content.lower()]
            is_valid = len(matches) > 0
            score = min(95, 40 + len(matches) * 15) if is_valid else 10
            
            return {
                "is_valid_lead": is_valid,
                "match_score": score,
                "detected_budget": "See Post Details",
                "summary": "সম্ভাব্য ক্লায়েন্ট রিকোয়ারমেন্ট সনাক্ত করা হয়েছে।" if is_valid else "সাধারণ পোস্ট বা আলোচনা।",
                "contact_info": contact_str
            }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": QUALIFICATION_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Post Content:\n{content}"}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            data = json.loads(response.choices[0].message.content)
            if contact_str != "Not Found" and data.get("contact_info") in [None, "None"]:
                data["contact_info"] = contact_str
            return data
        except Exception as e:
            return {
                "is_valid_lead": True,
                "match_score": 75,
                "detected_budget": "Unknown",
                "summary": f"স্বয়ংক্রিয় বিশ্লেষণ (ত্রুটি: {str(e)[:30]})",
                "contact_info": contact_str
            }

    def generate_proposal(self, lead_title: str, lead_content: str, source: str = "facebook") -> str:
        """
        Drafts a customized, high-converting pitch for the qualified lead through the Alter-Ego lens.
        """
        skills_summary = ", ".join(DEFAULT_USER_PROFILE["primary_skills"])
        portfolio_summary = ", ".join(DEFAULT_USER_PROFILE["portfolio_links"])
        system_persona = self._build_alter_ego_system_prompt()
        
        user_prompt = f"""
Source: {source}
Job Title: {lead_title or 'Project Request'}
Job Details:
{lead_content}

Candidate Profile:
- Skills: {skills_summary}
- Portfolio: {portfolio_summary}
- Experience: {DEFAULT_USER_PROFILE['experience_years']} years

Task: Draft an authentic pitch written strictly in MY voice ({self.mbti_type} direct, high-value, no generic fluff).
"""
        if not self.client:
            is_bangla = any(ord(char) >= 0x0980 and ord(char) <= 0x09FF for char in lead_content)
            if is_bangla:
                pitch = (
                    f"শুভ অপরাহ্ন! আপনার প্রজেক্টের রিকোয়ারমেন্টটি পড়েছি। ফুলস্ট্যাক ডেভেলপমেন্ট এবং আধুনিক ওয়েব সলিউশনে ৪+ বছর ধরে কাজ করছি।\n\n"
                    f"আপনার প্রজেক্টটি নিখুঁত কোড কোয়ালিটি এবং দ্রুত ডেলিভারি নিশ্চিত করতে পারব।\n"
                    f"পোর্টফোলিও লিংক: {portfolio_summary}\n\n"
                    f"কাজের সুনির্দিষ্ট টাইমলাইন ও বিস্তারিত নিয়ে ইনবক্সে কথা বলতে পারেন। ধন্যবাদ।"
                )
            else:
                pitch = (
                    f"Hello! I reviewed your project scope carefully.\n"
                    f"With 4+ years of hands-on full-stack development and system architecture, I can deliver this cleanly and rapidly.\n\n"
                    f"Portfolio: {portfolio_summary}\n"
                    f"Let's connect in chat to discuss your specific milestones and deliverables."
                )
            return tone_mirror.clean_robotic_fillers(pitch)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"{system_persona}\n\n{PROPOSAL_SYSTEM_PROMPT}"},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                max_tokens=400
            )
            raw_text = response.choices[0].message.content.strip()
            return tone_mirror.clean_robotic_fillers(raw_text)
        except Exception as e:
            return f"Error generating proposal: {str(e)}"

# Singleton instance
engine = LLMEngine()
