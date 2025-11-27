import os
from typing import Dict, Optional, Any, List
from groq import Groq
import json
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

class AgentTestExecuteur:
    """
    Agent de test utilisant Groq Compound AI.
    NE CORRIGE PAS - renvoie juste le résultat du test en JSON.
    """
    
    def __init__(self, api_key: Optional[str] = None, use_mini: bool = False):
        """
        Initialise l'agent de test avec Groq Compound AI.
        
        Args:
            api_key: Clé API Groq (utilise GROQ_API_KEY si non fournie)
            use_mini: Si True, utilise compound-mini (plus rapide)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Clé API Groq requise!\n"
                "Option 1: export GROQ_API_KEY='votre_cle'\n"
                "Option 2: AgentTestExecuteur(api_key='votre_cle')\n"
                "Obtenir une clé: https://console.groq.com"
            )
        
        self.client = Groq(api_key=self.api_key)
        self.model = "groq/compound-mini" if use_mini else "groq/compound"
        
        print(f"✅ Agent initialisé avec {self.model}")
    
    def tester_agent(
        self,
        code_agent: str,
        description: str = "",
        test_cases: Optional[List[Dict[str, Any]]] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Teste un agent et renvoie le résultat en JSON.
        NE CORRIGE PAS LE CODE.
        
        Args:
            code_agent: Code Python de l'agent à tester
            description: Description de l'agent
            test_cases: Liste de cas de test
            timeout: Timeout en secondes
        
        Returns:
            Dict JSON avec:
            {
                "statut": "OK" | "ERREUR",
                "timestamp": "2025-01-01T12:00:00",
                "code_teste": "...",
                "description": "...",
                "resultats_tests": [...],
                "erreurs": [...] ou null,
                "message": "...",
                "execution_details": {...}
            }
        """
        print(f"\n{'='*70}")
        print(f"🔍 TEST DE L'AGENT AVEC GROQ COMPOUND AI")
        print(f"{'='*70}\n")
        
        # Initialiser le résultat JSON
        resultat_json = {
            "statut": "ERREUR",
            "timestamp": datetime.now().isoformat(),
            "code_teste": code_agent,
            "description": description,
            "resultats_tests": [],
            "erreurs": None,
            "message": "",
            "execution_details": {
                "model": self.model,
                "nombre_tests": len(test_cases) if test_cases else 0
            }
        }
        
        try:
            # Construire le prompt pour Compound
            prompt = self._construire_prompt_test(code_agent, description, test_cases)
            
            print(f"⚡ Exécution avec {self.model}...")
            
            # Appel à Compound AI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Tu es un testeur d'agent Python utilisant Compound AI.

IMPORTANT: Tu ne dois JAMAIS corriger le code. Tu testes uniquement.

Utilise l'exécution de code intégrée pour:
1. Exécuter le code de l'agent
2. Tester chaque cas de test
3. Capturer toutes les erreurs

Réponds UNIQUEMENT en JSON strict:
{
  "statut": "OK" ou "ERREUR",
  "tests_executes": nombre,
  "tests_reussis": nombre,
  "erreurs_detectees": ["liste des erreurs"] ou null,
  "output_execution": "sortie console",
  "message_final": "résumé"
}

