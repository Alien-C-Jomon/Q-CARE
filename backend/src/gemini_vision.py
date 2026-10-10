"""
Q-Care Gemini Vision Adapter
Version 2.0

Purpose:
- Send an image to Gemini for visual observation.
- Request structured, non-diagnostic observations.
- Convert Gemini output into Q-Care observation objects.
- Gracefully handle provider failures and quota limits.

Safety:
Gemini is used only for visual observation.
This module does NOT diagnose diseases, estimate medical severity,
or recommend treatment.
"""

import base64
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List


MODEL_NAME = "gemini-3.5-flash"


VISION_PROMPT = """
You are the visual observation component of Q-Care.

Analyze the supplied image ONLY for observable visual features.

DO NOT:
- diagnose a disease or medical condition
- identify a disease from appearance
- estimate medical severity
- recommend treatment
- tell the user whether they need a doctor

Focus only on:
- visible redness
- apparent swelling
- visible discoloration
- visible irritation
- visible lesions or marks
- apparent body region, if reasonably visible
- image quality and limitations

Return ONLY valid JSON using this exact structure:

{
  "observations": [
    {
      "feature": "short description of one visible feature",
      "confidence": 0.0
    }
  ],
  "limitations": [
    "short description of an image limitation"
  ]
}

Confidence must be a number between 0.0 and 1.0.

If a feature cannot be reliably observed, do not invent it.
If there is no relevant visual feature, return an empty observations list.

Remember:
This is visual observation only, NOT medical diagnosis.
"""


def _get_client():
    """Create a Gemini client using the local environment variable."""

    api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set."
        )

    from google import genai

    return genai.Client(api_key=api_key)


def _image_to_base64(image_path: str) -> str:
    """Read an image and convert it to base64."""

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Image file was not found: {image_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Image path is not a file: {image_path}"
        )

    return base64.b64encode(
        path.read_bytes()
    ).decode("utf-8")


def _get_mime_type(image_path: str) -> str:
    """Determine the MIME type for a supported image."""

    extension = Path(image_path).suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    if extension not in mime_types:
        raise ValueError(
            "Unsupported image format. "
            "Use JPG, JPEG, PNG, or WEBP."
        )

    return mime_types[extension]


def _extract_json(text: str) -> Dict[str, Any]:
    """
    Extract JSON from Gemini output.

    Handles:
    - plain JSON
    - JSON inside markdown code fences
    - JSON embedded inside additional text
    """

    if not text:
        return {
            "observations": [],
            "limitations": [
                "Gemini returned no visual observation."
            ],
        }

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned,
        ).strip()

    try:
        result = json.loads(cleaned)

        if isinstance(result, dict):
            return result

    except json.JSONDecodeError:
        pass

    match = re.search(
        r"\{.*\}",
        cleaned,
        flags=re.DOTALL,
    )

    if match:
        try:
            result = json.loads(match.group(0))

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError:
            pass

    return {
        "observations": [],
        "limitations": [
            "Gemini returned an unexpected response format."
        ],
        "raw_response": text,
    }


