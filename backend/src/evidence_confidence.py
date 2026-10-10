"""
Q-Care Evidence Confidence V2.6

Calculates confidence in the retrieved evidence set.

IMPORTANT:
This confidence score describes the QUALITY and COVERAGE
of available evidence.

It does NOT represent:
- probability of a disease
- diagnostic certainty
- medical diagnosis
"""

# =========================================================
# CONFIGURATION
# =========================================================

MAX_SOURCE_SCORE = 1.0

SOURCE_TIER_SCORES = {
    1: 1.0,
    2: 0.85,
    3: 0.60,
}


# =========================================================
# SOURCE QUALITY
# =========================================================

def calculate_source_quality(evidence_list):
    """
    Calculate the average trust level of evidence sources.

    Tier 1 = highest configured trust
    Tier 2 = established secondary source
    Tier 3 = unknown/lower-trust source
    """

    if not evidence_list:
        return 0.0

    scores = []

    for evidence in evidence_list:

        tier = evidence.get(
            "source_tier",
            3,
        )

        score = SOURCE_TIER_SCORES.get(
            tier,
            SOURCE_TIER_SCORES[3],
        )

        scores.append(score)

    return round(
        sum(scores) / len(scores),
        4,
    )


# =========================================================
# CONCEPT COVERAGE
# =========================================================

def calculate_concept_coverage_score(
    coverage,
):
    """
    Convert V2.5 concept coverage into a bounded score.
    """

    if not coverage:
        return 0.0

    ratio = coverage.get(
        "coverage_ratio",
        0.0,
    )

    return round(
        max(
            0.0,
            min(
                1.0,
                ratio,
            ),
        ),
        4,
    )


# =========================================================
# SOURCE AGREEMENT
# =========================================================

def calculate_source_agreement_score(
    source_agreement,
):
    """
    Measure diversity of supporting sources.

    One trusted source can still be useful.
    Multiple independent sources provide stronger
    evidence agreement.

    The score therefore increases gradually rather
    than treating one source as zero confidence.
    """

    if not source_agreement:
        return 0.0

    source_count = source_agreement.get(
        "source_count",
        0,
    )

    if source_count <= 0:
        return 0.0

    if source_count == 1:
        return 0.60

    if source_count == 2:
        return 0.85

    return 1.0


# =========================================================
# EVIDENCE STRENGTH
# =========================================================

def calculate_evidence_strength(
    evidence_list,
):
    """
    Estimate evidence strength from structured evidence
    metadata.

    This is deliberately conservative.
    """

    if not evidence_list:
        return 0.0

    scores = []

    for evidence in evidence_list:

        category = evidence.get(
            "category",
            "unknown",
        )

        tier = evidence.get(
            "source_tier",
            3,
        )

        base = SOURCE_TIER_SCORES.get(
            tier,
            SOURCE_TIER_SCORES[3],
        )

        # Clinical evidence is directly useful for
        # individual symptom questions.
        if category == "clinical":
            category_adjustment = 1.0

        # Population evidence is valuable but answers
        # a different type of question.
        elif category == "population":
            category_adjustment = 0.85

        elif category == "vaccination":
            category_adjustment = 0.85

        else:
            category_adjustment = 0.60

        scores.append(
            base * category_adjustment
        )

    return round(
        sum(scores) / len(scores),
        4,
    )


# =========================================================
# OVERALL CONFIDENCE
# =========================================================

def calculate_overall_confidence(
    source_quality,
    concept_coverage,
    source_agreement,
    evidence_strength,
):
    """
    Combine evidence dimensions into one bounded score.

    This is an evidence-quality score, not a medical
    probability.
    """

    weights = {
        "source_quality": 0.30,
        "concept_coverage": 0.30,
        "source_agreement": 0.15,
        "evidence_strength": 0.25,
    }

    score = (
        source_quality
        * weights["source_quality"]
        + concept_coverage
        * weights["concept_coverage"]
        + source_agreement
        * weights["source_agreement"]
        + evidence_strength
        * weights["evidence_strength"]
    )

    return round(
        max(
            0.0,
            min(
                1.0,
                score,
            ),
        ),
        4,
    )


# =========================================================
# CONFIDENCE LABEL
# =========================================================

def classify_confidence(
    confidence,
):
    """
    Convert numerical evidence confidence into
    an explanatory category.
    """

    if confidence >= 0.85:
        return "high"

    if confidence >= 0.65:
        return "moderate"

    if confidence >= 0.40:
        return "limited"

    return "insufficient"


# =========================================================
# FULL CONFIDENCE PROFILE
# =========================================================

def calculate_confidence_profile(
    fused_evidence,
):
    """
    Calculate a complete V2.6 confidence profile
    from a V2.5 fused evidence response.
    """

    evidence_list = fused_evidence.get(
        "evidence",
        [],
    )

    coverage = fused_evidence.get(
        "coverage",
        {},
    )

    source_agreement = fused_evidence.get(
        "source_agreement",
        {},
    )

    source_quality = (
        calculate_source_quality(
            evidence_list
        )
    )

    concept_coverage = (
        calculate_concept_coverage_score(
            coverage
        )
    )

    agreement = (
        calculate_source_agreement_score(
            source_agreement
        )
    )

    evidence_strength = (
        calculate_evidence_strength(
            evidence_list
        )
    )

    overall = (
        calculate_overall_confidence(
            source_quality,
            concept_coverage,
            agreement,
            evidence_strength,
        )
    )

    return {
        "source_quality": source_quality,
        "concept_coverage": concept_coverage,
        "source_agreement": agreement,
        "evidence_strength": evidence_strength,
        "overall_confidence": overall,
        "confidence_label": classify_confidence(
            overall
        ),
        "interpretation": (
            "Evidence quality and coverage assessment; "
            "not a diagnosis or disease probability."
        ),
    }