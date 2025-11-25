import requests
import streamlit as st
import uuid

# Agent 1 (Chat) endpoint
CHAT_API_URL = "http://localhost:8000/api/chat"

st.set_page_config(page_title="Agent Chat", page_icon="🤖")

st.title("🤖 Agent Chat - Créateur d'Agents")

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_spec" not in st.session_state:
    st.session_state.agent_spec = None

user_id = st.text_input("User ID", "yacine", key="user_id")

st.write(f"Session ID : `{st.session_state.session_id}`")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Display AgentSpec if generated
if st.session_state.agent_spec:
    with st.expander("✅ AgentSpec généré", expanded=True):
        st.json(st.session_state.agent_spec)

# Chat input
if prompt := st.chat_input("Décris ce que tu veux automatiser..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Call Agent 1 (Chat)
    try:
        response = requests.post(
            CHAT_API_URL,
            json={
                "session_id": st.session_state.session_id,
                "user_id": user_id,
                "message": prompt
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Add assistant message to chat
            assistant_message = data["message"]
            st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            
            with st.chat_message("assistant"):
                st.write(assistant_message)
            
            # If AgentSpec was generated, store it
            if data.get("agent_spec"):
                st.session_state.agent_spec = data["agent_spec"]
                st.rerun()
        else:
            st.error(f"Erreur API: {response.status_code} - {response.text}")
    except Exception as e:
        st.error(f"Erreur de connexion: {e}")
        st.info("Assure-toi que l'API est lancée : `python run_api.py`")

# Sidebar info
with st.sidebar:
    st.header("ℹ️ À propos")
    st.write("""
    Cette interface te permet de discuter avec **Agent 1** (Chat UX).
    
    L'agent va :
    1. 💬 Clarifier ton besoin
    2. ❓ Poser des questions
    3. ✅ Générer un AgentSpec quand c'est clair
    
    L'AgentSpec est créé par **Agent 2** (Interpretation Service).
    """)
    
    if st.button("🔄 Nouvelle conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.agent_spec = None
        st.rerun()
