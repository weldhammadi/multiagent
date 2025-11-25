"""
Validateur de réponses LLM pour l'Agent d'Outils.

Vérifie la structure et la cohérence des outils générés.
"""

from typing import Dict, Any, List


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
        return errors  # Arrêt si pas de metadata
    
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