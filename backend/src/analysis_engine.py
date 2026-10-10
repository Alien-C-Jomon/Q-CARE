"""
Q-Care Analysis Engine V1

Combines:
- Safety signals
- Clinical context
- Evidence Gate results

to produce precautionary next-step guidance.

IMPORTANT:
Q-Care does NOT diagnose diseases.

This engine does NOT calculate:
- disease probability
- diagnosis confidence
- medical severity scores

Its output is precautionary guidance only.
"""


# ==========================================================
# CONFIGURATION
# ==========================================================

SUPPORTED_CONTEXTS = {
    "individual_symptom",
    "emergency_signal",
    "prevention",
    "vaccination",
    "population_health",
    "general_health",
}


# ==========================================================
# SAFETY-FIRST RULES
# ==========================================================

def analyze_safety(safety):
    """
    Interpret the safety engine result.

    Safety signals always take priority over evidence ranking.
    """

    if not isinstance(safety, dict):
        return {
            "priority": "unknown",
            "recommendation": (
                "Unable to interpret the safety information."
            ),
        }

    urgency = safety.get(
        "urgency",
        "unknown",
    )

    if urgency == "urgent":
        return {
            "priority": "urgent",
            "recommendation": (
                "Seek urgent medical evaluation. "
                "If the situation appears life-threatening, "
                "contact local emergency services."
            ),
        }

    if urgency == "prompt":
        return {
            "priority": "prompt",
            "recommendation": (
                "Consider contacting a qualified healthcare "
                "professional, particularly if symptoms "
                "are worsening, severe, or persistent."
            ),
        }

    if urgency == "routine":
        return {
            "priority": "routine",
            "recommendation": (
                "No immediate safety signal was detected "
                "from the description."
            ),
        }

    return {
        "priority": "unknown",
        "recommendation": (
            "The available safety information is insufficient "
            "to determine an appropriate urgency category."
        ),
    }


# ==========================================================
# EVIDENCE INTERPRETATION
# ==========================================================

def analyze_evidence(evidence):
    """
    Interpret the Evidence Gate result.

    Relevance scores are treated only as retrieval-quality
    measurements.
    """

    if not isinstance(evidence, dict):
        return {
            "status": "unavailable",
            "recommendation": (
                "Verified evidence could not be evaluated."
            ),
        }

    available = evidence.get(
        "evidence_available",
        False,
    )

    accepted_count = evidence.get(
        "accepted_count",
        0,
    )

    if not available or accepted_count == 0:
        return {
            "status": "insufficient",
            "recommendation": (
                "No sufficiently relevant verified evidence "
                "was found. Q-Care should not generate a "
                "specific medical recommendation from the "
                "current evidence set."
            ),
        }

    accepted = evidence.get(
        "accepted",
        [],
    )

    strong_count = 0

    for item in accepted:

        gate = item.get(
            "gate",
            {},
        )

        if gate.get(
            "quality"
        ) == "strong":

            strong_count += 1

    if strong_count > 0:
        return {
            "status": "strong",
            "recommendation": (
                "Relevant verified evidence is available "
                "for precautionary guidance."
            ),
        }

    return {
        "status": "usable",
        "recommendation": (
            "Some relevant verified evidence is available, "
            "but the evidence should be interpreted cautiously."
        ),
    }


# ==========================================================
# CONTEXT INTERPRETATION
# ==========================================================

def analyze_context(
    query_context,
    context_confidence=0.0,
):
    """
    Interpret the clinical context classification.

    This describes the type of question, not the disease.
    """

    if query_context not in SUPPORTED_CONTEXTS:
        return {
            "context": "unknown",
            "confidence": 0.0,
            "description": (
                "The type of health request could not "
                "be reliably classified."
            ),
        }

    descriptions = {

        "individual_symptom":
            "The request concerns an individual's reported symptoms.",

        "emergency_signal":
            "The request contains a potentially urgent safety signal.",

        "prevention":
            "The request concerns prevention or risk reduction.",

        "vaccination":
            "The request concerns vaccination or immunization.",

        "population_health":
            "The request concerns population-level health information.",

        "general_health":
            "The request concerns general health information.",
    }

    return {
        "context": query_context,
        "confidence": context_confidence,
        "description": descriptions[
            query_context
        ],
    }


# ==========================================================
# FINAL RECOMMENDATION LOGIC
# ==========================================================

