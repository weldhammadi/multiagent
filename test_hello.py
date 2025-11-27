"""
Auto-generated agent by Orchestrator.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import os
from pathlib import Path

def save_audio_file(file_path: str, audio_bytes: bytes) -> bool:
    """Writes audio bytes to an MP4 file.

    Args:
        file_path (str): Destination path for the MP4 file.
        audio_bytes (bytes): Audio data to write.

    Returns:
        bool: True if the file was written successfully.

    Raises:
        RuntimeError: If the directory cannot be created or writing fails.
    """
    # Ensure the parent directory exists
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        raise RuntimeError(f"Impossible de créer le répertoire {path.parent}: {e}")

    try:
        with path.open("wb") as f:
            f.write(audio_bytes)
    except Exception as e:
        raise RuntimeError(f"Erreur lors de l'écriture du fichier {file_path}: {e}")

    return True

from groq import Groq
import os
from typing import Dict, Any


def generate_child_friendly_story_theme() -> Dict[str, Any]:
    """
    Génère un thème d’histoire créatif, ludique et adapté aux enfants, rédigé en français,
    en s’appuyant sur le modèle de grande taille ``openai/gpt-oss-120b`` via l’API Groq.

    Le thème retourné est une phrase courte (ou un petit paragraphe) qui peut servir
    de point de départ à un conteur, un auteur ou un enseignant.

    Returns:
        Dict[str, Any]: Dictionnaire contenant la clé **theme** avec le texte généré.
            Exemple::
                {
                    "theme": "Une aventure magique dans la forêt où les arbres parlent et
                              aident un petit écureuil à retrouver son trésor perdu."
                }

    Raises:
        ValueError: Si la variable d’environnement ``GROQ_API_KEY`` est absente.
        RuntimeError: Pour toute erreur provenant de l’appel à l’API Groq (ex. connexion,
                      dépassement de quota, réponse mal formée, etc.).
    """
    # --------------------------------------------------------------------- #
    # Étape 1 – Récupération sécurisée de la clé d’API
    # --------------------------------------------------------------------- #
    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "La variable d’environnement 'GROQ_API_KEY' n’est pas définie. "
            "Veuillez la configurer avant d’appeler la fonction."
        )

    # --------------------------------------------------------------------- #
    # Étape 2 – Instanciation du client Groq (seul le paramètre api_key est autorisé)
    # --------------------------------------------------------------------- #
    groq_client = Groq(api_key=api_key)

    # --------------------------------------------------------------------- #
    # Étape 3 – Construction du prompt adapté à la tâche
    # --------------------------------------------------------------------- #
    system_message: str = (
        "Tu es un assistant créatif spécialisé dans la rédaction de thèmes d’histoire "
        "pour les enfants. Le ton doit être joyeux, imaginaire et entièrement en français."
    )
    user_message: str = (
        "Propose un thème d’histoire original, ludique et adapté aux enfants de 4 à 8 ans. "
        "Le thème doit être court (une phrase ou deux) et évoquer un univers "
        "fantastique ou quotidien propice à l’imagination."
    )

    # --------------------------------------------------------------------- #
    # Étape 4 – Appel du modèle LLM via l’API Groq
    # --------------------------------------------------------------------- #
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,   # équilibre créativité / cohérence
            max_tokens=150,    # suffisant pour un thème concis
        )
    except Exception as exc:
        # Capture générique pour éviter la fuite d’informations sensibles
        raise RuntimeError(
            "Échec de l’appel à l’API Groq : " + str(exc)
        ) from exc

    # --------------------------------------------------------------------- #
    # Étape 5 – Extraction du texte généré et validation de la réponse
    # --------------------------------------------------------------------- #
    try:
        theme_text: str = llm_response.choices[0].message.content.strip()
        if not theme_text:
            raise ValueError("Le modèle a renvoyé un thème vide.")
    except (AttributeError, IndexError) as exc:
        raise RuntimeError(
            "Réponse inattendue de l’API Groq : le format de la réponse est invalide."
        ) from exc

    # --------------------------------------------------------------------- #
    # Étape 6 – Retour du résultat dans le format attendu
    # --------------------------------------------------------------------- #
    return {"theme": theme_text}

from groq import Groq
import os
from typing import Dict, Any

# Constants – keep them together for easy maintenance
_MODEL_NAME: str = "openai/gpt-oss-120b"
_TEMPERATURE: float = 0.6
_MAX_TOKENS: int = 2048
_SYSTEM_PROMPT: str = (
    "You are a creative children's author. Write vivid, age‑appropriate stories in French."
)


def generate_children_story(theme: str) -> Dict[str, Any]:
    """
    Generate a complete children’s story in French based on a given theme using the
    Groq LLM service (model ``openai/gpt-oss-120b``).

    The function validates the input, retrieves the Groq API key from the environment,
    calls the model, and returns the story text in a deterministic dictionary format.

    Args:
        theme: A non‑empty string describing the central theme of the story
               (e.g., ``"l\'amitié entre un dragon et un petit garçon"``).

    Returns:
        Dict[str, Any]: A dictionary containing the generated story.
            - ``story_text`` (str): The full story written in French.

    Raises:
        ValueError: If ``theme`` is not a non‑empty string or the ``GROQ_API_KEY`` is
                    missing from the environment.
        RuntimeError: If the request to the Groq API fails or an unexpected response
                      structure is received.
    """
    # --------------------------------------------------------------------- #
    # Step 1 – Input validation
    # --------------------------------------------------------------------- #
    if not isinstance(theme, str) or not theme.strip():
        raise ValueError("`theme` must be a non‑empty string.")

    # --------------------------------------------------------------------- #
    # Step 2 – Retrieve API key from environment
    # --------------------------------------------------------------------- #
    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    # --------------------------------------------------------------------- #
    # Step 3 – Initialise Groq client (only the API key is passed)
    # --------------------------------------------------------------------- #
    try:
        groq_client = Groq(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise Groq client: {exc}") from exc

    # --------------------------------------------------------------------- #
    # Step 4 – Build the prompt for the LLM
    # --------------------------------------------------------------------- #
    user_prompt: str = f"Écris une histoire complète pour enfants en français sur le thème suivant : \"{theme}\"."

    # --------------------------------------------------------------------- #
    # Step 5 – Call the LLM
    # --------------------------------------------------------------------- #
    try:
        llm_response = groq_client.chat.completions.create(
            model=_MODEL_NAME,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=_TEMPERATURE,
            max_tokens=_MAX_TOKENS,
        )
    except Exception as exc:
        raise RuntimeError(f"Groq API request failed: {exc}") from exc

    # --------------------------------------------------------------------- #
    # Step 6 – Extract the story text from the response
    # --------------------------------------------------------------------- #
    try:
        story_text: str = llm_response.choices[0].message.content  # type: ignore[attr-defined]
    except (AttributeError, IndexError) as exc:
        raise RuntimeError(
            "Unexpected response format from Groq API; unable to extract story text."
        ) from exc

    # --------------------------------------------------------------------- #
    # Step 7 – Return the result in the required format
    # --------------------------------------------------------------------- #
    return {"story_text": story_text}

**Python – Text‑to‑Speech (TTS) helper using Groq PlayAI TTS**

```python
"""
groq_tts.py – Production‑grade French (or any supported language) TTS helper.

