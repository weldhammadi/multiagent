"""
Agent d'Outils v2 - Recherche GitHub + Génération LLM

Workflow:
1. Recherche sur GitHub si un outil similaire existe (DÉSACTIVÉ TEMPORAIREMENT)
2. Si trouvé → Clone + CSV + Arrêt (pas de LLM)
3. Si aucun résultat pertinent → Génération via Groq LLM
"""

import json
import os 
import sys
from pathlib import Path
from typing import Dict, Any, List
from dotenv import load_dotenv

# Chargement des variables .env
load_dotenv()

# === IMPORTS DE L'ARCHITECTURE EXISTANTE ===
from llm_client import GroqClient
from agents.generator import ToolGenerator
from agents.validator import validate_tool_response
from agents.github_searcher import GitHubSearcher


# ======================================================
#  CONFIGURATION
# ======================================================
ENABLE_GITHUB_SEARCH = False  # ⚙️ Mettre à True pour réactiver GitHub


# ======================================================
#  UTILS
# ======================================================
def load_file_content(file_path: Path) -> str:
    """Charge le contenu d'un fichier texte."""
    try:
        return file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"❌ Fichier introuvable: {file_path}") from exc
    except Exception as exc:
        raise RuntimeError(f"❌ Erreur lecture fichier {file_path}: {exc}") from exc


def parse_llm_response(response: str) -> Dict[str, Any]:
    """Nettoie et parse le JSON brut renvoyé par le LLM."""
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


def extract_search_keywords(user_prompt: str) -> str:
    """Extrait les mots-clés à partir du prompt utilisateur."""
    lines = user_prompt.split("\n")

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

    BAD_KEYWORDS = ["aucun", "pas trouvé", "non disponible", "n'a été", "n'a été"]
    if any(x in keywords.lower() for x in BAD_KEYWORDS):
        return "python utility tool"

    return keywords[:100]


# ======================================================
#  PHASE 1 : GITHUB (CONSERVÉ MAIS DÉSACTIVÉ)
# ======================================================
def search_github(searcher: GitHubSearcher, keywords: str, output_dir: Path) -> List[Dict[str, Any]]:
    print(f"\n🔍 Recherche sur GitHub avec: '{keywords}'")

    try:
        results = searcher.search_repositories(keywords, language="python", max_results=5)
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
            readme = searcher.get_readme(owner, name)
            preview = readme[:120].replace("\n", " ") if readme else "README indisponible"
            repo["readme_preview"] = preview
            print(f"    📄 README: {preview}")

    searcher.save_results_to_csv(results, output_dir / "github_search_results.csv")
    print("💾 Historique sauvegardé dans: output/github_search_results.csv")

    return results


def clone_best_repository(searcher: GitHubSearcher, repos: List[Dict[str, Any]], output_dir: Path) -> bool:
    best = max(repos, key=lambda r: r["stars"])
    print(f"\n🔥 Clone du repo le plus pertinent: {best['full_name']} ({best['stars']} ⭐)")

    dest = output_dir / "cloned_repos" / best["name"]
    success = searcher.clone_repository(best["clone_url"], dest)

    if success:
        print(f"🎉 Repo cloné dans: {dest}")
        return True

    print("⚠️ Clone échoué (git absent ou timeout)")
    return False


# ======================================================
#  PHASE 2 : LLM
# ======================================================
def generate_with_llm(user_prompt: str, output_dir: Path) -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("⚠️ Variable GROQ_API_KEY manquante dans .env")

    context = load_file_content(Path("prompts/tools_context.txt"))
    llm = GroqClient()
    response = llm.generate_tool(context=context, user_request=user_prompt)

    tool_data = parse_llm_response(response)
    errors = validate_tool_response(tool_data)

    if errors:
        raise ValueError(f"❌ Erreurs de validation tool : {errors}")

    generator = ToolGenerator(output_dir)
    name = tool_data["metadata"].get("nom", "tool")

    files = generator.save_tool(name, tool_data["source_code"], tool_data["metadata"])
    
    print("\n🎉 Outil généré par LLM !")
    print(f"📌 {files['python']}")
    print(f"📌 {files['metadata']}")
    
    # Affichage fichiers supplémentaires
    if "env" in files:
        print(f"🔐 {files['env']} (⚠️  À remplir manuellement)")
    
    if "config_files" in files:
        for config_name, config_path in files["config_files"].items():
            print(f"⚙️  {config_path} (⚠️  À remplir manuellement)")


# ======================================================
#  MAIN
# ======================================================
def main() -> None:
    print("🚀 Agent d'Outils v2 - Génération LLM")
    if ENABLE_GITHUB_SEARCH:
        print("🔍 Recherche GitHub : ACTIVÉE")
    else:
        print("⏸️  Recherche GitHub : DÉSACTIVÉE (génération directe)")
    print("=" * 60)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    user_prompt = load_file_content(Path("prompts/example_prompt.txt"))
    
    # Phase 1: GitHub (DÉSACTIVÉ TEMPORAIREMENT)
    if ENABLE_GITHUB_SEARCH:
        keywords = extract_search_keywords(user_prompt)
        results = search_github(GitHubSearcher(), keywords, output_dir)
        if results and clone_best_repository(GitHubSearcher(), results, output_dir):
            print("\n🎉 Outil trouvé sur GitHub. Fin.")
            return

    # Phase 2: LLM (toujours actif)
    if ENABLE_GITHUB_SEARCH:
        print("\n⚙️ Aucun outil trouvé. Génération via LLM...")
    else:
        print("\n⚙️ Génération directe via LLM...")
    
    generate_with_llm(user_prompt, output_dir)


if __name__ == "__main__":
    main()