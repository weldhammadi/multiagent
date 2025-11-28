from __future__ import annotations

import os
import logging
from typing import Dict, Any, Final, Literal, TypedDict

from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# --------------------------------------------------------------------------- #
# Logging configuration (application‑wide, can be overridden by the caller)
# --------------------------------------------------------------------------- #

_logger = logging.getLogger(__name__)
if not _logger.handlers:  # Prevent duplicate handlers in interactive sessions
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Children story generation
# --------------------------------------------------------------------------- #

def generate_children_story(prompt: str) -> Dict[str, Any]:
    """
    Generates a short children's story based on a user‑provided prompt or theme.

    Args:
        prompt (str): A non‑empty description, theme or seed sentence that will
            guide the story generation.

    Returns:
        Dict[str, Any]: ``{'story_text': <generated story>}``.

    Raises:
        ValueError: If ``prompt`` is invalid or the API key is missing.
        RuntimeError: If the Groq request fails or returns an unexpected format.
    """
    # Validate input
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("prompt must be a non‑empty string")

    # Retrieve API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    # Initialise Groq client
    groq_client = Groq(api_key=api_key)

    # Build messages
    system_message = (
        "You are a creative storyteller specialized in writing short, "
        "engaging, age‑appropriate stories for children aged 3‑8. "
        "Use simple language, vivid imagination, and a gentle moral."
    )
    user_message = f"Write a children's story based on the following prompt: {prompt}"

    # Call the LLM
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6,
            max_tokens=1024,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to generate story via Groq API: {exc}") from exc

    # Extract story text
    try:
        story_text = llm_response.choices[0].message.content
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Unexpected response format from Groq API") from exc

    return {"story_text": story_text}

# --------------------------------------------------------------------------- #
# Text‑to‑Speech helper
# --------------------------------------------------------------------------- #

SUPPORTED_VOICES: Final[list[str]] = [
    "Aaliyah-PlayAI", "Adelaide-PlayAI", "Angelo-PlayAI", "Arista-PlayAI",
    "Atlas-PlayAI", "Basil-PlayAI", "Briggs-PlayAI", "Calum-PlayAI",
    "Celeste-PlayAI", "Cheyenne-PlayAI", "Chip-PlayAI", "Cillian-PlayAI",
    "Deedee-PlayAI", "Eleanor-PlayAI", "Fritz-PlayAI", "Gail-PlayAI",
    "Indigo-PlayAI", "Jennifer-PlayAI", "Judy-PlayAI", "Mamaw-PlayAI",
    "Mason-PlayAI", "Mikail-PlayAI", "Mitch-PlayAI", "Nia-PlayAI",
    "Quinn-PlayAI", "Ruby-PlayAI", "Thunder-PlayAI",
]

SupportedFormat = Literal["mp3", "opus", "aac", "flac", "wav"]

class SpeechResult(TypedDict):
    """Typed dictionary returned by ``generate_speech``."""
    audio_bytes: bytes

def generate_speech(
    *,
    text: str,
    voice: str = "Aaliyah-PlayAI",
    speed: float = 1.0,
    output_format: SupportedFormat = "mp3",
) -> SpeechResult:
    """
    Generate spoken audio from plain text using Groq’s PlayAI TTS model.

    Args:
        text: Non‑empty string to be spoken.
        voice: One of the voices listed in ``SUPPORTED_VOICES``.
        speed: Speech speed multiplier between 0.25 and 4.0.
        output_format: Desired audio container format.

    Returns:
        SpeechResult containing the raw audio bytes.

    Raises:
        ValueError: For invalid arguments or missing API key.
        RuntimeError: If the Groq API call fails or returns an unexpected response.
    """
    # Input validation
    if not isinstance(text, str) or not text.strip():
        raise ValueError("`text` must be a non‑empty string.")
    if voice not in SUPPORTED_VOICES:
        raise ValueError(f"`voice` must be one of the supported voices: {SUPPORTED_VOICES}")
    if not isinstance(speed, (int, float)):
        raise ValueError("`speed` must be a numeric type.")
    if not 0.25 <= speed <= 4.0:
        raise ValueError("`speed` must be between 0.25 and 4.0 (inclusive).")
    if output_format not in ("mp3", "opus", "aac", "flac", "wav"):
        raise ValueError("`output_format` must be one of: mp3, opus, aac, flac, wav.")

    # Retrieve API key
    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    # Initialise Groq client
    groq_client = Groq(api_key=api_key)

    # Call the TTS endpoint
    try:
        tts_response = groq_client.audio.speech.create(
            model="playai-tts",
            voice=voice,
            input=text,
            speed=speed,
            response_format=output_format,
        )
    except Exception as exc:
        _logger.error("Groq TTS request failed: %s", exc)
        raise RuntimeError(f"Failed to generate speech via Groq API: {exc}") from exc

    # The response is expected to contain raw bytes in ``content`` attribute
    try:
        audio_bytes = tts_response.content
        if not isinstance(audio_bytes, (bytes, bytearray)):
            raise TypeError
    except Exception as exc:
        raise RuntimeError("Unexpected response format from Groq TTS API") from exc

    return {"audio_bytes": bytes(audio_bytes)}

# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    _logger.info("🚀 Running my_agent...")
    # Example usage (can be removed or replaced with real workflow)
    try:
        story = generate_children_story("A brave rabbit discovers a hidden garden")
        _logger.info("Generated story: %s", story["story_text"][:100] + "...")

        speech = generate_speech(
            text=story["story_text"],
            voice="Fritz-PlayAI",
            speed=1.0,
            output_format="mp3",
        )
        # Save the audio to a file for demonstration purposes
        output_path = "story.mp3"
        with open(output_path, "wb") as f:
            f.write(speech["audio_bytes"])
        _logger.info("Audio saved to %s", output_path)
    except Exception as e:
        _logger.exception("An error occurred: %s", e)