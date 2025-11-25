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
    
    def save_tool(
        self,
        tool_name: str,
        source_code: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Path]:
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
                
        Raises:
            RuntimeError: Si erreur d'écriture fichier
        """
        # Nettoyage nom
        clean_name = self._sanitize_tool_name(tool_name)
        
        # Chemins fichiers
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
        
        return {
            "python": python_file,
            "metadata": metadata_file
        }