"""
Q-Care Evidence Engine V2.3

Intent-aware evidence retrieval.

The engine separates:

- Individual symptom questions
- Emergency signals
- Prevention questions
- Vaccination questions
- Population-health/statistical questions
- General health questions

The engine retrieves evidence only from sources appropriate
to the detected intent.

Q-Care does NOT diagnose medical conditions.
"""

import re
import requests

from src.clinical_context import classify_context


REQUEST_TIMEOUT = 12


# =========================================================
# TRUSTED SOURCES
# =========================================================

TRUSTED_SOURCES = [
    {
        "name": "World Health Organization",
        "tier": 1,
        "type": "public_health",
        "website": "https://www.who.int/",
    },
    {
        "name": "National Library of Medicine / MedlinePlus",
        "tier": 1,
        "type": "medical_information",
        "website": "https://medlineplus.gov/",
    },
    {
        "name": "Centers for Disease Control and Prevention",
        "tier": 1,
        "type": "public_health",
        "website": "https://www.cdc.gov/",
    },
]


# =========================================================
# MEDLINEPLUS CLINICAL TOPICS
# =========================================================

MEDLINEPLUS_TOPIC_MAP = {
    "fever": "https://medlineplus.gov/fever.html",
    "headache": "https://medlineplus.gov/headache.html",
    "swelling": "https://medlineplus.gov/edema.html",
    "eye": "https://medlineplus.gov/eyeliddisorders.html",
    "eyelid": "https://medlineplus.gov/eyeliddisorders.html",
    "breathing": "https://medlineplus.gov/breathingproblems.html",
    "shortness of breath": "https://medlineplus.gov/breathingproblems.html",
    "chest pain": "https://medlineplus.gov/chestpain.html",
    "vomiting": "https://medlineplus.gov/nauseaandvomiting.html",
    "abdominal pain": "https://medlineplus.gov/abdominalpain.html",
    "vision": "https://medlineplus.gov/vision.html",
}


# =========================================================
# WHO HEALTH TOPICS
# =========================================================

WHO_TOPIC_MAP = {
    "malaria": "https://www.who.int/health-topics/malaria",
    "dengue": "https://www.who.int/health-topics/dengue-and-severe-dengue",
    "measles": "https://www.who.int/health-topics/measles",
    "yellow fever": "https://www.who.int/news-room/fact-sheets/detail/yellow-fever",
    "tuberculosis": "https://www.who.int/health-topics/tuberculosis",
    "influenza": "https://www.who.int/health-topics/influenza-seasonal",
    "flu": "https://www.who.int/health-topics/influenza-seasonal",
}


# =========================================================
# CONCEPT GROUPS
# =========================================================

CONCEPT_GROUPS = {

    "fever": [
        "fever",
        "high fever",
        "temperature",
    ],

    "headache": [
        "headache",
        "head pain",
        "migraine",
    ],

    "swelling": [
        "swelling",
        "swollen",
        "puffiness",
        "puffy",
    ],

    "eye": [
        "eye",
        "eyes",
        "eyelid",
        "eyelids",
    ],

    "breathing": [
        "difficulty breathing",
        "breathing difficulty",
        "shortness of breath",
        "can't breathe",
        "cannot breathe",
    ],

    "chest pain": [
        "chest pain",
    ],

    "vomiting": [
        "vomiting",
        "vomit",
    ],

    "abdominal pain": [
        "abdominal pain",
        "stomach pain",
    ],

    "vision": [
        "vision loss",
        "blurred vision",
        "vision",
    ],
}


# =========================================================
# SPECIFIC MULTI-WORD TOPICS
# =========================================================

SPECIAL_TOPICS = [
    "yellow fever",
    "rheumatic fever",
]


# =========================================================
# POPULATION / STATISTIC INTENT
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


