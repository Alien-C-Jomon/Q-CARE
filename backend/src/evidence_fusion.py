"""
Q-Care Evidence Fusion V2.5

Combines retrieved evidence into a structured evidence set.

The purpose is to preserve:
- the original query
- detected clinical concepts
- source trust
- evidence type
- evidence context
- source agreement
- redundancy

This module does NOT diagnose conditions.
"""

from collections import Counter


# =========================================================
# SOURCE TRUST
# =========================================================

SOURCE_TIERS = {
    "World Health Organization": 1,
    "National Library of Medicine / MedlinePlus": 1,
    "Centers for Disease Control and Prevention": 1,
}


# =========================================================
# EVIDENCE TYPE LABELS
# =========================================================

CLINICAL_TYPES = {
    "clinical_information",
}

POPULATION_TYPES = {
    "public_health_statistic",
    "epidemiological_data",
}

VACCINATION_TYPES = {
    "vaccination_information",
}


# =========================================================
# SOURCE TIER
# =========================================================

def get_source_tier(source):
    """
    Return the configured trust tier.

    Unknown sources are deliberately assigned a lower tier.
    """

    return SOURCE_TIERS.get(
        source,
        3,
    )


# =========================================================
# EVIDENCE NORMALIZATION
# =========================================================

def normalize_evidence(evidence):
    """
    Convert one evidence record into a consistent structure.
    """

    source = evidence.get(
        "source",
        "Unknown source",
    )

    evidence_type = evidence.get(
        "evidence_type",
        "unknown",
    )

    evidence_context = evidence.get(
        "evidence_context",
        "unknown",
    )

    return {
        **evidence,
        "source_tier": get_source_tier(source),
        "evidence_type": evidence_type,
        "evidence_context": evidence_context,
    }


# =========================================================
# CONCEPT COVERAGE
# =========================================================

def calculate_concept_coverage(
    concepts,
    evidence,
):
    """
    Determine which query concepts are represented
    by an evidence item.

    Evidence topic matching is intentionally conservative.
    """

    if not concepts:
        return []

    topic = str(
        evidence.get(
            "topic",
            "",
        )
    ).lower()

    title = str(
        evidence.get(
            "title",
            "",
        )
    ).lower()

    combined = f"{topic} {title}"

    matched = []

    for concept in concepts:

        concept_lower = concept.lower()

        if concept_lower in combined:
            matched.append(concept)

    return sorted(set(matched))


# =========================================================
# EVIDENCE CATEGORY
# =========================================================

def classify_evidence_category(evidence_type):

    if evidence_type in CLINICAL_TYPES:
        return "clinical"

    if evidence_type in POPULATION_TYPES:
        return "population"

    if evidence_type in VACCINATION_TYPES:
        return "vaccination"

    return "unknown"


# =========================================================
# REDUNDANCY
# =========================================================

def evidence_signature(evidence):
    """
    Create a simple signature for detecting duplicate
    evidence records.
    """

    return (
        evidence.get("source"),
        evidence.get("title"),
        evidence.get("topic"),
    )


def remove_duplicate_evidence(evidence_list):

    seen = set()
    unique = []

    for evidence in evidence_list:

        signature = evidence_signature(
            evidence
        )

        if signature in seen:
            continue

        seen.add(signature)
        unique.append(evidence)

    return unique


# =========================================================
# SOURCE AGREEMENT
# =========================================================

def calculate_source_agreement(evidence_list):

    sources = [
        evidence.get("source")
        for evidence in evidence_list
    ]

    counts = Counter(
        source
        for source in sources
        if source
    )

    return {
        "unique_sources": sorted(
            counts.keys()
        ),
        "source_count": len(counts),
        "source_distribution": dict(counts),
    }


# =========================================================
# CONCEPT COVERAGE SUMMARY
# =========================================================

def calculate_coverage_summary(
    concepts,
    evidence_list,
):

    covered = set()

    for evidence in evidence_list:

        matched = evidence.get(
            "matched_concepts",
            [],
        )

        covered.update(
            matched
        )

    missing = [
        concept
        for concept in concepts
        if concept not in covered
    ]

    return {
        "requested_concepts": concepts,
        "covered_concepts": sorted(
            covered
        ),
        "missing_concepts": missing,
        "coverage_ratio": (
            len(covered) / len(concepts)
            if concepts
            else 0.0
        ),
    }


# =========================================================
# FUSION
# =========================================================

def fuse_evidence(
    query,
    concepts,
    results,
    context=None,
):

    normalized_results = []

    for raw_evidence in results:

        evidence = normalize_evidence(
            raw_evidence
        )

        evidence["matched_concepts"] = (
            calculate_concept_coverage(
                concepts,
                evidence,
            )
        )

        evidence["category"] = (
            classify_evidence_category(
                evidence["evidence_type"]
            )
        )

        normalized_results.append(
            evidence
        )

    normalized_results = (
        remove_duplicate_evidence(
            normalized_results
        )
    )

    source_agreement = (
        calculate_source_agreement(
            normalized_results
        )
    )

    coverage = (
        calculate_coverage_summary(
            concepts,
            normalized_results,
        )
    )

    categories = Counter(
        evidence["category"]
        for evidence in normalized_results
    )

    return {
        "query": query,
        "context": context,
        "concepts": concepts,
        "evidence": normalized_results,
        "evidence_count": len(
            normalized_results
        ),
        "source_agreement": source_agreement,
        "coverage": coverage,
        "category_distribution": dict(
            categories
        ),
        "status": (
            "evidence_fused"
            if normalized_results
            else "no_evidence"
        ),
    }


# =========================================================
# FUSION FROM V2.4 RESPONSE
# =========================================================

def fuse_retrieval_response(
    retrieval_response,
):

    return fuse_evidence(
        query=retrieval_response.get(
            "query",
            "",
        ),
        concepts=retrieval_response.get(
            "concepts",
            [],
        ),
        results=retrieval_response.get(
            "results",
            [],
        ),
        context=retrieval_response.get(
            "context",
            {},
        ),
    )