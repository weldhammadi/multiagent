"""
ToolAgent - Agent d'Outils complet.

Combine toutes les fonctionnalités:
- Recherche GitHub pour outils existants
- Génération via LLM (Groq API)
- Validation des réponses LLM
- Génération de fichiers (code source, metadata, .env, config)
"""

import os
import csv
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
from dotenv import load_dotenv
from groq import Groq, APIError, APIConnectionError, RateLimitError


class ToolAgent:
    """
    Agent complet pour la génération et recherche d'outils Python.
    
    Attributes:
        output_dir: Répertoire de sortie pour les fichiers générés
        enable_github_search: Active/désactive la recherche GitHub
        model: Modèle LLM à utiliser
        max_tokens: Limite de tokens en sortie
        temperature: Température de génération
    """
    
    def __init__(
        self,
        output_dir: str = "output",
        enable_github_search: bool = False,
        model: str = "openai/gpt-oss-120b",
        max_tokens: int = 8000,
        temperature: float = 0.1,
        github_timeout: int = 10,
        llm_timeout: int = 60
    ) -> None:
        """
        Initialise le ToolAgent.
        
        Args:
            output_dir: Chemin du dossier de sortie
            enable_github_search: Active la recherche GitHub avant génération LLM
            model: Modèle LLM à utiliser (défaut: openai/gpt-oss-120b)
            max_tokens: Limite de tokens en sortie
            temperature: Température de génération (plus bas = plus déterministe)
            github_timeout: Timeout pour les requêtes GitHub
            llm_timeout: Timeout pour les requêtes LLM
            
        Raises:
            RuntimeError: Si impossible de créer le dossier de sortie
        """
        # Chargement des variables .env
        load_dotenv()
        
        # Configuration sortie
        self.output_dir = Path(output_dir)
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise RuntimeError(
                f"Impossible de créer le dossier {output_dir}: {exc}"
            ) from exc
        
        # Configuration GitHub
        self.enable_github_search = enable_github_search
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_search_api_url = "https://api.github.com/search/repositories"
        self.github_timeout = github_timeout
        
        # Configuration LLM
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.llm_timeout = llm_timeout
        self._groq_client: Optional[Groq] = None
    
    # ==========================================================================
    #  PROPRIÉTÉS
    # ==========================================================================
    
    @property
    def groq_client(self) -> Groq:
        """
        Lazy loading du client Groq.
        
        Returns:
            Instance du client Groq
            
        Raises:
            RuntimeError: Si GROQ_API_KEY n'est pas définie
        """
        if self._groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            
            if not api_key:
                raise RuntimeError(
                    "Variable d'environnement GROQ_API_KEY manquante. "
                    "Configurez votre clé API dans .env"
                )
            
            try:
                self._groq_client = Groq(api_key=api_key)
            except Exception as exc:
                raise RuntimeError(
                    f"Impossible d'initialiser le client Groq: {exc}"
                ) from exc
        
        return self._groq_client
    
    # ==========================================================================
    #  MÉTHODES UTILITAIRES
    # ==========================================================================
    
    @staticmethod
    def load_file_content(file_path: Path) -> str:
        """
        Charge le contenu d'un fichier texte.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Contenu du fichier
            
        Raises:
            FileNotFoundError: Si fichier introuvable
            RuntimeError: Si erreur de lecture
        """
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"❌ Fichier introuvable: {file_path}") from exc
        except Exception as exc:
            raise RuntimeError(f"❌ Erreur lecture fichier {file_path}: {exc}") from exc
    
    @staticmethod
    def parse_llm_response(response: str) -> Dict[str, Any]:
        """
        Nettoie et parse le JSON brut renvoyé par le LLM.
        
        Args:
            response: Réponse brute du LLM
            
        Returns:
            Dictionnaire parsé avec 'source_code' et 'metadata'
            
        Raises:
            ValueError: Si JSON invalide ou structure incorrecte
        """
        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"❌ JSON invalide renvoyé par LLM: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("❌ La réponse LLM doit être un objet JSON")

        if "source_code" not in data or "metadata" not in data:
            raise ValueError("❌ Le JSON doit contenir 'source_code' ET 'metadata'")

        return data
    
    @staticmethod
    def extract_search_keywords(user_prompt: str) -> str:
        """
        Extrait les mots-clés à partir du prompt utilisateur.
        
        Args:
            user_prompt: Prompt de l'utilisateur
            
        Returns:
            Mots-clés extraits pour la recherche
        """
        lines = user_prompt.split("\n")
        keywords = ""

        for line in lines:
            if "Objectif" in line or "objectif" in line:
                if ":" in line:
                    keywords = line.split(":", 1)[1].strip()
                    keywords = keywords.replace("*", "")
                    break
        else:
            for line in lines:
                clean = line.strip().replace("*", "").replace("#", "")
                if clean and len(clean) > 10:
                    keywords = clean
                    break
            else:
                return "python utility tool"

        BAD_KEYWORDS = ["aucun", "pas trouvé", "non disponible", "n'a été"]
        if any(x in keywords.lower() for x in BAD_KEYWORDS):
            return "python utility tool"

        return keywords[:100]
    
    def _sanitize_tool_name(self, tool_name: str) -> str:
        """
        Nettoie le nom de l'outil pour un nom de fichier valide.
        
        Args:
            tool_name: Nom brut de l'outil
            
        Returns:
            Nom nettoyé (snake_case, alphanumerique + underscore)
        """
        sanitized = "".join(
            c if c.isalnum() or c == "_" else "_"
            for c in tool_name.lower()
        )
        
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        
        sanitized = sanitized.strip("_")
        
        if not sanitized:
            sanitized = "tool"
        
        return sanitized
    
    # ==========================================================================
    #  VALIDATION
    # ==========================================================================
    
    @staticmethod
    def validate_tool_response(tool_data: Dict[str, Any]) -> List[str]:
        """
        Valide la structure complète d'un outil généré.
        
        Args:
            tool_data: Dictionnaire contenant 'source_code' et 'metadata'
            
        Returns:
            Liste des erreurs de validation (vide si valide)
        """
        errors: List[str] = []
        
        # Validation clés principales
        if "source_code" not in tool_data:
            errors.append("Clé 'source_code' manquante")
        elif not isinstance(tool_data["source_code"], str):
            errors.append("'source_code' doit être une string")
        elif len(tool_data["source_code"].strip()) == 0:
            errors.append("'source_code' est vide")
        
        if "metadata" not in tool_data:
            errors.append("Clé 'metadata' manquante")
            return errors
        
        metadata = tool_data["metadata"]
        
        if not isinstance(metadata, dict):
            errors.append("'metadata' doit être un objet JSON")
            return errors
        
        # Validation champs metadata obligatoires
        required_fields = ["nom", "inputs", "output", "description"]
        
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Champ obligatoire manquant dans metadata: '{field}'")
        
        # Validation types metadata
        if "nom" in metadata:
            if not isinstance(metadata["nom"], str):
                errors.append("metadata.nom doit être une string")
            elif len(metadata["nom"].strip()) == 0:
                errors.append("metadata.nom ne peut pas être vide")
        
        if "inputs" in metadata:
            if not isinstance(metadata["inputs"], dict):
                errors.append("metadata.inputs doit être un objet (dict)")
        
        if "output" in metadata:
            if not isinstance(metadata["output"], str):
                errors.append("metadata.output doit être une string")
        
        if "description" in metadata:
            if not isinstance(metadata["description"], str):
                errors.append("metadata.description doit être une string")
            elif len(metadata["description"].strip()) == 0:
                errors.append("metadata.description ne peut pas être vide")
        
        # Validation champs optionnels
        if "schema_output" in metadata:
            if not isinstance(metadata["schema_output"], dict):
                errors.append("metadata.schema_output doit être un objet (dict)")
        
        if "dependencies" in metadata:
            if not isinstance(metadata["dependencies"], list):
                errors.append("metadata.dependencies doit être une liste")
            else:
                for dep in metadata["dependencies"]:
                    if not isinstance(dep, str):
                        errors.append(
                            f"metadata.dependencies contient un élément non-string: {dep}"
                        )
                        break
        
        if "env_vars" in metadata:
            if not isinstance(metadata["env_vars"], list):
                errors.append("metadata.env_vars doit être une liste")
            else:
                for var in metadata["env_vars"]:
                    if not isinstance(var, str):
                        errors.append(
                            f"metadata.env_vars contient un élément non-string: {var}"
                        )
                        break
        
        return errors
    
    # ==========================================================================
    #  GITHUB SEARCH
    # ==========================================================================
    
    def _get_github_headers(self) -> Dict[str, str]:
        """
        Génère les headers pour les requêtes GitHub.
        
        Returns:
            Dictionnaire de headers HTTP
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Python-ToolAgent"
        }
        
        if self.github_token:
            headers["Authorization"] = f"Bearer {self.github_token}"
        
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
        search_query = f"{query} language:{language}"
        
        params = {
            "q": search_query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results
        }
        
        try:
            response = requests.get(
                self.github_search_api_url,
                headers=self._get_github_headers(),
                params=params,
                timeout=self.github_timeout
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
        """
        readme_url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        
        try:
            response = requests.get(
                readme_url,
                headers={
                    **self._get_github_headers(),
                    "Accept": "application/vnd.github.v3.raw"
                },
                timeout=self.github_timeout
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
    
    def clone_repository(self, clone_url: str, destination: Path) -> bool:
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
            return False
        except Exception:
            return False
    
    def save_search_results_to_csv(
        self,
        results: List[Dict[str, Any]],
        csv_path: Optional[Path] = None
    ) -> Path:
        """
        Sauvegarde les résultats de recherche dans un CSV.
        
        Args:
            results: Liste des repos trouvés
            csv_path: Chemin du fichier CSV (optionnel)
            
        Returns:
            Chemin du fichier CSV créé
            
        Raises:
            RuntimeError: Si erreur d'écriture
        """
        if csv_path is None:
            csv_path = self.output_dir / "github_search_results.csv"
        
        if not results:
            return csv_path
        
        try:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                fieldnames = [
                    "name", "full_name", "description", "html_url",
                    "clone_url", "stars", "language", "updated_at", "readme_preview"
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    writer.writerow(result)
            
            return csv_path
                    
        except Exception as exc:
            raise RuntimeError(
                f"Erreur sauvegarde CSV {csv_path}: {exc}"
            ) from exc
    
    def _search_github(self, keywords: str) -> List[Dict[str, Any]]:
        """
        Effectue une recherche GitHub complète avec affichage.
        
        Args:
            keywords: Mots-clés de recherche
            
        Returns:
            Liste des repositories trouvés
        """
        print(f"\n🔍 Recherche sur GitHub avec: '{keywords}'")

        try:
            results = self.search_repositories(keywords, language="python", max_results=5)
        except RuntimeError as exc:
            print(f"⚠️ Erreur API GitHub: {exc}")
            return []

        if not results:
            print("ℹ️ Aucun repository pertinent trouvé.")
            return []

        print(f"✓ {len(results)} repository(s) trouvé(s)")

        for idx, repo in enumerate(results):
            print(f"📦 {idx+1}. {repo['full_name']} ({repo['stars']} ⭐)")

            owner_repo = repo["full_name"].split("/")
            if len(owner_repo) == 2:
                owner, name = owner_repo
                readme = self.get_readme(owner, name)
                preview = readme[:120].replace("\n", " ") if readme else "README indisponible"
                repo["readme_preview"] = preview
                print(f"    📄 README: {preview}")

        self.save_search_results_to_csv(results)
        print("💾 Historique sauvegardé dans: output/github_search_results.csv")

        return results

    def _clone_best_repository(self, repos: List[Dict[str, Any]]) -> bool:
        """
        Clone le meilleur repository trouvé.
        
        Args:
            repos: Liste des repositories
            
        Returns:
            True si clone réussi, False sinon
        """
        best = max(repos, key=lambda r: r["stars"])
        print(f"\n🔥 Clone du repo le plus pertinent: {best['full_name']} ({best['stars']} ⭐)")

        dest = self.output_dir / "cloned_repos" / best["name"]
        success = self.clone_repository(best["clone_url"], dest)

        if success:
            print(f"🎉 Repo cloné dans: {dest}")
            return True

        print("⚠️ Clone échoué (git absent ou timeout)")
        return False
    
    # ==========================================================================
    #  LLM GENERATION
    # ==========================================================================
    
    def call_llm(
        self,
        context: str,
        user_request: str,
        timeout: Optional[int] = None
    ) -> str:
        """
        Génère une réponse via le LLM Groq.
        
        Args:
            context: Contexte permanent avec règles strictes
            user_request: Demande spécifique de l'utilisateur
            timeout: Timeout en secondes (utilise self.llm_timeout si None)
            
        Returns:
            Réponse brute du LLM
            
        Raises:
            RuntimeError: Si erreur API, timeout ou rate limit
        """
        if timeout is None:
            timeout = self.llm_timeout
        
        messages = [
            {"role": "system", "content": context},
            {"role": "user", "content": user_request}
        ]
        
        try:
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                timeout=timeout
            )
            
            if not response.choices:
                raise RuntimeError("Réponse LLM vide - aucun choix retourné")
            
            content = response.choices[0].message.content
            
            if not content:
                raise RuntimeError("Contenu de réponse LLM vide")
            
            return content
            
        except RateLimitError as exc:
            raise RuntimeError(
                f"Limite de débit Groq atteinte. Réessayez dans quelques secondes. "
                f"Détails: {exc}"
            ) from exc
        
        except APIConnectionError as exc:
            raise RuntimeError(
                f"Erreur de connexion à l'API Groq. Vérifiez votre réseau. "
                f"Détails: {exc}"
            ) from exc
        
        except APIError as exc:
            raise RuntimeError(
                f"Erreur API Groq: {exc}"
            ) from exc
        
        except Exception as exc:
            raise RuntimeError(
                f"Erreur inattendue lors de l'appel Groq: {type(exc).__name__}: {exc}"
            ) from exc
    
    # ==========================================================================
    #  FILE GENERATION
    # ==========================================================================
    
    def _create_env_file(self, tool_name: str, env_vars: List[str]) -> Path:
        """
        Crée un fichier .env avec les variables nécessaires (clés vides).
        
        Args:
            tool_name: Nom de l'outil
            env_vars: Liste des variables d'environnement requises
            
        Returns:
            Chemin du fichier .env créé
            
        Raises:
            RuntimeError: Si erreur d'écriture fichier
        """
        clean_name = self._sanitize_tool_name(tool_name)
        env_file = self.output_dir / f"{clean_name}.env"
        
        if env_file.exists():
            print(f"⚠️  Fichier {env_file.name} existe déjà, il ne sera pas écrasé")
            return env_file
        
        env_content = "\n".join(f"{var}=" for var in env_vars) + "\n"
        
        try:
            env_file.write_text(env_content, encoding="utf-8")
            print(f"📝 Fichier {env_file.name} créé (à remplir manuellement)")
            return env_file
        except Exception as exc:
            raise RuntimeError(
                f"Erreur lors de la création du fichier .env {env_file}: {exc}"
            ) from exc
    
    def _create_config_files(self, tool_name: str, config_files: List[str]) -> Dict[str, Path]:
        """
        Crée des fichiers JSON de configuration vides.
        
        Args:
            tool_name: Nom de l'outil
            config_files: Liste des noms de fichiers JSON à créer
            
        Returns:
            Dictionnaire {nom_fichier: Path} des fichiers créés
            
        Raises:
            RuntimeError: Si erreur d'écriture fichier
        """
        clean_name = self._sanitize_tool_name(tool_name)
        created_files = {}
        
        for config_name in config_files:
            if config_name.endswith(".json"):
                config_name = config_name[:-5]
            
            config_file = self.output_dir / f"{clean_name}_{config_name}.json"
            
            if config_file.exists():
                print(f"⚠️  Fichier {config_file.name} existe déjà, il ne sera pas écrasé")
                created_files[config_name] = config_file
                continue
            
            try:
                config_file.write_text("{}\n", encoding="utf-8")
                print(f"📝 Fichier {config_file.name} créé (à remplir manuellement)")
                created_files[config_name] = config_file
            except Exception as exc:
                raise RuntimeError(
                    f"Erreur lors de la création du fichier config {config_file}: {exc}"
                ) from exc
        
        return created_files
    
    def save_tool(
        self,
        tool_name: str,
        source_code: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sauvegarde l'outil et ses métadonnées.
        
        Args:
            tool_name: Nom de l'outil
            source_code: Code Python source
            metadata: Métadonnées JSON de l'outil
            
        Returns:
            Dictionnaire avec chemins des fichiers créés:
                - 'python': chemin du fichier .py
                - 'metadata': chemin du fichier .json
                - 'env' (optionnel): chemin du fichier .env
                - 'config_files' (optionnel): dict des fichiers JSON créés
                
        Raises:
            RuntimeError: Si erreur d'écriture fichier
        """
        clean_name = self._sanitize_tool_name(tool_name)
        
        python_file = self.output_dir / f"{clean_name}.py"
        metadata_file = self.output_dir / f"{clean_name}_metadata.json"
        
        try:
            python_file.write_text(source_code, encoding="utf-8")
        except Exception as exc:
            raise RuntimeError(
                f"Erreur lors de la sauvegarde du fichier Python {python_file}: {exc}"
            ) from exc
        
        try:
            metadata_file.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as exc:
            raise RuntimeError(
                f"Erreur lors de la sauvegarde des métadonnées {metadata_file}: {exc}"
            ) from exc
        
        result = {
            "python": python_file,
            "metadata": metadata_file
        }
        
        env_vars = metadata.get("env_vars", [])
        if env_vars and isinstance(env_vars, list) and len(env_vars) > 0:
            env_file = self._create_env_file(tool_name, env_vars)
            result["env"] = env_file
        
        config_files = metadata.get("config_files", [])
        if config_files and isinstance(config_files, list) and len(config_files) > 0:
            created_configs = self._create_config_files(tool_name, config_files)
            result["config_files"] = created_configs
        
        return result
    
    # ==========================================================================
    #  MAIN METHODS
    # ==========================================================================
    
    def generate_tool(
        self,
        user_prompt: str,
        context_file: Optional[Path] = None,
        save_files: bool = True
    ) -> Dict[str, Any]:
        """
        Génère un outil via LLM et optionnellement le sauvegarde.
        
        Args:
            user_prompt: Demande de l'utilisateur
            context_file: Fichier de contexte (défaut: prompts/tools_context.txt)
            save_files: Si True, sauvegarde les fichiers individuels (défaut: True)
                       Mettre à False quand appelé par l'orchestrateur
            
        Returns:
            Dictionnaire avec 'source_code', 'metadata' et 'files' (si save_files=True)
            
        Raises:
            RuntimeError: Si erreur de génération
            ValueError: Si validation échoue
        """
        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("⚠️ Variable GROQ_API_KEY manquante dans .env")
        
        if context_file is None:
            context_file = Path("prompts/tools_context.txt")
        
        context = self.load_file_content(context_file)
        response = self.call_llm(context=context, user_request=user_prompt)
        
        tool_data = self.parse_llm_response(response)
        errors = self.validate_tool_response(tool_data)
        
        if errors:
            raise ValueError(f"❌ Erreurs de validation tool : {errors}")
        
        result = {
            "source_code": tool_data["source_code"],
            "metadata": tool_data["metadata"]
        }
        
        # Sauvegarder uniquement si demandé (pas quand appelé par orchestrateur)
        if save_files:
            name = tool_data["metadata"].get("nom", "tool")
            files = self.save_tool(name, tool_data["source_code"], tool_data["metadata"])
            result["files"] = files
        
        return result
    
    def run(
        self,
        user_prompt: Optional[str] = None,
        prompt_file: Optional[Path] = None,
        context_file: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Exécute le workflow complet de l'agent.
        
        Workflow:
        1. Recherche sur GitHub si activé
        2. Si trouvé → Clone + CSV + Arrêt
        3. Sinon → Génération via LLM
        
        Args:
            user_prompt: Prompt utilisateur (priorité sur prompt_file)
            prompt_file: Fichier contenant le prompt (défaut: prompts/example_prompt.txt)
            context_file: Fichier de contexte LLM (défaut: prompts/tools_context.txt)
            
        Returns:
            Dictionnaire avec résultats:
                - 'source': 'github' ou 'llm'
                - 'data': données de l'outil généré ou cloné
                
        Raises:
            RuntimeError: Si erreur d'exécution
            ValueError: Si validation échoue
        """
        print("🚀 ToolAgent - Génération d'outils Python")
        if self.enable_github_search:
            print("🔍 Recherche GitHub : ACTIVÉE")
        else:
            print("⏸️  Recherche GitHub : DÉSACTIVÉE (génération directe)")
        print("=" * 60)
        
        # Chargement du prompt
        if user_prompt is None:
            if prompt_file is None:
                prompt_file = Path("prompts/example_prompt.txt")
            user_prompt = self.load_file_content(prompt_file)
        
        # Phase 1: GitHub (si activé)
        if self.enable_github_search:
            keywords = self.extract_search_keywords(user_prompt)
            results = self._search_github(keywords)
            
            if results and self._clone_best_repository(results):
                print("\n🎉 Outil trouvé sur GitHub. Fin.")
                return {
                    "source": "github",
                    "data": {
                        "repositories": results,
                        "cloned": results[0] if results else None
                    }
                }
        
        # Phase 2: LLM
        if self.enable_github_search:
            print("\n⚙️ Aucun outil trouvé. Génération via LLM...")
        else:
            print("\n⚙️ Génération directe via LLM...")
        
        tool_result = self.generate_tool(user_prompt, context_file)
        
        print("\n🎉 Outil généré par LLM !")
        print(f"📌 {tool_result['files']['python']}")
        print(f"📌 {tool_result['files']['metadata']}")
        
        if "env" in tool_result["files"]:
            print(f"🔐 {tool_result['files']['env']} (⚠️  À remplir manuellement)")
        
        if "config_files" in tool_result["files"]:
            for config_name, config_path in tool_result["files"]["config_files"].items():
                print(f"⚙️  {config_path} (⚠️  À remplir manuellement)")
        
        return {
            "source": "llm",
            "data": tool_result
        }


# ==========================================================================
#  MAIN
# ==========================================================================

if __name__ == "__main__":
    # Exemple d'utilisation
    agent = ToolAgent(
        output_dir="output",
        enable_github_search=False  # Mettre à True pour activer GitHub
    )
    
    result = agent.run()
    print(f"\n✅ Source: {result['source']}")
