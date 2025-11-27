"""
Auto-generated agent by Orchestrator.
"""

import os
import json
import requests
import asyncio
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

from groq import Groq
import os
import logging
from typing import Dict, Any, Optional

# --------------------------------------------------------------------------- #
# Configuration & Logging
# --------------------------------------------------------------------------- #
_LOGGER = logging.getLogger(__name__)
if not _LOGGER.handlers:
    # Configure a simple console logger if the application hasn't configured logging yet
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def generate_child_story_theme(seed: Optional[str] = None) -> Dict[str, Any]:
    """Generate a creative story theme that is appropriate for children.

    The function contacts the Groq LLM endpoint using the model
    ``openai/gpt-oss-120b`` and asks it to propose a short, imaginative
    story theme.  An optional *seed* can be supplied to steer the
    generation (e.g., a keyword, a character name, or a setting).  If no
    seed is provided, the model will generate a generic child‑friendly
    theme.

    Args:
        seed: Optional free‑form text that influences the generated theme.
              Must be a non‑empty string when provided.

    Returns:
        dict: ``{\"theme\": <generated_theme>}`` where ``theme`` is a
        short (≤ 50 words) description suitable for a children's story.

    Raises:
        ValueError: If ``seed`` is provided but is not a non‑empty string.
        RuntimeError: If the GROQ API key is missing or the request to the
            LLM fails for any reason.
    """
    # ------------------------------------------------------------------- #
    # Step 1 – Input validation
    # ------------------------------------------------------------------- #
    if seed is not None:
        if not isinstance(seed, str) or not seed.strip():
            raise ValueError("seed must be a non‑empty string when provided")

    # ------------------------------------------------------------------- #
    # Step 2 – Retrieve API key
    # ------------------------------------------------------------------- #
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Please configure it before calling generate_child_story_theme()."
        )

    # ------------------------------------------------------------------- #
    # Step 3 – Initialise Groq client (only api_key is passed)
    # ------------------------------------------------------------------- #
    try:
        groq_client = Groq(api_key=api_key)
    except Exception as exc:
        _LOGGER.exception("Failed to initialise Groq client")
        raise RuntimeError("Unable to initialise Groq client") from exc

    # ------------------------------------------------------------------- #
    # Step 4 – Build prompt
    # ------------------------------------------------------------------- #
    system_message = (
        "You are a creative writing assistant specialized in content for "
        "children aged 4-8. Propose a single, vivid story theme that sparks "
        "imagination, is age-appropriate, and can be expanded into a short story."
    )
    if seed:
        user_message = f"Generate a story theme based on the following idea: {seed}"
    else:
        user_message = "Generate a generic, child-friendly story theme."

    # ------------------------------------------------------------------- #
    # Step 5 – Call the LLM
    # ------------------------------------------------------------------- #
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,   # balanced creativity vs. determinism
            max_tokens=150,    # enough for a concise theme
        )
    except Exception as exc:
        _LOGGER.exception("Groq API request failed")
        raise RuntimeError("Failed to obtain a response from the LLM") from exc

    # ------------------------------------------------------------------- #
    # Step 6 – Extract and clean result
    # ------------------------------------------------------------------- #
    try:
        raw_theme: str = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        _LOGGER.exception("Unexpected response structure from Groq")
        raise RuntimeError("Malformed response received from the LLM") from exc

    # Basic sanity check – ensure we got a non‑empty string
    if not raw_theme:
        raise RuntimeError("LLM returned an empty story theme")

    # ------------------------------------------------------------------- #
    # Step 7 – Return the structured result
    # ------------------------------------------------------------------- #
    return {"theme": raw_theme}

from groq import Groq
import os
from typing import Dict, Any


