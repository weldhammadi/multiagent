"""
Auto-generated agent by Orchestrator.
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()


def generate_children_story(topic: str) -> Dict[str, Any]:
    """
    Generate a short, engaging children's story based on a given topic using the
    Groq LLM (model ``openai/gpt-oss-120b``).

    The function validates the input, retrieves the Groq API key from the
    environment, calls the model with a carefully crafted prompt and returns the
    story text.

    Args:
        topic: A non‑empty string describing the theme, character, or setting of
               the desired story (e.g. ``"a brave rabbit"``, ``"the magic forest"``).

    Returns:
        Dict[str, Any]: A dictionary containing the generated story.
            - ``story`` (str): The full text of the children's story produced by
              the LLM.

    Raises:
        ValueError: If ``topic`` is not a non‑empty string or the ``GROQ_API_KEY``
                    environment variable is missing.
        RuntimeError: If the request to the Groq API fails for any reason.
    """
    # Step 1 – Input validation
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("`topic` must be a non‑empty string.")

    # Step 2 – Retrieve API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Environment variable `GROQ_API_KEY` is not set.")

    # Step 3 – Initialise Groq client (only the api_key is passed)
    try:
        groq_client = Groq(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise Groq client: {exc}") from exc

    # Step 4 – Build the prompt
    system_message = (
        "You are a creative children's author. Write vivid, age‑appropriate "
        "stories that spark imagination and convey gentle lessons."
    )
    user_message = (
        f"Write a short, engaging children's story (about 200‑300 words) about: "
        f"{topic.strip()}."
    )

    # Step 5 – Call the LLM
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.6,
            max_tokens=500,
        )
    except Exception as exc:
        raise RuntimeError(f"Groq API request failed: {exc}") from exc

    # Step 6 – Extract the story text
    try:
        story_text: str = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Unexpected response format from Groq API.") from exc

    # Step 7 – Return the result
    return {"story": story_text}


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Running my_agent...")
    # TODO: Implement main workflow here
    # Available functions:
    # - generate_children_story()
    # - generated_function()  # placeholder for future implementation
    pass