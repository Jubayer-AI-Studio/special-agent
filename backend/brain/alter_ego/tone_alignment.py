"""
Special Agent - Tone Alignment & Persona Mirror
Filters out robotic AI filler and ensures output resonates with the user's authentic DNA.
"""

import re
import os
import json
from typing import Dict, Any

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "persona_profile.json")

def load_persona_profile() -> Dict[str, Any]:
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

ROBOTIC_AI_PATTERNS = [
    r"(?i)^certainly!?",
    r"(?i)^sure thing!?",
    r"(?i)as an ai( language model)?",
    r"(?i)i hope this (email|message) finds you well",
    r"(?i)in conclusion,?",
    r"(?i)it is important to note that",
    r"(?i)please feel free to ask",
    r"(?i)i am just a computer program",
    r"(?i)let me know if you need further assistance"
]

class ToneAlignmentMirror:
    def __init__(self):
        self.profile = load_persona_profile()

    def clean_robotic_fillers(self, text: str) -> str:
        """
        Removes typical corporate AI conversational filler phrases.
        """
        cleaned = text.strip()
        for pattern in ROBOTIC_AI_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned)
        # Normalize double newlines and trailing whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned).strip()
        return cleaned

    def verify_alignment(self, text: str) -> Dict[str, Any]:
        """
        Evaluates text against user persona rules.
        """
        cleaned = self.clean_robotic_fillers(text)
        has_forbidden = False
        violations = []

        forbidden_list = self.profile.get("communication_dna", {}).get("forbidden_patterns", [])
        for f in forbidden_list:
            if f.lower() in text.lower():
                has_forbidden = True
                violations.append(f)

        return {
            "is_aligned": not has_forbidden,
            "violations": violations,
            "sanitized_text": cleaned
        }

tone_mirror = ToneAlignmentMirror()
