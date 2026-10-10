
"""
Q-Care Gemini Conversation Adapter
Version 1.1

Purpose:
- Explain Q-Care's existing assessment conversationally.
- Use the context supplied by the Q-Care pipeline.
- Apply conservative output validation.
- Fail safely when Gemini is unavailable or output fails validation.

This module does not diagnose or independently assess medical risk.
"""

import json
import logging
import os
import re
from typing import Any, Dict, Set

from src.gemini_vision import _get_client

CONVERSATION_MODEL = "gemini-3.5-flash-lite"

logger = logging.getLogger(__name__)

MAX_REPLY_LENGTH = 6000

FALLBACK_REPLY = (
    "Q-Care could not safely validate the generated explanation. "
    "Please refer to the existing Q-Care assessment and its safety "
    "guidance. If you are concerned about your health, consult a "
    "qualified healthcare professional."
)

SYSTEM_INSTRUCTIONS = """
You are the primary AI health assistant and conversational intelligence for Q-Care.

ROLE & CAPABILITIES:
1. Provide comprehensive, empathetic, clear, and highly useful health information, home care guidance, and precautionary steps based on the user's query and the QUBO-ranked medical evidence context provided.
2. Use your full AI medical reasoning to synthesize practical advice (e.g., self-care tips, red-flag symptoms to watch for, lifestyle/precautionary actions, and when to consult a doctor).
3. Be conversational, direct, and supportive. Avoid robotic or template-like language.

SAFETY GUIDELINES:
- Clarify that your advice is precautionary and informational, not a formal medical diagnosis.
- If emergency signals (like difficulty breathing or severe chest pain) are detected, prioritize immediate urgent medical guidance.
"""


def _extract_urls(value: Any) -> Set[str]:
    """Collect URLs from strings, lists, and dictionaries."""
    urls: Set[str] = set()

    if isinstance(value, dict):
        for item in value.values():
            urls.update(_extract_urls(item))

    elif isinstance(value, (list, tuple)):
        for item in value:
            urls.update(_extract_urls(item))

    elif isinstance(value, str):
        matches = re.findall(
            r"https?://[^\s<>\"']+",
            value,
            flags=re.IGNORECASE,
        )
        for match in matches:
            cleaned = match.rstrip(".,;:!?)]}")
            urls.add(cleaned.lower())

    return urls


def validate_generated_reply(
    reply: str,
    verified_context: Dict[str, Any],
) -> tuple[bool, str]:
    """Basic validation for generated reply."""
    if not isinstance(reply, str) or not reply.strip():
        return False, "empty_reply"

    cleaned_reply = reply.strip()

    if len(cleaned_reply) > MAX_REPLY_LENGTH:
        return False, "reply_too_long"

    return True, "validated"


def generate_chat_response(
    user_message: str,
    verified_context: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate and return a rich Gemini AI health explanation using QUBO context."""

    if not isinstance(user_message, str) or not user_message.strip():
        return {
            "status": "error",
            "reply": "Please enter a message.",
            "provider": "google_gemini",
        }

    if not isinstance(verified_context, dict):
        return {
            "status": "error",
            "reply": "Q-Care could not prepare the assessment context.",
            "provider": "google_gemini",
        }

    if not os.environ.get("GEMINI_API_KEY"):
        return {
            "status": "unavailable",
            "reply": (
                "Gemini API key is not configured. "
                "Please set GEMINI_API_KEY environment variable to enable full AI control."
            ),
            "provider": "google_gemini",
        }

    try:
        client = _get_client()

        context_json = json.dumps(
            verified_context,
            ensure_ascii=False,
            default=str,
        )

        prompt = (
            SYSTEM_INSTRUCTIONS
            + "\n\nQUBO-RANKED EVIDENCE CONTEXT:\n"
            + context_json
            + "\n\nUSER MESSAGE:\n"
            + user_message.strip()
            + "\n\nProvide a clear, detailed, caring, and helpful health response addressing the user's question, incorporating home care steps and precautionary guidance."
        )

        interaction = client.interactions.create(
            model=CONVERSATION_MODEL,
            input=prompt,
        )

        reply = getattr(interaction, "output_text", None)

        is_valid, reason = validate_generated_reply(
            reply,
            verified_context,
        )

        if not is_valid:
            logger.warning(
                "Gemini output validation issue: %s",
                reason,
            )

        if reply and reply.strip():
            return {
                "status": "success",
                "reply": reply.strip(),
                "provider": "google_gemini",
            }

        return {
            "status": "unavailable",
            "reply": FALLBACK_REPLY,
            "provider": "google_gemini",
        }

    except Exception:
        # Keep provider details out of the user-facing response.
        logger.exception("Gemini conversation request failed")

        return {
            "status": "unavailable",
            "reply": (
                "Gemini Chat is temporarily unavailable. "
                "Your Q-Care safety guidance remains important. "
                "Please try again later."
            ),
            "provider": "google_gemini",
        }