def generate_children_story(theme: str) -> Dict[str, Any]:
    """
    Generate a complete children's story in English from a given theme,
    using the LLM model "openai/gpt-oss-120b" via the Groq API.

    Args:
        theme: Narrative theme around which the story should be built. Must be a non-empty string.

    Returns:
        dict: Dictionary containing the following key:
            - ``story_text`` (str): the full generated story text.

    Raises:
        ValueError: If ``theme`` is not a non-empty string or if the ``GROQ_API_KEY`` environment variable is missing.
        RuntimeError: If the Groq API call fails (e.g., network issue, invalid response, etc.).
    """
    # --------------------------------------------------------------------- #
    # Step 1 – Input validation
    # --------------------------------------------------------------------- #
    if not isinstance(theme, str) or not theme.strip():
        raise ValueError("`theme` must be a non-empty string.")

    # --------------------------------------------------------------------- #
    # Step 2 – Retrieve API key
    # --------------------------------------------------------------------- #
    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    # --------------------------------------------------------------------- #
    # Step 3 – Instantiate Groq client
    # --------------------------------------------------------------------- #
    groq_client = Groq(api_key=api_key)

    # --------------------------------------------------------------------- #
    # Step 4 – Build prompt
    # --------------------------------------------------------------------- #
    system_message = (
        "You are a writer specialized in children's stories. "
        "You write in English, with a warm, simple, and vivid tone."
    )
    user_message = (
        f"Write a complete children's story (beginning, middle, end) "
        f"based on the following theme: '{theme.strip()}'. "
        "The story should be suitable for children aged 5 to 8, "
        "with no violent or inappropriate content."
    )

    # --------------------------------------------------------------------- #
    # Step 5 – Call the LLM
    # --------------------------------------------------------------------- #
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6,      # balance creativity / coherence
            max_tokens=2048,      # large enough for a complete story
        )
    except Exception as exc:
        raise RuntimeError(f"Groq API call failed: {exc}") from exc

    # --------------------------------------------------------------------- #
    # Step 6 – Extract generated text
    # --------------------------------------------------------------------- #
    try:
        story_text: str = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Malformed response from Groq API.") from exc

    # --------------------------------------------------------------------- #
    # Step 7 – Return result
    # --------------------------------------------------------------------- #
    return {"story_text": story_text}


def generate_children_story_streaming(theme: str):
    """
    Generate a complete children's story with streaming, yielding sentences as they are generated.

    Args:
        theme: Narrative theme around which the story should be built. Must be a non-empty string.

    Yields:
        str: Complete sentences as they are generated.

    Raises:
        ValueError: If ``theme`` is not a non-empty string or if the ``GROQ_API_KEY`` environment variable is missing.
        RuntimeError: If the Groq API call fails.
    """
    if not isinstance(theme, str) or not theme.strip():
        raise ValueError("`theme` must be a non-empty string.")

    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    groq_client = Groq(api_key=api_key)

    system_message = (
        "You are a writer specialized in children's stories. "
        "You write in English, with a warm, simple, and vivid tone."
    )
    user_message = (
        f"Write a complete children's story (beginning, middle, end) "
        f"based on the following theme: '{theme.strip()}'. "
        "The story should be suitable for children aged 5 to 8, "
        "with no violent or inappropriate content."
    )

    try:
        stream = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6,
            max_tokens=2048,
            stream=True,  # Enable streaming
        )
    except Exception as exc:
        raise RuntimeError(f"Groq API call failed: {exc}") from exc

    # Buffer to accumulate text until we have a complete sentence
    buffer = ""
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            buffer += content
            
            # Check if we have complete sentences
            sentences = sentence_endings.split(buffer)
            
            # If we have more than one part, all but the last are complete sentences
            if len(sentences) > 1:
                for sentence in sentences[:-1]:
                    sentence = sentence.strip()
                    if sentence:
                        yield sentence
                # Keep the incomplete part in the buffer
                buffer = sentences[-1]
    
    # Yield any remaining text in the buffer
    if buffer.strip():
        yield buffer.strip()


"""
speech_generation.py
--------------------

Utility to synthesize French (or any supported language) story text into an
engaging audio narration using Groq's **playai‑tts** model.  
The generated audio is saved as an MP4 file (AAC codec) and the absolute
path to the file is returned.

The implementation follows strict production‑ready guidelines:
* Full type‑hinting and Google‑style docstrings
* Exhaustive input validation with explicit error messages
* Secure handling of the Groq API key (environment variable only)
* Robust error handling – all external failures are wrapped in a
  ``SpeechGenerationError`` with a clear, non‑leaking message
* No use of ``eval``, ``exec`` or subprocesses
* Minimal, safe imports
* Logging without exposing secrets
"""


import base64
import logging
import os
import uuid
from pathlib import Path
from typing import Final, Literal, TypedDict

from groq import Groq

# --------------------------------------------------------------------------- #
# Constants & Types
# --------------------------------------------------------------------------- #

