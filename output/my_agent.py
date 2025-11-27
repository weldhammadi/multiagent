import os
import json
import sys
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()


def fetch_weather(location: str) -> Dict:
    """Retrieve current weather data for a given location using the OpenWeatherMap API.

    Args:
        location (str): Name of the city or location (e.g., "Paris,FR").

    Returns:
        Dict: Parsed JSON response containing weather information.

    Raises:
        RuntimeError: If the required environment variable is missing, the request fails,
            or the API returns a non‑successful status code.
    """
    api_key: str | None = os.getenv("OPENWEATHER_API_KEY")
    if api_key is None:
        raise RuntimeError("La variable d'environnement OPENWEATHER_API_KEY est manquante.")

    endpoint: str = "https://api.openweathermap.org/data/2.5/weather"
    params: Dict[str, str] = {
        "q": location,
        "appid": api_key,
        "units": "metric",
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
    except requests.RequestException as exc:
        raise RuntimeError(f"Erreur lors de la requête vers OpenWeatherMap: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"OpenWeatherMap a renvoyé le statut {response.status_code}: {response.text}"
        )

    try:
        weather_data: Dict = response.json()
    except ValueError as exc:
        raise RuntimeError("Impossible de décoder la réponse JSON du service météo.") from exc

    return weather_data


def generate_weather_summary(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a natural‑language summary of the provided weather data using the
    ``openai/gpt-oss-120b`` model via the Groq API.

    The function validates the input, builds a concise prompt, calls the LLM,
    and returns the generated summary.

    Args:
        weather_data (Dict[str, Any]): A dictionary containing weather
            information (e.g., temperature, humidity, wind, forecast). The
            dictionary must not be empty and must be JSON‑serialisable.

    Returns:
        Dict[str, Any]: A dictionary with a single key:
            - ``summary`` (str): The natural‑language summary produced by the
              model.

    Raises:
        ValueError: If ``weather_data`` is not a dict, is empty, or cannot be
            JSON‑serialised.
        RuntimeError: If the Groq API call fails or returns an unexpected
            response.
    """
    if not isinstance(weather_data, dict):
        raise ValueError("weather_data must be a dictionary.")
    if not weather_data:
        raise ValueError("weather_data must not be empty.")

    try:
        weather_json: str = json.dumps(weather_data, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as exc:
        raise ValueError("weather_data contains non‑serialisable values.") from exc

    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables.")

    groq_client = Groq(api_key=api_key)

    system_message = (
        "You are a concise and friendly weather analyst. "
        "Summarise the provided weather data in natural language, "
        "highlighting the most relevant details for a general audience."
    )
    user_message = f"Weather data:\n{weather_json}\n\nProvide a short summary."

    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=300,
        )
    except Exception as exc:
        raise RuntimeError("Failed to obtain a response from Groq API.") from exc

    try:
        summary: str = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError("Unexpected response structure from Groq API.") from exc

    return {"summary": summary}


if __name__ == '__main__':
    # Ensure stdout can handle Unicode characters on Windows
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Fallback for environments where reconfigure is unavailable

    print("🚀 Running my_agent...")
    # TODO: Implement main workflow here
    # Available functions:
    # - fetch_weather()
    # - generate_weather_summary()
    pass