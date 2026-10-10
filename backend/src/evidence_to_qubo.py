"""
Q-Care Evidence-to-QUBO Adapter V1

Converts fused evidence records into transparent optimization
scores suitable for the Q-Care QUBO/QAOA evidence-selection layer.

IMPORTANT:
These scores represent evidence-selection usefulness.

They do NOT represent:
- disease probability
- diagnostic certainty
- medical severity
- clinical effectiveness
"""

from typing import Any, Dict, List


# =========================================================
# CONFIGURATION
# =========================================================

RELEVANCE_WEIGHT = 0.40
COVERAGE_WEIGHT = 0.30
QUALITY_WEIGHT = 0.30

REDUNDANCY_PENALTY_WEIGHT = 0.20

MAX_SCORE = 10.0


# =========================================================
# BOUNDED VALUE HELPER
# =========================================================

def _bounded(value: float) -> float:
    """
    Clamp a numerical value to the range [0, 1].
    """

    return max(
        0.0,
        min(
            1.0,
            float(value),
        ),
    )


# =========================================================
# RELEVANCE
# =========================================================

def calculate_relevance(
    evidence: Dict[str, Any],
    concepts: List[str],
) -> float:
    """
    Estimate evidence relevance from structured metadata.

    If an upstream relevance score already exists, use it.

    Otherwise, conservatively derive relevance from the
    proportion of requested concepts matched by the evidence.

    Returns a value in [0, 1].
    """

    if "relevance_score" in evidence:
        try:
            return _bounded(
                float(evidence["relevance_score"])
            )
        except (TypeError, ValueError):
            pass

    matched = evidence.get(
        "matched_concepts",
        [],
    )

    if not concepts:
        return 0.0

    return _bounded(
        len(set(matched))
        / len(set(concepts))
    )


# =========================================================
# CONCEPT COVERAGE
# =========================================================

def calculate_coverage(
    evidence: Dict[str, Any],
    concepts: List[str],
) -> float:
    """
    Calculate evidence-level concept coverage.

    This is intentionally based only on concepts explicitly
    matched during the fusion stage.
    """

    matched = evidence.get(
        "matched_concepts",
        [],
    )

    if not concepts:
        return 0.0

    return _bounded(
        len(set(matched))
        / len(set(concepts))
    )


# =========================================================
# SOURCE QUALITY
# =========================================================

SOURCE_TIER_QUALITY = {
    1: 1.00,
    2: 0.85,
    3: 0.60,
}


def calculate_source_quality(
    evidence: Dict[str, Any],
) -> float:
    """
    Convert the existing source tier into a bounded
    source-quality score.

    Tier 1 = 1.00
    Tier 2 = 0.85
    Tier 3 = 0.60
    """

    tier = evidence.get(
        "source_tier",
        3,
    )

    try:
        tier = int(tier)
    except (TypeError, ValueError):
        tier = 3

    return SOURCE_TIER_QUALITY.get(
        tier,
        SOURCE_TIER_QUALITY[3],
    )


# =========================================================
# REDUNDANCY
# =========================================================

def calculate_redundancy(
    evidence: Dict[str, Any],
) -> float:
    """
    Return a bounded redundancy value.

    Evidence fusion already removes exact duplicates, so
    the default redundancy is zero unless an upstream
    component explicitly supplies a redundancy_score.

    This keeps the adapter from inventing redundancy data.
    """

    if "redundancy_score" not in evidence:
        return 0.0

    try:
        return _bounded(
            float(
                evidence["redundancy_score"]
            )
        )
    except (TypeError, ValueError):
        return 0.0


# =========================================================
# SCORE
# =========================================================

def calculate_selection_score(
    evidence: Dict[str, Any],
    concepts: List[str],
) -> Dict[str, float]:
    """
    Calculate a transparent 0-10 evidence-selection score.

    Formula:

        base =
            0.40 * relevance
          + 0.30 * coverage
          + 0.30 * source_quality

        final =
            base - 0.20 * redundancy

    The result is scaled to 0-10.

    This is an optimization score only.
    """

    relevance = calculate_relevance(
        evidence,
        concepts,
    )

    coverage = calculate_coverage(
        evidence,
        concepts,
    )

    source_quality = calculate_source_quality(
        evidence,
    )

    redundancy = calculate_redundancy(
        evidence,
    )

    base_score = (
        RELEVANCE_WEIGHT * relevance
        + COVERAGE_WEIGHT * coverage
        + QUALITY_WEIGHT * source_quality
    )

    adjusted_score = (
        base_score
        - REDUNDANCY_PENALTY_WEIGHT * redundancy
    )

    score = _bounded(
        adjusted_score
    ) * MAX_SCORE

    return {
        "relevance": round(
            relevance,
            4,
        ),
        "coverage": round(
            coverage,
            4,
        ),
        "source_quality": round(
            source_quality,
            4,
        ),
        "redundancy": round(
            redundancy,
            4,
        ),
        "base_score": round(
            base_score,
            4,
        ),
        "selection_score": round(
            score,
            4,
        ),
    }


# =========================================================
# ADAPT FUSED EVIDENCE
# =========================================================

def adapt_fused_evidence(
    fused_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert a V2.5 fused evidence response into a QUBO-ready
    evidence representation.

    Existing evidence records are preserved.

    New selection metadata is added under:
        evidence_selection
    """

    concepts = fused_evidence.get(
        "concepts",
        [],
    )

    evidence_list = fused_evidence.get(
        "evidence",
        [],
    )

    adapted = []

    for index, evidence in enumerate(
        evidence_list
    ):

        score_profile = calculate_selection_score(
            evidence,
            concepts,
        )

        adapted_evidence = {
            **evidence,
            "evidence_index": index,
            "evidence_selection": score_profile,
        }

        adapted.append(
            adapted_evidence
        )

    scores = [
        evidence["evidence_selection"]["selection_score"]
        for evidence in adapted
    ]

    return {
        "query": fused_evidence.get(
            "query",
            "",
        ),
        "context": fused_evidence.get(
            "context",
            {},
        ),
        "concepts": concepts,
        "evidence": adapted,
        "selection_scores": scores,
        "evidence_count": len(adapted),
        "status": (
            "qubo_ready"
            if adapted
            else "no_evidence"
        ),
    }


# =========================================================
# QUBO INPUT
# =========================================================

def build_qubo_input(
    fused_evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build the exact score vector needed by the existing
    Q-Care QUBO/QAOA optimizer.

    The optimizer can then receive:

        scores = result["scores"]

    """

    adapted = adapt_fused_evidence(
        fused_evidence
    )

    return {
        "scores": adapted["selection_scores"],
        "maximum_selected": 2,
        "evidence": adapted["evidence"],
        "query": adapted["query"],
        "concepts": adapted["concepts"],
        "status": adapted["status"],
    }