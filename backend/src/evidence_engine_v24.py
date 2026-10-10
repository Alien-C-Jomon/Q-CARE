"""
Q-Care Evidence Engine V2.4

Intent-aware, ambiguity-aware evidence retrieval.

V2.4 adds:

- Clinical vs population separation
- Vaccination intent detection
- Statistical intent detection
- Disease/topic specificity
- Ambiguity detection
- Clarification-required responses
- Trusted-source routing
- Emergency separation

Q-Care does NOT diagnose medical conditions.
"""

import re
import requests

from src.clinical_context import classify_context
from src.evidence_engine_v23 import (
    MEDLINEPLUS_TOPIC_MAP,
    WHO_TOPIC_MAP,
    CONCEPT_GROUPS,
    SPECIAL_TOPICS,
    TRUSTED_SOURCES,
    fetch_url,
)


REQUEST_TIMEOUT = 12


# =========================================================
# INTENT TERMS
# =========================================================

STATISTIC_TERMS = [
    "number of",
    "number",
    "reported cases",
    "reported case",
    "case count",
    "cases",
    "case",
    "incidence",
    "prevalence",
    "statistics",
    "statistic",
    "surveillance",
    "trend",
    "trends",
    "rate",
    "rates",
    "burden",
    "mortality",
    "deaths",
]


VACCINATION_TERMS = [
    "vaccine",
    "vaccination",
    "vaccinated",
    "immunization",
    "immunisation",
    "immunized",
    "immunised",
    "coverage",
]


# =========================================================
# GENERIC / NON-SPECIFIC CONCEPTS
# =========================================================

GENERIC_SYMPTOM_CONCEPTS = {
    "fever",
    "headache",
    "swelling",
    "eye",
    "breathing",
    "chest pain",
    "vomiting",
    "abdominal pain",
    "vision",
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(text):

    if not text or not isinstance(text, str):
        return ""

    text = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "[redacted-email]",
        text,
    )

    text = re.sub(
        r"\b(?:\+?\d[\d\s().-]{7,}\d)\b",
        "[redacted-phone]",
        text,
    )

    return " ".join(text.split())


# =========================================================
# TERM DETECTION
# =========================================================

def contains_any(text, terms):

    text_lower = text.lower()

    return any(
        term in text_lower
        for term in terms
    )


def detect_statistic_intent(text):

    return contains_any(
        text,
        STATISTIC_TERMS,
    )


def detect_vaccination_intent(text):

    return contains_any(
        text,
        VACCINATION_TERMS,
    )


# =========================================================
# CONCEPT EXTRACTION
# =========================================================

def extract_concepts(text):

    normalized = normalize_text(text).lower()

    concepts = []

    # Protect multi-word disease topics first.
    for topic in SPECIAL_TOPICS:

        if topic in normalized:
            concepts.append(topic)

    reduced = normalized

    for topic in SPECIAL_TOPICS:
        reduced = reduced.replace(topic, " ")

    for concept, terms in CONCEPT_GROUPS.items():

        for term in terms:

            if term in reduced:
                concepts.append(concept)
                break

    return sorted(set(concepts))


# =========================================================
# TOPIC EXTRACTION
# =========================================================

def extract_topics(text):

    normalized = normalize_text(text).lower()

    all_topics = set(
        list(MEDLINEPLUS_TOPIC_MAP.keys())
        + list(WHO_TOPIC_MAP.keys())
    )

    topics = []

    for topic in sorted(
        all_topics,
        key=len,
        reverse=True,
    ):

        if topic in normalized:
            topics.append(topic)

    return sorted(
        set(topics),
        key=len,
        reverse=True,
    )


# =========================================================
# SPECIFIC DISEASE DETECTION
# =========================================================

def extract_specific_topics(text):

    """
    Identify named diseases/topics.

    Generic symptoms such as 'fever' are NOT considered
    specific diseases.
    """

    normalized = normalize_text(text).lower()

    specific_topics = []

    # WHO topics
    for topic in WHO_TOPIC_MAP:

        if topic in normalized:
            specific_topics.append(topic)

    # Explicit special topics
    for topic in SPECIAL_TOPICS:

        if topic in normalized:
            specific_topics.append(topic)

    return sorted(
        set(specific_topics),
        key=len,
        reverse=True,
    )


# =========================================================
# AMBIGUITY DETECTION
# =========================================================

