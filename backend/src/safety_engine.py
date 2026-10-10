"""
Q-Care Safety Engine

The safety engine is the first layer of Q-Care.
It checks whether a health request is appropriate for
the system to process and assigns a precautionary urgency level.

Q-Care does NOT diagnose diseases.
"""

# Words and phrases that should trigger urgent evaluation.
URGENT_KEYWORDS = [
    "difficulty breathing",
    "can't breathe",
    "cannot breathe",
    "severe chest pain",
    "unconscious",
    "fainted",
    "seizure",
    "heavy bleeding",
    "severe bleeding",
    "stroke",
]

# Symptoms that may require prompt medical evaluation,
# but are not automatically emergencies.
PROMPT_KEYWORDS = [
    "high fever",
    "persistent vomiting",
    "severe headache",
    "severe abdominal pain",
    "vision loss",
    "swelling",
    "persistent pain",
]


def check_safety(text):
    """
    Check a user's health description for safety signals.

    Returns a dictionary containing:
    - urgency: precautionary urgency category
    - matched_signals: words/phrases detected
    - action: recommended next step
    """

    if not text or not isinstance(text, str):
        return {
            "urgency": "unknown",
            "matched_signals": [],
            "action": "Please provide a clear description of the health concern."
        }

    text_lower = text.lower()

    urgent_matches = [
        keyword for keyword in URGENT_KEYWORDS
        if keyword in text_lower
    ]

    if urgent_matches:
        return {
            "urgency": "urgent",
            "matched_signals": urgent_matches,
            "action": (
                "Seek urgent medical evaluation. "
                "If the situation appears life-threatening, contact local emergency services."
            )
        }

    prompt_matches = [
        keyword for keyword in PROMPT_KEYWORDS
        if keyword in text_lower
    ]

    if prompt_matches:
        return {
            "urgency": "prompt",
            "matched_signals": prompt_matches,
            "action": (
                "Consider contacting a qualified healthcare professional "
                "for appropriate evaluation, especially if symptoms are worsening or persistent."
            )
        }

    return {
        "urgency": "routine",
        "matched_signals": [],
        "action": (
            "No immediate safety signal was detected from the description. "
            "This does not rule out a medical problem."
        )
    }