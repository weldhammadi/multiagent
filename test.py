import os
from dotenv import load_dotenv

# Charger les variables de .env
load_dotenv()
from agents.agents_testeur import AgentTestExecuteur
import json

# 📌 Nom du fichier à tester
file_to_test = "test_hello.py"

# 📌 Lire le code du fichier
with open(file_to_test, "r", encoding="utf-8") as f:
    code_content = f.read()

# 📌 Créer l'agent testeur
agent = AgentTestExecuteur()

# 📌 Tester le code lu
result = agent.tester_agent(
    code_agent=code_content,
    description=f"Test automatique du fichier {file_to_test}",
    test_cases=None  # Tu peux laisser None si tu ne veux pas de test_cases
)

# 📌 Afficher le résultat à l’écran
print(json.dumps(result, indent=2, ensure_ascii=False))

# 📌 Sauvegarder le résultat dans un JSON
agent.sauvegarder_resultat(result, f"result_test_{file_to_test}.json")
