"""
Q-Care Evidence Ranker V4
=========================

Ranks retrieved evidence for Q-Care.

Design goals:
    1. Exact concept matches should outrank partial/related matches.
    2. Retrieval-provided evidence metadata must be preserved.
    3. Individual symptom queries should prefer individual clinical evidence.
    4. Population/statistical evidence should not outrank clinical evidence
       for an individual symptom query.
    5. Output remains compatible with the V5 evidence gate and later stages.

Important:
    This ranker evaluates evidence relevance and quality.
    It does NOT diagnose disease or estimate disease probability.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# SOURCE QUALITY
# ---------------------------------------------------------------------------

SOURCE_TIER_WEIGHT = {
    1: 1.00,
    2: 0.85,
    3: 0.70,
}


# ---------------------------------------------------------------------------
# CONCEPT GROUPS
# ---------------------------------------------------------------------------

CONCEPT_GROUPS = {
    "fever": {
        "exact_terms": [
            "fever",
        ],
        "related_terms": [
            "febrile",
            "temperature",
            "high temperature",
        ],
    },

    "headache": {
        "exact_terms": [
            "headache",
        ],
        "related_terms": [
            "head pain",
            "migraine",
        ],
    },

    "swelling": {
        "exact_terms": [
            "swelling",
            "swollen",
        ],
        "related_terms": [
            "inflammation",
            "edema",
        ],
    },

    "eye": {
        "exact_terms": [
            "eye",
            "eyes",
            "eyelid",
            "eyelids",
        ],
        "related_terms": [
            "ocular",
            "vision",
        ],
    },

    "breathing": {
        "exact_terms": [
            "difficulty breathing",
            "trouble breathing",
            "shortness of breath",
            "breathing difficulty",
        ],
        "related_terms": [
            "respiratory",
            "breathlessness",
            "dyspnea",
        ],
    },

    "chest pain": {
        "exact_terms": [
            "chest pain",
        ],
        "related_terms": [
            "chest discomfort",
            "thoracic pain",
        ],
    },

    "vomiting": {
        "exact_terms": [
            "vomiting",
            "vomit",
        ],
        "related_terms": [
            "nausea",
            "throwing up",
        ],
    },

    "abdominal pain": {
        "exact_terms": [
            "abdominal pain",
            "stomach pain",
        ],
        "related_terms": [
            "belly pain",
            "abdominal discomfort",
        ],
    },

    "vision": {
        "exact_terms": [
            "vision",
            "visual",
            "blurred vision",
            "vision loss",
            "loss of vision",
        ],
        "related_terms": [
            "eyesight",
            "visual disturbance",
        ],
    },

    "cough": {
        "exact_terms": [
            "cough",
            "coughing",
        ],
        "related_terms": [
            "respiratory",
        ],
    },

    "sore throat": {
        "exact_terms": [
            "sore throat",
            "throat pain",
        ],
        "related_terms": [
            "pharyngitis",
        ],
    },

    "diarrhea": {
        "exact_terms": [
            "diarrhea",
            "loose stools",
        ],
        "related_terms": [
            "gastrointestinal",
        ],
    },

    "rash": {
        "exact_terms": [
            "rash",
            "skin rash",
        ],
        "related_terms": [
            "skin eruption",
        ],
    },

    "dizziness": {
        "exact_terms": [
            "dizziness",
            "dizzy",
        ],
        "related_terms": [
            "vertigo",
            "lightheadedness",
        ],
    },

    "fatigue": {
        "exact_terms": [
            "fatigue",
            "tiredness",
        ],
        "related_terms": [
            "very tired",
            "weakness",
        ],
    },
}


# ---------------------------------------------------------------------------
# EVIDENCE TYPE TERMS
# ---------------------------------------------------------------------------

EVIDENCE_TYPE_TERMS = {
    "epidemiological_data": [
        "incidence",
        "prevalence",
        "epidemiology",
        "surveillance",
        "reported cases",
        "case count",
        "population rate",
    ],

    "vaccination": [
        "vaccination",
        "vaccine",
        "vaccines",
        "immunization",
        "immunisation",
        "vaccine coverage",
    ],

    "public_health_statistic": [
        "statistics",
        "statistic",
        "coverage",
        "population",
        "rate",
        "number of cases",
        "reported cases",
        "indicator",
    ],

    "clinical_information": [
        "symptoms",
        "treatment",
        "diagnosis",
        "causes",
        "clinical",
        "patient",
        "health care provider",
        "healthcare provider",
    ],
}


# ---------------------------------------------------------------------------
# CONTEXT TERMS
# ---------------------------------------------------------------------------

CONTEXT_TERMS = {
    "population": [
        "population",
        "incidence",
        "prevalence",
        "surveillance",
        "reported cases",
        "number of cases",
        "statistics",
        "coverage",
        "rate",
        "outbreak",
    ],

    "vaccination": [
        "vaccination",
        "vaccine",
        "immunization",
        "immunisation",
        "vaccine coverage",
    ],

    "individual": [
        "symptoms",
        "treatment",
        "patient",
        "health care provider",
        "healthcare provider",
        "you have",
        "you may",
    ],
}


# ---------------------------------------------------------------------------
# TEXT HELPERS
# ---------------------------------------------------------------------------

def _normalize_text(value: Any) -> str:
    """
    Normalize text for matching.
    """

    if value is None:
        return ""

    text = str(value).lower()

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _contains_phrase(text: str, phrase: str) -> bool:
    """
    Check for a phrase using word boundaries where possible.

    This prevents a concept such as 'fever' from being treated
    as an exact title match for 'hay fever' or 'valley fever'.
    """

    phrase = _normalize_text(phrase)

    if not phrase:
        return False

    pattern = r"(?<!\w)" + re.escape(phrase) + r"(?!\w)"

    return bool(re.search(pattern, text))


def _tokenize(text: str) -> List[str]:
    """
    Basic tokenization.
    """

    return re.findall(r"\b[a-z0-9]+\b", text.lower())


# ---------------------------------------------------------------------------
# QUERY CONCEPT EXTRACTION
# ---------------------------------------------------------------------------

def extract_query_concepts(
    query: str,
) -> List[str]:
    """
    Extract concepts from the query using the known concept groups.

    This function is intentionally local to the ranker so the ranker
    remains usable with older retrieval responses.
    """

    text = _normalize_text(query)

    concepts: List[str] = []

    for concept, group in CONCEPT_GROUPS.items():

        terms = (
            group.get("exact_terms", [])
            + group.get("related_terms", [])
        )

        for term in terms:

            if _contains_phrase(text, term):
                concepts.append(concept)
                break

    return concepts


# ---------------------------------------------------------------------------
# EVIDENCE METADATA
# ---------------------------------------------------------------------------

def classify_evidence_type(
    evidence_text: str,
) -> Dict[str, Any]:
    """
    Infer evidence type from text.

    IMPORTANT:
        This function is only a fallback.

    If retrieval already supplied explicit evidence_type metadata,
    rank_retrieval_response() preserves that metadata instead.
    """

    text = _normalize_text(evidence_text)

    if not text:
        return {
            "evidence_type": "unknown",
            "matched_terms": [],
            "reason": "No evidence text was available.",
            "context": "unknown",
        }

    # Epidemiological evidence gets highest classification precedence.
    matched = [
        term
        for term in EVIDENCE_TYPE_TERMS["epidemiological_data"]
        if _contains_phrase(text, term)
    ]

    if matched:
        return {
            "evidence_type": "epidemiological_data",
            "matched_terms": matched,
            "reason": "Evidence contains epidemiological/statistical terminology.",
            "context": "population",
        }

    # Vaccination evidence.
    matched = [
        term
        for term in EVIDENCE_TYPE_TERMS["vaccination"]
        if _contains_phrase(text, term)
    ]

    if matched:
        return {
            "evidence_type": "vaccination",
            "matched_terms": matched,
            "reason": "Evidence contains vaccination/immunization terminology.",
            "context": "vaccination",
        }

    # Public-health statistics.
    matched = [
        term
        for term in EVIDENCE_TYPE_TERMS["public_health_statistic"]
        if _contains_phrase(text, term)
    ]

    if matched:
        return {
            "evidence_type": "public_health_statistic",
            "matched_terms": matched,
            "reason": "Evidence contains population/statistical terminology.",
            "context": "population",
        }

    # Clinical information.
    matched = [
        term
        for term in EVIDENCE_TYPE_TERMS["clinical_information"]
        if _contains_phrase(text, term)
    ]

    if matched:
        return {
            "evidence_type": "clinical_information",
            "matched_terms": matched,
            "reason": "Evidence contains clinical-information terminology.",
            "context": "individual",
        }

    return {
        "evidence_type": "unknown",
        "matched_terms": [],
        "reason": "No strong evidence-type terminology was detected.",
        "context": "unknown",
    }


def _get_explicit_metadata(
    evidence: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Preserve metadata supplied by the retrieval layer.

    Supported forms:

        evidence["evidence_type"]
        evidence["evidence_context"]

    and legacy nested forms:

        evidence["relevance"]["evidence_type"]
        evidence["relevance"]["context"]
    """

    relevance = evidence.get("relevance")

    if not isinstance(relevance, dict):
        relevance = {}

    explicit_type = (
        evidence.get("evidence_type")
        or relevance.get("evidence_type")
    )

    explicit_context = (
        evidence.get("evidence_context")
        or evidence.get("context")
        or relevance.get("evidence_context")
        or relevance.get("context")
    )

    return {
        "evidence_type": explicit_type,
        "evidence_context": explicit_context,
    }


