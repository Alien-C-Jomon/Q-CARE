"""
Q-Care Evidence Ranking Engine v3.2

Ranks retrieved evidence using:
- health concept matching
- phrase matching
- evidence-type classification
- individual-vs-population context
- source-tier weighting
- specialized-context detection

IMPORTANT:
This is a retrieval-relevance score.

It is NOT:
- a diagnosis
- disease probability
- medical severity
- emergency probability
"""

import re


SOURCE_TIER_WEIGHT = {
    1: 1.00,
    2: 0.85,
    3: 0.70,
}


CONCEPT_GROUPS = {
    "fever": {
        "fever",
        "high fever",
        "temperature",
    },

    "headache": {
        "headache",
        "head pain",
        "migraine",
    },

    "swelling": {
        "swelling",
        "swollen",
        "puffiness",
        "puffy",
    },

    "eye": {
        "eye",
        "eyes",
        "eyelid",
        "eyelids",
    },

    "breathing": {
        "difficulty breathing",
        "breathing difficulty",
        "shortness of breath",
        "can't breathe",
        "cannot breathe",
    },

    "chest pain": {
        "chest pain",
    },

    "vomiting": {
        "vomiting",
        "vomit",
    },

    "abdominal pain": {
        "abdominal pain",
        "stomach pain",
        "belly pain",
    },

    "vision": {
        "vision loss",
        "blurred vision",
        "blurred eyesight",
    },
}


SPECIALIZED_TERMS = {
    "coverage",
    "vaccination",
    "immunization",
    "reported cases",
    "reported case",
    "number of cases",
    "case count",
    "incidence",
    "prevalence",
    "register",
    "surveillance",
    "health facilities",
    "public sector",
    "prophylaxis",
}


VACCINATION_TERMS = {
    "vaccination",
    "vaccine",
    "immunization",
    "immunisation",
}


EPIDEMIOLOGICAL_TERMS = {
    "reported",
    "cases",
    "case",
    "number of cases",
    "case count",
    "incidence",
    "prevalence",
    "surveillance",
    "epidemiology",
    "mortality",
    "morbidity",
    "outbreak",
}


PUBLIC_HEALTH_TERMS = {
    "coverage",
    "health facilities",
    "health facility",
    "public sector",
    "statistics",
    "statistic",
    "indicator",
    "percentage",
    "percent",
    "proportion",
    "aged under",
    "aged over",
    "among",
    "population",
    "households",
}


CLINICAL_TERMS = {
    "symptoms",
    "symptom",
    "signs",
    "sign",
    "diagnosis",
    "diagnostic",
    "clinical",
    "patient",
    "patients",
    "condition",
    "medical",
    "swollen",
    "swelling",
    "headache",
    "fever",
    "vomiting",
    "pain",
    "breathing",
    "shortness",
    "vision",
}


INDIVIDUAL_CONTEXT_TERMS = {
    "patient",
    "patients",
    "person",
    "individual",
    "you",
    "your",
    "symptom",
    "symptoms",
    "sign",
    "signs",
    "diagnosis",
    "clinical",
    "medical advice",
    "medical information",
}


POPULATION_CONTEXT_TERMS = {
    "children",
    "child",
    "adults",
    "adult",
    "population",
    "people",
    "households",
    "aged",
    "among",
    "community",
    "public",
    "health facilities",
    "public sector",
}


def normalize_text(text):
    """Normalize text while preserving useful words and phrases."""

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


def extract_terms(text):
    """Extract useful individual terms."""

    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "but",
        "by",
        "do",
        "for",
        "from",
        "has",
        "have",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "of",
        "on",
        "or",
        "the",
        "this",
        "to",
        "with",
    }

    normalized = normalize_text(text)

    return [
        term
        for term in normalized.split()
        if term not in stop_words
        and len(term) > 1
    ]


def detect_concepts(text):
    """Detect known health concepts."""

    normalized = normalize_text(text)

    concepts = []

    for concept, phrases in CONCEPT_GROUPS.items():

        for phrase in phrases:

            phrase_normalized = normalize_text(
                phrase
            )

            if phrase_normalized in normalized:
                concepts.append(concept)
                break

    return concepts


def find_phrase_matches(text, phrases):
    """Find normalized phrase matches."""

    normalized = normalize_text(text)

    matches = []

    for phrase in phrases:

        normalized_phrase = normalize_text(
            phrase
        )

        if normalized_phrase in normalized:
            matches.append(phrase)

    return matches


