"""
Special Agent - Alter-Ego & Memory Automated Test Suite
Verifies psychometric modeling, 3-tier memory retention, tone sanitization, and consultation loop.
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.brain.alter_ego.mbti_matrix import get_mbti_details, generate_cognitive_system_prompt
from backend.brain.alter_ego.tone_alignment import tone_mirror
from backend.memory.episodic_memory import episodic_store
from backend.memory.semantic_memory import semantic_store
from backend.memory.feedback_learner import learner
from backend.brain.llm_engine import engine

def test_alter_ego_suite():
    print("=" * 65)
    print("🧠 ALTER-EGO & DIGITAL TWIN: AUTOMATED VERIFICATION SUITE")
    print("=" * 65)

    # 1. MBTI Psychometric Test
    print("[1/5] Testing MBTI 16-Personality Matrix...", end=" ")
    intj_data = get_mbti_details("INTJ")
    assert intj_data["name"] == "Architect / Mastermind", "MBTI lookup failed"
    prompt = generate_cognitive_system_prompt("INTJ")
    assert "INTJ" in prompt and "Ni" in prompt, "Cognitive prompt failed"
    print("PASSED! (INTJ Architect Model Verified)")

    # 2. Tone Alignment & Robotic Filler Sanitizer
    print("[2/5] Testing Tone Alignment & Anti-Robotic Filter...", end=" ")
    dirty_text = "Certainly! I hope this message finds you well. We can build your e-commerce store with high performance."
    cleaned = tone_mirror.clean_robotic_fillers(dirty_text)
    assert "Certainly!" not in cleaned, "Filler removal failed"
    assert "I hope this message finds you well" not in cleaned, "Filler removal failed"
    print(f"PASSED! (Sanitized: '{cleaned[:45]}...')")

    # 3. Semantic & Episodic Memory
    print("[3/5] Testing 3-Tier Memory Engine (Episodic & Semantic)...", end=" ")
    semantic_store.store_fact("identity", "preferred_payment_gateway", "bKash & Nagad")
    recalled = semantic_store.recall_fact("preferred_payment_gateway")
    assert recalled == "bKash & Nagad", "Semantic memory recall failed"
    
    ep_id = episodic_store.log_episode("milestone", "Alter-Ego architecture verified", "Full green test")
    assert ep_id > 0, "Episodic logging failed"
    print("PASSED! (Fact & Episode successfully stored & recalled)")

    # 4. Feedback Learner (Dynamic Adaptation)
    print("[4/5] Testing Feedback Learner (Never Repeat Mistake)...", end=" ")
    learner.learn_rule("সব সময় ক্লায়েন্টের বাজেটের বিষয়ে স্বচ্ছ থাকবে")
    active_rules = learner.get_active_rules()
    assert len(active_rules) > 0, "Learner rule missing"
    print(f"PASSED! ({len(active_rules)} active rules injected into cognitive stack)")

    # 5. Alter-Ego Consultation Loop
    print("[5/5] Testing Alter-Ego Direct Consultation...", end=" ")
    reply = engine.consult_alter_ego("আমাদের কি এই বাজেটে কাজ শুরু করা উচিত?")
    assert len(reply) > 20, "Alter-Ego consultation returned empty"
    print("PASSED!")
    print("\n" + "-" * 65)
    print("🗣️ Sample Alter-Ego Output:")
    print(reply)
    print("-" * 65)

    print("\n✨ ALL PSYCHOMETRIC & MEMORY SUBSYSTEMS FULLY SYNCHRONIZED!")
    print("=" * 65)

if __name__ == "__main__":
    test_alter_ego_suite()
