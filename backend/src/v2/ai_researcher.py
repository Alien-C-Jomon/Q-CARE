import os
import json

from google import genai
from google.genai import types


MODEL = os.getenv("QCARE_AI_MODEL", "gemini-3.5-flash-lite")


def _client():
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("Gemini API key is not configured.")
    return genai.Client(api_key=key)


def research_user_question(user_text, conversation=None):
    """
    Ask Gemini to dynamically understand the user's request and
    investigate current information using Google Search grounding.

    This is a research stage. It does NOT produce the final
    medical conclusion.
    """

    conversation = conversation or []

    system = """
You are the Q-CARE V2 research agent.

Your job is to investigate the user's health question, not to
give a diagnosis.

FIRST understand what the user is actually asking.
THEN determine what information is needed.
THEN use Google Search when current or external information
would improve the answer.

Prioritize authoritative medical/public-health information,
especially WHO, MedlinePlus/NLM, CDC, government health agencies,
and reputable medical institutions.

Search dynamically. Do not rely on a fixed list of symptoms.

Return JSON with:
{
  "intent": "...",
  "key_concepts": [],
  "questions_to_resolve": [],
  "search_focus": [],
  "candidate_claims": [],
  "sources": []
}

Do not diagnose.
Do not assign an emergency score.
"""

    prompt = system + "\nUSER QUESTION:\n" + user_text

    if conversation:
        prompt += "\nRECENT CONVERSATION:\n" + json.dumps(conversation[-10:], ensure_ascii=False)


    client = _client()

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            tools=[
                types.Tool(
                    google_search=types.GoogleSearch()
                )
            ],
        ),
    )

    try:
        data = json.loads(response.text)
    except Exception:
        data = {
            "intent": "general_health_question",
            "key_concepts": [],
            "questions_to_resolve": [],
            "search_focus": [],
            "candidate_claims": [],
            "sources": [],
            "raw_research": response.text,
        }

    return {
        "status": "success",
        "model": MODEL,
        "research": data,
        "raw_text": response.text,
    }
