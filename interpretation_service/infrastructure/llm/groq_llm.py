import json
from typing import Dict, Any

import httpx

from interpretation_service.ports.llm_port import ILLMProvider
from interpretation_service.domain.models import NormalizedInput, AgentSpec
from interpretation_service.infrastructure.config.settings import settings


class GroqLLMProvider(ILLMProvider):
    """
    Implémentation du provider LLM utilisant Groq (API compatible OpenAI).
    """

    async def analyze_and_structure(self, input_data: NormalizedInput) -> AgentSpec:
        system_prompt = """
        Tu es un analyseur expert. Tu dois convertir la demande utilisateur
        en un JSON *strict* respectant exactement cette structure :
        {
          "agent_purpose": "...",
          "high_level_goal": "...",
          "inputs": [
            {"name": "...", "type": "...", "description": "..."}
          ],
          "outputs": [
            {"name": "...", "type": "...", "description": "..."}
          ],
          "constraints": ["..."],
          "success_criteria": ["..."],
          "needs_clarification": false,
          "clarification_question": null
        }
        Retourne *uniquement* ce JSON, sans texte autour.
        """.strip()

        user_prompt = f"""
        Texte utilisateur:
        "{input_data.text}"

        Contexte utilisateur :
        {json.dumps(input_data.user_context, indent=2, ensure_ascii=False)}
        """.strip()

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
        }

        payload: Dict[str, Any] = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.groq_api_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            result = response.json()

        raw_json = result["choices"][0]["message"]["content"]
        data = json.loads(raw_json)
        return AgentSpec(**data)

