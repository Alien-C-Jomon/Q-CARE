"""
Q-Care Clinical Context Engine V1

Determines what kind of health question the user is asking.

IMPORTANT:
This module does NOT diagnose diseases.
It only identifies the context and intent of the request.
"""

import re


# --------------------------------------------------
# Context categories
# --------------------------------------------------

CONTEXT_INDIVIDUAL_SYMPTOM = "individual_symptom"
CONTEXT_EMERGENCY_SIGNAL = "emergency_signal"
CONTEXT_PREVENTION = "prevention"
CONTEXT_VACCINATION = "vaccination"
CONTEXT_POPULATION_HEALTH = "population_health"
CONTEXT_GENERAL_HEALTH = "general_health"


# --------------------------------------------------
# Keyword groups
# --------------------------------------------------

EMERGENCY_TERMS = {
    "difficulty breathing",
    "cannot breathe",
    "can't breathe",
    "severe chest pain",
    "unconscious",
    "fainted",
    "seizure",
    "heavy bleeding",
    "severe bleeding",
}


VACCINATION_TERMS = {
    "vaccine",
    "vaccination",
    "vaccinated",
    "immunization",
    "immunisation",
}


POPULATION_TERMS = {
    "population",
    "reported cases",
    "number of cases",
    "case count",
    "incidence",
    "prevalence",
    "coverage",
    "statistics",
    "statistic",
    "outbreak",
    "surveillance",
    "health facilities",
    "public sector",
    "reported",
    "cases",
}


PREVENTION_TERMS = {
    "prevent",
    "prevention",
    "avoid",
    "risk reduction",
    "protect against",
}


SYMPTOM_TERMS = {
    "fever",
    "headache",
    "migraine",
    "swelling",
    "swollen",
    "puffiness",
    "puffy",
    "pain",
    "vomiting",
    "vomit",
    "cough",
    "breathing",
    "shortness of breath",
    "vision loss",
    "blurred vision",
}


INDIVIDUAL_TERMS = {
    "i have",
    "i am",
    "my",
    "me",
    "myself",
    "i feel",
    "i'm having",
    "i've got",
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def normalize_text(text):
    """Normalize user input."""

    if not isinstance(text, str):
        return ""

    text = text.lower()

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def find_matches(text, terms):
    """Return terms found in normalized text."""

    normalized = normalize_text(text)

    return [
        term
        for term in terms
        if normalize_text(term) in normalized
    ]


# --------------------------------------------------
# Main classifier
# --------------------------------------------------

def classify_context(text):
    """
    Classify the user's health-query context.

    Returns:
        {
            "context": "...",
            "matched_terms": [...],
            "confidence": 0.0-1.0,
            "reason": "..."
        }

    This is a context classifier only.
    It does NOT determine disease probability.
    """

    normalized = normalize_text(text)

    if not normalized:
        return {
            "context": CONTEXT_GENERAL_HEALTH,
            "matched_terms": [],
            "confidence": 0.0,
            "reason": (
                "No usable health-query text "
                "was provided."
            ),
        }


    # --------------------------------------------------
    # 1. Emergency signal
    # --------------------------------------------------

    emergency_matches = find_matches(
        normalized,
        EMERGENCY_TERMS,
    )

    if emergency_matches:

        return {
            "context": CONTEXT_EMERGENCY_SIGNAL,
            "matched_terms": emergency_matches,
            "confidence": 1.0,
            "reason": (
                "The query contains a recognized "
                "urgent safety signal."
            ),
        }


    # --------------------------------------------------
    # 2. Vaccination
    # --------------------------------------------------

    vaccination_matches = find_matches(
        normalized,
        VACCINATION_TERMS,
    )

    if vaccination_matches:

        return {
            "context": CONTEXT_VACCINATION,
            "matched_terms": vaccination_matches,
            "confidence": 1.0,
            "reason": (
                "The query is primarily about "
                "vaccination or immunization."
            ),
        }


    # --------------------------------------------------
    # 3. Population health
    # --------------------------------------------------

    population_matches = find_matches(
        normalized,
        POPULATION_TERMS,
    )

    if population_matches:

        return {
            "context": CONTEXT_POPULATION_HEALTH,
            "matched_terms": population_matches,
            "confidence": 0.95,
            "reason": (
                "The query contains population-level "
                "health or epidemiological terminology."
            ),
        }


    # --------------------------------------------------
    # 4. Prevention
    # --------------------------------------------------

    prevention_matches = find_matches(
        normalized,
        PREVENTION_TERMS,
    )

    if prevention_matches:

        return {
            "context": CONTEXT_PREVENTION,
            "matched_terms": prevention_matches,
            "confidence": 0.9,
            "reason": (
                "The query is focused on prevention "
                "or risk reduction."
            ),
        }


    # --------------------------------------------------
    # 5. Individual symptom
    # --------------------------------------------------

    symptom_matches = find_matches(
        normalized,
        SYMPTOM_TERMS,
    )

    individual_matches = find_matches(
        normalized,
        INDIVIDUAL_TERMS,
    )

    if symptom_matches:

        confidence = 0.85

        if individual_matches:
            confidence = 0.95

        return {
            "context": CONTEXT_INDIVIDUAL_SYMPTOM,
            "matched_terms": list(
                dict.fromkeys(
                    symptom_matches
                    + individual_matches
                )
            ),
            "confidence": confidence,
            "reason": (
                "The query describes a symptom "
                "or health concern involving an "
                "individual."
            ),
        }


    # --------------------------------------------------
    # 6. General health
    # --------------------------------------------------

    return {
        "context": CONTEXT_GENERAL_HEALTH,
        "matched_terms": [],
        "confidence": 0.5,
        "reason": (
            "No specific clinical context "
            "was identified."
        ),
    }