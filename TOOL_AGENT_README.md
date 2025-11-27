# ToolAgent - Documentation API

Agent complet pour la génération et recherche d'outils Python.

---

## Installation

```python
from tool_agent import ToolAgent
```

**Dépendances requises:**
```bash
pip install requests python-dotenv groq
```

**Variables d'environnement (.env):**
```
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_token  # Optionnel, pour augmenter les limites API
```

---

## Constructeur

### `ToolAgent.__init__(...)`

Initialise l'agent avec la configuration.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `output_dir` | `str` | `"output"` | Répertoire de sortie pour les fichiers générés |
| `enable_github_search` | `bool` | `False` | Active la recherche GitHub avant génération LLM |
| `model` | `str` | `"openai/gpt-oss-120b"` | Modèle LLM à utiliser |
| `max_tokens` | `int` | `8000` | Limite de tokens en sortie |
| `temperature` | `float` | `0.1` | Température de génération (0.0-2.0) |
| `github_timeout` | `int` | `10` | Timeout pour les requêtes GitHub (secondes) |
| `llm_timeout` | `int` | `60` | Timeout pour les requêtes LLM (secondes) |

**Exemple:**
```python
agent = ToolAgent(
    output_dir="output",
    enable_github_search=True,
    temperature=0.2
)
```

---

## Méthodes Principales

### `run(...)`

Exécute le workflow complet de l'agent (recherche GitHub → génération LLM).

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `user_prompt` | `Optional[str]` | `None` | Prompt utilisateur (priorité sur prompt_file) |
| `prompt_file` | `Optional[Path]` | `None` | Fichier contenant le prompt |
| `context_file` | `Optional[Path]` | `None` | Fichier de contexte LLM |

**Retour:** `Dict[str, Any]`
```python
{
    "source": "github" | "llm",
    "data": {
        # Si source == "github":
        "repositories": [...],
        "cloned": {...}
        
        # Si source == "llm":
        "source_code": "...",
        "metadata": {...},
        "files": {...}
    }
}
```

**Exemple:**
```python
result = agent.run(user_prompt="Crée un outil de conversion CSV vers JSON")
print(result["source"])  # "llm" ou "github"
```

---

### `generate_tool(...)`

Génère un outil via LLM et le sauvegarde.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `user_prompt` | `str` | *requis* | Demande de l'utilisateur |
| `context_file` | `Optional[Path]` | `None` | Fichier de contexte (défaut: `prompts/tools_context.txt`) |

**Retour:** `Dict[str, Any]`
```python
{
    "source_code": "def my_tool(...):\n    ...",
    "metadata": {
        "nom": "my_tool",
        "description": "...",
        "inputs": {...},
        "output": "...",
        "dependencies": [...],
        "env_vars": [...]
    },
    "files": {
        "python": Path("output/my_tool.py"),
        "metadata": Path("output/my_tool_metadata.json"),
        "env": Path("output/my_tool.env"),  # Optionnel
        "config_files": {...}  # Optionnel
    }
}
```

**Exemple:**
```python
tool = agent.generate_tool("Crée une fonction qui télécharge une image depuis une URL")
print(tool["files"]["python"])
```

---

## Méthodes GitHub

### `search_repositories(...)`

Recherche des repositories sur GitHub.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `query` | `str` | *requis* | Mots-clés de recherche |
| `language` | `str` | `"python"` | Langage de programmation |
| `max_results` | `int` | `5` | Nombre max de résultats |

**Retour:** `List[Dict[str, Any]]`
```python
[
    {
        "name": "repo-name",
        "full_name": "owner/repo-name",
        "description": "Description du repo",
        "html_url": "https://github.com/owner/repo-name",
        "clone_url": "https://github.com/owner/repo-name.git",
        "stars": 1234,
        "language": "Python",
        "updated_at": "2024-01-15T10:30:00Z"
    },
    ...
]
```

**Exemple:**
```python
repos = agent.search_repositories("csv parser", max_results=10)
for repo in repos:
    print(f"{repo['full_name']} - {repo['stars']} ⭐")
```

---

### `get_readme(...)`

Récupère le contenu du README d'un repository.

| Paramètre | Type | Description |
|-----------|------|-------------|
| `owner` | `str` | Propriétaire du repo |
| `repo` | `str` | Nom du repo |

**Retour:** `Optional[str]` - Contenu du README ou `None` si non trouvé.

**Exemple:**
```python
readme = agent.get_readme("pandas-dev", "pandas")
if readme:
    print(readme[:500])
```

---

### `clone_repository(...)`

Clone un repository GitHub localement.

| Paramètre | Type | Description |
|-----------|------|-------------|
| `clone_url` | `str` | URL de clone du repo |
| `destination` | `Path` | Chemin de destination |

**Retour:** `bool` - `True` si succès, `False` sinon.

**Exemple:**
```python
success = agent.clone_repository(
    "https://github.com/owner/repo.git",
    Path("output/cloned_repos/repo")
)
```

---

### `save_search_results_to_csv(...)`