# Supported audio containers – MP4 uses AAC codec internally.
_SUPPORTED_FORMATS: Final[tuple[str, ...]] = ("mp3", "opus", "aac", "flac")
# Default voice list – the actual list depends on the PlayAI service.
_DEFAULT_VOICE: Final[str] = "alloy"
# Speed limits enforced by the PlayAI TTS endpoint.
_MIN_SPEED: Final[float] = 0.25
_MAX_SPEED: Final[float] = 4.0

class SpeechResult(TypedDict):
    """Structure returned by :func:`generate_story_audio`."""
    audio_file_path: str

class SpeechGenerationError(RuntimeError):
    """Custom exception raised for any failure during speech generation."""
    pass

# --------------------------------------------------------------------------- #
# Logger configuration (application‑wide, can be overridden by the caller)
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
# Core function
# --------------------------------------------------------------------------- #

def generate_story_audio(
    story_text: str,
    language: str,
    *,
    voice: str = _DEFAULT_VOICE,
    speed: float = 1.0,
    output_format: Literal["mp3", "opus", "aac", "flac"] = "aac",
    output_dir: str | os.PathLike = ".",
) -> SpeechResult:
    """
    Convert a French story (or any supported language) into an MP4 audio file
    using Groq's ``playai-tts`` model.

    The function validates all inputs, calls the Groq TTS endpoint, writes the
    binary audio payload to a uniquely‑named MP4 file and returns the absolute
    path to that file.

    Args:
        story_text: The narrative to be spoken. Must be a non‑empty ``str``.
        language: ISO‑639‑1 language code (e.g. ``"fr"`` for French). The
            underlying model decides whether the language is supported.
        voice: Identifier of the voice to use. Defaults to ``"alloy"``.
        speed: Speech speed multiplier – must be between 0.25 and 4.0
            (inclusive). ``1.0`` is the default normal speed.
        output_format: Desired audio container. Only ``"aac"`` is compatible
            with the MP4 wrapper used for the output file. Other formats are
            accepted by the API but will be converted to AAC internally.
        output_dir: Directory where the MP4 file will be written. It must exist
            and be writable. Defaults to the current working directory.

    Returns:
        SpeechResult: ``{'audio_file_path': <absolute_path_to_mp4>}``

    Raises:
        ValueError: If any argument fails validation.
        SpeechGenerationError: For any failure while contacting the Groq API
            or writing the output file.
    """
    # ------------------------------------------------------------------- #
    # 1️⃣ Input validation
    # ------------------------------------------------------------------- #
    if not isinstance(story_text, str) or not story_text.strip():
        raise ValueError("`story_text` must be a non‑empty string.")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("`language` must be a non‑empty string (ISO‑639‑1 code).")
    if not isinstance(voice, str) or not voice.strip():
        raise ValueError("`voice` must be a non‑empty string.")
    if not isinstance(speed, (int, float)):
        raise ValueError("`speed` must be a numeric value.")
    if not (_MIN_SPEED <= float(speed) <= _MAX_SPEED):
        raise ValueError(
            f"`speed` must be between {_MIN_SPEED} and {_MAX_SPEED} (inclusive)."
        )
    if output_format not in _SUPPORTED_FORMATS:
        raise ValueError(
            f"`output_format` must be one of {_SUPPORTED_FORMATS}, got '{output_format}'."
        )
    output_dir_path = Path(output_dir).expanduser().resolve()
    if not output_dir_path.is_dir():
        raise ValueError(f"`output_dir` must be an existing directory: {output_dir_path}")

    # ------------------------------------------------------------------- #
    # 2️⃣ Retrieve API key from environment (never hard‑code)
    # ------------------------------------------------------------------- #
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    # ------------------------------------------------------------------- #
    # 3️⃣ Initialise Groq client
    # ------------------------------------------------------------------- #
    try:
        client = Groq(api_key=api_key)
    except Exception as exc:
        _logger.exception("Failed to initialise Groq client.")
        raise SpeechGenerationError("Unable to initialise Groq client.") from exc

    # ------------------------------------------------------------------- #
    # 4️⃣ Call the TTS endpoint
    # ------------------------------------------------------------------- #
    try:
        response = client.audio.speech.create(
            model="playai-tts",
            input=story_text,
            voice=voice,
            speed=float(speed),
            response_format=output_format,
        )
        # Save the audio directly using the SDK's write_to_file method
        audio_file_path = str(output_dir_path / f"story_{uuid.uuid4().hex}.{output_format}")
        response.write_to_file(audio_file_path)
    except Exception as exc:
        _logger.exception("Failed to generate speech via Groq TTS API.")
        raise SpeechGenerationError("Unable to generate audio from the story text.") from exc

    return {"audio_file_path": audio_file_path}