def _normalize_observations(
    data: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Convert Gemini observations into Q-Care format."""

    raw_observations = data.get(
        "observations",
        [],
    )

    if not isinstance(raw_observations, list):
        return []

    observations = []

    for item in raw_observations:

        if not isinstance(item, dict):
            continue

        feature = item.get("feature")

        if not feature:
            continue

        observation = {
            "feature": str(feature),
            "type": "visual_observation",
        }

        confidence = item.get("confidence")

        if confidence is not None:

            try:
                confidence = float(confidence)

                confidence = max(
                    0.0,
                    min(1.0, confidence),
                )

                observation["confidence"] = round(
                    confidence,
                    3,
                )

            except (TypeError, ValueError):
                pass

        observations.append(observation)

    return observations


def _classify_provider_error(exc: Exception) -> Dict[str, str]:
    """
    Convert a Gemini/API exception into a safe Q-Care error category.

    This function deliberately uses the provider error text because
    the google-genai SDK can expose different exception classes across
    SDK versions.
    """

    error_text = str(exc)
    normalized = error_text.lower()

    # Free-tier / request quota.
    if (
        "429" in normalized
        or "rate limit" in normalized
        or "too_many_requests" in normalized
        or "quota" in normalized
    ):
        return {
            "code": "rate_limited",
            "message": (
                "Gemini vision request limit reached. "
                "Image analysis is temporarily unavailable."
            ),
        }

    # Temporary provider/service failure.
    if (
        "503" in normalized
        or "service unavailable" in normalized
        or "temporarily unavailable" in normalized
        or "temporary" in normalized
    ):
        return {
            "code": "temporarily_unavailable",
            "message": (
                "Gemini vision is temporarily unavailable. "
                "Q-Care can continue without Gemini observations."
            ),
        }

    # Authentication/configuration.
    if (
        "401" in normalized
        or "403" in normalized
        or "api key" in normalized
        or "authentication" in normalized
        or "permission" in normalized
    ):
        return {
            "code": "configuration_error",
            "message": (
                "Gemini vision authentication or configuration "
                "needs attention."
            ),
        }

    # Invalid request / malformed image/provider input.
    if (
        "400" in normalized
        or "invalid_request" in normalized
        or "invalid argument" in normalized
        or "bad request" in normalized
    ):
        return {
            "code": "provider_request_error",
            "message": (
                "Gemini rejected the image analysis request."
            ),
        }

    # Generic provider/network failure.
    return {
        "code": "provider_error",
        "message": (
            "Gemini vision could not complete the image analysis."
        ),
    }


def analyze_image_with_gemini(
    image_path: str,
) -> Dict[str, Any]:
    """
    Send an image to Gemini and return structured
    non-diagnostic visual observations.

    Provider failures are returned as structured Q-Care errors
    instead of being allowed to break the application.
    """

    try:

        client = _get_client()

        image_data = _image_to_base64(
            image_path
        )

        mime_type = _get_mime_type(
            image_path
        )

        interaction = client.interactions.create(
            model=MODEL_NAME,
            input=[
                {
                    "type": "text",
                    "text": VISION_PROMPT,
                },
                {
                    "type": "image",
                    "data": image_data,
                    "mime_type": mime_type,
                },
            ],
        )

        response_text = interaction.output_text

        parsed = _extract_json(
            response_text
        )

        observations = _normalize_observations(
            parsed
        )

        limitations = parsed.get(
            "limitations",
            [],
        )

        if not isinstance(limitations, list):
            limitations = []

        # Detect a structurally invalid provider response.
        if (
            not isinstance(parsed, dict)
            or (
                not observations
                and not limitations
            )
        ):
            return {
                "status": "error",
                "provider": "google_gemini",
                "model": MODEL_NAME,
                "diagnostic": False,
                "error_code": "invalid_provider_response",
                "error_message": (
                    "Gemini returned an unexpected "
                    "visual observation response."
                ),
                "observations": [],
                "limitations": [
                    "Gemini response could not be interpreted safely."
                ],
                "raw_response": response_text,
            }

        return {
            "status": "success",
            "provider": "google_gemini",
            "model": MODEL_NAME,
            "diagnostic": False,
            "error_code": None,
            "error_message": None,
            "observations": observations,
            "limitations": [
                str(item)
                for item in limitations
            ],
            "raw_response": response_text,
        }

    except FileNotFoundError as exc:

        return {
            "status": "error",
            "provider": "google_gemini",
            "model": MODEL_NAME,
            "diagnostic": False,
            "error_code": "input_error",
            "error_message": str(exc),
            "observations": [],
            "limitations": [],
        }

    except ValueError as exc:

        return {
            "status": "error",
            "provider": "google_gemini",
            "model": MODEL_NAME,
            "diagnostic": False,
            "error_code": "input_error",
            "error_message": str(exc),
            "observations": [],
            "limitations": [],
        }

    except RuntimeError as exc:

        return {
            "status": "error",
            "provider": "google_gemini",
            "model": MODEL_NAME,
            "diagnostic": False,
            "error_code": "configuration_error",
            "error_message": str(exc),
            "observations": [],
            "limitations": [],
        }

    except Exception as exc:

        provider_error = _classify_provider_error(
            exc
        )

        return {
            "status": "error",
            "provider": "google_gemini",
            "model": MODEL_NAME,
            "diagnostic": False,
            "error_code": provider_error["code"],
            "error_message": provider_error["message"],
            "observations": [],
            "limitations": [],
        }


def gemini_to_qcare_input(
    gemini_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert Gemini output into the existing Q-Care image format.

    Gemini failures remain explicit so downstream Q-Care components
    can safely decide whether another evidence source should be used.
    """

    if not isinstance(gemini_result, dict):
        return {
            "status": "invalid_input",
            "source": "image",
            "diagnostic": False,
            "text": "",
            "observations": [],
            "limitations": [],
            "provider_available": False,
        }

    observations = gemini_result.get(
        "observations",
        [],
    )

    if not isinstance(observations, list):
        observations = []

    observation_text = ", ".join(
        item.get("feature", "")
        for item in observations
        if isinstance(item, dict)
        and item.get("feature")
    )

    status = gemini_result.get(
        "status",
        "unknown",
    )

    provider_available = status == "success"

    result = {
        "status": status,
        "source": "image",
        "provider": gemini_result.get(
            "provider",
            "google_gemini",
        ),
        "model": gemini_result.get(
            "model",
            MODEL_NAME,
        ),
        "diagnostic": False,
        "text": observation_text,
        "observations": observations,
        "limitations": gemini_result.get(
            "limitations",
            [],
        ),
        "provider_available": provider_available,
    }

    if gemini_result.get("error_code"):
        result["error_code"] = gemini_result[
            "error_code"
        ]

    if gemini_result.get("error_message"):
        result["error_message"] = gemini_result[
            "error_message"
        ]

    return result


if __name__ == "__main__":

    print("Q-Care Gemini Vision Adapter")
    print("Version: 2.0")
    print(f"Model: {MODEL_NAME}")
    print("Diagnostic mode: DISABLED")
    print("Gemini provider: READY")