def classify_evidence_type(evidence_text):
    """
    Classify evidence using contextual precedence.

    Population/public-health context is evaluated before
    clinical keywords so that phrases such as:

        "fever cases"
        "fever coverage"
        "children with fever"

    are not incorrectly treated as individual clinical evidence.
    """

    normalized = normalize_text(
        evidence_text
    )

    if not normalized:
        return {
            "type": "unknown",
            "matched_terms": [],
            "reason": (
                "No evidence text was available."
            ),
            "context": "unknown",
        }

    vaccination_matches = find_phrase_matches(
        normalized,
        VACCINATION_TERMS,
    )

    epidemiological_matches = (
        find_phrase_matches(
            normalized,
            EPIDEMIOLOGICAL_TERMS,
        )
    )

    public_health_matches = (
        find_phrase_matches(
            normalized,
            PUBLIC_HEALTH_TERMS,
        )
    )

    individual_matches = (
        find_phrase_matches(
            normalized,
            INDIVIDUAL_CONTEXT_TERMS,
        )
    )

    population_matches = (
        find_phrase_matches(
            normalized,
            POPULATION_CONTEXT_TERMS,
        )
    )

    clinical_matches = find_phrase_matches(
        normalized,
        CLINICAL_TERMS,
    )

    # --------------------------------------------------
    # 1. Epidemiological context
    # --------------------------------------------------

    if epidemiological_matches:

        return {
            "type": "epidemiological_data",
            "matched_terms": (
                epidemiological_matches
            ),
            "reason": (
                "The evidence describes "
                "population-level case, incidence, "
                "prevalence, surveillance, or "
                "outbreak information."
            ),
            "context": "population",
        }

    # --------------------------------------------------
    # 2. Vaccination context
    # --------------------------------------------------

    if vaccination_matches:

        return {
            "type": "vaccination_information",
            "matched_terms": (
                vaccination_matches
            ),
            "reason": (
                "The evidence describes "
                "vaccination, vaccine, or "
                "immunization information."
            ),
            "context": (
                "population"
                if population_matches
                else "general"
            ),
        }

    # --------------------------------------------------
    # 3. Public-health/statistical context
    # --------------------------------------------------

    population_indicator = (
        bool(population_matches)
        or bool(public_health_matches)
    )

    if population_indicator:

        combined_matches = list(
            dict.fromkeys(
                population_matches
                + public_health_matches
            )
        )

        return {
            "type": "public_health_statistic",
            "matched_terms": combined_matches,
            "reason": (
                "The evidence describes "
                "population-level, facility-level, "
                "coverage, indicator, or statistical "
                "information rather than an "
                "individual clinical presentation."
            ),
            "context": "population",
        }

    # --------------------------------------------------
    # 4. Individual clinical context
    # --------------------------------------------------

    if individual_matches:

        combined_matches = list(
            dict.fromkeys(
                individual_matches
                + clinical_matches
            )
        )

        return {
            "type": "clinical_information",
            "matched_terms": combined_matches,
            "reason": (
                "The evidence contains indicators "
                "of individual clinical or "
                "patient-focused information."
            ),
            "context": "individual",
        }

    # --------------------------------------------------
    # 5. Direct symptom-style clinical evidence
    # --------------------------------------------------

    direct_symptom_terms = {
        "swelling",
        "swollen",
        "headache",
        "pain",
        "breathing",
        "shortness",
        "vomiting",
        "vision",
        "fever",
    }

    direct_matches = [
        term
        for term in clinical_matches
        if term in direct_symptom_terms
    ]

    if direct_matches:

        return {
            "type": "clinical_information",
            "matched_terms": direct_matches,
            "reason": (
                "The evidence directly describes "
                "a health symptom or clinical "
                "presentation without population-level "
                "indicators."
            ),
            "context": "individual",
        }

    return {
        "type": "unknown",
        "matched_terms": [],
        "reason": (
            "No recognized evidence-type "
            "or context indicators were found."
        ),
        "context": "unknown",
    }


