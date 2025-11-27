import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional, Literal
from dotenv import load_dotenv

from groq import Groq

# Load environment variables
load_dotenv()

# --------------------------------------------------------------------------- #
# Configuration & constants
# --------------------------------------------------------------------------- #

SUPPORTED_VOICES = [
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

SUPPORTED_FORMATS = ("mp3", "opus", "aac", "flac", "wav")
GROQ_TTS_MODEL = "openai/gpt-oss-120b"

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #

LOGGER = logging.getLogger(__name__)
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    LOGGER.addHandler(handler)
    LOGGER.setLevel(logging.INFO)


def write_audio_file(audio_bytes: bytes, file_path: str) -> str:
    """Write audio data to a file and return its absolute path."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.isdir(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"Impossible de créer le répertoire '{directory}': {exc}")

    try:
        with open(file_path, "wb") as f:
            f.write(audio_bytes)
    except OSError as exc:
        raise RuntimeError(f"Échec de l'écriture du fichier audio à '{file_path}': {exc}")

    return os.path.abspath(file_path)


def generate_children_story(theme: str, length_words: int) -> Dict[str, Any]:
    """Generate a children's story using the Groq LLM."""
    if not isinstance(theme, str) or not theme.strip():
        raise ValueError("`theme` must be a non‑empty string.")
    if not isinstance(length_words, int) or length_words <= 0:
        raise ValueError("`length_words` must be a positive integer.")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Environment variable `GROQ_API_KEY` is not set.")

    groq_client = Groq(api_key=api_key)

    system_message = (
        "You are a creative children's author. Write engaging, age‑appropriate "
        "stories with vivid imagination, simple language, and a positive moral."
    )
    user_message = (
        f"Write a children's story about \"{theme}\" that is approximately "
        f"{length_words} words long. The story should have a clear beginning, "
        f"middle, and end, and be suitable for readers aged 4‑8."
    )

    estimated_tokens = int(length_words * 0.75) + 100
    max_tokens = min(estimated_tokens, 4096)

    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6,
            max_tokens=max_tokens,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to generate story via Groq API: {exc}") from exc

    try:
        story_text = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Unexpected response format from Groq API.") from exc

    return {"story_text": story_text}


def convert_story_to_audio(
    story_text: str,
    *,
    voice: str = "Aaliyah-PlayAI",
    speed: float = 1.0,
    output_format: Literal["mp3", "opus", "aac", "flac", "wav"] = "mp3",
) -> Dict[str, bytes]:
    """Convert a story text into spoken audio bytes using Groq PlayAI TTS."""
    if not isinstance(story_text, str) or not story_text.strip():
        raise ValueError("`story_text` must be a non‑empty string.")

    if voice not in SUPPORTED_VOICES:
        raise ValueError(f"`voice` must be one of the supported voices: {SUPPORTED_VOICES}")

    if not isinstance(speed, (int, float)):
        raise ValueError("`speed` must be a numeric type.")
    if not 0.25 <= speed <= 4.0:
        raise ValueError("`speed` must be between 0.25 and 4.0 (inclusive).")

    if output_format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"`output_format` must be one of {SUPPORTED_FORMATS}, got '{output_format}'."
        )

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    client = Groq(api_key=api_key)

    try:
        response = client.audio.speech.create(
            model=GROQ_TTS_MODEL,
            input=story_text,
            voice=voice,
            speed=speed,
            response_format=output_format,
        )
    except Exception as exc:
        LOGGER.error("Groq TTS request failed: %s", exc)
        raise

    # The Groq SDK returns the raw audio bytes in the `audio` attribute.
    try:
        audio_bytes = response.audio
    except AttributeError as exc:
        raise RuntimeError("Failed to retrieve audio bytes from Groq response.") from exc

    return {"audio_bytes": audio_bytes}


if __name__ == "__main__":
    LOGGER.info("🚀 Running my_agent...")
    # Example workflow (can be replaced with actual logic)
    try:
        story = generate_children_story("friendship in the forest", 200)
        audio_result = convert_story_to_audio(story["story_text"])
        file_path = write_audio_file(audio_result["audio_bytes"], "output/story.mp3")
        LOGGER.info("Audio file saved to %s", file_path)
    except Exception as e:
        LOGGER.exception("An error occurred: %s", e)