Sauvegarde les résultats de recherche dans un CSV.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `results` | `List[Dict[str, Any]]` | *requis* | Liste des repos trouvés |
| `csv_path` | `Optional[Path]` | `None` | Chemin du fichier CSV |

**Retour:** `Path` - Chemin du fichier CSV créé.

**Exemple:**
```python
repos = agent.search_repositories("web scraper")
csv_file = agent.save_search_results_to_csv(repos)
```

---

## Méthodes LLM

### `call_llm(...)`

Génère une réponse via le LLM Groq.

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `context` | `str` | *requis* | Contexte système (règles, format) |
| `user_request` | `str` | *requis* | Demande de l'utilisateur |
| `timeout` | `Optional[int]` | `None` | Timeout en secondes |

**Retour:** `str` - Réponse brute du LLM.

**Exemple:**
```python
response = agent.call_llm(
    context="Tu es un expert Python...",
    user_request="Génère une fonction de tri"
)
```

---

## Méthodes de Validation

### `validate_tool_response(...)` *(statique)*

Valide la structure d'un outil généré.

| Paramètre | Type | Description |
|-----------|------|-------------|
| `tool_data` | `Dict[str, Any]` | Dictionnaire avec `source_code` et `metadata` |

**Retour:** `List[str]` - Liste des erreurs (vide si valide).

**Structure attendue:**
```python
{
    "source_code": "def ...",  # Requis, non vide
    "metadata": {
        "nom": "tool_name",           # Requis, string non vide
        "description": "...",          # Requis, string non vide
        "inputs": {"param": "type"},   # Requis, dict
        "output": "type",              # Requis, string
        "dependencies": ["lib"],       # Optionnel, list[str]
        "env_vars": ["VAR"],           # Optionnel, list[str]
        "schema_output": {...},        # Optionnel, dict
        "config_files": ["file.json"]  # Optionnel, list[str]
    }
}
```

**Exemple:**
```python
errors = ToolAgent.validate_tool_response(tool_data)
if errors:
    print(f"Erreurs: {errors}")
```

---

## Méthodes de Sauvegarde

### `save_tool(...)`

Sauvegarde l'outil et ses métadonnées.

| Paramètre | Type | Description |
|-----------|------|-------------|
| `tool_name` | `str` | Nom de l'outil |
| `source_code` | `str` | Code Python source |
| `metadata` | `Dict[str, Any]` | Métadonnées JSON |

**Retour:** `Dict[str, Any]`
```python
{
    "python": Path("output/tool.py"),
    "metadata": Path("output/tool_metadata.json"),
    "env": Path("output/tool.env"),  # Si env_vars présent
    "config_files": {                 # Si config_files présent
        "config": Path("output/tool_config.json")
    }
}
```

**Exemple:**
```python
files = agent.save_tool(
    tool_name="csv_parser",
    source_code="def parse_csv(path): ...",
    metadata={"nom": "csv_parser", "description": "...", "inputs": {}, "output": "dict"}
)
```

---

## Méthodes Utilitaires

### `load_file_content(...)` *(statique)*

| Paramètre | Type | Description |
|-----------|------|-------------|
| `file_path` | `Path` | Chemin du fichier |

**Retour:** `str` - Contenu du fichier.

---

### `parse_llm_response(...)` *(statique)*

| Paramètre | Type | Description |
|-----------|------|-------------|
| `response` | `str` | Réponse brute du LLM |

**Retour:** `Dict[str, Any]` - JSON parsé avec `source_code` et `metadata`.

---

### `extract_search_keywords(...)` *(statique)*

| Paramètre | Type | Description |
|-----------|------|-------------|
| `user_prompt` | `str` | Prompt utilisateur |

**Retour:** `str` - Mots-clés extraits pour la recherche GitHub.

---

## Exemple Complet

```python
from tool_agent import ToolAgent
from pathlib import Path

# Initialisation
agent = ToolAgent(
    output_dir="output",
    enable_github_search=True,
    model="openai/gpt-oss-120b",
    temperature=0.1
)

# Workflow complet
result = agent.run(
    user_prompt="""
    Objectif: Créer un outil de conversion CSV vers JSON
    
    L'outil doit:
    - Lire un fichier CSV
    - Convertir en JSON
    - Sauvegarder le résultat
    """
)

if result["source"] == "github":
    print("Outil trouvé sur GitHub!")
    print(f"Repo: {result['data']['cloned']['full_name']}")
else:
    print("Outil généré par LLM!")
    print(f"Fichier: {result['data']['files']['python']}")
```

---

## Gestion des Erreurs

| Exception | Cause |
|-----------|-------|
| `RuntimeError` | GROQ_API_KEY manquante, erreur API, timeout |
| `ValueError` | JSON invalide, validation échouée |
| `FileNotFoundError` | Fichier de contexte/prompt introuvable |

```python
try:
    result = agent.run()
except RuntimeError as e:
    print(f"Erreur d'exécution: {e}")
except ValueError as e:
    print(f"Erreur de validation: {e}")
```