# ---------------------------------------------------------------------------
# QUERY CONTEXT
# ---------------------------------------------------------------------------

def _classify_query_context(
    query: str,
) -> Dict[str, Any]:
    """
    Classify the query context.

    Priority:

        emergency
        vaccination
        population
        prevention
        individual
        general
    """

    text = _normalize_text(query)

    if not text:
        return {
            "context": "general",
            "confidence": 0.0,
            "matched_terms": [],
        }

    emergency_terms = [
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

    vaccination_terms = [
        "vaccination",
        "vaccine",
        "vaccines",
        "immunization",
        "immunisation",
        "vaccine coverage",
    ]

    population_terms = [
        "number of cases",
        "reported cases",
        "incidence",
        "prevalence",
        "population",
        "statistics",
        "statistic",
        "coverage",
        "rate",
        "outbreak",
        "surveillance",
    ]

    prevention_terms = [
        "prevent",
        "prevention",
        "how can i avoid",
        "avoid getting",
        "reduce risk",
    ]

    individual_terms = [
        "i have",
        "i'm having",
        "im having",
        "my ",
        "me ",
        "i feel",
        "i am feeling",
        "symptom",
        "symptoms",
    ]

    def matches(terms: List[str]) -> List[str]:

        return [
            term
            for term in terms
            if term in text
        ]

    matched = matches(emergency_terms)

    if matched:
        return {
            "context": "emergency",
            "confidence": 1.0,
            "matched_terms": matched,
        }

    matched = matches(vaccination_terms)

    if matched:
        return {
            "context": "vaccination",
            "confidence": 0.95,
            "matched_terms": matched,
        }

    matched = matches(population_terms)

    if matched:
        return {
            "context": "population",
            "confidence": 0.95,
            "matched_terms": matched,
        }

    matched = matches(prevention_terms)

    if matched:
        return {
            "context": "prevention",
            "confidence": 0.90,
            "matched_terms": matched,
        }

    matched = matches(individual_terms)

    if matched or extract_query_concepts(text):

        return {
            "context": "individual",
            "confidence": 0.95,
            "matched_terms": matched,
        }

    return {
        "context": "general",
        "confidence": 0.50,
        "matched_terms": [],
    }


# ---------------------------------------------------------------------------
# CONTEXT ADJUSTMENT
# ---------------------------------------------------------------------------

def calculate_context_adjustment(
    query_context: str,
    evidence_type: str,
    evidence_context: str,
) -> float:
    """
    Calculate contextual relevance adjustment.

    This is deliberately conservative.

    Individual symptom queries should prioritize individual
    clinical evidence and penalize population/statistical
    evidence.

    The function does not determine medical severity.
    """

    query_context = _normalize_text(query_context)
    evidence_type = _normalize_text(evidence_type)
    evidence_context = _normalize_text(evidence_context)

    # Individual symptom query.
    if query_context == "individual":

        if evidence_context == "individual":
            return 10.0

        if evidence_context == "population":
            return -25.0

        if evidence_type in {
            "public_health_statistic",
            "epidemiological_data",
        }:
            return -25.0

        if evidence_type == "vaccination":
            return -15.0

        if evidence_context == "vaccination":
            return -15.0

        return 0.0

    # Emergency queries still prioritize directly relevant clinical
    # evidence, while population statistics are not primary.
    if query_context == "emergency":

        if evidence_context == "individual":
            return 15.0

        if evidence_context == "population":
            return -25.0

        if evidence_type in {
            "public_health_statistic",
            "epidemiological_data",
        }:
            return -25.0

        return 0.0

    # Population queries should favor population evidence.
    if query_context == "population":

        if evidence_context == "population":
            return 15.0

        if evidence_type in {
            "public_health_statistic",
            "epidemiological_data",
        }:
            return 15.0

        if evidence_context == "individual":
            return -10.0

        return 0.0

    # Vaccination queries.
    if query_context == "vaccination":

        if evidence_type == "vaccination":
            return 15.0

        if evidence_context == "vaccination":
            return 15.0

        if evidence_context == "population":
            return 8.0

        return 0.0

    # Prevention queries can reasonably use both clinical and
    # population/public-health evidence.
    if query_context == "prevention":

        if evidence_context in {
            "individual",
            "population",
        }:
            return 5.0

        return 0.0

    return 0.0


# ---------------------------------------------------------------------------
# EXACT CONCEPT MATCHING
# ---------------------------------------------------------------------------

def _concept_match_strength(
    concept: str,
    title: str,
    topic: str,
    evidence_text: str,
) -> Dict[str, Any]:
    """
    Determine how strongly one requested concept matches evidence.

    Scores:

        1.00 = exact title/topic concept
        0.75 = exact concept phrase appears elsewhere
        0.45 = related concept
        0.00 = no meaningful match

    Crucially:

        query concept = fever
        title = Fever          -> 1.00
        title = Hay Fever      -> 0.45
        title = Valley Fever   -> 0.45

    This prevents substring matching from treating all "fever"
    compounds as the same condition.
    """

    concept = _normalize_text(concept)

    title_text = _normalize_text(title)
    topic_text = _normalize_text(topic)
    evidence_text = _normalize_text(evidence_text)

    group = CONCEPT_GROUPS.get(
        concept,
        {
            "exact_terms": [concept],
            "related_terms": [],
        },
    )

    exact_terms = group.get(
        "exact_terms",
        [concept],
    )

    related_terms = group.get(
        "related_terms",
        [],
    )

    # ---------------------------------------------------------------
    # Exact title/topic match
    # ---------------------------------------------------------------

    for term in exact_terms:

        if title_text == term or topic_text == term:
            return {
                "strength": 1.00,
                "matched_term": term,
                "match_type": "exact_title",
            }

    # ---------------------------------------------------------------
    # Exact phrase inside title/topic, but with additional words.
    #
    # Example:
    #     query = fever
    #     title = Dengue Fever
    #
    # This is NOT an exact condition match.
    # Treat it as a related/partial match.
    # ---------------------------------------------------------------

    for term in exact_terms:

        if (
            _contains_phrase(title_text, term)
            or _contains_phrase(topic_text, term)
        ):

            # If the title/topic consists of the concept plus
            # modifiers, classify it as partial rather than exact.
            title_tokens = set(_tokenize(title_text))
            concept_tokens = set(_tokenize(term))

            if title_tokens == concept_tokens:
                return {
                    "strength": 1.00,
                    "matched_term": term,
                    "match_type": "exact_title",
                }

            return {
                "strength": 0.45,
                "matched_term": term,
                "match_type": "partial_title",
            }

    # ---------------------------------------------------------------
    # Exact concept phrase elsewhere in evidence.
    # ---------------------------------------------------------------

    for term in exact_terms:

        if _contains_phrase(evidence_text, term):
            return {
                "strength": 0.75,
                "matched_term": term,
                "match_type": "exact_body_phrase",
            }

    # ---------------------------------------------------------------
    # Related concept.
    # ---------------------------------------------------------------

    for term in related_terms:

        if _contains_phrase(title_text, term) or _contains_phrase(
            topic_text,
            term,
        ):

            return {
                "strength": 0.45,
                "matched_term": term,
                "match_type": "related_title",
            }

    for term in related_terms:

        if _contains_phrase(evidence_text, term):

            return {
                "strength": 0.25,
                "matched_term": term,
                "match_type": "related_body",
            }

    return {
        "strength": 0.00,
        "matched_term": None,
        "match_type": "none",
    }


# ---------------------------------------------------------------------------
# RELEVANCE CALCULATION
# ---------------------------------------------------------------------------

def calculate_relevance(
    query: str,
    evidence_text: str,
    source_tier: int = 1,
    query_context: str | None = None,
    evidence_type: str | None = None,
    evidence_context: str | None = None,
) -> Dict[str, Any]:
    """
    Calculate a bounded 0–100 relevance score.

    The score considers:

        - exact concept matching
        - related concept matching
        - phrase overlap
        - source tier
        - evidence context
        - evidence type

    Explicit evidence metadata takes precedence over
    text-based inference.
    """

    query_text = _normalize_text(query)
    evidence_text_normalized = _normalize_text(
        evidence_text
    )

    if query_context is None:

        query_context_info = _classify_query_context(
            query_text
        )

        query_context = query_context_info[
            "context"
        ]

    else:

        query_context_info = {
            "context": query_context,
            "confidence": 1.0,
            "matched_terms": [],
        }

    if evidence_type is None or evidence_context is None:

        inferred = classify_evidence_type(
            evidence_text_normalized
        )

        if evidence_type is None:
            evidence_type = inferred[
                "evidence_type"
            ]

        if evidence_context is None:
            evidence_context = inferred[
                "context"
            ]

    evidence_type = (
        evidence_type
        or "unknown"
    )

    evidence_context = (
        evidence_context
        or "unknown"
    )

    concepts = extract_query_concepts(
        query_text
    )

    # If concept extraction cannot identify anything,
    # fall back to conservative token overlap.
    if not concepts:

        query_tokens = set(
            _tokenize(query_text)
        )

        evidence_tokens = set(
            _tokenize(evidence_text_normalized)
        )

        overlap = query_tokens.intersection(
            evidence_tokens
        )

        phrase_matches = len(overlap)

        base_score = min(
            40.0,
            float(
                phrase_matches * 10
            ),
        )

        context_adjustment = calculate_context_adjustment(
            query_context,
            evidence_type,
            evidence_context,
        )

        source_weight = SOURCE_TIER_WEIGHT.get(
            source_tier,
            0.70,
        )

        score = (
            base_score
            + context_adjustment
        ) * source_weight

        score = max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

        return {
            "score": round(score, 2),
            "matched_concepts": [],
            "matched_terms": list(overlap),
            "phrase_matches": phrase_matches,
            "specialized_penalty": 0.0,
            "context_adjustment": context_adjustment,
            "query_context": query_context,
            "evidence_type": evidence_type,
            "evidence_type_reason": (
                "Fallback token-overlap scoring."
            ),
            "context": evidence_context,
            "source_weight": source_weight,
            "reason": (
                "No predefined health concepts were detected; "
                "conservative token-overlap scoring was used."
            ),
        }

    # ---------------------------------------------------------------
    # Concept matching
    # ---------------------------------------------------------------

    concept_strengths: Dict[str, float] = {}

    matched_terms: List[str] = []
    matched_concepts: List[str] = []

    for concept in concepts:

        title = ""

        # evidence_text can contain the title when this function
        # is called directly. The richer title-aware calculation
        # happens in rank_retrieval_response().
        result = _concept_match_strength(
            concept,
            title="",
            topic="",
            evidence_text=evidence_text_normalized,
        )

        strength = result["strength"]

        if strength > 0:

            concept_strengths[
                concept
            ] = strength

            matched_concepts.append(
                concept
            )

            if result.get(
                "matched_term"
            ):
                matched_terms.append(
                    result["matched_term"]
                )

    # ---------------------------------------------------------------
    # Base score
    # ---------------------------------------------------------------

    if concept_strengths:

        strongest_match = max(
            concept_strengths.values()
        )

        coverage = (
            len(concept_strengths)
            / max(
                len(concepts),
                1,
            )
        )

        # Exact concept = high base.
        # Partial/related concept = lower base.
        base_score = (
            55.0 * strongest_match
            + 15.0 * coverage
        )

    else:

        base_score = 0.0

    # ---------------------------------------------------------------
    # Phrase overlap
    # ---------------------------------------------------------------

    query_tokens = set(
        _tokenize(query_text)
    )

    evidence_tokens = set(
        _tokenize(evidence_text_normalized)
    )

    overlap = query_tokens.intersection(
        evidence_tokens
    )

    phrase_matches = len(overlap)

    phrase_bonus = min(
        10.0,
        phrase_matches * 2.0,
    )

    # ---------------------------------------------------------------
    # Context
    # ---------------------------------------------------------------

    context_adjustment = calculate_context_adjustment(
        query_context,
        evidence_type,
        evidence_context,
    )

    # ---------------------------------------------------------------
    # Specialized mismatch penalty
    # ---------------------------------------------------------------

    specialized_penalty = 0.0

    # For an individual query, a population/statistical record
    # is explicitly penalized.
    if query_context == "individual":

        if evidence_context == "population":
            specialized_penalty = 15.0

        elif evidence_type in {
            "public_health_statistic",
            "epidemiological_data",
        }:
            specialized_penalty = 15.0

    # ---------------------------------------------------------------
    # Source quality
    # ---------------------------------------------------------------

    source_weight = SOURCE_TIER_WEIGHT.get(
        source_tier,
        0.70,
    )

    # ---------------------------------------------------------------
    # Final score
    # ---------------------------------------------------------------

    raw_score = (
        base_score
        + phrase_bonus
        + context_adjustment
        - specialized_penalty
    )

    score = raw_score * source_weight

    score = max(
        0.0,
        min(
            100.0,
            score,
        ),
    )

    return {
        "score": round(
            score,
            2,
        ),
        "matched_concepts": matched_concepts,
        "matched_terms": matched_terms,
        "phrase_matches": phrase_matches,
        "specialized_penalty": specialized_penalty,
        "context_adjustment": context_adjustment,
        "query_context": query_context,
        "evidence_type": evidence_type,
        "evidence_type_reason": (
            "Explicit retrieval metadata preserved."
            if evidence_type
            else "Evidence type inferred from text."
        ),
        "context": evidence_context,
        "source_weight": source_weight,
        "reason": (
            "Evidence was ranked using concept relevance, "
            "source tier, evidence context, and evidence type."
        ),
    }


# ---------------------------------------------------------------------------
# TITLE-AWARE RELEVANCE
# ---------------------------------------------------------------------------

def _calculate_title_aware_relevance(
    query: str,
    evidence: Dict[str, Any],
    source_tier: int,
    query_context: str,
) -> Dict[str, Any]:
    """
    Calculate relevance using structured evidence fields.

    This is the primary ranking path.

    It gives exact title/topic matches a major advantage over
    compound/related titles.
    """

    title = _normalize_text(
        evidence.get("title")
        or ""
    )

    topic = _normalize_text(
        evidence.get("topic")
        or evidence.get("indicator_name")
        or ""
    )

    summary = _normalize_text(
        evidence.get("summary")
        or evidence.get("content")
        or evidence.get("text")
        or ""
    )

    combined_text = " ".join(
        part
        for part in [
            title,
            topic,
            summary,
        ]
        if part
    )

    concepts = extract_query_concepts(
        query
    )

    explicit = _get_explicit_metadata(
        evidence
    )

    evidence_type = (
        explicit["evidence_type"]
    )

    evidence_context = (
        explicit["evidence_context"]
    )

    # Infer only missing metadata.
    inferred = classify_evidence_type(
        combined_text
    )

    if not evidence_type:
        evidence_type = inferred[
            "evidence_type"
        ]

    if not evidence_context:
        evidence_context = inferred[
            "context"
        ]

    matched_concepts = []
    matched_terms = []
    match_types = []
    strengths = []

    for concept in concepts:

        match = _concept_match_strength(
            concept,
            title=title,
            topic=topic,
            evidence_text=summary,
        )

        strength = match[
            "strength"
        ]

        if strength > 0:

            matched_concepts.append(
                concept
            )

            strengths.append(
                strength
            )

            if match.get(
                "matched_term"
            ):
                matched_terms.append(
                    match["matched_term"]
                )

            match_types.append(
                match["match_type"]
            )

    # ---------------------------------------------------------------
    # Base relevance
    # ---------------------------------------------------------------
    # For individual symptom queries, structured title/topic matches
    # are much more reliable than incidental body-text mentions.

    if strengths:

        strongest = max(
            strengths
        )

        coverage = (
            len(
                set(
                    matched_concepts
                )
            )
            / max(
                len(concepts),
                1,
            )
        )

        title_or_topic_matches = {
            "exact_title",
            "exact_topic",
            "partial_title",
            "partial_topic",
            "related_title",
            "related_topic",
        }

        has_structured_match = any(
            match_type in title_or_topic_matches
            for match_type in match_types
        )

        if (
            query_context == "individual"
            and not has_structured_match
        ):
            # Weak body-only relevance for individual symptoms.
            base_score = (
                25.0 * strongest
                + 5.0 * coverage
            )
        else:
            base_score = (
                75.0 * strongest
                + 15.0 * coverage
            )

    else:

        base_score = 0.0

    # ---------------------------------------------------------------
    # Exact title bonus
    # ---------------------------------------------------------------

    exact_title_bonus = 0.0

    if "exact_title" in match_types:

        exact_title_bonus = 8.0

    # ---------------------------------------------------------------
    # Multi-concept bonus
    # ---------------------------------------------------------------
    # For individual symptom queries, only structured title/topic matches
    # qualify for this bonus. Incidental body mentions do not.

    multi_concept_bonus = 0.0

    structured_match_types = {
        "exact_title",
        "exact_topic",
        "partial_title",
        "partial_topic",
        "related_title",
        "related_topic",
    }

    structured_concepts = {
        concept
        for concept, match_type in zip(matched_concepts, match_types)
        if match_type in structured_match_types
    }

    if len(structured_concepts) >= 2:

        multi_concept_bonus = 7.0

    # ---------------------------------------------------------------
    # Body phrase overlap
    # ---------------------------------------------------------------

    query_tokens = set(
        _tokenize(query)
    )

    evidence_tokens = set(
        _tokenize(combined_text)
    )

    overlap = query_tokens.intersection(
        evidence_tokens
    )

    phrase_matches = len(
        overlap
    )

    phrase_bonus = min(
        5.0,
        phrase_matches * 1.0,
    )

    # ---------------------------------------------------------------
    # Context adjustment
    # ---------------------------------------------------------------

    context_adjustment = calculate_context_adjustment(
        query_context,
        evidence_type,
        evidence_context,
    )

    # ---------------------------------------------------------------
    # Specialized penalty
    # ---------------------------------------------------------------

    specialized_penalty = 0.0

    if query_context in {
        "individual",
        "emergency",
    }:

        if evidence_context == "population":

            specialized_penalty = 15.0

        elif evidence_type in {
            "public_health_statistic",
            "epidemiological_data",
        }:

            specialized_penalty = 15.0

    # ---------------------------------------------------------------
    # Compound-title penalty
    # ---------------------------------------------------------------

    compound_title_penalty = 0.0

    # If a concept appears in the title but the title contains
    # additional disease/condition words, reduce its score.
    #
    # Example:
    #     Fever          -> no penalty
    #     Hay Fever      -> penalty
    #     Valley Fever   -> penalty
    #
    if (
        "partial_title"
        in match_types
    ):

        compound_title_penalty = 20.0

    # ---------------------------------------------------------------
    # Source tier
    # ---------------------------------------------------------------

    source_weight = SOURCE_TIER_WEIGHT.get(
        source_tier,
        0.70,
    )

    # ---------------------------------------------------------------
    # Final score
    # ---------------------------------------------------------------

    raw_score = (
        base_score
        + exact_title_bonus
        + multi_concept_bonus
        + phrase_bonus
        + context_adjustment
        - specialized_penalty
        - compound_title_penalty
    )

    score = raw_score * source_weight

    score = max(
        0.0,
        min(
            100.0,
            score,
        ),
    )

    # ---------------------------------------------------------------
    # Reason
    # ---------------------------------------------------------------

    if "exact_title" in match_types:

        reason = (
            "Exact requested concept matched the evidence "
            "title/topic."
        )

    elif "partial_title" in match_types:

        reason = (
            "Requested concept appears in a compound evidence "
            "title; relevance was reduced."
        )

    elif matched_concepts:

        reason = (
            "Requested concept was found in evidence content "
            "or related terminology."
        )

    else:

        reason = (
            "No strong requested-concept match was found."
        )

    return {
        "score": round(
            score,
            2,
        ),
        "matched_concepts": matched_concepts,
        "matched_terms": matched_terms,
        "match_types": match_types,
        "phrase_matches": phrase_matches,
        "exact_title_bonus": exact_title_bonus,
        "multi_concept_bonus": multi_concept_bonus,
        "compound_title_penalty": compound_title_penalty,
        "specialized_penalty": specialized_penalty,
        "context_adjustment": context_adjustment,
        "query_context": query_context,
        "evidence_type": evidence_type,
        "evidence_type_reason": (
            "Explicit retrieval metadata preserved."
            if explicit["evidence_type"]
            else inferred["reason"]
        ),
        "context": evidence_context,
        "source_weight": source_weight,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# RANK EVIDENCE
# ---------------------------------------------------------------------------

def rank_evidence(
    query: str,
    evidence_items: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Rank a list of evidence records.
    """

    query_context_info = _classify_query_context(
        query
    )

    query_context = query_context_info[
        "context"
    ]

    ranked = []

    for item in evidence_items:

        evidence = dict(
            item
        )

        source_tier = int(
            evidence.get(
                "tier",
                3,
            )
        )

        relevance = _calculate_title_aware_relevance(
            query=query,
            evidence=evidence,
            source_tier=source_tier,
            query_context=query_context,
        )

        evidence["relevance"] = relevance

        ranked.append(
            evidence
        )

    ranked.sort(
        key=lambda item: item.get(
            "relevance",
            {}
        ).get(
            "score",
            0.0,
        ),
        reverse=True,
    )

    return ranked


# ---------------------------------------------------------------------------
# RANK RETRIEVAL RESPONSE
# ---------------------------------------------------------------------------

def rank_retrieval_response(
    query: str,
    retrieval_response: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Rank a complete retrieval response.

    Expected retrieval structure:

        {
            "query": "...",
            "context": {...},
            "sources": [
                {
                    "source": "...",
                    "results": [...]
                }
            ]
        }

    The returned structure remains compatible with the existing
    Q-Care evidence gate.
    """

    query_context_info = retrieval_response.get(
        "context"
    )

    if not isinstance(
        query_context_info,
        dict,
    ):

        query_context_info = _classify_query_context(
            query
        )

    query_context = query_context_info.get(
        "context",
        "general",
    )

    context_confidence = query_context_info.get(
        "confidence",
        0.50,
    )

    flattened: List[Dict[str, Any]] = []

    # ---------------------------------------------------------------
    # Preferred source structure
    # ---------------------------------------------------------------

    sources = retrieval_response.get(
        "sources",
        [],
    )

    if isinstance(
        sources,
        list,
    ):

        for source_block in sources:

            if not isinstance(
                source_block,
                dict,
            ):
                continue

            source_name = source_block.get(
                "source"
            )

            default_tier = source_block.get(
                "tier",
                3,
            )

            source_results = source_block.get(
                "results",
                [],
            )

            if not isinstance(
                source_results,
                list,
            ):
                continue

            for result in source_results:

                if not isinstance(
                    result,
                    dict,
                ):
                    continue

                evidence = dict(
                    result
                )

                if source_name:
                    evidence[
                        "source"
                    ] = source_name

                if (
                    "tier"
                    not in evidence
                ):

                    evidence[
                        "tier"
                    ] = default_tier

                flattened.append(
                    evidence
                )

    # ---------------------------------------------------------------
    # Fallback flattened structure
    # ---------------------------------------------------------------

    if not flattened:

        raw_results = retrieval_response.get(
            "results",
            [],
        )

        if isinstance(
            raw_results,
            list,
        ):

            for result in raw_results:

                if isinstance(
                    result,
                    dict,
                ):

                    flattened.append(
                        dict(result)
                    )

    # ---------------------------------------------------------------
    # Rank
    # ---------------------------------------------------------------

    ranked_results = rank_evidence(
        query=query,
        evidence_items=flattened,
    )

    return {
        "query": query,
        "status": retrieval_response.get(
            "status",
            "completed",
        ),
        "query_context": query_context,
        "context_confidence": context_confidence,
        "context_reason": query_context_info.get(
            "reason",
            "",
        ),
        "results": ranked_results,
        "count": len(
            ranked_results
        ),
    }


# ---------------------------------------------------------------------------
# MODULE TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print(
        "Q-Care Evidence Ranker V4"
    )

    print(
        "-------------------------"
    )

    test_query = (
        "I have a fever and headache"
    )

    test_evidence = [
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "tier": 1,
            "title": "Fever",
            "topic": "Fever",
            "summary": (
                "Fever is a higher than normal "
                "body temperature."
            ),
            "evidence_type": (
                "clinical_information"
            ),
            "evidence_context": (
                "individual"
            ),
        },
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "tier": 1,
            "title": "Hay Fever",
            "topic": "Hay Fever",
            "summary": (
                "Hay fever is an allergic condition."
            ),
            "evidence_type": (
                "clinical_information"
            ),
            "evidence_context": (
                "individual"
            ),
        },
        {
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "tier": 1,
            "title": "Headache",
            "topic": "Headache",
            "summary": (
                "Headaches can have many causes."
            ),
            "evidence_type": (
                "clinical_information"
            ),
            "evidence_context": (
                "individual"
            ),
        },
    ]

    ranked = rank_evidence(
        test_query,
        test_evidence,
    )

    for index, item in enumerate(
        ranked,
        start=1,
    ):

        relevance = item.get(
            "relevance",
            {},
        )

        print(
            index,
            "|",
            item.get("title"),
            "| SCORE:",
            relevance.get("score"),
            "| MATCH:",
            relevance.get("match_types"),
            "| TYPE:",
            relevance.get("evidence_type"),
            "| CONTEXT:",
            relevance.get("context"),
        )