def detect_ambiguity(
    text,
    context,
    concepts,
    specific_topics,
    statistic_intent,
    vaccination_intent,
):

    context_name = context["context"]

    # -----------------------------------------------------
    # Population statistics
    # -----------------------------------------------------

    if context_name == "population_health":

        if statistic_intent:

            if not specific_topics:

                symptom_concepts = [
                    concept
                    for concept in concepts
                    if concept in GENERIC_SYMPTOM_CONCEPTS
                ]

                if symptom_concepts:

                    return {
                        "ambiguous": True,
                        "type": "unspecified_population_topic",
                        "reason": (
                            "A population-level statistic was requested "
                            "but no specific disease or health condition "
                            "was identified."
                        ),
                        "message": (
                            "Which disease or health condition do you "
                            "mean? Q-Care will not assume a specific "
                            "condition from a generic symptom."
                        ),
                    }

    # -----------------------------------------------------
    # Vaccination
    # -----------------------------------------------------

    if context_name == "vaccination":

        if vaccination_intent:

            if not specific_topics:

                return {
                    "ambiguous": True,
                    "type": "unspecified_vaccination_topic",
                    "reason": (
                        "Vaccination information was requested "
                        "without identifying a specific disease "
                        "or vaccine."
                    ),
                    "message": (
                        "Which disease or vaccine do you mean? "
                        "Q-Care will not assume a specific vaccine."
                    ),
                }

    # -----------------------------------------------------
    # Otherwise clear enough
    # -----------------------------------------------------

    return {
        "ambiguous": False,
        "type": None,
        "reason": None,
        "message": None,
    }


# =========================================================
# QUERY PROFILE
# =========================================================

def build_query_profile(text):

    cleaned = normalize_text(text)

    context = classify_context(cleaned)

    concepts = extract_concepts(cleaned)

    topics = extract_topics(cleaned)

    specific_topics = extract_specific_topics(cleaned)

    statistic_intent = detect_statistic_intent(cleaned)

    vaccination_intent = detect_vaccination_intent(cleaned)

    ambiguity = detect_ambiguity(
        text=cleaned,
        context=context,
        concepts=concepts,
        specific_topics=specific_topics,
        statistic_intent=statistic_intent,
        vaccination_intent=vaccination_intent,
    )

    return {
        "text": cleaned,
        "context": context,
        "concepts": concepts,
        "topics": topics,
        "specific_topics": specific_topics,
        "statistic_intent": statistic_intent,
        "vaccination_intent": vaccination_intent,
        "ambiguity": ambiguity,
    }


# =========================================================
# CLINICAL RETRIEVAL
# =========================================================

def retrieve_clinical_evidence(profile):

    context = profile["context"]["context"]

    if context not in {
        "individual_symptom",
        "emergency_signal",
        "general_health",
    }:

        return {
            "results": [],
            "sources": [],
        }

    results = []
    sources = []

    checked_urls = set()

    for concept in profile["concepts"]:

        url = MEDLINEPLUS_TOPIC_MAP.get(concept)

        if not url:
            continue

        if url in checked_urls:
            continue

        checked_urls.add(url)

        fetched = fetch_url(url)

        sources.append({
            "source": (
                "National Library of Medicine / MedlinePlus"
            ),
            "status": fetched["status"],
            "status_code": fetched["status_code"],
        })

        if fetched["status"] == "success":

            results.append({
                "source": (
                    "National Library of Medicine / MedlinePlus"
                ),
                "title": concept.title(),
                "url": url,
                "topic": concept,
                "evidence_type": "clinical_information",
                "evidence_context": "individual",
                "retrieval_status": "success",
            })

    return {
        "results": results,
        "sources": sources,
    }


# =========================================================
# WHO HEALTH TOPICS
# =========================================================

def retrieve_health_topics(profile):

    context = profile["context"]["context"]

    if context not in {
        "prevention",
        "vaccination",
        "general_health",
    }:

        return {
            "results": [],
            "sources": [],
        }

    results = []
    sources = []

    checked_urls = set()

    # Only retrieve named WHO topics.
    for topic in profile["specific_topics"]:

        url = WHO_TOPIC_MAP.get(topic)

        if not url:
            continue

        if url in checked_urls:
            continue

        checked_urls.add(url)

        fetched = fetch_url(url)

        sources.append({
            "source": "World Health Organization",
            "status": fetched["status"],
            "status_code": fetched["status_code"],
        })

        if fetched["status"] == "success":

            evidence_type = (
                "vaccination_information"
                if profile["vaccination_intent"]
                else "clinical_information"
            )

            results.append({
                "source": "World Health Organization",
                "title": topic.title(),
                "url": url,
                "topic": topic,
                "evidence_type": evidence_type,
                "evidence_context": "individual",
                "retrieval_status": "success",
            })

    return {
        "results": results,
        "sources": sources,
    }


# =========================================================
# WHO GHO POPULATION RETRIEVAL
# =========================================================

