"""Auto-generated agent by Orchestrator."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Final, Literal, TypedDict

import requests
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# --------------------------------------------------------------------------- #
# Configuration & constants
# --------------------------------------------------------------------------- #

# Supported PlayAI voices (as documented by Groq)
SUPPORTED_VOICES: Final[list[str]] = [
    "Aaliyah-PlayAI",
    "Adelaide-PlayAI",
    "Angelo-PlayAI",
    "Arista-PlayAI",
    "Atlas-PlayAI",
    "Basil-PlayAI",
    "Briggs-PlayAI",
    "Calum-PlayAI",
    "Celeste-PlayAI",
    "Cheyenne-PlayAI",
    "Chip-PlayAI",
    "Cillian-PlayAI",
    "Deedee-PlayAI",
    "Eleanor-PlayAI",
    "Fritz-PlayAI",
    "Gail-PlayAI",
    "Indigo-PlayAI",
    "Jennifer-PlayAI",
    "Judy-PlayAI",
    "Mamaw-PlayAI",
    "Mason-PlayAI",
    "Mikail-PlayAI",
    "Mitch-PlayAI",
    "Nia-PlayAI",
    "Quinn-PlayAI",
    "Ruby-PlayAI",
    "Thunder-PlayAI",
]

# The *only* model we are allowed to call (strict requirement)
TTS_MODEL: Final[str] = "openai/gpt-oss-120b"

# --------------------------------------------------------------------------- #
# Logging configuration (application‑wide, can be overridden by the host)
# --------------------------------------------------------------------------- #

LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:  # avoid duplicate handlers when imported multiple times
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Public return type for TTS
# --------------------------------------------------------------------------- #


class SpeechResult(TypedDict):
    """Dictionary returned by :func:`generate_speech`."""

    audio_bytes: bytes
    """Raw audio payload returned by Groq (binary data)."""

    text_length: int
    """Number of characters in the original ``text`` argument."""

    voice_used: str
    """Voice that was actually used for synthesis."""


# --------------------------------------------------------------------------- #
# Exceptions
# --------------------------------------------------------------------------- #


class GroqTTSConfigurationError(RuntimeError):
    """Raised when the environment or input configuration is invalid."""


class GroqTTSAPIError(RuntimeError):
    """Raised when the Groq API returns an error or an unexpected response."""


# --------------------------------------------------------------------------- #
# Core functions
# --------------------------------------------------------------------------- #


def generate_children_story(theme: str, length: int) -> Dict[str, Any]:
    """
    Generate a short children's story based on a given theme and desired length
    using the Groq LLM model ``openai/gpt-oss-120b``.

    Args:
        theme: The central theme or topic of the story.
        length: Approximate desired length of the story measured in words.

    Returns:
        A dictionary containing the generated story under the key ``"story"``.

    Raises:
        ValueError: If inputs are invalid.
        RuntimeError: If the Groq API call fails.
    """
    if not isinstance(theme, str) or not theme.strip():
        raise ValueError("`theme` must be a non‑empty string.")
    if not isinstance(length, int) or length <= 0:
        raise ValueError("`length` must be a positive integer.")

    MIN_WORDS, MAX_WORDS = 20, 1000
    if not (MIN_WORDS <= length <= MAX_WORDS):
        raise ValueError(f"`length` must be between {MIN_WORDS} and {MAX_WORDS} words.")

    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    groq_client = Groq(api_key=api_key)

    system_message = (
        "You are a creative children's author. Write a short, engaging, "
        "and age‑appropriate story."
    )
    user_message = (
        f"Write a children's story about **{theme}**. "
        f"The story should be approximately {length} words long, "
        f"contain a clear beginning, middle, and end, and use simple language."
    )

    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6,
            max_tokens=length * 2,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to generate story via Groq API: {exc}") from exc

    try:
        story_text: str = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError(
            "Unexpected response format from Groq API; unable to extract story."
        ) from exc

    return {"story": story_text}


def generate_speech(
    text: str,
    voice: str = "Aaliyah-PlayAI",
    *,
    response_format: Literal["mp3", "opus", "aac", "flac", "wav"] = "mp3",
) -> SpeechResult:
    """
    Generate spoken audio from a text string using Groq's PlayAI‑TTS model.

    Args:
        text: The text to be spoken. Must be a non‑empty string.
        voice: Identifier of the voice to use. Must be in ``SUPPORTED_VOICES``.
        response_format: Desired audio container format.

    Returns:
        A ``SpeechResult`` dictionary containing the raw audio bytes, the length
        of the input text and the voice that was used.

    Raises:
        ValueError: If any argument fails validation.
        GroqTTSConfigurationError: If the ``GROQ_API_KEY`` environment variable is missing.
        GroqTTSAPIError: If the request to Groq fails or the response cannot be interpreted.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("`text` must be a non‑empty string.")
    if voice not in SUPPORTED_VOICES:
        raise ValueError(f"`voice` must be one of {SUPPORTED_VOICES!r}. Got {voice!r}.")
    if response_format not in ("mp3", "opus", "aac", "flac", "wav"):
        raise ValueError("`response_format` must be one of: mp3, opus, aac, flac, wav.")

    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqTTSConfigurationError("Environment variable `GROQ_API_KEY` is not set.")

    try:
        client = Groq(api_key=api_key)
    except Exception as exc:
        LOGGER.exception("Failed to initialise Groq client.")
        raise GroqTTSConfigurationError("Could not create Groq client – check the API key.") from exc

    try:
        response = client.audio.speech.create(
            model=TTS_MODEL,
            input=text,
            voice=voice,
            response_format=response_format,
        )
    except Exception as exc:
        LOGGER.exception("Groq TTS API request failed.")
        raise GroqTTSAPIError("Failed to generate speech via Groq API.") from exc

    try:
        if hasattr(response, "content"):
            audio_bytes = response.content
        else:
            # Fallback: treat response as a file‑like object
            audio_bytes = response.read()
    except Exception as exc:
        raise GroqTTSAPIError("Unable to extract audio bytes from Groq response.") from exc

    return SpeechResult(
        audio_bytes=audio_bytes,
        text_length=len(text),
        voice_used=voice,
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("Running my_agent_420...")
    # Example usage (can be removed or replaced with real workflow)
    try:
        story = generate_children_story("friendship", 150)
        print("Generated story:", story["story"][:200], "...")

        speech = generate_speech("Hello world!", voice="Aaliyah-PlayAI")
        print(f"Generated speech: {len(speech['audio_bytes'])} bytes, format mp3.")
    except Exception as e:
        LOGGER.error("An error occurred: %s", e)