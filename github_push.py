# git_push.py
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

GIT_REMOTE = os.getenv("GIT_REMOTE", "origin")
BRANCH_NAME = os.getenv("GITHUB_BRANCH", "mohamed")
GIT_CWD = Path(os.getenv("GIT_CWD", Path.cwd()))  # répertoire du repo

# Fichiers typiques d'un agent à pousser
AGENT_FILES = [
    "src/source_code.py",
    "config/prompt.txt",
    "config/settings.json",
    "config/llm.json",
    "requirements.txt",
    "app.py",
    "README.md",
]


def run_cmd(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> Tuple[int, str, str]:
    """Exécute une commande shell et retourne (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def ensure_git_repo(cwd: Path) -> bool:
    """Vérifie que cwd contient un dépôt Git."""
    try:
        _, out, _ = run_cmd(["git", "rev-parse", "--is-inside-work-tree"], cwd)
        return out == "true"
    except subprocess.CalledProcessError:
        return False


def get_current_branch(cwd: Path) -> Optional[str]:
    try:
        _, out, _ = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd)
        return out
    except subprocess.CalledProcessError:
        return None


def switch_or_create_branch(branch: str, cwd: Path) -> None:
    """Se place sur la branche, la crée si elle n'existe pas localement."""
    # Existe localement ?
    rc, _, _ = run_cmd(["git", "rev-parse", "--verify", branch], cwd, check=False)
    if rc == 0:
        run_cmd(["git", "checkout", branch], cwd)
        return
    # Essaye de suivre la branche distante si elle existe
    rc, _, _ = run_cmd(["git", "ls-remote", "--heads", GIT_REMOTE, branch], cwd, check=False)
    if rc == 0:
        run_cmd(["git", "checkout", "-B", branch, f"{GIT_REMOTE}/{branch}"], cwd)
    else:
        run_cmd(["git", "checkout", "-b", branch], cwd)


def has_changes(cwd: Path) -> bool:
    """Vérifie s'il y a des changements à commit."""
    # Index ou worktree modifiés
    _, out, _ = run_cmd(["git", "status", "--porcelain"], cwd)
    return len(out.strip()) > 0


def stage_paths(paths: List[Path], cwd: Path) -> None:
    """Ajoute des chemins au staging. Ignore ceux qui n'existent pas."""
    added = False
    for p in paths:
        if p.exists():
            run_cmd(["git", "add", str(p)], cwd)
            added = True
        else:
            print(f"Fichier manquant (non ajouté) : {p}")
    if not added:
        # Fallback: si rien n'a été ajouté explicitement, on ajoute tout
        run_cmd(["git", "add", "."], cwd)


def commit_and_push(message: str, branch: str, cwd: Path, dry_run: bool = False) -> bool:
    """Effectue le commit et pousse sur le remote. Retourne True si succès."""
    if not has_changes(cwd):
        print("Aucun changement à commit. Push ignoré.")
        return True  # pas une erreur fonctionnelle

    try:
        run_cmd(["git", "commit", "-m", message], cwd)
        if dry_run:
            print(f"Dry-run activé. Commit effectué localement, push non exécuté.")
            return True
        # S’assure qu'on est sur la bonne branche
        current = get_current_branch(cwd)
        if current != branch:
            switch_or_create_branch(branch, cwd)
        run_cmd(["git", "push", GIT_REMOTE, branch], cwd)
        print(f"Push effectué sur {GIT_REMOTE}/{branch}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du commit/push: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        return False


def push_project(commit_message: str = "Mise à jour complète du projet multi-agents",
                 branch: Optional[str] = None,
                 dry_run: bool = False) -> bool:
    """Push global du projet principal."""
    branch = branch or BRANCH_NAME
    if not ensure_git_repo(GIT_CWD):
        print(f"Le répertoire {GIT_CWD} n'est pas un dépôt Git.")
        return False

    try:
        # Stage global
        run_cmd(["git", "add", "."], GIT_CWD)
        return commit_and_push(commit_message, branch, GIT_CWD, dry_run=dry_run)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du push global: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        return False


def push_agent_output(agent_name: str,
                      commit_message: Optional[str] = None,
                      branch: Optional[str] = None,
                      dry_run: bool = False) -> bool:
    """Push uniquement les fichiers générés par un agent spécifique."""
    branch = branch or BRANCH_NAME
    agent_path = GIT_CWD / "agents_output" / agent_name
    commit_message = commit_message or f"Ajout sortie agent {agent_name}"

    if not ensure_git_repo(GIT_CWD):
        print(f"Le répertoire {GIT_CWD} n'est pas un dépôt Git.")
        return False

    if not agent_path.exists() or not agent_path.is_dir():
        print(f"Le dossier {agent_path} n'existe pas.")
        return False

    try:
        # Stage fichiers ciblés s'ils existent
        to_stage = [agent_path / f for f in AGENT_FILES]
        stage_paths(to_stage, GIT_CWD)

        return commit_and_push(commit_message, branch, GIT_CWD, dry_run=dry_run)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors du push de l'agent {agent_name}: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}")
        return False


if __name__ == "__main__":
    # Push global
    push_project("Mise à jour complète du projet multi-agents")

    # Push séparé pour chaque agent généré
    agents_dir = GIT_CWD / "output"
    if agents_dir.exists():
        for agent_name in os.listdir(agents_dir):
            agent_path = agents_dir / agent_name
            if agent_path.is_dir():
                push_agent_output(agent_name)