def calculate_relevance(
    query,
    evidence_text,
    source_tier=1,
):
    """
    Calculate concept-aware retrieval relevance.

    Score is bounded from 0 to 100.

    This score represents retrieval relevance only.
    """

    query_normalized = normalize_text(
        query
    )

    evidence_normalized = normalize_text(
        evidence_text
    )

    source_weight = SOURCE_TIER_WEIGHT.get(
        source_tier,
        0.5,
    )

    if (
        not query_normalized
        or not evidence_normalized
    ):
        return {
            "score": 0.0,
            "matched_concepts": [],
            "matched_terms": [],
            "phrase_matches": [],
            "specialized_penalty": 0.0,
            "evidence_type": "unknown",
            "evidence_type_reason": (
                "Insufficient text."
            ),
            "context": "unknown",
            "source_weight": source_weight,
            "reason": (
                "Insufficient text for "
                "relevance matching."
            ),
        }

    query_concepts = detect_concepts(
        query_normalized
    )

    evidence_concepts = detect_concepts(
        evidence_normalized
    )

    matched_concepts = [
        concept
        for concept in query_concepts
        if concept in evidence_concepts
    ]

    if query_concepts:
        concept_ratio = (
            len(matched_concepts)
            / len(query_concepts)
        )
    else:
        concept_ratio = 0.0

    query_terms = extract_terms(
        query_normalized
    )

    evidence_terms = set(
        extract_terms(
            evidence_normalized
        )
    )

    matched_terms = [
        term
        for term in query_terms
        if term in evidence_terms
    ]

    if query_terms:
        term_ratio = (
            len(matched_terms)
            / len(query_terms)
        )
    else:
        term_ratio = 0.0

    phrase_matches = []

    for concept in query_concepts:

        phrases = CONCEPT_GROUPS.get(
            concept,
            set(),
        )

        for phrase in phrases:

            phrase_normalized = normalize_text(
                phrase
            )

            if (
                len(
                    phrase_normalized.split()
                ) > 1
                and phrase_normalized
                in evidence_normalized
                and phrase_normalized
                in query_normalized
            ):
                phrase_matches.append(
                    phrase
                )

    evidence_type_result = (
        classify_evidence_type(
            evidence_normalized
        )
    )

    evidence_type = (
        evidence_type_result["type"]
    )

    base_score = (
        concept_ratio * 65
        + term_ratio * 25
        + min(
            len(phrase_matches) * 10,
            10,
        )
    )

    specialized_matches = [
        term
        for term in SPECIALIZED_TERMS
        if normalize_text(term)
        in evidence_normalized
    ]

    specialized_penalty = 0.0

    if (
        specialized_matches
        and matched_concepts
    ):
        specialized_penalty = min(
            len(specialized_matches) * 8,
            24,
        )

    evidence_type_adjustment = {
        "clinical_information": 8.0,
        "unknown": 0.0,
        "public_health_statistic": -8.0,
        "epidemiological_data": -8.0,
        "vaccination_information": -10.0,
    }

    type_adjustment = (
        evidence_type_adjustment.get(
            evidence_type,
            0.0,
        )
    )

    score_before_source = (
        base_score
        - specialized_penalty
        + type_adjustment
    )

    score_before_source = max(
        0.0,
        score_before_source,
    )

    score = (
        score_before_source
        * source_weight
    )

    score = round(
        min(
            max(score, 0.0),
            100.0,
        ),
        2,
    )

    if score >= 70:
        reason = (
            "High concept-level relevance "
            "to the query."
        )

    elif score >= 40:
        reason = (
            "Moderate concept-level relevance "
            "to the query."
        )

    elif score > 0:
        reason = (
            "Low concept-level relevance "
            "to the query."
        )

    else:
        reason = (
            "No meaningful concept-level "
            "relevance detected."
        )

    if specialized_penalty > 0:
        reason += (
            " Specialized public-health "
            "indicators reduced the relevance."
        )

    if type_adjustment > 0:
        reason += (
            " Direct clinical context "
            "increased relevance."
        )

    elif type_adjustment < 0:
        reason += (
            " Population-level evidence "
            "was down-weighted for individual "
            "symptom context."
        )

    return {
        "score": score,
        "matched_concepts": matched_concepts,
        "matched_terms": matched_terms,
        "phrase_matches": phrase_matches,
        "specialized_penalty": specialized_penalty,
        "evidence_type": evidence_type,
        "evidence_type_reason": (
            evidence_type_result["reason"]
        ),
        "context": (
            evidence_type_result["context"]
        ),
        "source_weight": source_weight,
        "reason": reason,
    }


def rank_evidence(
    query,
    evidence_items,
):
    """Rank evidence from highest to lowest relevance."""

    ranked = []

    for item in evidence_items:

        if not isinstance(item, dict):
            continue

        evidence_text = (
            item.get("indicator_name")
            or item.get("title")
            or item.get("text")
            or item.get("content")
            or ""
        )

        source_tier = item.get(
            "tier",
            1,
        )

        relevance = calculate_relevance(
            query=query,
            evidence_text=evidence_text,
            source_tier=source_tier,
        )

        ranked_item = dict(item)

        ranked_item["relevance"] = (
            relevance
        )

        ranked.append(ranked_item)

    ranked.sort(
        key=lambda item:
            item["relevance"]["score"],
        reverse=True,
    )

    return ranked


def rank_retrieval_response(
    query,
    retrieval_response,
):
    """Rank evidence contained in a retrieval response."""

    if not isinstance(
        retrieval_response,
        dict,
    ):
        return {
            "query": query,
            "status": "invalid_input",
            "results": [],
            "count": 0,
        }

    evidence_items = []

    for source in retrieval_response.get(
        "sources",
        [],
    ):

        source_name = source.get(
            "source",
            "Unknown source",
        )

        source_tier = source.get(
            "tier",
            1,
        )

        for result in source.get(
            "results",
            [],
        ):

            if not isinstance(
                result,
                dict,
            ):
                continue

            item = dict(result)

            item["source"] = source_name
            item["tier"] = source_tier

            evidence_items.append(item)

    ranked = rank_evidence(
        query,
        evidence_items,
    )

    return {
        "query": query,
        "status": "completed",
        "results": ranked,
        "count": len(ranked),
    }