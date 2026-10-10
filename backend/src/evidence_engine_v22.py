"""
Q-Care Evidence Engine V2.2

Evidence retrieval strategy:

1. Individual symptoms:
   Prefer trusted clinical/symptom resources.

2. Prevention:
   Prefer trusted health-topic resources.

3. Vaccination:
   Prefer vaccination-specific resources.

4. Population health:
   Use WHO GHO statistical data when appropriate.

5. Emergency signals:
   Do not allow missing web evidence to override
   the Safety Engine's urgent classification.

This module retrieves evidence.
It does NOT diagnose medical conditions.
"""

import re
import requests

from src.clinical_context import classify_context


REQUEST_TIMEOUT = 12


# ---------------------------------------------------------
# TRUSTED SOURCE DEFINITIONS
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# CLINICAL / SYMPTOM RESOURCES
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# WHO HEALTH TOPICS
# ---------------------------------------------------------

WHO_TOPIC_MAP = {
    "malaria": "https://www.who.int/health-topics/malaria",
    "dengue": "https://www.who.int/health-topics/dengue-and-severe-dengue",
    "measles": "https://www.who.int/health-topics/measles",
    "yellow fever": "https://www.who.int/news-room/fact-sheets/detail/yellow-fever",
    "tuberculosis": "https://www.who.int/health-topics/tuberculosis",
    "influenza": "https://www.who.int/health-topics/influenza-seasonal",
    "flu": "https://www.who.int/health-topics/influenza-seasonal",
}


# ---------------------------------------------------------
# CONCEPT GROUPS
# ---------------------------------------------------------

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


# More specific medical topics must be recognized first.
SPECIAL_TOPICS = [
    "yellow fever",
    "rheumatic fever",
]


# ---------------------------------------------------------
# TEXT NORMALIZATION
# ---------------------------------------------------------

def normalize_text(text):
    """
    Normalize text and remove obvious contact information.
    """

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


# ---------------------------------------------------------
# CONCEPT EXTRACTION
# ---------------------------------------------------------

def extract_concepts(text):
    """
    Extract health concepts.

    Specific multi-word topics are protected from
    accidental splitting into generic concepts.
    """

    normalized = normalize_text(text).lower()

    concepts = []

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


# ---------------------------------------------------------
# TOPIC EXTRACTION
# ---------------------------------------------------------

def extract_topics(text):
    """
    Extract mapped health topics.

    Longer phrases are checked before shorter phrases.
    """

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


# ---------------------------------------------------------
# RETRIEVAL QUERY
# ---------------------------------------------------------

def build_evidence_query(text):
    """
    Convert a raw user request into structured retrieval data.
    """

    cleaned = normalize_text(text)

    context = classify_context(cleaned)

    return {
        "text": cleaned,
        "context": context,
        "concepts": extract_concepts(cleaned),
        "topics": extract_topics(cleaned),
    }


# ---------------------------------------------------------
# SAFE URL FETCH
# ---------------------------------------------------------

def fetch_url(url):
    """
    Fetch a trusted public page.

    Only retrieval metadata is returned.
    Medical interpretation happens elsewhere.
    """

    try:

        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Q-Care/2.2 research retrieval client"
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


# ---------------------------------------------------------
# MEDLINEPLUS RETRIEVAL
# ---------------------------------------------------------

