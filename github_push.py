import os
import subprocess

BRANCH_NAME = os.getenv("GITHUB_BRANCH", "mohamed")  # Branche par défaut

# Fichiers typiques d'un agent à pousser
AGENT_FILES = [
    "src/source_code.py",
    "config/prompt.txt",
    "config/settings.json",
    "config/llm.json",
    "requirements.txt",
    "app.py",
    "README.md"
]

def push_project(commit_message: str = "Mise à jour complète du projet multi-agents") -> bool:
    """Push global du projet principal."""
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", BRANCH_NAME], check=True)
        print(f"Projet principal poussé avec succès sur la branche {BRANCH_NAME}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du push global : {e}")
        return False

def push_agent_output(agent_name: str, commit_message: str = None) -> bool:
    """Push uniquement les fichiers générés par un agent spécifique."""
    agent_path = os.path.join("agents_output", agent_name)
    if commit_message is None:
        commit_message = f"Ajout sortie agent {agent_name}"

    try:
        if not os.path.exists(agent_path):
            print(f"Le dossier {agent_path} n'existe pas.")
            return False

        # Ajout des fichiers définis
        for file in AGENT_FILES:
            file_path = os.path.join(agent_path, file)
            if os.path.exists(file_path):
                subprocess.run(["git", "add", file_path], check=True)
                print(f"Fichier ajouté au commit : {file_path}")
            else:
                print(f"Fichier manquant (non ajouté) : {file_path}")

        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push", "origin", BRANCH_NAME], check=True)

        print(f"Agent {agent_name} poussé avec succès sur la branche {BRANCH_NAME}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du push de l'agent {agent_name} : {e}")
        return False

if __name__ == "__main__":
    # 1. Push global du projet principal
    push_project("Mise à jour complète du projet multi-agents")

    # 2. Push séparé pour chaque agent généré
    agents_dir = "agents_output"
    if os.path.exists(agents_dir):
        for agent_name in os.listdir(agents_dir):
            agent_path = os.path.join(agents_dir, agent_name)
            if os.path.isdir(agent_path):
                push_agent_output(agent_name)