# =========================================================
# VACCINATION INTENT
# =========================================================

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
# INTENT HELPERS
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

    # Protect special topics first.
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

    topics = []

    all_topics = set(
        list(MEDLINEPLUS_TOPIC_MAP.keys())
        + list(WHO_TOPIC_MAP.keys())
    )

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
# QUERY ANALYSIS
# =========================================================

def build_query_profile(text):

    cleaned = normalize_text(text)

    context = classify_context(cleaned)

    return {
        "text": cleaned,
        "context": context,
        "concepts": extract_concepts(cleaned),
        "topics": extract_topics(cleaned),
        "statistic_intent": detect_statistic_intent(cleaned),
        "vaccination_intent": detect_vaccination_intent(cleaned),
    }


# =========================================================
# SAFE FETCH
# =========================================================

def fetch_url(url):

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Q-Care/2.3 research retrieval client"
            },
        )

        if response.status_code != 200:

            return {
                "status": "unavailable",
                "status_code": response.status_code,
                "url": url,
            }

        return {
            "status": "success",
            "status_code": response.status_code,
            "url": url,
        }

    except requests.Timeout:

        return {
            "status": "timeout",
            "status_code": None,
            "url": url,
        }

    except requests.RequestException:

        return {
            "status": "request_error",
            "status_code": None,
            "url": url,
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
            "source": "National Library of Medicine / MedlinePlus",
            "status": fetched["status"],
            "status_code": fetched["status_code"],
        })

        if fetched["status"] == "success":

            results.append({
                "source": "National Library of Medicine / MedlinePlus",
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
# WHO HEALTH-TOPIC RETRIEVAL
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

    for topic in profile["topics"]:

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

            results.append({
                "source": "World Health Organization",
                "title": topic.title(),
                "url": url,
                "topic": topic,
                "evidence_type": (
                    "vaccination_information"
                    if profile["vaccination_intent"]
                    else "clinical_information"
                ),
                "evidence_context": "individual",
                "retrieval_status": "success",
            })

    return {
        "results": results,
        "sources": sources,
    }


# =========================================================
# WHO POPULATION RETRIEVAL
# =========================================================

def retrieve_population_evidence(profile):

    context = profile["context"]["context"]

    # Only population/statistical questions can reach GHO.
    if context not in {
        "population_health",
        "vaccination",
    }:

        return {
            "results": [],
            "sources": [],
        }

    # Require actual statistical/vaccination intent.
    if not (
        profile["statistic_intent"]
        or profile["vaccination_intent"]
    ):

        return {
            "results": [],
            "sources": [],
        }

    concepts = profile["concepts"]

    if not concepts:

        return {
            "results": [],
            "sources": [],
        }

    # Build a search phrase while preserving specific topics.
    search_terms = []

    for concept in concepts:

        if concept in SPECIAL_TOPICS:

            search_terms.append(concept)

        else:

            search_terms.append(concept)

    query = " ".join(search_terms).strip()

    if not query:

        return {
            "results": [],
            "sources": [],
        }

    safe_query = query.replace("'", "''")

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
                "User-Agent": "Q-Care/2.3 research retrieval client"
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

        records = payload.get("value", [])

        results = []

        for record in records[:20]:

            indicator_name = record.get(
                "IndicatorName",
                "WHO health indicator",
            )

            indicator_lower = indicator_name.lower()

            # ---------------------------------------------
            # RELEVANCE FILTER
            # ---------------------------------------------

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

    except (requests.RequestException, ValueError):

        return {
            "results": [],
            "sources": [{
                "source": "World Health Organization",
                "status": "request_error",
                "status_code": None,
            }],
        }


# =========================================================
# MAIN ENGINE
# =========================================================

def retrieve_evidence_v23(text):

    profile = build_query_profile(text)

    clinical = retrieve_clinical_evidence(profile)

    health_topics = retrieve_health_topics(profile)

    population = retrieve_population_evidence(profile)

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
        "statistic_intent": profile["statistic_intent"],
        "vaccination_intent": profile["vaccination_intent"],
        "results": results,
        "sources": sources,
        "status": status,
    }