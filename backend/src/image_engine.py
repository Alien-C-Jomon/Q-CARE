"""
Q-Care Image Observation Engine
Version 3.0

Purpose:
- Validate uploaded images.
- Extract image metadata.
- Provide a provider-neutral vision interface.
- Convert visual observations into Q-Care input.

Safety:
This module does NOT diagnose diseases.
Vision output is treated as observational information only.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


VISION_PROMPT = """
Describe only observable visual features in this image that could
be relevant to a health assessment.

Do not diagnose a disease or medical condition.
Do not estimate medical severity.
Do not recommend treatment.

Focus on:
- visible redness
- apparent swelling
- visible discoloration
- visible irritation
- visible lesions or marks
- approximate body region if reasonably apparent
- image quality or limitations

Clearly state uncertainty when the image does not provide enough
information.
"""


def validate_image_path(image_path: str) -> Dict[str, Any]:
    """Validate an image path and supported format."""

    path = Path(image_path)

    if not path.exists():
        return {
            "valid": False,
            "status": "not_found",
            "message": "Image file was not found.",
        }

    if not path.is_file():
        return {
            "valid": False,
            "status": "not_a_file",
            "message": "The supplied path is not a file.",
        }

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return {
            "valid": False,
            "status": "unsupported_format",
            "message": (
                "Unsupported image format. "
                "Use JPG, JPEG, PNG, or WEBP."
            ),
        }

    return {
        "valid": True,
        "status": "valid",
        "message": "Image is valid.",
        "filename": path.name,
        "extension": path.suffix.lower(),
    }


def load_image_metadata(image_path: str) -> Dict[str, Any]:
    """Load basic image metadata using Pillow."""

    validation = validate_image_path(image_path)

    if not validation["valid"]:
        return {
            "status": "error",
            "image_valid": False,
            "message": validation["message"],
        }

    path = Path(image_path)

    try:
        from PIL import Image

        with Image.open(path) as image:
            width, height = image.size

            return {
                "status": "loaded",
                "image_valid": True,
                "filename": path.name,
                "format": image.format,
                "width": width,
                "height": height,
                "aspect_ratio": (
                    round(width / height, 3)
                    if height
                    else None
                ),
                "mode": image.mode,
            }

    except Exception as exc:
        return {
            "status": "error",
            "image_valid": True,
            "message": f"Image loading failed: {exc}",
        }


def create_observation(
    feature: str,
    confidence: Optional[float] = None,
) -> Dict[str, Any]:
    """Create one structured non-diagnostic visual observation."""

    observation = {
        "feature": str(feature),
        "type": "visual_observation",
    }

    if confidence is not None:
        confidence = max(0.0, min(1.0, float(confidence)))
        observation["confidence"] = round(confidence, 3)

    return observation


def normalize_provider_observations(
    provider_output: Any,
) -> List[Dict[str, Any]]:
    """
    Convert provider output into Q-Care observation objects.

    Accepted prototype formats:
    - ["visible redness", "apparent swelling"]
    - [{"feature": "visible redness", "confidence": 0.8}]
    """

    if provider_output is None:
        return []

    if isinstance(provider_output, str):
        return [
            create_observation(provider_output)
        ]

    if not isinstance(provider_output, list):
        return []

    observations = []

    for item in provider_output:

        if isinstance(item, str):
            observations.append(
                create_observation(item)
            )

        elif isinstance(item, dict):

            feature = item.get("feature")

            if feature:
                observations.append(
                    create_observation(
                        feature,
                        item.get("confidence"),
                    )
                )

    return observations


def analyze_image(
    image_path: str,
    provider_output: Any = None,
) -> Dict[str, Any]:
    """
    Analyze an image using the provider-neutral interface.

    provider_output represents observations returned by a future
    vision provider. No diagnosis is performed here.
    """

    metadata = load_image_metadata(image_path)

    if metadata.get("status") != "loaded":
        return {
            "status": metadata.get("status", "error"),
            "image_valid": metadata.get(
                "image_valid",
                False,
            ),
            "diagnostic": False,
            "observations": [],
            "message": metadata.get(
                "message",
                "Image could not be loaded.",
            ),
        }

    observations = normalize_provider_observations(
        provider_output
    )

    return {
        "status": "analyzed",
        "image_valid": True,
        "diagnostic": False,
        "observation_type": "visual_observation",
        "metadata": metadata,
        "observations": observations,
        "vision_prompt": VISION_PROMPT.strip(),
        "message": (
            "Image processed successfully. "
            "Visual observations are descriptive only."
        ),
    }


def image_to_qcare_input(
    image_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Convert image observations into a safe Q-Care input object.
    """

    if not isinstance(image_result, dict):
        return {
            "status": "invalid_input",
            "source": "image",
            "diagnostic": False,
            "text": "",
            "observations": [],
        }

    observations = image_result.get(
        "observations",
        [],
    )

    observation_text = ", ".join(
        item.get("feature", "")
        for item in observations
        if isinstance(item, dict)
        and item.get("feature")
    )

    return {
        "status": image_result.get(
            "status",
            "unknown",
        ),
        "source": "image",
        "diagnostic": False,
        "text": observation_text,
        "observations": observations,
        "image_metadata": image_result.get(
            "metadata",
            {},
        ),
    }


def analyze_with_provider(
    image_path: str,
    provider_output: Any = None,
) -> Dict[str, Any]:
    """
    Main provider-neutral entry point.

    A real vision provider can later supply provider_output
    without changing the Q-Care evidence/quantum pipeline.
    """

    return analyze_image(
        image_path=image_path,
        provider_output=provider_output,
    )


if __name__ == "__main__":
    print("Q-Care Image Observation Engine")
    print("Version: 3.0")
    print("Diagnostic mode: DISABLED")
    print("Vision provider interface: READY")
    print("Observation normalization: READY")
    print("Q-Care image adapter: READY")