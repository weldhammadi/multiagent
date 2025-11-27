# agents/llm_agent.py
import os
from typing import List, Dict, Any, Optional

# Petite simulation d'un LLM — remplace par OpenAI ou un autre modèle si tu veux
class LlmAgent:
    def __init__(self, model: Optional[str] = None):
        self.model = model or os.getenv("LLM_MODEL", "simulated")

    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        s = ""
        for it in history:
            s += f"{it.get('role','')}: {it.get('text','')}\n"
        return s

    def generate(self, user_id: str, message: str, history: List[Dict[str, Any]]) -> str:
        # Simulé : echo + résumé du nombre d'interactions
        hist_txt = self._format_history(history)
        return f"[LLM simulated response] Pour {user_id} — message: «{message}» — {len(history)} interactions précédentes.\nContexte:\n{hist_txt}"

    # Si tu veux brancher OpenAI, ajoute une méthode generate_openai ici (optionnelle)
