import os
import json
from typing import Any, Dict, List
import requests


def get_users() -> List[Dict[str, Any]]:
    """Récupère la liste des utilisateurs depuis l'API JSONPlaceholder.

    Cette fonction effectue une requête GET vers
    ``https://jsonplaceholder.typicode.com/users`` avec un timeout de 10
    secondes et retourne le corps de la réponse décodé en JSON.

    Returns:
        List[Dict[str, Any]]: La collection d'utilisateurs telle que fournie
        par l'API.

    Raises:
        RuntimeError: Si la requête échoue (problème réseau, statut HTTP != 200,
        ou impossibilité de décoder la réponse JSON).
    """
    url = "https://jsonplaceholder.typicode.com/users"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            raise RuntimeError(
                f"Échec de la requête HTTP, statut {response.status_code}"
            )
        return response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Erreur réseau lors de la récupération des utilisateurs: {exc}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Impossible de décoder la réponse JSON: {exc}")
