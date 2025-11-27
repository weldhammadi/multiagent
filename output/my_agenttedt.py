"""Auto-generated agent by Orchestrator."""

import os
import json
import requests
import sys
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()


def read_csv(file_path: str) -> str:
    """Read a CSV file and return its raw content as a string.

    Args:
        file_path (str): Path to the CSV file.

    Returns:
        str: Raw content of the CSV file.

    Raises:
        RuntimeError: If the file does not exist or cannot be read.
    """
    if not os.path.isfile(file_path):
        raise RuntimeError(f"Le fichier CSV '{file_path}' est introuvable.")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Erreur lors de la lecture du fichier CSV: {e}")


def analyze_csv_insights(csv_content: str) -> Dict[str, Any]:
    """
    Analyse le contenu d'un fichier CSV à l'aide du modèle LLM
    ``openai/gpt-oss-120b`` via l'API Groq et renvoie des insights
    concis et basés sur les données.

    Le modèle agit comme un analyste de données : il identifie les
    tendances, les valeurs remarquables, les corrélations éventuelles
    et toute information pertinente qui peut être extraite du tableau.

    Args:
        csv_content (str): Chaîne contenant le texte complet du CSV.
            Le texte doit être non‑vide et encodé en UTF‑8. Aucun
            pré‑traitement (par ex. suppression d’en‑têtes) n’est requis ;
            le LLM gère le format CSV.

    Returns:
        Dict[str, Any]: Dictionnaire contenant une seule clé :
            - ``insights`` (str) : texte généré par le LLM résumant les
              observations majeures du jeu de données.

    Raises:
        ValueError: Si ``csv_content`` n'est pas une chaîne non vide ou si
            la variable d'environnement ``GROQ_API_KEY`` est absente.
        RuntimeError: En cas d'échec de l'appel à l'API Groq ou de réponse
            inattendue du modèle.
    """
    # Step 1 – Validation des entrées
    if not isinstance(csv_content, str) or not csv_content.strip():
        raise ValueError("csv_content must be a non‑empty string")

    # Step 2 – Récupération de la clé API
    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")

    # Step 3 – Instanciation du client Groq
    try:
        groq_client = Groq(api_key=api_key)
    except Exception as exc:
        raise RuntimeError(f"Failed to initialise Groq client: {exc}") from exc

    # Step 4 – Construction du prompt
    system_message = (
        "You are an expert data analyst. Analyze the provided CSV data and "
        "produce concise, data‑driven insights. Highlight key trends, "
        "outliers, correlations and any actionable information."
    )
    user_message = f"CSV data:\n{csv_content}"

    # Step 5 – Appel du modèle LLM
    try:
        llm_response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            temperature=0.5,
            max_tokens=1024,
        )
    except Exception as exc:
        raise RuntimeError(f"Groq API request failed: {exc}") from exc

    # Step 6 – Extraction du texte de réponse
    try:
        result_text: str = llm_response.choices[0].message.content.strip()
    except (AttributeError, IndexError) as exc:
        raise RuntimeError(
            "Unexpected response structure from Groq API"
        ) from exc

    # Step 7 – Retour du dictionnaire conforme à la spécification
    return {"insights": result_text}


if __name__ == "__main__":
    # Ensure stdout can handle UTF‑8 characters on Windows
    if sys.platform.startswith("win"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("Running my_agenttedt...")
    # TODO: Implement main workflow here
    # Available functions:
    # - read_csv()
    # - analyze_csv_insights()
    pass