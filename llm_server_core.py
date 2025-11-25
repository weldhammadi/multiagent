"""Clean core module for prompt generation tests.

Provides minimal dataclasses and an AgentAssembler with the
`_generate_execution_prompt` method needed by the unit tests.
This file intentionally contains a small, dependency-free implementation
so tests can import and exercise prompt generation reliably.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any


class AgentType(Enum):
    DATA_PROCESSOR = "data_processor"
    WEB_SCRAPER = "web_scraper"
    API_CONSUMER = "api_consumer"
    FILE_MANAGER = "file_manager"
    AI_ASSISTANT = "ai_assistant"
    CUSTOM = "custom"


@dataclass
class AgentRequirements:
    role: str
    description: str
    agent_type: AgentType
    objectives: List[str]
    tools_needed: List[Dict[str, Any]]
    models_needed: List[Dict[str, Any]]
    constraints: List[str]
    input_format: str
    output_format: str


@dataclass
class ExecutionPlan:
    agent_requirements: AgentRequirements
    tools_to_generate: List[Dict[str, Any]]
    models_to_configure: List[Dict[str, Any]]
    dependencies: List[str]
    architecture_type: str
    estimated_complexity: str


class AgentAssembler:
    """Assemble des prompts pour un agent principal.

    Seule la méthode `_generate_execution_prompt` est implémentée car elle
    est nécessaire aux tests unitaires fournis.
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def _generate_execution_prompt(self, plan: ExecutionPlan) -> str:
        """Génère un prompt système à partir d'un `ExecutionPlan`.

        Le prompt contient: identité, objectifs, outils disponibles, modèles,
        format de sortie, règles de base et un exemple.
        """
        req = plan.agent_requirements

        identity = f"Tu es {req.role} - {req.description}"

        objectives = "\n".join(f"- {o}" for o in (req.objectives or []))
        if not objectives:
            objectives = "- Réaliser la tâche demandée"

        if req.tools_needed:
            tools_section = "\n".join(
                f"- {t.get('name')}({', '.join(t.get('params', []))}) -> {t.get('returns', 'Any')}: {t.get('description', '')}"
                for t in req.tools_needed
            )
        else:
            tools_section = "Aucun outil externe disponible."

        if req.models_needed:
            models_section = "\n".join(
                f"- {m.get('purpose', '')} ({m.get('model_type', m.get('model', 'llm'))}) via {m.get('provider', '')}"
                for m in req.models_needed
            )
        else:
            models_section = "Aucun modèle externe requis."

        tone = "technique et concis"
        if req.agent_type == AgentType.AI_ASSISTANT:
            tone = "conversationnel mais précis"

        output_format = (req.output_format or "json").lower()
        if output_format == "json":
            format_example = '{"status": "success|error", "data": <result>, "error": null}'
        else:
            format_example = f"Format attendu: {req.output_format}"

        rules = [
            "Valide et nettoie les données d'entrée.",
            "Sois concis et donne des réponses exploitables.",
            "Ne pas exécuter de code arbitraire fourni par l'utilisateur sans validation.",
        ]

        prompt_parts = [
            identity,
            "\nOBJECTIFS:",
            objectives,
            "\nOUTILS DISPONIBLES:",
            tools_section,
            "\nMODÈLES:",
            models_section,
            "\nTON & RÈGLES:",
            f"Ton attendu: {tone}",
            "\nRÈGLES:",
            "\n".join(rules),
            "\nFORMAT DE SORTIE:",
            format_example,
            "\nEXEMPLE:",
            f"Input: {{\"example\": \"valeur\"}} -> Output: {format_example}",
        ]

        prompt = "\n\n".join(prompt_parts)
        return prompt
