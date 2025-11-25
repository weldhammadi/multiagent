"""Script de test: génère un agent en mode automatique (sans appel réseau LLM).

Ce script instancie `LLMServer`, remplace la méthode d'analyse par une
implémentation factice et lance `process_request` avec `auto_approve=True`.

Ne réalise pas de déploiement externe.
"""
from pathlib import Path
import json
import os
import sys

# Ajouter le répertoire racine du projet au chemin d'import pour permettre
# d'importer les modules situés à la racine lorsque ce script est exécuté
# depuis `tools/`.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Charger .env si nécessaire
from dotenv import load_dotenv
load_dotenv()

from llm_server_core import LLMServer, AgentRequirements, AgentType


def fake_analyze(user_request: str) -> AgentRequirements:
    """Retourne des requirements factices pour éviter des appels réseau."""
    return AgentRequirements(
        role="agent_de_test",
        description="Agent généré pour test local (aucun appel LLM).",
        agent_type=AgentType.CUSTOM,
        objectives=["Tester la génération de fichiers"],
        tools_needed=[],
        models_needed=[],
        constraints=[],
        input_format="dict",
        output_format="dict"
    )


def main():
    project_root = Path('.')

    # Instancier le serveur (utilise GROQ_API_KEY si présent)
    server = LLMServer(project_root)

    # Remplacer l'analyseur par la version factice
    server.analyzer.analyze = fake_analyze

    # Lancer la génération en mode auto-approval pour éviter prompts
    print("Lancement du test de génération d'agent (auto-approve=True)")
    result = server.process_request("Créer un agent de test.", auto_approve=True)

    print("\nRésultat de la génération (résumé):")
    print(json.dumps({
        'status': result.get('status'),
        'agent_name': result.get('agent_name'),
        'files': {k: str(v) for k, v in result.get('files', {}).items()} if result.get('files') else {}
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
