import os
import json
import ast
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv
from groq import Groq

# Chargement des variables d'environnement (.env)
load_dotenv()

# -------------------------------------------------------------------
# Définition des classes AgentSpec
# -------------------------------------------------------------------

@dataclass
class InputSpec:
    name: str
    type: str
    description: str

@dataclass
class OutputSpec:
    name: str
    type: str
    description: str

@dataclass
class AgentSpec:
    request_id: str
    user_id: str
    agent_purpose: str
    high_level_goal: str
    agent_type: str                    # "TOOL_CREATOR" | "MODEL_USER" | "DEBUGGER"
    routing_decision: str              # "TOOL" | "MODEL" | "DEBUG"
    confidence: str                    # "faible" | "moyenne" | "élevée"
    inputs: List[InputSpec] = field(default_factory=list)
    outputs: List[OutputSpec] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    status: str = "created"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @staticmethod
    def from_json(data: Dict[str, Any]) -> "AgentSpec":
        spec = data.get("spec", {})
        return AgentSpec(
            request_id=data.get("request_id", str(uuid.uuid4())),
            user_id=data.get("user_id", "anonymous"),
            agent_purpose=spec.get("agent_purpose", ""),
            high_level_goal=spec.get("high_level_goal", ""),
            agent_type=spec.get("agent_type", ""),
            routing_decision=spec.get("routing_decision", ""),
            confidence=spec.get("confidence", "moyenne"),
            inputs=[InputSpec(**inp) for inp in spec.get("inputs", [])],
            outputs=[OutputSpec(**out) for out in spec.get("outputs", [])],
            constraints=spec.get("constraints", []),
            success_criteria=spec.get("success_criteria", []),
            needs_clarification=spec.get("needs_clarification", False),
            clarification_question=spec.get("clarification_question"),
            status=data.get("status", data.get("status", "created")),
            created_at=data.get("created_at", datetime.utcnow().isoformat())
        )

    def to_json(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "spec": {
                "agent_purpose": self.agent_purpose,
                "high_level_goal": self.high_level_goal,
                "agent_type": self.agent_type,
                "routing_decision": self.routing_decision,
                "confidence": self.confidence,
                "inputs": [inp.__dict__ for inp in self.inputs],
                "outputs": [out.__dict__ for out in self.outputs],
                "constraints": self.constraints,
                "success_criteria": self.success_criteria,
                "needs_clarification": self.needs_clarification,
                "clarification_question": self.clarification_question
            },
            "status": self.status,
            "created_at": self.created_at
        }

# -------------------------------------------------------------------
# Orchestrateur
# -------------------------------------------------------------------

