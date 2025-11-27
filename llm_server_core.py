import os
import json
import ast
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from groq import Groq

# On charge les variables d'environnement (.env)
load_dotenv()

class Orchestrator:
    """
    Le Cerveau du système.
    Responsabilités :
    1. Analyser la demande utilisateur (Routing).
    2. Choisir l'agent approprié (Tool ou Model).
    3. Valider le code généré via une exécution sécurisée.
    4. Faire appel au Debug Agent en cas d'erreur.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY manquante dans le fichier .env")
        
        self.client = Groq(api_key=self.api_key)
        
        # Configuration du modèle (Llama3-70b est excellent pour le code)
        self.model_name = "llama3-70b-8192" 

    def analyze_request(self, user_request: str) -> str:
        """
        DÉCISION (ROUTING) : Détermine si c'est une tâche pour l'agent OUTILS ou MODÈLES.
        """
        system_prompt = (
            "Tu es un routeur intelligent. Analyse la demande. "
            "Si la demande implique de créer une fonction utilitaire classique (maths, fichiers, traitement de texte), réponds 'TOOL'. "
            "Si la demande implique d'utiliser une IA, un prompt, ou du contexte sémantique, réponds 'MODEL'. "
            "Réponds UNIQUEMENT par le mot clé."
        )
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_request}
            ],
            model=self.model_name,
            temperature=0
        )
        return response.choices[0].message.content.strip().upper()

    def _simulate_agent_call(self, agent_type: str, request: str) -> Dict[str, Any]:
        """
        PLACEHOLDER : Ici, vous importerez vos vrais agents (agents/tool_agent.py, etc.)
        Pour l'instant, on simule leur réponse pour tester l'orchestrateur.
        """
        print(f"🔄 Appel à l'agent {agent_type} pour : {request}")
        
        # Simulation d'une réponse d'agent (Format JSON strict requis)
        # TODO: Remplacer ceci par : return tool_agent.generate(request)
        return {
            "source_code": "def ma_fonction():\n    print('Hello World')\n    return True",
            "fonction": {"nom": "ma_fonction", "input": "None", "output": "Bool"}
        }

    def _test_code_validity(self, source_code: str) -> Optional[str]:
        """
        GATEKEEPER : Vérifie si le code est syntaxiquement correct.
        Retourne None si tout va bien, ou le message d'erreur (str) si ça plante.
        """
        try:
            # 1. Analyse syntaxique (ast) - Vérifie la structure sans exécuter
            ast.parse(source_code)
            
            # 2. Exécution contrôlée (optionnelle mais recommandée pour le runtime)
            # Attention : exec() est dangereux en prod, mais OK pour un projet local contrôlé.
            context = {}
            exec(source_code, context)
            
            return None # Pas d'erreur
        except Exception as e:
            return str(e)

    def _debug_loop(self, failed_code: str, error_msg: str) -> Dict[str, Any]:
        """
        AGENT DE DEBUG (Orange) : Tente de réparer le code.
        """
        print(f"🛠️ DÉTECTION D'ERREUR : {error_msg}. L'agent de Debug prend le relais...")
        
        prompt = f"""
        Le code suivant contient une erreur :
        CODE:
        {failed_code}
        
        ERREUR:
        {error_msg}
        
        Corrige le code. Renvoie UNIQUEMENT le code Python corrigé dans un bloc json formaté ainsi :
        {{"source_code": "..."}}
        """
        
        response = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Tu es un expert en débogage Python. Tu réponds en JSON pur."},
                {"role": "user", "content": prompt}
            ],
            model=self.model_name,
            response_format={"type": "json_object"} # Force le JSON (Feature Groq)
        )
        
        return json.loads(response.choices[0].message.content)

    def run_workflow(self, user_request: str):
        print(f"🚀 Démarrage du workflow pour : '{user_request}'")
        
        # 1. ROUTING
        agent_type = self.analyze_request(user_request)
        print(f"👉 Route choisie : {agent_type}")
        
        # 2. GÉNÉRATION
        # Note: Dans la version finale, importez vos classes Agent ici
        agent_output = self._simulate_agent_call(agent_type, user_request)
        current_code = agent_output.get("source_code", "")
        
        # 3. BOUCLE DE VALIDATION (Max 3 essais)
        max_retries = 3
        is_valid = False
        
        for attempt in range(max_retries):
            error = self._test_code_validity(current_code)
            
            if error is None:
                print("✅ Code validé avec succès !")
                is_valid = True
                break
            else:
                print(f"❌ Échec essai {attempt + 1}/{max_retries}")
                # Appel au Debug Agent
                correction = self._debug_loop(current_code, error)
                current_code = correction.get("source_code", current_code)

        # 4. RESULTAT FINAL
        if is_valid:
            # Ici, on renverrait vers github_push.py
            return {
                "status": "success",
                "final_code": current_code,
                "type": agent_type
            }
        else:
            return {
                "status": "failure",
                "error": "Impossible de générer un code fonctionnel après 3 essais."
            }

# Pour tester directement le fichier (python core/orchestrator.py)
if __name__ == "__main__":
    orchestrator = Orchestrator()
    result = orchestrator.run_workflow("Crée une fonction qui calcule la suite de Fibonacci")
    print("\n--- RÉSULTAT FINAL ---")
    print(json.dumps(result, indent=2))
 