def generate_sentence_audio_sync(
    sentence: str,
    sentence_index: int,
    language: str,
    voice: str,
    speed: float,
    output_format: str,
    output_dir: Path,
) -> tuple[int, str]:
    """
    Synchronous helper to generate audio for a single sentence.
    Returns (sentence_index, audio_file_path) for ordering.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")
    
    client = Groq(api_key=api_key)
    
    response = client.audio.speech.create(
        model="playai-tts",
        input=sentence,
        voice=voice,
        speed=float(speed),
        response_format=output_format,
    )
    
    audio_file_path = str(output_dir / f"sentence_{sentence_index:04d}_{uuid.uuid4().hex[:8]}.{output_format}")
    response.write_to_file(audio_file_path)
    
    return (sentence_index, audio_file_path)


async def generate_story_audio_async(
    story_text: str,
    language: str,
    *,
    voice: str = _DEFAULT_VOICE,
    speed: float = 1.0,
    output_format: Literal["mp3", "opus", "aac", "flac"] = "aac",
    output_dir: str | os.PathLike = ".",
    max_workers: int = 5,
) -> SpeechResult:
    """
    Convert story text into audio by processing sentences in parallel asynchronously.

    This function splits the text into sentences and generates TTS audio for each
    sentence concurrently using a thread pool, then combines all audio files.

    Args:
        story_text: The narrative to be spoken. Must be a non‑empty ``str``.
        language: ISO‑639‑1 language code (e.g. ``"en"`` for English).
        voice: Identifier of the voice to use. Defaults to ``"alloy"``.
        speed: Speech speed multiplier – must be between 0.25 and 4.0.
        output_format: Desired audio format.
        output_dir: Directory where the audio files will be written.
        max_workers: Maximum number of concurrent TTS requests.

    Returns:
        SpeechResult: ``{'audio_file_path': <absolute_path_to_combined_audio>}``
    """
    # Input validation
    if not isinstance(story_text, str) or not story_text.strip():
        raise ValueError("`story_text` must be a non‑empty string.")
    if not isinstance(language, str) or not language.strip():
        raise ValueError("`language` must be a non‑empty string.")
    if not (_MIN_SPEED <= float(speed) <= _MAX_SPEED):
        raise ValueError(f"`speed` must be between {_MIN_SPEED} and {_MAX_SPEED}.")
    
    output_dir_path = Path(output_dir).expanduser().resolve()
    if not output_dir_path.is_dir():
        raise ValueError(f"`output_dir` must be an existing directory: {output_dir_path}")

    # Split text into sentences
    sentence_pattern = re.compile(r'(?<=[.!?])\s+')
    sentences = [s.strip() for s in sentence_pattern.split(story_text) if s.strip()]
    
    if not sentences:
        raise ValueError("No sentences found in story_text.")

    _logger.info(f"Processing {len(sentences)} sentences with async TTS...")

    # Create temp directory for sentence audio files
    temp_dir = output_dir_path / f"temp_audio_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(exist_ok=True)

    # Process sentences in parallel using ThreadPoolExecutor
    loop = asyncio.get_event_loop()
    audio_files: List[tuple[int, str]] = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                generate_sentence_audio_sync,
                sentence,
                idx,
                language,
                voice,
                speed,
                output_format,
                temp_dir,
            )
            for idx, sentence in enumerate(sentences)
        ]
        
        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                _logger.error(f"TTS generation failed: {result}")
                raise SpeechGenerationError(f"Failed to generate audio: {result}")
            audio_files.append(result)

    # Sort by sentence index to maintain order
    audio_files.sort(key=lambda x: x[0])
    sorted_audio_paths = [path for _, path in audio_files]

    # Combine all audio files
    combined_audio_path = str(output_dir_path / f"story_{uuid.uuid4().hex}.{output_format}")
    
    # Simple concatenation - read all files and write combined
    with open(combined_audio_path, 'wb') as combined:
        for audio_path in sorted_audio_paths:
            with open(audio_path, 'rb') as audio_file:
                combined.write(audio_file.read())

    # Clean up temporary files
    for audio_path in sorted_audio_paths:
        try:
            os.remove(audio_path)
        except OSError:
            pass
    try:
        temp_dir.rmdir()
    except OSError:
        pass

    _logger.info(f"Combined audio saved to: {combined_audio_path}")
    return {"audio_file_path": combined_audio_path}


async def generate_story_with_streaming_tts(
    theme: str,
    language: str = "en",
    voice: str = "Aaliyah-PlayAI",
    speed: float = 1.0,
    output_format: Literal["mp3", "opus", "aac", "flac"] = "mp3",
    output_dir: str | os.PathLike = ".",
    max_workers: int = 5,
) -> Dict[str, Any]:
    """
    Generate a children's story with streaming LLM and async TTS processing.
    
    The LLM streams sentences as they are generated, and TTS processes each
    sentence asynchronously in parallel. All audio files are combined at the end.

    Args:
        theme: Story theme.
        language: Language code for TTS.
        voice: TTS voice identifier.
        speed: Speech speed multiplier.
        output_format: Audio format.
        output_dir: Output directory.
        max_workers: Max concurrent TTS workers.

    Returns:
        dict: Contains 'story_text' and 'audio_file_path'.
    """
    output_dir_path = Path(output_dir).expanduser().resolve()
    if not output_dir_path.is_dir():
        raise ValueError(f"`output_dir` must be an existing directory: {output_dir_path}")

    # Create temp directory for sentence audio files
    temp_dir = output_dir_path / f"temp_audio_{uuid.uuid4().hex[:8]}"
    temp_dir.mkdir(exist_ok=True)

    sentences: List[str] = []
    tts_tasks: List[asyncio.Task] = []
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=max_workers)

    print("📖 Streaming story generation with async TTS...")

    try:
        # Stream sentences from LLM and submit TTS tasks immediately
        for idx, sentence in enumerate(generate_children_story_streaming(theme)):
            sentences.append(sentence)
            print(f"  📝 Sentence {idx + 1}: {sentence[:50]}...")
            
            # Submit TTS task immediately for this sentence
            task = loop.run_in_executor(
                executor,
                generate_sentence_audio_sync,
                sentence,
                idx,
                language,
                voice,
                speed,
                output_format,
                temp_dir,
            )
            tts_tasks.append(task)

        print(f"\n⏳ Waiting for {len(tts_tasks)} TTS tasks to complete...")
        
        # Wait for all TTS tasks to complete
        results = await asyncio.gather(*tts_tasks, return_exceptions=True)
        
        audio_files: List[tuple[int, str]] = []
        for result in results:
            if isinstance(result, Exception):
                _logger.error(f"TTS generation failed: {result}")
                raise SpeechGenerationError(f"Failed to generate audio: {result}")
            audio_files.append(result)

        # Sort by sentence index to maintain order
        audio_files.sort(key=lambda x: x[0])
        sorted_audio_paths = [path for _, path in audio_files]

        # Combine all audio files
        combined_audio_path = str(output_dir_path / f"story_{uuid.uuid4().hex}.{output_format}")
        
        with open(combined_audio_path, 'wb') as combined:
            for audio_path in sorted_audio_paths:
                with open(audio_path, 'rb') as audio_file:
                    combined.write(audio_file.read())

        # Clean up temporary files
        for audio_path in sorted_audio_paths:
            try:
                os.remove(audio_path)
            except OSError:
                pass
        try:
            temp_dir.rmdir()
        except OSError:
            pass

        full_story = " ".join(sentences)
        
        return {
            "story_text": full_story,
            "audio_file_path": combined_audio_path,
        }

    finally:
        executor.shutdown(wait=False)

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("🚀 Running kids_story_agent with async TTS...")
    
    # 1. Generate a story theme
    print("📖 Generating story theme...")
    theme_result = generate_child_story_theme(seed="magic forest adventure")
    theme = theme_result["theme"]
    print(f"✨ Theme: {theme}\n")
    
    # 2. Generate story with streaming LLM + async TTS (faster!)
    print("✍️  Generating story with streaming + async TTS...")
    result = asyncio.run(generate_story_with_streaming_tts(
        theme=theme,
        language="en",
        voice="Aaliyah-PlayAI",
        speed=1.0,
        output_format="mp3",
        output_dir=".",
        max_workers=5,
    ))
    
    print(f"\n📚 Story:\n{result['story_text']}\n")
    print(f"🔊 Audio saved to: {result['audio_file_path']}")
    print("\n✅ Kids story agent completed successfully!")