def retrieve_population_evidence(profile):

    context_name = profile["context"]["context"]

    if context_name not in {
        "population_health",
        "vaccination",
    }:

        return {
            "results": [],
            "sources": [],
        }

    # -----------------------------------------------------
    # Do not retrieve anything when ambiguity exists.
    # -----------------------------------------------------

    if profile["ambiguity"]["ambiguous"]:

        return {
            "results": [],
            "sources": [],
        }

    if not (
        profile["statistic_intent"]
        or profile["vaccination_intent"]
    ):

        return {
            "results": [],
            "sources": [],
        }

    specific_topics = profile["specific_topics"]

    concepts = profile["concepts"]

    # -----------------------------------------------------
    # Build query
    # -----------------------------------------------------

    if specific_topics:

        query = " ".join(
            specific_topics
        )

    else:

        query = " ".join(
            concepts
        )

    if not query:

        return {
            "results": [],
            "sources": [],
        }

    safe_query = query.replace(
        "'",
        "''",
    )

    url = "https://ghoapi.azureedge.net/api/Indicator"

    try:

        response = requests.get(
            url,
            params={
                "$filter": (
                    "contains("
                    f"IndicatorName,'{safe_query}'"
                    ")"
                ),
                "$format": "json",
            },
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Q-Care/2.4 research retrieval client"
            },
        )

        if response.status_code != 200:

            return {
                "results": [],
                "sources": [{
                    "source": "World Health Organization",
                    "status": "unavailable",
                    "status_code": response.status_code,
                }],
            }

        payload = response.json()

        records = payload.get(
            "value",
            [],
        )

        results = []

        for record in records[:50]:

            indicator_name = record.get(
                "IndicatorName",
                "WHO health indicator",
            )

            indicator_lower = indicator_name.lower()

            # -------------------------------------------------
            # Vaccination filtering
            # -------------------------------------------------

            if profile["vaccination_intent"]:

                vaccination_match = any(
                    term in indicator_lower
                    for term in [
                        "vaccine",
                        "vaccination",
                        "immunization",
                        "immunisation",
                        "coverage",
                    ]
                )

                if not vaccination_match:
                    continue

            # -------------------------------------------------
            # Statistical filtering
            # -------------------------------------------------

            elif profile["statistic_intent"]:

                statistic_match = any(
                    term in indicator_lower
                    for term in [
                        "number",
                        "reported",
                        "cases",
                        "incidence",
                        "prevalence",
                        "mortality",
                        "deaths",
                        "surveillance",
                        "rate",
                        "burden",
                    ]
                )

                if not statistic_match:
                    continue

            results.append({
                "source": "World Health Organization",
                "title": indicator_name,
                "indicator_code": record.get(
                    "IndicatorCode"
                ),
                "evidence_type": (
                    "vaccination_information"
                    if profile["vaccination_intent"]
                    else "public_health_statistic"
                ),
                "evidence_context": "population",
                "topic": query,
                "retrieval_status": "success",
            })

        return {
            "results": results,
            "sources": [{
                "source": "World Health Organization",
                "status": "success",
                "status_code": response.status_code,
            }],
        }

    except requests.Timeout:

        return {
            "results": [],
            "sources": [{
                "source": "World Health Organization",
                "status": "timeout",
                "status_code": None,
            }],
        }

    except (
        requests.RequestException,
        ValueError,
    ):

        return {
            "results": [],
            "sources": [{
                "source": "World Health Organization",
                "status": "request_error",
                "status_code": None,
            }],
        }


# =========================================================
# MAIN V2.4 ENGINE
# =========================================================

def retrieve_evidence_v24(text):

    profile = build_query_profile(text)

    # -----------------------------------------------------
    # Ambiguity is handled before retrieval.
    # -----------------------------------------------------

    if profile["ambiguity"]["ambiguous"]:

        return {
            "query": profile["text"],
            "context": profile["context"],
            "concepts": profile["concepts"],
            "topics": profile["topics"],
            "specific_topics": profile["specific_topics"],
            "statistic_intent": profile["statistic_intent"],
            "vaccination_intent": profile["vaccination_intent"],
            "ambiguity": profile["ambiguity"],
            "results": [],
            "sources": [],
            "status": "clarification_required",
        }

    clinical = retrieve_clinical_evidence(
        profile
    )

    health_topics = retrieve_health_topics(
        profile
    )

    population = retrieve_population_evidence(
        profile
    )

    results = (
        clinical["results"]
        + health_topics["results"]
        + population["results"]
    )

    sources = (
        clinical["sources"]
        + health_topics["sources"]
        + population["sources"]
    )

    if results:

        status = "completed"

    elif sources:

        status = "no_relevant_evidence"

    else:

        status = "no_sources"

    return {
        "query": profile["text"],
        "context": profile["context"],
        "concepts": profile["concepts"],
        "topics": profile["topics"],
        "specific_topics": profile["specific_topics"],
        "statistic_intent": profile["statistic_intent"],
        "vaccination_intent": profile["vaccination_intent"],
        "ambiguity": profile["ambiguity"],
        "results": results,
        "sources": sources,
        "status": status,
    }