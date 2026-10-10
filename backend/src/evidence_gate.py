"""
Q-Care Evidence Gate V1

Filters ranked evidence before it reaches the analysis engine.

The gate answers one question:

    "Is this evidence relevant enough to be considered?"

IMPORTANT:
This module does NOT:
- diagnose diseases
- estimate disease probability
- determine medical severity
- determine emergency probability
- replace a healthcare professional

It only controls evidence quality and relevance.
"""


# ==========================================================
# CONFIGURATION
# ==========================================================

# Evidence scoring thresholds.

STRONG_EVIDENCE_THRESHOLD = 70.0
USABLE_EVIDENCE_THRESHOLD = 50.0


# Maximum number of evidence items passed downstream.

DEFAULT_MAX_RESULTS = 5


# ==========================================================
# EVIDENCE QUALITY CLASSIFICATION
# ==========================================================

def classify_evidence_quality(score):
    """
    Convert a V4 relevance score into a simple quality class.

    This is a retrieval-quality classification only.
    """

    try:
        score = float(score)
    except (TypeError, ValueError):
        score = 0.0

    if score >= STRONG_EVIDENCE_THRESHOLD:
        return "strong"

    if score >= USABLE_EVIDENCE_THRESHOLD:
        return "usable"

    return "insufficient"


# ==========================================================
# EVIDENCE USABILITY
# ==========================================================

def is_evidence_usable(
    evidence,
    minimum_score=USABLE_EVIDENCE_THRESHOLD,
):
    """
    Determine whether one ranked evidence item is usable.

    Evidence must contain a valid relevance score.

    Evidence below the threshold is rejected.
    """

    if not isinstance(
        evidence,
        dict,
    ):
        return False

    relevance = evidence.get(
        "relevance",
        {},
    )

    if not isinstance(
        relevance,
        dict,
    ):
        return False

    score = relevance.get(
        "score",
        0.0,
    )

    try:
        score = float(score)
    except (TypeError, ValueError):
        return False

    return score >= minimum_score


# ==========================================================
# GATE RANKED EVIDENCE
# ==========================================================

def apply_evidence_gate(
    ranked_results,
    minimum_score=USABLE_EVIDENCE_THRESHOLD,
    max_results=DEFAULT_MAX_RESULTS,
):
    """
    Filter ranked evidence using a minimum relevance threshold.

    Returns:

        {
            "status": "...",
            "evidence_available": True/False,
            "accepted_count": int,
            "rejected_count": int,
            "accepted": [...],
            "rejected": [...],
            "message": "..."
        }

    This function does not modify the original evidence items.
    """

    if not isinstance(
        ranked_results,
        list,
    ):
        return {
            "status": "invalid_input",
            "evidence_available": False,
            "accepted_count": 0,
            "rejected_count": 0,
            "accepted": [],
            "rejected": [],
            "message": (
                "No valid ranked evidence "
                "was provided."
            ),
        }


    accepted = []
    rejected = []


    for evidence in ranked_results:

        if not isinstance(
            evidence,
            dict,
        ):
            continue


        relevance = evidence.get(
            "relevance",
            {},
        )


        score = relevance.get(
            "score",
            0.0,
        )


        try:
            score = float(score)
        except (TypeError, ValueError):
            score = 0.0


        quality = classify_evidence_quality(
            score
        )


        evidence_copy = dict(
            evidence
        )


        evidence_copy["gate"] = {

            "accepted":
                score >= minimum_score,

            "quality":
                quality,

            "threshold":
                minimum_score,
        }


        if score >= minimum_score:

            accepted.append(
                evidence_copy
            )

        else:

            rejected.append(
                evidence_copy
            )


    # ------------------------------------------------------
    # Keep only the strongest accepted evidence.
    # ------------------------------------------------------

    accepted = accepted[
        :max_results
    ]


    # ------------------------------------------------------
    # Determine overall result.
    # ------------------------------------------------------

    if accepted:

        return {

            "status":
                "evidence_available",

            "evidence_available":
                True,

            "accepted_count":
                len(accepted),

            "rejected_count":
                len(rejected),

            "accepted":
                accepted,

            "rejected":
                rejected,

            "message": (
                "Sufficiently relevant "
                "verified evidence was found "
                "for downstream analysis."
            ),
        }


    return {

        "status":
            "insufficient_evidence",

        "evidence_available":
            False,

        "accepted_count":
            0,

        "rejected_count":
            len(rejected),

        "accepted":
            [],

        "rejected":
            rejected,

        "message": (
            "No sufficiently relevant "
            "evidence was found. "
            "Q-Care should not generate "
            "a confident recommendation "
            "from the available evidence."
        ),
    }


# ==========================================================
# CONVENIENCE FUNCTION
# ==========================================================

def gate_ranked_response(
    ranked_response,
    minimum_score=USABLE_EVIDENCE_THRESHOLD,
    max_results=DEFAULT_MAX_RESULTS,
):
    """
    Apply the evidence gate directly to a V4 ranked response.

    Preserves query and context information.
    """

    if not isinstance(
        ranked_response,
        dict,
    ):
        return {
            "status": "invalid_input",
            "query": "",
            "query_context": "unknown",
            "evidence_available": False,
            "accepted_count": 0,
            "rejected_count": 0,
            "accepted": [],
            "rejected": [],
            "message": (
                "Invalid ranked response."
            ),
        }


    gate_result = apply_evidence_gate(

        ranked_results=
            ranked_response.get(
                "results",
                []
            ),

        minimum_score=
            minimum_score,

        max_results=
            max_results,
    )


    return {

        "status":
            gate_result["status"],

        "query":
            ranked_response.get(
                "query",
                "",
            ),

        "query_context":
            ranked_response.get(
                "query_context",
                "unknown",
            ),

        "context_confidence":
            ranked_response.get(
                "context_confidence",
                0.0,
            ),

        "evidence_available":
            gate_result[
                "evidence_available"
            ],

        "accepted_count":
            gate_result[
                "accepted_count"
            ],

        "rejected_count":
            gate_result[
                "rejected_count"
            ],

        "accepted":
            gate_result[
                "accepted"
            ],

        "rejected":
            gate_result[
                "rejected"
            ],

        "message":
            gate_result[
                "message"
            ],

        "threshold":
            minimum_score,
    }