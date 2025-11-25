import streamlit as st
from orchestrator import orchestrate
from github_push import push_project

st.set_page_config(page_title="Multi-Agents Orchestrator", layout="wide")
st.title("Multi-Agents Tester")

# Zone de saisie utilisateur
user_input = st.text_area("Entrez votre demande :", placeholder="Décrivez la tâche à réaliser")

if st.button("Lancer les agents"):
    if user_input.strip():
        with st.spinner("Exécution des agents..."):
            try:
                # Agent_output minimal pour lancer l'orchestration
                agent_output = {
                    "source_code": "# Code généré par défaut",
                    "fonction": {
                        "nom": "fonction_test",
                        "input": ["param1"],
                        "output": ["resultat"],
                        "descriptif": "Fonction de test générée par orchestrateur"
                    }
                }

                # Exécution de l'orchestration
                result = orchestrate(user_input, agent_output)

                st.success("Orchestration terminée avec succès.")
                st.write("Résultat brut :", result)

                # Optionnel : push automatique après orchestration
                if st.checkbox("Pousser automatiquement sur GitHub après orchestration"):
                    success = push_project("Mise à jour automatique après orchestration")
                    if success:
                        st.success("Push GitHub effectué avec succès.")
                    else:
                        st.error("Échec du push GitHub.")

            except Exception as e:
                st.error(f"Erreur lors de l'exécution des agents : {e}")
    else:
        st.warning("Veuillez entrer une demande avant de lancer les agents.")