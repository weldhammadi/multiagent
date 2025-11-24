from typing import List

from interpretation_service.ports.llm_port import ILLMProvider
from interpretation_service.domain.models import NormalizedInput, AgentSpec, IOField


class MockLLMProvider(ILLMProvider):
    """
    Implémentation mock du LLM.
    Ne fait qu'une structuration simple et déterministe
    pour tester le pipeline end-to-end.
    """

    async def analyze_and_structure(self, input_data: NormalizedInput) -> AgentSpec:
        text = input_data.text.lower()

        if "email" in text or "mail" in text:
            agent_purpose = "Email Monitor"
            high_level_goal = "Surveiller les emails entrants et générer des alertes."
            inputs: List[IOField] = [
                IOField(
                    name="email_credentials",
                    type="secure_string",
                    description="Identifiants de la boîte mail à surveiller.",
                )
            ]
            outputs: List[IOField] = [
                IOField(
                    name="alert_summary",
                    type="string",
                    description="Résumé des emails importants détectés.",
                )
            ]
            success_criteria = [
                "Les emails sont vérifiés régulièrement.",
                "Les alertes sont générées pour les messages importants.",
            ]
        else:
            agent_purpose = "Generic Agent"
            high_level_goal = "Automatiser la tâche décrite par l'utilisateur."
            inputs = [
                IOField(
                    name="input_data",
                    type="string",
                    description="Données d'entrée à traiter.",
                )
            ]
            outputs = [
                IOField(
                    name="result",
                    type="string",
                    description="Résultat de l'automatisation.",
                )
            ]
            success_criteria = ["La tâche est exécutée correctement."]

        return AgentSpec(
            agent_purpose=agent_purpose,
            high_level_goal=high_level_goal,
            inputs=inputs,
            outputs=outputs,
            constraints=[],
            success_criteria=success_criteria,
            needs_clarification=False,
        )

