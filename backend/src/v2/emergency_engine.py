"""
Q-CARE V2 Emergency Engine

Produces a precautionary 1-10 urgency indicator.
This is not a diagnosis or a guarantee of safety.
"""

RED_FLAG_PATTERNS = {
    "severe_breathing_difficulty": 10,
    "severe_chest_pain": 10,
    "unconscious": 10,
    "seizure": 10,
    "severe_bleeding": 10,
    "stroke_warning": 10,
    "blue_lips": 10,
    "rapidly_worsening": 9,
    "very_high_risk": 9,
}


def calculate_emergency_score(text, research=None):
    """
    Conservative deterministic safety layer.
    AI/Quantum outputs can inform context but cannot suppress
    explicit emergency signals.
    """
    lowered = (text or "").lower()

    for phrase, score in RED_FLAG_PATTERNS.items():
        readable = phrase.replace("_", " ")
        if readable in lowered:
            return {
                "score": score,
                "label": "Urgent - See Doctor Now" if score == 10 else "Very urgent",
                "reason": "A potentially serious warning sign was detected.",
                "source": "safety_gate",
            }

    return {
        "score": 1,
        "label": "Pretty normal",
        "reason": "No explicit emergency warning signal was detected by the safety gate.",
        "source": "safety_gate",
    }