class Orchestrator:
    """
    Le Cerveau du système.
    Responsabilités :
    1. Analyser la demande utilisateur et générer un AgentSpec JSON enrichi.
    2. Choisir l'agent approprié (TOOL, MODEL ou DEBUG).
    3. Générer et valider le code via une exécution contrôlée.
    4. Faire appel à l'agent de debug en cas d'erreur.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY manquante dans le fichier .env")
        self.client = Groq(api_key=self.api_key)
        # Ajustez le nom du modèle à votre configuration Groq
        self.model_name = "openai/gpt-oss-120b"

    def analyze_request(self, user_request: str, user_id: str = "anonymous") -> AgentSpec:
        """
        Analyse la demande et génère un AgentSpec JSON enrichi utilisable par le workflow.
        """
        system_prompt = (
            "Tu es le cerveau et l’orchestrateur d’un système multi-agents.\n"
            "Analyse la demande utilisateur et retourne un objet JSON strict décrivant l'AgentSpec.\n\n"
            "Format attendu :\n"
            "{\n"
            '  "request_id": "<uuid>",\n'
            f'  "user_id": "{user_id}",\n'
            '  "spec": {\n'
            '    "agent_purpose": "But précis de l’agent",\n'
            '    "high_level_goal": "Objectif global",\n'
            '    "agent_type": "TOOL_CREATOR | MODEL_USER | DEBUGGER",\n'
            '    "routing_decision": "TOOL | MODEL | DEBUG",\n'
            '    "confidence": "faible | moyenne | élevée",\n'
            '    "inputs": [ { "name": "...", "type": "...", "description": "..." } ],\n'
            '    "outputs": [ { "name": "...", "type": "...", "description": "..." } ],\n'
            '    "constraints": ["..."],\n'
            '    "success_criteria": ["..."],\n'
            '    "needs_clarification": false,\n'
            '    "clarification_question": null\n'
            '  },\n'
            '  "status": "created",\n'
            '  "created_at": "<timestamp ISO8601>"\n'
            "}\n\n"
            "Contraintes :\n"
            "- Réponds uniquement en JSON valide.\n"
            "- Pas de texte hors JSON."
        )

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            model=self.model_name,
            temperature=0,
            response_format={"type": "json_object"}
        )

        agent_spec_json = json.loads(response.choices[0].message.content)
        return AgentSpec.from_json(agent_spec_json)

    def _simulate_agent_call(self, agent_type: str, request: str) -> Dict[str, Any]:
        """
        Remplacez cette simulation par l'appel à vos vrais agents:
        - TOOL_CREATOR -> agents/tool_agent.py
        - MODEL_USER   -> agents/model_agent.py
        - DEBUGGER     -> agents/debug_agent.py
        """
        print(f"Appel à l'agent {agent_type} pour la requête: {request}")
        return {
            "source_code": "def ma_fonction():\n    print('Hello World')\n    return True",
            "fonction": {"nom": "ma_fonction", "input": "None", "output": "Bool"}
        }

    def _test_code_validity(self, source_code: str) -> Optional[str]:
        """
        Vérifie la validité syntaxique et exécute le code dans un contexte isolé.
        Attention: exec() ne doit pas exécuter de code non fiable en production.
        """
        try:
            ast.parse(source_code)
            context = {}
            exec(source_code, context)
            return None
        except Exception as e:
            return str(e)

    def _debug_loop(self, failed_code: str, error_msg: str) -> Dict[str, Any]:
        """
        Appel à l'agent de debug pour corriger le code et retourner un JSON:
        {"source_code": "<code corrigé>"}
        """
        print(f"Erreur détectée: {error_msg}. Passage à l'agent de debug.")
        prompt = f"""
        Le code suivant contient une erreur :
        CODE:
        {failed_code}

        ERREUR:
        {error_msg}

        Corrige le code. Renvoie uniquement le code Python corrigé dans un bloc JSON formaté ainsi :
        {{"source_code": "..."}}
        """

        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Tu es un expert en débogage Python. Tu réponds en JSON pur."},
                {"role": "user", "content": prompt}
            ],
            model=self.model_name,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def run_workflow(self, user_request: str, user_id: str = "anonymous") -> Dict[str, Any]:
        """
        Exécute le workflow complet:
        1) Analyse et génération d'AgentSpec,
        2) Appel de l'agent choisi,
        3) Validation et correction en boucle,
        4) Retour du résultat final et de l'AgentSpec.
        """
        print(f"Démarrage du workflow pour: '{user_request}'")

        # 1. Analyse et AgentSpec
        agent_spec = self.analyze_request(user_request, user_id)
        print(f"Décision: {agent_spec.routing_decision} | Agent: {agent_spec.agent_type} | Confiance: {agent_spec.confidence}")

        # 2. Génération par l'agent
        agent_output = self._simulate_agent_call(agent_spec.agent_type, user_request)
        current_code = agent_output.get("source_code", "")

        # 3. Validation et corrections (max 3 essais)
        max_retries = 3
        is_valid = False
        for attempt in range(max_retries):
            error = self._test_code_validity(current_code)
            if error is None:
                print("Code validé.")
                is_valid = True
                break
            print(f"Echec essai {attempt + 1}/{max_retries}: {error}")
            correction = self._debug_loop(current_code, error)
            current_code = correction.get("source_code", current_code)

        # 4. Résultat final
        result: Dict[str, Any]
        if is_valid:
            result = {
                "status": "success",
                "final_code": current_code,
                "agent_spec": agent_spec.to_json()
            }
        else:
            result = {
                "status": "failure",
                "error": "Impossible de générer un code fonctionnel après 3 essais.",
                "agent_spec": agent_spec.to_json()
            }
        return result

# Exécution directe pour test
if __name__ == "__main__":
    orchestrator = Orchestrator()
    output = orchestrator.run_workflow("Crée une fonction qui calcule la suite de Fibonacci", user_id="yacine")
    print("\n--- RÉSULTAT FINAL ---")
    print(json.dumps(output, indent=2, ensure_ascii=False))