NE PROPOSE AUCUNE CORRECTION. Rapporte juste les résultats."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.0,  # Déterministe
                max_tokens=8000
            )
            
            # Analyser la réponse
            content = response.choices[0].message.content
            print(f"✅ Réponse reçue de Compound\n")
            
            # Extraire le JSON de la réponse
            test_result = self._extraire_json(content)
            
            # Remplir le résultat final
            if test_result:
                resultat_json["statut"] = test_result.get("statut", "ERREUR")
                resultat_json["message"] = test_result.get("message_final", "")
                resultat_json["erreurs"] = test_result.get("erreurs_detectees")
                resultat_json["resultats_tests"] = {
                    "tests_executes": test_result.get("tests_executes", 0),
                    "tests_reussis": test_result.get("tests_reussis", 0),
                    "output": test_result.get("output_execution", "")
                }
            else:
                # Si pas de JSON, analyser le texte
                resultat_json = self._analyser_reponse_texte(content, resultat_json)
            
            # Ajouter les stats d'usage
            if hasattr(response, 'usage'):
                resultat_json["execution_details"]["tokens"] = {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                }
            
        except Exception as e:
            resultat_json["statut"] = "ERREUR"
            resultat_json["erreurs"] = [f"Erreur API: {str(e)}"]
            resultat_json["message"] = f"Échec de l'exécution: {str(e)}"
            print(f"❌ Erreur: {str(e)}")
        
        return resultat_json
    
    def sauvegarder_resultat(
        self,
        resultat: Dict[str, Any],
        fichier: str = "resultat_test.json"
    ) -> str:
        """
        Sauvegarde le résultat du test dans un fichier JSON.
        
        Returns:
            Chemin du fichier créé
        """
        with open(fichier, 'w', encoding='utf-8') as f:
            json.dump(resultat, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Résultat sauvegardé dans: {fichier}")
        return fichier
    
    def _construire_prompt_test(
        self,
        code: str,
        description: str,
        test_cases: Optional[List[Dict]]
    ) -> str:
        """Construit le prompt pour le test."""
        prompt = f"""# AGENT À TESTER (NE PAS CORRIGER)

## Description
{description if description else "Aucune description"}

## Code de l'agent
```python
{code}
```
"""
        
        if test_cases:
            prompt += "\n## Cas de test à exécuter\n"
            for i, test in enumerate(test_cases, 1):
                prompt += f"\nTest {i}:\n"
                if 'input' in test:
                    prompt += f"  Input: {test['input']}\n"
                if 'expected' in test:
                    prompt += f"  Expected: {test['expected']}\n"
                if 'description' in test:
                    prompt += f"  Description: {test['description']}\n"
        
        prompt += """

## MISSION
1. Exécute ce code avec l'outil d'exécution de code intégré
2. Teste chaque cas de test
3. Capture toutes les erreurs (syntaxe, runtime, logique)
4. NE PROPOSE AUCUNE CORRECTION
5. Renvoie un JSON avec les résultats

RAPPEL: Tu es un TESTEUR, pas un CORRECTEUR."""
        
        return prompt
    
    def _extraire_json(self, texte: str) -> Optional[Dict]:
        """Extrait le JSON de la réponse."""
        import re
        
        # Chercher un bloc JSON
        json_pattern = r'\{[\s\S]*?"statut"[\s\S]*?\}'
        matches = re.findall(json_pattern, texte)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        return None
    
    def _analyser_reponse_texte(
        self,
        content: str,
        resultat_base: Dict
    ) -> Dict:
        """Analyse la réponse textuelle si pas de JSON."""
        content_lower = content.lower()
        
        # Détection de succès
        if any(mot in content_lower for mot in ["ok", "succès", "passed", "réussi"]):
            resultat_base["statut"] = "OK"
            resultat_base["message"] = "Tous les tests sont passés"
        else:
            resultat_base["statut"] = "ERREUR"
            
            # Chercher les erreurs dans le texte
            erreurs = []
            for ligne in content.split('\n'):
                if any(mot in ligne.lower() for mot in ["error", "erreur", "exception", "traceback"]):
                    erreurs.append(ligne.strip())
            
            resultat_base["erreurs"] = erreurs if erreurs else ["Erreur détectée (voir message)"]
            resultat_base["message"] = content[:500]
        
        return resultat_base


# ============================================================================
# CODE DE TEST
# ============================================================================

def test_agent_exemple():
    """Fonction pour tester l'AgentTestExecuteur."""
    
    print("="*70)
    print("🧪 TEST DE L'AGENT TEST EXECUTEUR")
    print("="*70)
    
    # Code d'agent à tester (avec des erreurs volontaires)
    code_agent = """
def calculer_statistiques(nombres):
    \"\"\"Calcule des statistiques sur une liste de nombres.\"\"\"
    if not nombres:
        return {"erreur": "Liste vide"}
    
    total = sum(nombres)
    moyenne = total / len(nombres)
    maximum = max(nombres)
    minimum = min(nombres)
    
    return {
        "moyenne": moyenne,
        "total": total,
        "max": maximum,
        "min": minimum,
        "count": len(nombres)
    }

# Tests automatiques
print("Test 1:", calculer_statistiques([1, 2, 3, 4, 5]))
print("Test 2:", calculer_statistiques([10, 20, 30]))
print("Test 3:", calculer_statistiques([]))  # Doit gérer liste vide
print("Test 4:", calculer_statistiques([-5, 0, 5]))  # Nombres négatifs
"""
    
    # Cas de test
    test_cases = [
        {
            "input": "[1, 2, 3, 4, 5]",
            "expected": "moyenne=3, total=15, max=5, min=1",
            "description": "Liste normale de nombres positifs"
        },
        {
            "input": "[]",
            "expected": "Gestion d'erreur pour liste vide",
            "description": "Cas limite: liste vide"
        },
        {
            "input": "[-5, 0, 5]",
            "expected": "Gestion correcte des nombres négatifs",
            "description": "Nombres négatifs et zéro"
        }
    ]
    
    try:
        # Créer l'agent (va chercher GROQ_API_KEY automatiquement)
        agent = AgentTestExecuteur(use_mini=False)
        
        # Tester l'agent
        resultat = agent.tester_agent(
            code_agent=code_agent,
            description="Agent qui calcule des statistiques sur des nombres",
            test_cases=test_cases
        )
        
        # Afficher le résultat
        print("\n" + "="*70)
        print("📊 RÉSULTAT DU TEST")
        print("="*70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
        
        # Sauvegarder dans un fichier
        fichier = agent.sauvegarder_resultat(resultat, "resultat_test_agent.json")
        
        print(f"\n{'='*70}")
        print(f"✅ Test terminé!")
        print(f"📁 Résultat sauvegardé dans: {fichier}")
        print(f"{'='*70}\n")
        
        return resultat
        
    except ValueError as e:
        print(f"\n❌ ERREUR: {e}\n")
        print("📝 COMMENT CONFIGURER LA CLÉ API:")
        print("-" * 70)
        print("Option 1 - Variable d'environnement (recommandé):")
        print("  export GROQ_API_KEY='votre_cle_api_ici'")
        print("\nOption 2 - Dans le code:")
        print("  agent = AgentTestExecuteur(api_key='votre_cle_api_ici')")
        print("\nOption 3 - Fichier .env:")
        print("  Créer un fichier .env avec:")
        print("  GROQ_API_KEY=votre_cle_api_ici")
        print("\n🔑 Obtenir une clé gratuite:")
        print("  https://console.groq.com/keys")
        print("="*70 + "\n")
        return None