def retrieve_medlineplus(query_data):
    """
    Retrieve individual-symptom/clinical information
    from MedlinePlus.

    This path is intentionally separate from WHO GHO.
    """

    context = query_data["context"]["context"]

    allowed_contexts = {
        "individual_symptom",
        "emergency_signal",
        "general_health",
    }

    if context not in allowed_contexts:
        return {
            "results": [],
            "sources": [],
        }

    results = []
    sources = []

    topics_checked = set()

    for concept in query_data["concepts"]:

        topic = concept

        # Generic "eye" and "eyelid" are both mapped.
        url = MEDLINEPLUS_TOPIC_MAP.get(topic)

        if not url:
            continue

        if url in topics_checked:
            continue

        topics_checked.add(url)

        fetched = fetch_url(url)

        sources.append({
            "source": "National Library of Medicine / MedlinePlus",
            "status": fetched["status"],
            "status_code": fetched["status_code"],
        })

        if fetched["status"] == "success":

            results.append({
                "source": "National Library of Medicine / MedlinePlus",
                "title": topic.title(),
                "url": url,
                "topic": topic,
                "evidence_type": "clinical_information",
                "evidence_context": "individual",
                "retrieval_status": "success",
            })

    return {
        "results": results,
        "sources": sources,
    }


# ---------------------------------------------------------
# WHO TOPIC RETRIEVAL
# ---------------------------------------------------------

def retrieve_who_topics(query_data):
    """
    Retrieve WHO health-topic pages.

    Primarily useful for diseases, prevention and
    public-health education.
    """

    context = query_data["context"]["context"]

    allowed_contexts = {
        "prevention",
        "vaccination",
        "general_health",
    }

    if context not in allowed_contexts:
        return {
            "results": [],
            "sources": [],
        }

    results = []
    sources = []

    for topic in query_data["topics"]:

        url = WHO_TOPIC_MAP.get(topic)

        if not url:
            continue

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
                "evidence_type": "clinical_information",
                "evidence_context": "individual",
                "retrieval_status": "success",
            })

    return {
        "results": results,
        "sources": sources,
    }


# ---------------------------------------------------------
# WHO POPULATION DATA
# ---------------------------------------------------------

def retrieve_population_evidence(query_data):
    """
    Retrieve WHO GHO indicators only for population-level
    or vaccination-statistics questions.

    Individual symptom questions do not use this endpoint.
    """

    context = query_data["context"]["context"]

    if context not in {
        "population_health",
        "vaccination",
    }:

        return {
            "results": [],
            "sources": [],
        }

    concepts = query_data["concepts"]

    if not concepts:

        return {
            "results": [],
            "sources": [],
        }

    # Specific disease phrases are not converted into generic
    # symptom searches.
    statistical_concepts = [
        concept
        for concept in concepts
        if concept not in SPECIAL_TOPICS
    ]

    if not statistical_concepts:

        return {
            "results": [],
            "sources": [],
        }

    query = " ".join(statistical_concepts)

    safe_query = query.replace("'", "''")

    url = "https://ghoapi.azureedge.net/api/Indicator"

    try:

        response = requests.get(
            url,
            params={
                "$filter": f"contains(IndicatorName,'{safe_query}')",
                "$format": "json",
            },
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Q-Care/2.2 research retrieval client"
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

        for record in records[:10]:

            results.append({
                "source": "World Health Organization",
                "title": record.get(
                    "IndicatorName",
                    "WHO health indicator",
                ),
                "indicator_code": record.get(
                    "IndicatorCode"
                ),
                "evidence_type": "public_health_statistic",
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


# ---------------------------------------------------------
# MAIN V2.2 ENGINE
# ---------------------------------------------------------

def retrieve_evidence_v22(text):
    """
    Main Q-Care Evidence Engine V2.2 entry point.
    """

    query_data = build_evidence_query(text)

    medlineplus = retrieve_medlineplus(query_data)

    who_topics = retrieve_who_topics(query_data)

    population = retrieve_population_evidence(query_data)

    results = (
        medlineplus["results"]
        + who_topics["results"]
        + population["results"]
    )

    sources = (
        medlineplus["sources"]
        + who_topics["sources"]
        + population["sources"]
    )

    if results:
        status = "completed"

    elif sources:
        status = "no_relevant_evidence"

    else:
        status = "no_sources"

    return {
        "query": query_data["text"],
        "context": query_data["context"],
        "concepts": query_data["concepts"],
        "topics": query_data["topics"],
        "results": results,
        "sources": sources,
        "status": status,
    }