# 🧠 Interpretation Agent

Cet agent est le "cerveau" du système multi-agents. Il est responsable de comprendre les demandes de l'utilisateur (texte ou voix) et de les transformer en une spécification technique structurée (`AgentSpec`) que d'autres agents pourront exécuter.

## 🚀 Fonctionnalités

*   **Conversation Gateway** : Un assistant conversationnel qui discute avec l'utilisateur pour affiner son besoin avant de lancer l'interprétation.
*   **Analyse du langage naturel** : Comprend les intentions de l'utilisateur.
*   **Structuration** : Génère un JSON standardisé définissant le but, les entrées, les sorties et les contraintes de l'agent demandé.
*   **Architecture Hexagonale** : Code propre, testable et découplé.

## 🛠️ Installation

1.  **Prérequis** : Python 3.10+
2.  **Cloner le projet** (si ce n'est pas déjà fait).
3.  **Installer les dépendances** :
    ```bash
    pip install -r interpretation_service/requirements.txt
    ```
4.  **Configuration** :
    *   Copiez `.env.example` vers `.env`.
    *   Ajoutez votre clé API Groq dans `.env` :
        ```env
        GROQ_API_KEY=gsk_...
        GROQ_MODEL=llama3-70b-8192
        ```

## 🎮 Utilisation

Il y a trois façons d'interagir avec l'agent :

### 1. Interface Web (Recommandé)

C'est la méthode la plus conviviale, incluant le chat multi-tours.

1.  Lancez le serveur API :
    ```bash
    python -m uvicorn interpretation_service.interfaces.api.http_api:app --reload
    ```
2.  Ouvrez le fichier `interpretation_service/interfaces/api/static/index.html` dans votre navigateur.
3.  Discutez avec l'assistant !

### 2. API HTTP

Pour intégrer l'agent dans d'autres systèmes.

#### Endpoint de Chat (Conversation Gateway)
*   **Endpoint** : `POST /chat`
*   **Payload** :
    ```json
    {
      "session_id": "session_123",
      "user_id": "user_123",
      "message": "Je veux un agent qui surveille le prix du Bitcoin",
      "metadata": {}
    }
    ```
*   **Réponse** :
    ```json
    {
      "session_id": "session_123",
      "reply": "D'accord, sur quelle plateforme voulez-vous surveiller le prix ?",
      "done": false,
      "agent_spec": null
    }
    ```
    (Quand `done` est `true`, `agent_spec` contient la spécification finale).

#### Endpoint d'Interprétation Directe (Core)
*   **Endpoint** : `POST /interpret`
*   **Payload** :
    ```json
    {
      "user_id": "user_123",
      "text": "Résumé complet du besoin...",
      "metadata": {}
    }
    ```

### 3. Ligne de Commande (CLI)

Pour tester rapidement le moteur d'interprétation sans le chat.

```bash
python -m interpretation_service.interfaces.cli.simulate_request
```

## 🏗️ Architecture

Le projet suit l'architecture hexagonale (Ports & Adapters) :

*   `domain/` : Modèles (`conversation_models.py`, `models.py`) et logique métier pure.
*   `application/` :
    *   `conversation/` : Service de gestion du chat (`ConversationAgentService`).
    *   `services/` : Service d'interprétation (`RequestInterpreterService`).
*   `ports/` : Interfaces abstraites (pour le LLM, le STT, le Bus, la Mémoire).
*   `infrastructure/` : Implémentations concrètes (Groq, In-Memory, etc.).
*   `interfaces/` : Points d'entrée (CLI, API HTTP).