The module exposes a single public function ``generate_speech`` that:
* validates its inputs,
* reads the Groq API key from the ``GROQ_API_KEY`` environment variable,
* creates a :class:`groq.Groq` client,
* calls ``client.audio.speech.create`` with the *PlayAI‑TTS* model,
* returns the raw audio bytes (MP4‑compatible) in a deterministic dictionary.

The implementation follows clean‑code / SOLID principles, includes exhaustive
type‑hints, Google‑style docstrings, and defensive error handling suitable for
critical production environments.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Dict

from groq import Groq

# --------------------------------------------------------------------------- #
# Configuration & constants
# --------------------------------------------------------------------------- #

# Supported language‑to‑voice mapping (extend as needed)
_LANGUAGE_VOICE_MAP: Dict[str, str] = {
    "fr": "Fritz-PlayAI",          # French
    "en": "Alloy-PlayAI",          # English (fallback)
    "es": "Luna-PlayAI",           # Spanish
    "de": "Klaus-PlayAI",          # German
}

# Allowed output container – MP4 is required for the specification
_OUTPUT_FORMAT: str = "mp4"

# Speed limits enforced by the PlayAI‑TTS service
_MIN_SPEED: float = 0.25
_MAX_SPEED: float = 4.0

# --------------------------------------------------------------------------- #
# Logging configuration (application‑wide, no secrets emitted)
# --------------------------------------------------------------------------- #

_logger = logging.getLogger(__name__)
if not _logger.handlers:
    # Configure a simple console logger if the host application has not done so.
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _handler.setFormatter(_formatter)
    _logger.addHandler(_handler)
    _logger.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def generate_speech(
    text: str,
    language: str = "fr",
    speed: float = 1.0,
) -> Dict[str, bytes]:
    """
    Convert *text* into spoken audio using Groq’s PlayAI‑TTS model.

    The function is deliberately strict: any malformed input raises a
    ``ValueError`` with a clear message, and all runtime failures are wrapped
    into a ``RuntimeError`` that does **not** leak credentials or internal
    request details.

    Args:
        text: The plain‑text to be spoken. Must be a non‑empty ``str``.
        language: ISO‑639‑1 language code (e.g. ``"fr"``, ``"en"``). Determines
            the voice that will be used. Defaults to French (``"fr"``).
        speed: Speech speed factor. Must be between 0.25 × normal and
            4.0 × normal. Default is ``1.0`` (real‑time).

    Returns:
        dict: ``{"audio_bytes": <bytes>}`` where the value contains MP4‑compatible
        audio data ready to be written to a file or streamed.

    Raises:
        ValueError: If any argument fails validation or the API key is missing.
        RuntimeError: For network‑level or Groq‑SDK errors that cannot be
        recovered from.

    Example:
        >>> result = generate_speech(
        ...     text="Il était une fois un petit robot.",
        ...     language="fr",
        ...     speed=1.2,
        ... )
        >>> with open("story.mp4", "wb") as f:
        ...     f.write(result["audio_bytes"])
    """
    # ------------------------------------------------------------------- #
    # 1️⃣ Input validation
    # ------------------------------------------------------------------- #
    if not isinstance(text, str) or not text.strip():
        raise ValueError("`text` must be a non‑empty string.")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("`language` must be a non‑empty ISO‑639‑1 code string.")
    if not isinstance(speed, (int, float)):
        raise ValueError("`speed` must be a numeric type.")
    if not _MIN_SPEED <= speed <= _MAX_SPEED:
        raise ValueError(
            f"`speed` must be between {_MIN_SPEED} and {_MAX_SPEED} (inclusive)."

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("🚀 Running kids_story_agent...")
    # TODO: Implement main workflow here
    # Available functions:
    # - save_audio_file()
    # - generate_child_friendly_story_theme()
    # - generate_children_story()
    # - generate_speech()
    pass
