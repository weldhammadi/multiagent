"""
Recherche d'outils existants sur GitHub.

Module pour chercher, analyser et cloner des repositories GitHub.
"""

import os
import csv
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests


class GitHubSearcher:
    """
    Chercheur d'outils Python sur GitHub.
    
    Attributes:
        token: Token GitHub pour authentification (optionnel)
        search_api_url: URL de l'API de recherche GitHub
        timeout: Timeout pour les requêtes HTTP
    """
    
    def __init__(self, timeout: int = 10) -> None:
        """
        Initialise le chercheur GitHub.
        
        Args:
            timeout: Timeout en secondes pour les requêtes
        """
        self.token = os.getenv("GITHUB_TOKEN")
        self.search_api_url = "https://api.github.com/search/repositories"
        self.timeout = timeout
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Génère les headers pour les requêtes GitHub.
        
        Returns:
            Dictionnaire de headers HTTP
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Python-Agent-Outils"
        }
        
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        return headers
    
    def search_repositories(
        self,
        query: str,
        language: str = "python",
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recherche des repositories sur GitHub.
        
        Args:
            query: Mots-clés de recherche
            language: Langage de programmation (défaut: python)
            max_results: Nombre max de résultats
            
        Returns:
            Liste de dictionnaires avec les infos des repos trouvés
            
        Raises:
            RuntimeError: Si erreur API ou réseau
        """
        # Construction query
        search_query = f"{query} language:{language}"
        
        params = {
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results
        }
        
        try:
            response = requests.get(
                self.search_api_url,
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                f"Timeout lors de la recherche GitHub: {exc}"
            ) from exc
        
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Erreur lors de la recherche GitHub: {exc}"
            ) from exc
        
        data = response.json()
        items = data.get("items", [])
        
        results = []
        for item in items:
            results.append({
                "name": item.get("name", ""),
                "full_name": item.get("full_name", ""),
                "description": item.get("description", ""),
                "html_url": item.get("html_url", ""),
                "clone_url": item.get("clone_url", ""),
                "stars": item.get("stargazers_count", 0),
                "language": item.get("language", ""),
                "updated_at": item.get("updated_at", "")
            })
        
        return results
    
    def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        Récupère le contenu du README d'un repository.
        
        Args:
            owner: Propriétaire du repo
            repo: Nom du repo
            
        Returns:
            Contenu du README en texte brut (None si erreur)
            
        Raises:
            RuntimeError: Si erreur API grave
        """
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        
        try:
            response = requests.get(
                readme_url,
                headers={
                    **self._get_headers(),
                    "Accept": "application/vnd.github.v3.raw"
                },
                timeout=self.timeout
            )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            return response.text
            
        except requests.exceptions.Timeout:
            return None
        
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(
                f"Erreur récupération README {owner}/{repo}: {exc}"
            ) from exc
    
    def clone_repository(
        self,
        clone_url: str,
        destination: Path
    ) -> bool:
        """
        Clone un repository GitHub localement.
        
        Args:
            clone_url: URL de clone du repo
            destination: Chemin de destination
            
        Returns:
            True si succès, False sinon
        """
        try:
            destination.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                ["git", "clone", clone_url, str(destination)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            return False
        
        except FileNotFoundError:
            # Git n'est pas installé
            return False
        
        except Exception:
            return False
    
    def save_results_to_csv(
        self,
        results: List[Dict[str, Any]],
        csv_path: Path
    ) -> None:
        """
        Sauvegarde les résultats de recherche dans un CSV.
        
        Args:
            results: Liste des repos trouvés
            csv_path: Chemin du fichier CSV
            
        Raises:
            RuntimeError: Si erreur d'écriture
        """
        if not results:
            return
        
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "name",
                    "full_name",
                    "description",
                    "html_url",
                    "clone_url",
                    "stars",
                    "language",
                    "updated_at",
                    "readme_preview"
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    writer.writerow(result)
                    
        except Exception as exc:
            raise RuntimeError(
                f"Erreur sauvegarde CSV {csv_path}: {exc}"
            ) from exc