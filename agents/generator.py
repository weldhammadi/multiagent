"""
Générateur de fichiers pour les outils Python.

Sauvegarde le code source et les métadonnées dans des fichiers structurés.
"""

import json
from pathlib import Path
from typing import Dict, Any


class ToolGenerator:
    """
    Générateur de fichiers pour outils Python utilitaires.
    
    Attributes:
        output_dir: Répertoire de sortie pour les fichiers générés
    """
    
    def __init__(self, output_dir: Path) -> None:
        """
        Initialise le générateur.
        
        Args:
            output_dir: Chemin du dossier de sortie
            
        Raises:
            RuntimeError: Si impossible de créer le dossier
        """
        self.output_dir = output_dir
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise RuntimeError(
                f"Impossible de créer le dossier {output_dir}: {exc}"
            ) from exc
    
    def _sanitize_tool_name(self, tool_name: str) -> str:
        """
        Nettoie le nom de l'outil pour un nom de fichier valide.
        
        Args:
            tool_name: Nom brut de l'outil
            
        Returns:
            Nom nettoyé (snake_case, alphanumerique + underscore)
        """
        # Remplacement caractères non valides
        sanitized = "".join(
            c if c.isalnum() or c == "_" else "_"
            for c in tool_name.lower()
        )
        
        # Suppression underscores multiples
        while "__" in sanitized:
            sanitized = sanitized.replace("__", "_")
        
        # Suppression underscores début/fin
        sanitized = sanitized.strip("_")
        
        # Fallback si vide
        if not sanitized:
            sanitized = "tool"
        
        return sanitized
    
    def _create_env_file(self, tool_name: str, env_vars: list) -> Path:
        """
        Crée un fichier .env avec les variables nécessaires (clés vides).
        
        Args:
            tool_name: Nom de l'outil
            env_vars: Liste des variables d'environnement requises
            
        Returns:
            Chemin du fichier .env créé (ou None si déjà existant)
            
        Raises:
            RuntimeError: Si erreur d'écriture fichier
        """
        clean_name = self._sanitize_tool_name(tool_name)
        env_file = self.output_dir / f"{clean_name}.env"
        
        # Ne jamais écraser un fichier existant
        if env_file.exists():
            print(f"⚠️  Fichier {env_file.name} existe déjà, il ne sera pas écrasé")
            return env_file
        
        # Génération du contenu .env (clés vides uniquement)
        env_content = "\n".join(f"{var}=" for var in env_vars)
        env_content += "\n"  # Ligne vide finale
        
        try:
            env_file.write_text(env_content, encoding="utf-8")
            print(f"📝 Fichier {env_file.name} créé (à remplir manuellement)")
            return env_file
        except Exception as exc:
            raise RuntimeError(
                f"Erreur lors de la création du fichier .env {env_file}: {exc}"
            ) from exc
    
    def _create_config_files(self, tool_name: str, config_files: list) -> Dict[str, Path]:
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
            # Nettoyage du nom (enlever .json si présent)
            if config_name.endswith(".json"):
                config_name = config_name[:-5]
            
            config_file = self.output_dir / f"{clean_name}_{config_name}.json"
            
            # Ne jamais écraser un fichier existant
            if config_file.exists():
                print(f"⚠️  Fichier {config_file.name} existe déjà, il ne sera pas écrasé")
                created_files[config_name] = config_file
                continue
            
            # Création d'un JSON vide
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
        # Nettoyage nom
        clean_name = self._sanitize_tool_name(tool_name)
        
        # Chemins fichiers principaux
        python_file = self.output_dir / f"{clean_name}.py"
        metadata_file = self.output_dir / f"{clean_name}_metadata.json"
        
        # Sauvegarde code Python
        try:
            python_file.write_text(source_code, encoding="utf-8")
        except Exception as exc:
            raise RuntimeError(
                f"Erreur lors de la sauvegarde du fichier Python {python_file}: {exc}"
            ) from exc
        
        # Sauvegarde metadata JSON
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
        
        # === NOUVEAUTÉ : Création fichier .env si nécessaire ===
        env_vars = metadata.get("env_vars", [])
        if env_vars and isinstance(env_vars, list) and len(env_vars) > 0:
            env_file = self._create_env_file(tool_name, env_vars)
            result["env"] = env_file
        
        # === NOUVEAUTÉ : Création fichiers JSON config si nécessaire ===
        config_files = metadata.get("config_files", [])
        if config_files and isinstance(config_files, list) and len(config_files) > 0:
            created_configs = self._create_config_files(tool_name, config_files)
            result["config_files"] = created_configs
        
        return result