def build_recommendation(
    safety_result,
    evidence_result,
    context_result,
):
    """
    Combine safety, evidence, and context.

    Safety takes priority.
    Evidence determines whether detailed guidance
    is appropriate.
    """

    safety_priority = safety_result.get(
        "priority",
        "unknown",
    )

    evidence_status = evidence_result.get(
        "status",
        "unavailable",
    )

    context = context_result.get(
        "context",
        "unknown",
    )


    # ------------------------------------------------------
    # 1. URGENT SAFETY SIGNAL
    # ------------------------------------------------------

    if safety_priority == "urgent":

        return {
            "category":
                "urgent",

            "action":
                safety_result[
                    "recommendation"
                ],

            "reason":
                "A safety signal was detected.",

            "evidence_used":
                evidence_status,

            "diagnostic_claim":
                False,
        }


    # ------------------------------------------------------
    # 2. PROMPT MEDICAL EVALUATION
    # ------------------------------------------------------

    if safety_priority == "prompt":

        if evidence_status == "insufficient":

            return {
                "category":
                    "prompt",

                "action":
                    safety_result[
                        "recommendation"
                    ],

                "reason":
                    "The safety engine detected a "
                    "potentially concerning signal, "
                    "while the evidence gate did not "
                    "find sufficient relevant evidence.",

                "evidence_used":
                    evidence_status,

                "diagnostic_claim":
                    False,
            }

        return {
            "category":
                "prompt",

            "action":
                safety_result[
                    "recommendation"
                ],

            "reason":
                "The safety engine detected a "
                "potentially concerning signal.",

            "evidence_used":
                evidence_status,

            "diagnostic_claim":
                False,
        }


    # ------------------------------------------------------
    # 3. INSUFFICIENT EVIDENCE
    # ------------------------------------------------------

    if evidence_status == "insufficient":

        return {
            "category":
                "insufficient_evidence",

            "action":
                (
                    "Q-Care does not have enough "
                    "relevant verified evidence to "
                    "provide specific guidance. "
                    "Consider consulting a qualified "
                    "healthcare professional if the "
                    "concern persists or worsens."
                ),

            "reason":
                "Evidence Gate rejected the available evidence.",

            "evidence_used":
                evidence_status,

            "diagnostic_claim":
                False,
        }


    # ------------------------------------------------------
    # 4. INDIVIDUAL SYMPTOM
    # ------------------------------------------------------

    if context == "individual_symptom":

        return {
            "category":
                "precautionary_guidance",

            "action":
                (
                    "Relevant verified information is "
                    "available. Use it for general "
                    "precautionary guidance and monitor "
                    "whether symptoms improve, persist, "
                    "or worsen."
                ),

            "reason":
                "The request concerns an individual's "
                "reported symptoms.",

            "evidence_used":
                evidence_status,

            "diagnostic_claim":
                False,
        }


    # ------------------------------------------------------
    # 5. GENERAL HEALTH
    # ------------------------------------------------------

    if context == "general_health":

        return {
            "category":
                "general_information",

            "action":
                (
                    "Relevant verified health information "
                    "is available for general educational use."
                ),

            "reason":
                "The request is general health information.",

            "evidence_used":
                evidence_status,

            "diagnostic_claim":
                False,
        }


    # ------------------------------------------------------
    # 6. POPULATION / VACCINATION / PREVENTION
    # ------------------------------------------------------

    if context in {
        "population_health",
        "vaccination",
        "prevention",
    }:

        return {
            "category":
                "health_information",

            "action":
                (
                    "Relevant verified information is "
                    "available for health education and "
                    "decision support."
                ),

            "reason":
                (
                    "The request concerns "
                    + context.replace(
                        "_",
                        " ",
                    )
                    + "."
                ),

            "evidence_used":
                evidence_status,

            "diagnostic_claim":
                False,
        }


    # ------------------------------------------------------
    # 7. FALLBACK
    # ------------------------------------------------------

    return {
        "category":
            "cautious_information",

        "action":
            (
                "Relevant verified evidence is available, "
                "but the request should be interpreted "
                "cautiously."
            ),

        "reason":
            "The request context was not specific enough.",

        "evidence_used":
            evidence_status,

        "diagnostic_claim":
            False,
    }


# ==========================================================
# MAIN ANALYSIS FUNCTION
# ==========================================================

def analyze_assessment(
    safety,
    evidence,
    query_context,
    context_confidence=0.0,
):
    """
    Main Q-Care analysis pipeline.

    Returns a structured, non-diagnostic assessment.
    """

    safety_result = analyze_safety(
        safety
    )

    evidence_result = analyze_evidence(
        evidence
    )

    context_result = analyze_context(
        query_context,
        context_confidence,
    )

    recommendation = build_recommendation(
        safety_result,
        evidence_result,
        context_result,
    )

    return {

        "status":
            "completed",

        "safety":
            safety_result,

        "evidence":
            evidence_result,

        "context":
            context_result,

        "recommendation":
            recommendation,

        "diagnostic":
            False,

        "disclaimer":
            (
                "Q-Care provides precautionary "
                "health information and does not "
                "diagnose medical conditions."
            ),
    }