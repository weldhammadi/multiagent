"""
Auto-generated agent by Orchestrator.
"""

from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, List, Optional, Literal

import requests
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# --------------------------------------------------------------------------- #
# CONSTANTS (no magic numbers)
# --------------------------------------------------------------------------- #
MODEL_NAME: str = "openai/gpt-oss-120b"
TEMPERATURE: float = 0.6          # balanced creativity / determinism
MAX_TOKENS_PER_WORD: int = 2      # rough estimate: 1 word ≈ 2 tokens
MIN_LENGTH: int = 10              # enforce a minimal story length
MAX_LENGTH: int = 2000            # safeguard against excessively large requests

# Supported PlayAI voices (as documented by Groq)
SUPPORTED_VOICES: List[str] = [
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

AudioFormat = Literal["mp3", "opus", "aac", "flac", "wav"]

# --------------------------------------------------------------------------- #
# Logging configuration (application‑wide, can be overridden by the caller)
# --------------------------------------------------------------------------- #
LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:  # Prevent duplicate handlers in interactive sessions
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


def save_audio_file(audio_bytes: bytes, filename: str) -> str:
    """Write audio data to a file and return its absolute path.

    Args:
        audio_bytes (bytes): The raw audio data to be written.
        filename (str): Desired file name (may include a relative path).

    Returns:
        str: Absolute path to the written file.

    Raises:
        RuntimeError: If ``audio_bytes`` is empty, ``filename`` is empty, or the file
            cannot be written for any reason.
    """
    if not isinstance(audio_bytes, (bytes, bytearray)):
        raise RuntimeError("Le paramètre audio_bytes doit être de type bytes.")
    if not audio_bytes:
        raise RuntimeError("Le contenu audio_bytes est vide.")
    if not isinstance(filename, str) or not filename:
        raise RuntimeError("Le paramètre filename doit être une chaîne non vide.")

    file_path: str = os.path.abspath(filename)
    directory: str = os.path.dirname(file_path)
    if directory and not os.path.isdir(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"Impossible de créer le répertoire '{directory}': {exc}")

    try:
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
    except OSError as exc:
        raise RuntimeError(f"Échec de l'écriture du fichier audio '{file_path}': {exc}")

    return file_path


def generate_children_story(topic: str, length: int) -> Dict[str, Any]:
    """
    Generate a short children's story using a Large Language Model (LLM) hosted on Groq.

    Args:
        topic (str): The central theme or subject of the story.
        length (int): Desired length of the story in **words**.

    Returns:
        Dict[str, Any]: ``{"story": <str>}`` containing the generated story.

    Raises:
        ValueError: If inputs are invalid.
        RuntimeError: If the Groq API call fails.
    """
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("`topic` must be a non‑empty string.")
    if not isinstance(length, int):
        raise ValueError("`length` must be an integer.")
    if not (MIN_LENGTH <= length <= MAX_LENGTH):
        raise ValueError(
            f"`length` must be between {MIN_LENGTH} and {MAX_LENGTH} words (got {length})."
        )

    api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "Environment variable `GROQ_API_KEY` is not set. Please configure your Groq API key."
        )

    groq_client = Groq(api_key=api_key)

    system_message = (
        "You are a creative children's author. Write engaging, age‑appropriate "
        "stories that spark imagination."
    )
    user_message = (
        f"Write a children's story about **{topic}** that is approximately "
        f"{length} words long. The story should have a clear beginning, middle, "
        f"and end, and should be suitable for children aged 4‑8."
    )

    try:
        llm_response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=TEMPERATURE,
            max_tokens=length * MAX_TOKENS_PER_WORD,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to generate story via Groq API: {exc}") from exc

    try:
        story: str = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError(
            "Unexpected response structure from Groq API; unable to extract story."
        ) from exc

    return {"story": story}


def synthesize_story(
    story: str,
    voice: str = "Aaliyah-PlayAI",
    speed: float = 1.0,
    response_format: AudioFormat = "mp3",
) -> Dict[str, bytes]:
    """
    Convert a story text into spoken audio bytes using Groq's PlayAI‑TTS model.

    Args:
        story: The narrative to be spoken.
        voice: One of the voices listed in ``SUPPORTED_VOICES``.
        speed: Speech speed multiplier (0.25‑4.0).
        response_format: Desired audio container format.

    Returns:
        dict: ``{"audio_bytes": <bytes>}``.

    Raises:
        ValueError: If validation fails or the API key is missing.
        RuntimeError: If the Groq API call fails.
    """
    if not isinstance(story, str) or not story.strip():
        raise ValueError("`story` must be a non‑empty string.")
    if voice not in SUPPORTED_VOICES:
        raise ValueError(f"`voice` must be one of the supported voices: {SUPPORTED_VOICES}")
    if not isinstance(speed, (int, float)):
        raise ValueError("`speed` must be a numeric type.")
    if not 0.25 <= float(speed) <= 4.0:
        raise ValueError("`speed` must be between 0.25 and 4.0 (inclusive).")
    if response_format not in ("mp3", "opus", "aac", "flac", "wav"):
        raise ValueError("`response_format` must be one of: mp3, opus, aac, flac, wav.")

    api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set or empty.")

    try:
        client = Groq(api_key=api_key)
    except Exception as exc:
        LOGGER.exception("Failed to initialise Groq client.")
        raise RuntimeError("Could not create Groq client.") from exc

    try:
        response = client.audio.speech.create(
            model="openai/gpt-oss-120b",
            input=story,
            voice=voice,
            speed=float(speed),
            response_format=response_format,
        )
    except Exception as exc:
        LOGGER.exception("Groq TTS request failed.")
        raise RuntimeError("Error while calling Groq TTS endpoint.") from exc

    try:
        audio_bytes: bytes = response.content  # type: ignore[attr-defined]
    except Exception as exc:
        raise RuntimeError("Failed to extract audio bytes from Groq response.") from exc

    return {"audio_bytes": audio_bytes}


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    print("Running my_agent...")
    # Example usage (can be replaced with real workflow)
    try:
        story_data = generate_children_story(topic="a brave rabbit", length=150)
        story_text = story_data["story"]
        tts_result = synthesize_story(story=story_text, voice="Fritz-PlayAI")
        audio_path = save_audio_file(tts_result["audio_bytes"], "output/story.mp3")
        print(f"Story saved to: {audio_path}")
    except Exception as e:
        LOGGER.error("An error occurred: %s", e)