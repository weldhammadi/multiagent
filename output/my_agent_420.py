"""Auto-generated agent by Orchestrator."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

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

ALLOWED_FORMATS = {"mp3", "opus", "aac", "flac", "wav"}
MIN_SPEED = 0.25
MAX_SPEED = 4.0
FORCED_MODEL = "openai/gpt-oss-120b"

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Utility functions
# --------------------------------------------------------------------------- #


def save_audio_file(audio_bytes: bytes, filename: str) -> str:
    """Enregistre les octets audio dans un fichier et renvoie le chemin absolu."""
    if not isinstance(audio_bytes, (bytes, bytearray)):
        raise RuntimeError("Le paramètre audio_bytes doit être de type bytes.")
    if not isinstance(filename, str) or not filename:
        raise RuntimeError("Le paramètre filename doit être une chaîne non vide.")

    directory = os.path.dirname(filename)
    if directory and not os.path.isdir(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as exc:
            raise RuntimeError(f"Impossible de créer le répertoire '{directory}': {exc}")

    try:
        with open(filename, "wb") as file:
            file.write(audio_bytes)
    except OSError as exc:
        raise RuntimeError(f"Échec de l'écriture du fichier '{filename}': {exc}")

    return os.path.abspath(filename)


def generate_children_story(theme: str, length: int) -> Dict[str, Any]:
    """Génère une histoire pour enfants à partir d'un thème et d'une longueur."""
    if not isinstance(theme, str) or not theme.strip():
        raise ValueError("theme must be a non‑empty string")
    if not isinstance(length, int) or length <= 0:
        raise ValueError("length must be a positive integer")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    groq_client = Groq(api_key=api_key)

    system_message = (
        "You are a creative writer specialized in crafting engaging, age‑appropriate "
        "children's stories."
    )
    user_message = (
        f"Write a children's story about \"{theme}\" that is approximately "
        f"{length} words long. The story should be imaginative, friendly, and suitable "
        f"for young readers."
    )

    estimated_tokens = min(8192, max(256, length * 5))
    temperature = 0.6

    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
            max_tokens=estimated_tokens,
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to generate story via Groq API: {exc}") from exc

    try:
        story_text = llm_response.choices[0].message.content
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Unexpected response format from Groq API") from exc

    return {"story_text": story_text}


def generate_story_speech(
    story_text: str,
    voice: str = "Aaliyah-PlayAI",
    speed: float = 1.0,
    response_format: str = "mp3",
) -> Dict[str, bytes]:
    """Convert a story text to spoken audio bytes using Groq TTS."""
    if not isinstance(story_text, str) or not story_text.strip():
        raise ValueError("`story_text` must be a non‑empty string.")
    if voice not in SUPPORTED_VOICES:
        raise ValueError(f"`voice` must be one of {SUPPORTED_VOICES!r}. Received: {voice!r}")
    if not isinstance(speed, (int, float)):
        raise ValueError("`speed` must be a numeric type.")
    if not (MIN_SPEED <= speed <= MAX_SPEED):
        raise ValueError(f"`speed` must be between {MIN_SPEED} and {MAX_SPEED}. Received: {speed}")
    if response_format not in ALLOWED_FORMATS:
        raise ValueError(
            f"`response_format` must be one of {sorted(ALLOWED_FORMATS)}. Received: {response_format!r}"
        )

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    try:
        client = Groq(api_key=api_key)
        response = client.audio.speech.create(
            model=FORCED_MODEL,
            voice=voice,
            input=story_text,
            speed=speed,
            response_format=response_format,
        )
    except Exception as exc:
        logger.error("Groq TTS request failed: %s", exc)
        raise RuntimeError(f"Failed to generate speech via Groq API: {exc}") from exc

    # The Groq SDK returns raw bytes in the `content` attribute for speech responses.
    audio_bytes = getattr(response, "content", None) or getattr(response, "audio_bytes", None)
    if not isinstance(audio_bytes, (bytes, bytearray)):
        raise RuntimeError("Groq TTS response did not contain audio bytes.")

    return {"audio_bytes": bytes(audio_bytes)}


# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    logger.info("🚀 Running my_agent_420...")
    # Example workflow (can be replaced with real logic)
    try:
        story = generate_children_story(theme="friendship", length=200)
        speech = generate_story_speech(story_text=story["story_text"], voice="Fritz-PlayAI")
        file_path = save_audio_file(speech["audio_bytes"], "output/story.mp3")
        logger.info("Audio saved to %s", file_path)
    except Exception as e:
        logger.exception("An error occurred: %s", e)